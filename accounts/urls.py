from django.urls import path
from .views import RegisterView
from .views import create_checkout_session,  stripe_webhook, payment_cancel, payment_success

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('create-checkout/', create_checkout_session),
    
     path('stripe/webhook/', stripe_webhook),
     
    path('success/', payment_success, name='payment_success'),
    path('cancel/', payment_cancel, name='payment_cancel'),
]
