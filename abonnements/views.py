import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Plan, UserSubscription

# Initialisation de la clé Stripe (à définir dans le .env)
# stripe.api_key = settings.STRIPE_SECRET_KEY

def checkout_session(request, plan_id):
    """
    Crée une session Stripe Checkout pour un abonnement.
    """
    if not request.user.is_authenticated:
        return redirect('login')
        
    try:
        plan = Plan.objects.get(id=plan_id)
        # TODO: Implémentation réelle avec stripe.checkout.Session.create
        # session = stripe.checkout.Session.create(...)
        # return redirect(session.url)
        return JsonResponse({'message': 'Checkout session setup pending', 'plan': plan.name})
    except Plan.DoesNotExist:
        return JsonResponse({'error': 'Plan not found'}, status=404)

@csrf_exempt
def stripe_webhook(request):
    """
    Webhook pour recevoir les événements Stripe (paiement réussi, abonnement expiré, etc.)
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # TODO: Vérification de la signature webhhok avec endpoint_secret
    
    # Logique d'écoute des événements (checkout.session.completed, invoice.payment_succeeded)
    return JsonResponse({'status': 'success'})
