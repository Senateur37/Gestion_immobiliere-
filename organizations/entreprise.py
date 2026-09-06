"""Lien entre l'organisation et l'`entreprise_id` des modules metier.

Deux notions a ne pas confondre.

**Le rattachement est actif.** Chaque ligne creee dans les modules porte
l'identifiant de l'organisation active, inscrit par le signal de
`organizations/rattachement.py`. Rien n'est laisse vide en attendant : le
jour ou plusieurs organisations coexisteront, aucune reprise de donnees ne
sera necessaire, puisque l'appartenance est deja enregistree.

**Le filtrage est differe.** Une seule organisation existe aujourd'hui :
restreindre les selections n'aurait aucun effet visible, sinon celui de
masquer d'eventuelles erreurs de rattachement. `filtrer_par_entreprise()`
est donc ecrite et testee, mais branchee nulle part.

Le jour du multi-entreprises, il n'y aura qu'une chose a faire : passer
FILTRER_PAR_ENTREPRISE a True et faire passer les selections des modules
par `filtrer_par_entreprise()`.
"""
from core.tenancy import get_current_organization_id

# Ne gouverne que le filtrage des selections. Le rattachement des lignes
# a leur organisation, lui, est toujours actif.
FILTRER_PAR_ENTREPRISE = False

def uid_de(organisation_pk):
    """UID d'une organisation, depuis sa cle primaire.

    Volontairement sans cache. Une premiere version en gardait un, pour
    epargner une lecture a chaque enregistrement : une cle primaire
    reutilisee — apres restauration d'une base, par exemple — servait
    alors l'UID d'une autre organisation. Rattacher une ligne a la
    mauvaise entreprise est un prix sans commune mesure avec le gain d'un
    SELECT sur cle primaire indexee.

    Renvoie la chaine vide si l'organisation n'existe plus : mieux vaut
    une ligne sans rattachement qu'une exception au milieu d'un
    enregistrement.
    """
    if organisation_pk is None:
        return ''

    from .models import Organization

    uid = (
        Organization.objects.filter(pk=organisation_pk)
        .values_list('uid', flat=True)
        .first()
    )
    return str(uid) if uid else ''


def entreprise_id_courant():
    """Identifiant de l'organisation active, sous forme de chaine.

    C'est l'UID et non la cle primaire : il ne change pas lors d'un export
    puis reimport, il ne renseigne pas sur le nombre d'organisations, et
    deux installations ne peuvent pas produire le meme.

    Les modules stockent un CharField et non une cle etrangere : ils
    restent ainsi utilisables dans un projet qui n'a pas d'organisations.

    Chaine vide hors contexte — commande d'administration, migration —
    plutot qu'une erreur : ces traitements sont legitimes et n'ont pas a
    echouer faute d'organisation active.
    """
    return uid_de(get_current_organization_id())


def filtrer_par_entreprise(queryset):
    """Restreint un queryset de module a l'organisation active.

    Sans effet tant que FILTRER_PAR_ENTREPRISE vaut False : la fonction
    existe et se teste des maintenant, pour que la bascule ne soit qu'un
    changement de valeur.
    """
    if not FILTRER_PAR_ENTREPRISE:
        return queryset

    identifiant = entreprise_id_courant()
    if not identifiant:
        # Hors contexte, on ne devine pas : mieux vaut ne rien renvoyer
        # que renvoyer les donnees de toutes les organisations.
        return queryset.none()
    return queryset.filter(entreprise_id=identifiant)
