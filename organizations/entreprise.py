"""Raccord entre l'organisation et l'`entreprise_id` des modules metier.

Les modules prefabriques (comptes, comptabilite_ohada, django_paie,
django_rh) portent un champ `entreprise_id` : une chaine opaque, et non
une cle etrangere, pour rester utilisables sans connaitre le modele
d'organisation du projet hote.

Aujourd'hui l'application ne sert qu'une entreprise : le champ reste vide
partout, et les modules se comportent exactement comme avant. Le jour ou
plusieurs entreprises coexisteront, il suffira de :

  1. mettre ACTIVER_MULTI_ENTREPRISES a True ;
  2. remplir `entreprise_id` sur les lignes existantes avec
     `entreprise_id_courant()` ;
  3. filtrer les selections des modules sur cette valeur.

Rien de tout cela n'est branche pour l'instant, volontairement : le
schema est pret, le comportement est inchange.
"""
from core.tenancy import get_current_organization_id

# Interrupteur unique du passage au multi-entreprises. Laisse a False tant
# que l'application ne sert qu'une entreprise.
ACTIVER_MULTI_ENTREPRISES = False

# Valeur employee en mono-entreprise. La chaine vide, et non None, pour
# que la contrainte d'unicite (entreprise_id, code) se comporte comme
# l'unicite simple d'avant : NULL n'est jamais egal a lui-meme en SQL,
# ce qui laisserait passer des doublons.
ENTREPRISE_UNIQUE = ''


def entreprise_id_courant():
    """Identifiant d'entreprise a inscrire sur les lignes des modules.

    Renvoie la chaine vide tant que le multi-entreprises n'est pas active,
    de sorte que tout le code appelant est deja ecrit correctement le jour
    de la bascule.
    """
    if not ACTIVER_MULTI_ENTREPRISES:
        return ENTREPRISE_UNIQUE

    organisation_id = get_current_organization_id()
    return str(organisation_id) if organisation_id is not None else ENTREPRISE_UNIQUE


def filtrer_par_entreprise(queryset):
    """Restreint un queryset de module a l'entreprise courante.

    Sans effet en mono-entreprise : le filtre porte alors sur la chaine
    vide, que toutes les lignes possedent.
    """
    return queryset.filter(entreprise_id=entreprise_id_courant())
