# Architecture ImmoPilot

État au 5 septembre 2026, branche `refonte/fondation`.

Ce document décrit ce qui est en place et, surtout, ce qui est **préparé mais
volontairement inactif**. Un lecteur qui découvre le projet doit pouvoir
distinguer les deux sans lire le code.

---

## 1. Le principe directeur

L'application ne sert **qu'une seule entreprise aujourd'hui**. Toute
l'architecture est néanmoins pensée pour en servir plusieurs, sans réécriture
et sans migration destructive le jour venu.

Concrètement, cela se traduit par deux mécanismes distincts, à ne pas
confondre :

| Mécanisme | Portée | État |
|---|---|---|
| `organizations.Organization` | Les apps du projet (Proprietes, Locations, finance) | **Actif** |
| `entreprise_id` | Les modules préfabriqués (comptes, comptabilité, paie, RH) | **Préparé, inactif** |

Le premier fonctionne déjà et cloisonne réellement les données. Le second est
un champ en base, rempli avec la chaîne vide, qui n'a encore aucun effet.

---

## 2. Multi-tenant des apps du projet — actif

### Le mécanisme

`core/tenancy.py` porte l'organisation active dans un `ContextVar`, posé par
`core/middleware.py` à chaque requête et remis à zéro après la réponse.

Tout modèle métier hérite de `core.models.TenantOwnedModel`, qui apporte la
clé étrangère vers l'organisation et, surtout, un manager qui **filtre
d'office** :

```python
Property.objects.all()   # uniquement l'organisation active
Property.all_objects     # toutes, réservé à l'administration
```

Une requête hors contexte lève `NoActiveOrganization` plutôt que de tout
retourner. L'isolation ne dépend donc pas de ce qu'un développeur pense à
écrire dans chaque vue.

### Ce qui est déjà rattaché

- `Proprietes` : Property, Unit, PropertyImage
- `Locations` : Lease, LeaseTenant, Inspection
- `finance` : RentCharge, Payment, PaymentAllocation

### Ce qui ne l'est pas encore

`Maintenance`, `Documents` et `Comptabilite.Transaction` se raccrochent au
périmètre indirectement, via `Unit` ou via leur propre champ `owner`. C'est
fonctionnel et cloisonné, mais transitoire.

### Deux pièges rencontrés, à connaître

**Les formulaires.** Django construit les `ModelChoiceField` à l'import du
module, donc hors de toute requête. Un formulaire portant sur un modèle
tenant doit déclarer son queryset explicitement et hériter de
`core.forms.TenantModelForm`, qui retire le champ `organization` — sans quoi
une liste déroulante énumérerait toutes les organisations. Un test parcourt
les formulaires de toutes les apps pour faire respecter ce contrat.

**L'ordre middleware / DRF.** Le middleware s'exécute *avant* que DRF
n'authentifie le jeton : l'utilisateur y est encore anonyme. La résolution
est donc refaite dans la permission `IsOrganizationMember`.

---

## 3. Multi-entreprises des modules préfabriqués — préparé, inactif

### Pourquoi un mécanisme différent

Les quatre modules (`comptes`, `comptabilite_ohada`, `django_paie`,
`django_rh`) sont des paquets réutilisables, partagés avec d'autres projets.
Leur faire pointer une clé étrangère vers `organizations.Organization` les
rendrait dépendants de ce projet-ci.

Ils portent donc un `entreprise_id` : un `CharField` indexé, opaque, que le
projet hôte remplit comme il l'entend. C'est la convention que `django_paie`
employait déjà ; elle a été généralisée aux trois autres.

### Ce qui a été fait

- `entreprise_id` ajouté à `Compte`, `CompteComptable`, `EcritureComptable`,
  `JournalComptable`, `ExerciceComptable`, `Employee`, `Department`.
- Les unicités globales sont devenues des unicités **par entreprise** :
  `code`, `reference`. Deux entreprises pourront avoir chacune leur
  `CAISSE-01` ; auparavant la seconde aurait été rejetée.

### Ce qui n'a pas été fait, volontairement

Le champ reste vide partout. Aucun filtrage n'est appliqué. Les écrans n'ont
pas été touchés. En mono-entreprise, `entreprise_id = ''` pour toutes les
lignes, donc l'unicité composée se comporte **exactement** comme l'unicité
simple d'avant.

La chaîne vide plutôt que `NULL` est un choix délibéré : en SQL, `NULL` n'est
jamais égal à lui-même, ce qui laisserait passer des doublons.

### La bascule, le jour venu

Tout passe par `organizations/entreprise.py` :

1. Mettre `ACTIVER_MULTI_ENTREPRISES = True`.
2. Remplir `entreprise_id` sur les lignes existantes.
3. Faire passer les sélections des modules par `filtrer_par_entreprise()`.

Le code appelant est déjà écrit correctement : `entreprise_id_courant()`
renvoie la chaîne vide tant que l'interrupteur est à `False`.

