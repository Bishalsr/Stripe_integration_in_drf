from django.conf import settings
from django.db import models
from django.utils import timezone

class Project(models.Model):

    PLAN_LIMITS = {
        'free': 3,
        'pro': 6,
        'premium': 9,
    }

    title = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def get_plan_limit(plan):
        return Project.PLAN_LIMITS.get(plan, 0)

    @staticmethod
    def can_create_project(user):
        from accounts.models import Subscription

        try:
            sub = Subscription.objects.get(user=user, is_active=True)
        except Subscription.DoesNotExist:
            return False, "No active subscription found"

        if sub.expires_at and sub.expires_at < timezone.now():
            return False, "Subscription expired"

        limit = Project.get_plan_limit(sub.plan)
        used = Project.objects.filter(
            owner=user,
            is_active=True
        ).count()

        if used >= limit:
            return False, f"Project limit reached ({limit}) for {sub.plan} plan"

        return True, ""
