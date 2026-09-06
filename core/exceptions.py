"""Exceptions du socle."""


class CoreError(Exception):
    """Racine des erreurs metier du socle."""


class NoActiveOrganization(CoreError):
    """Une requete filtree par organisation a ete tentee hors contexte."""


class DomainError(CoreError):
    """Regle metier violee.

    Les services levent cette exception plutot que de renvoyer None ou
    False : l'appelant ne peut pas l'ignorer par megarde. La couche API
    la traduit en reponse 400.
    """

    def __init__(self, message, code='invalid'):
        super().__init__(message)
        self.message = message
        self.code = code
