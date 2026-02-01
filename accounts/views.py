from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
import stripe
from django.conf import settings
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from .models import Subscription
from django.contrib.auth.models import User
from decouple import config


STRIPE_PRICE_FREE = config("STRIPE_PRICE_FREE")
STRIPE_PRICE_PRO = config("STRIPE_PRICE_PRO")
STRIPE_PRICE_PREM = config("STRIPE_PRICE_PREM")

PRICE_MAPPING = {
    "free": STRIPE_PRICE_FREE,
    "pro": STRIPE_PRICE_PRO,
    "premium": STRIPE_PRICE_PREM,
}

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        user_id = session['metadata']['user_id']
        user = User.objects.get(id=user_id)

        
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': 'free',
                'is_active': True,
                'expires_at': timezone.now() + timedelta(days=30)
            }
        )

    return HttpResponse(status=200)

class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    plan = request.data.get('plan', 'pro')
    price_id = PRICE_MAPPING.get(plan)

    if not price_id:
        return JsonResponse({"error": "Invalid plan"}, status=400)
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        customer_email=request.user.email,
        line_items=[{'price': price_id, 'quantity': 1}],
     
        success_url='http://localhost:8000/api/accounts/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url='http://localhost:8000/api/accounts/cancel/',
        metadata={
            'user_id': request.user.id
        }
    )
    return JsonResponse({'checkout_url': session.url})





def payment_success(request):
    session_id = request.GET.get('session_id')
    return HttpResponse(f"Payment successful! Session ID: {session_id}")

def payment_cancel(request):
    return HttpResponse("Payment canceled.")
