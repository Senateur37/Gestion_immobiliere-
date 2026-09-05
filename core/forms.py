"""Formulaires du socle."""
from django import forms


class TenantModelForm(forms.ModelForm):
    """Formulaire d'un modele rattache a une organisation.

    L'organisation vient du contexte de la requete, jamais d'un choix de
    l'utilisateur. L'exposer dans un formulaire serait doublement faux :
    la liste deroulante enumererait toutes les organisations de la
    plateforme, et un client pourrait poster l'identifiant d'une autre.

    Le champ est donc retire ici plutot que dans chaque `exclude`, ou il
    finirait tot ou tard par etre oublie.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('organization', None)
