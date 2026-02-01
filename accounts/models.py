from django.conf import settings
from django.db import models

class Subscription(models.Model):
    PLAN_CHOICES = (
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('premium', 'Premium'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"
