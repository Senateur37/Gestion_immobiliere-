"""Bus d'evenements metier interne.

Un encaissement interesse plusieurs domaines : la finance l'enregistre,
la comptabilite doit en tirer une ecriture, une quittance doit etre
produite, le locataire notifie. Ecrire ces appels a la suite dans le
service de paiement le rendrait dependant de tous les autres domaines.

Chaque domaine s'abonne donc a ce qui le concerne. Le bus est synchrone
et volontairement simple : pas de file d'attente, pas de serialisation.
Une file pourra se glisser derriere cette meme interface le jour ou un
traitement deviendra trop lent, sans toucher aux emetteurs.
"""
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

_abonnes = defaultdict(list)


class DomainEvent:
    """Fait metier avere. Nomme au passe : il a eu lieu."""

    def __repr__(self):
        details = ', '.join(f'{cle}={valeur!r}' for cle, valeur in vars(self).items())
        return f'{type(self).__name__}({details})'


def subscribe(event_type, handler):
    """Abonne un gestionnaire a un type d'evenement."""
    if handler not in _abonnes[event_type]:
        _abonnes[event_type].append(handler)
    return handler


def unsubscribe(event_type, handler):
    """Desabonne un gestionnaire, sans erreur s'il ne l'etait pas."""
    if handler in _abonnes[event_type]:
        _abonnes[event_type].remove(handler)


def publish(event):
    """Notifie les abonnes d'un evenement.

    L'echec d'un abonne ne doit pas annuler le fait metier : un paiement
    encaisse reste encaisse meme si la notification echoue. L'erreur est
    journalisee, et les autres abonnes sont tout de meme appeles.

    Les traitements qui ne tolerent pas cette indulgence — l'ecriture
    comptable, par exemple — doivent etre appeles dans la transaction du
    service, pas via le bus.
    """
    for handler in list(_abonnes[type(event)]):
        try:
            handler(event)
        except Exception:
            logger.exception(
                'Echec du gestionnaire %s pour %r', getattr(handler, '__name__', handler), event
            )


def clear_subscribers():
    """Vide les abonnements. Reserve aux tests."""
    _abonnes.clear()