---

## 4. Chaîne financière et comptable

```
RentCharge          ce que le locataire doit, pour une période
     ↓
Payment             ce qu'il a effectivement versé, en une fois
     ↓
PaymentAllocation   la part d'un versement imputée sur une échéance
     ↓
comptes.Compte      la caisse ou le compte mobile crédité
     ↓
EcritureComptable   l'écriture SYSCOHADA, en partie double
```

Un versement peut solder plusieurs échéances ; une échéance peut être soldée
par plusieurs versements. Le statut d'une échéance n'est jamais saisi : il
découle de ses imputations.

**Le compte encaisseur est obligatoire.** Sans lui, la somme n'entre dans
aucune trésorerie et ne produit aucune écriture : elle serait enregistrée
nulle part. Le service refuse la saisie (`compte_required`) et le formulaire
la rejette avant envoi.

Le passage de la finance à la comptabilité n'est pas un appel direct. Le
service financier crédite un compte ; `django-comptes` émet
`mouvement_valide` après commit ; `comptabilite_ohada` écoute ce signal et
produit l'écriture. Les deux domaines ne se connaissent pas.

**Conséquence à connaître** : le signal part sur `transaction.on_commit`.
Dans un `TestCase` Django la transaction n'est jamais validée, donc les tests
doivent employer `captureOnCommitCallbacks(execute=True)` pour voir
l'écriture apparaître.

### Bus d'événements interne

`core/events.py` distingue deux natures d'abonnés :

- **ordinaire** : sa défaillance est journalisée, l'opération se poursuit.
  Pour les notifications.
- **critique** (`subscribe(..., critical=True)`) : sa défaillance annule
  l'opération. Pour ce qui fait partie du fait métier lui-même.

Un abonné de notification qui tombe ne doit pas annuler un encaissement ;
une écriture comptable qui échoue, si.

---

## 5. Correctifs apportés aux modules préfabriqués

Ces défauts ont été constatés **par exécution**, pas par lecture. Ils sont
corrigés dans les paquets sources, donc bénéficient aux autres projets.

| Module | Défaut | Correctif |
|---|---|---|
| `comptabilite_ohada` | Une écriture 100 au débit / 40 au crédit était enregistrée **et marquée validée**. `est_equilibree` existait mais n'était jamais appelée. | Le service refuse toute écriture déséquilibrée, avant création. |
| `comptes` | `JournalCompteAdmin` sans `search_fields` alors qu'il est référencé en autocomplete : Django refusait de démarrer (`admin.E040`). | `search_fields` ajouté. |

### Limites connues, non corrigées

- **Portabilité.** Six des treize tests de `comptabilite_ohada` échouent sur
  `auth.User` codé en dur : les modules supposent le modèle utilisateur par
  défaut de Django. Échecs préexistants, sans rapport avec les correctifs
  ci-dessus, mais bloquants si ces tests doivent servir de garde-fou.
- **`comptes.get_comptes_permissions()`** filtre sur
  `codename__startswith="comptes_"` alors que les codenames déclarés sont
  `encaisser`, `decaisser`… La fonction ne renvoie donc jamais rien.
  `has_comptes_permission()` ne s'en sert pas, l'effet est limité.
- **L'équilibre n'est garanti qu'au niveau du service.** Une écriture créée
  directement par l'ORM peut toujours être déséquilibrée.

---

## 6. Permissions

Deux systèmes coexistent, reliés par `organizations/tresorerie.py`.

Les rôles d'organisation (`owner`, `manager`, `agent`, `accountant`) sont
hiérarchisés et gouvernent l'accès aux écrans du projet.

Les modules préfabriqués utilisent les permissions Django classiques. Sans
correspondance, un gestionnaire légitime se voyait refuser l'encaissement
d'un loyer. Le rôle est donc traduit en permissions concrètes à l'ajout d'un
membre et à chaque changement de rôle, selon le moindre privilège : un agent
encaisse, il ne clôture pas.

---

## 7. Une régularisation en attente

Deux encaissements créés avant l'intégration comptable (300 000 FCFA) ont été
rattachés à la caisse par la migration `finance/0003`, **sans mouvement de
trésorerie ni écriture** : une migration n'a pas à inventer des opérations
financières.

Le solde de la caisse ne reflète donc pas ces deux versements. Décider s'il
faut les régulariser — et à quelle date de valeur — est une décision métier,
pas technique.

---

## 8. Ce qui reste

- Rattacher `Maintenance`, `Documents` et `Transaction` à l'organisation.
- Supprimer l'app `Paiements`, dont plus aucune vue ne se sert (tables vides).
- Écrans des modules paie et RH : aucun n'a été créé, par décision.
- Front React sur `/api/v1/`.
- **Faire tourner les identifiants Neon** : ils sont sortis du code, mais
  restent dans l'historique Git d'un dépôt public.
