from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def premium_required(view_func):
    """
    Décorateur pour bloquer l'accès aux vues si l'utilisateur n'a pas
    un abonnement actif (Premium ou Entreprise).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        # On vérifie si l'utilisateur possède un abonnement actif
        if hasattr(request.user, 'subscription'):
            sub = request.user.subscription
            if sub.status in ['active', 'trialing']:
                return view_func(request, *args, **kwargs)
                
        # Si aucun abonnement actif, on lève une exception 403 
        # (ou on pourrait rediriger vers une page "Upgradez votre plan")
        raise PermissionDenied("Cette fonctionnalité nécessite un abonnement Premium.")
        
    return _wrapped_view
