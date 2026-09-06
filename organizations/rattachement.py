"""Rattachement automatique des modules metier a l'organisation.

Les modules prefabriques portent un `entreprise_id` mais ne savent pas
d'ou le tirer : ils ignorent tout du modele Organization de ce projet.

Plutot que de laisser ce champ vide en attendant une reprise ulterieure
— qui obligerait a repasser sur toutes les lignes le jour du
multi-entreprises — on le remplit des maintenant, a chaque enregistrement,
depuis l'organisation active.

Une seule organisation existe aujourd'hui. Le champ porte neanmoins son
identifiant reel, si bien que le passage a plusieurs organisations ne
demandera aucune reprise de donnees : les lignes sont deja rattachees.

Le branchement se fait par signal `pre_save`, sans modifier les modules :
ils restent utilisables tels quels dans un projet qui n'a pas
d'organisations.
"""
import logging

from django.apps import apps
from django.db.models.signals import pre_save

logger = logging.getLogger(__name__)

# Modules dont les modeles portent un entreprise_id.
APPS_CONCERNEES = ('comptes', 'comptabilite_ohada', 'django_paie', 'rh')


def identifiant_organisation_active():
    """UID de l'organisation active, sous forme de chaine.

    Chaine vide hors contexte : une tache d'administration ou une
    migration ne doit pas echouer faute d'organisation, et une ligne sans
    rattachement reste reconnaissable.
    """
    from .entreprise import entreprise_id_courant

    return entreprise_id_courant()


def _rattacher(sender, instance, **kwargs):
    """Inscrit l'organisation active avant enregistrement.

    On ne recrit jamais un rattachement existant : une ligne appartient a
    l'organisation qui l'a creee, meme si elle est modifiee plus tard
    depuis un autre contexte.
    """
    if getattr(instance, 'entreprise_id', None):
        return
    identifiant = identifiant_organisation_active()
    if identifiant:
        instance.entreprise_id = identifiant


def modeles_rattachables():
    """Modeles des modules portant un champ entreprise_id."""
    trouves = []
    for modele in apps.get_models():
        if modele._meta.app_label not in APPS_CONCERNEES:
            continue
        if any(champ.name == 'entreprise_id' for champ in modele._meta.fields):
            trouves.append(modele)
    return trouves


def connecter():
    """Branche le rattachement sur tous les modeles concernes."""
    modeles = modeles_rattachables()
    for modele in modeles:
        pre_save.connect(
            _rattacher,
            sender=modele,
            dispatch_uid=f'rattachement_organisation_{modele._meta.label_lower}',
        )
    logger.info('Rattachement a l organisation actif sur %s modeles', len(modeles))
    return modeles
