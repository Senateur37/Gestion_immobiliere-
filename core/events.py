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
# Abonnes dont l'echec doit faire echouer l'operation entiere.
_abonnes_critiques = defaultdict(list)


class DomainEvent:
    """Fait metier avere. Nomme au passe : il a eu lieu."""

    def __repr__(self):
        details = ', '.join(f'{cle}={valeur!r}' for cle, valeur in vars(self).items())
        return f'{type(self).__name__}({details})'


def subscribe(event_type, handler, critical=False):
    """Abonne un gestionnaire a un type d'evenement.

    Un abonne ordinaire est un effet de bord : sa defaillance est
    journalisee et l'operation se poursuit. Un abonne `critical` fait
    partie du fait metier lui-meme — l'ecriture comptable d'un
    encaissement, par exemple : son echec doit annuler l'operation
    plutot que laisser la base dans un etat incoherent.
    """
    registre = _abonnes_critiques if critical else _abonnes
    if handler not in registre[event_type]:
        registre[event_type].append(handler)
    return handler


def unsubscribe(event_type, handler):
    """Desabonne un gestionnaire, sans erreur s'il ne l'etait pas."""
    for registre in (_abonnes, _abonnes_critiques):
        if handler in registre[event_type]:
            registre[event_type].remove(handler)


def publish(event):
    """Notifie les abonnes d'un evenement.

    L'echec d'un abonne ne doit pas annuler le fait metier : un paiement
    encaisse reste encaisse meme si la notification echoue. L'erreur est
    journalisee, et les autres abonnes sont tout de meme appeles.

    Les traitements qui ne tolerent pas cette indulgence — l'ecriture
    comptable, par exemple — doivent etre appeles dans la transaction du
    service, pas via le bus.
    """
    # Les abonnes critiques passent d'abord, et sans filet : si l'ecriture
    # comptable echoue, l'encaissement qui l'a declenchee doit etre annule
    # avec elle.
    for handler in list(_abonnes_critiques[type(event)]):
        handler(event)

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
    _abonnes_critiques.clear()
