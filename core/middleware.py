"""Resolution de l'organisation active a chaque requete."""
from organizations.selectors import resolve_membership_for_request

from .tenancy import request_scope, set_current_organization

# En-tete permettant a un utilisateur membre de plusieurs organisations
# de choisir celle sur laquelle il travaille. Le front l'envoie ; le
# serveur verifie toujours que le membership existe.
ORGANIZATION_HEADER = 'HTTP_X_ORGANIZATION'


def activate_organization(request):
    """Resout l'organisation de la requete et l'installe dans le contexte.

    Appelable a deux moments, parce que les deux fronts n'authentifient
    pas au meme instant :

    - le middleware, pour l'interface Django, ou l'utilisateur est deja
      connu grace a la session ;
    - la permission DRF, pour l'API, ou l'utilisateur n'est authentifie
      qu'une fois entre dans la vue. Appeler la resolution uniquement
      depuis le middleware donnerait toujours un utilisateur anonyme.

    Idempotente : le second appel ne refait pas le travail du premier.
    """
    membership = getattr(request, 'membership', None)
    if membership is not None:
        return membership

    membership = resolve_membership_for_request(request)
    request.membership = membership
    request.organization = membership.organization if membership else None
    if membership is not None:
        set_current_organization(membership.organization_id)
    return membership


class OrganizationMiddleware:
    """Place l'organisation de l'utilisateur dans le contexte d'execution.

    Sans organisation active, les managers de core.managers levent
    NoActiveOrganization : l'echec est bruyant plutot que silencieux.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # request_scope garantit que le perimetre de cette requete ne
        # survit pas a sa reponse : les workers sont reutilises.
        with request_scope():
            request.membership = None
            request.organization = None
            activate_organization(request)
            return self.get_response(request)
