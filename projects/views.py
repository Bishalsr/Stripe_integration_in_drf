from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectSerializer, ProjectListSerializer
from .permissions import IsOwner
from accounts.models import Subscription


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwner]

    def get_queryset(self):
        return Project.objects.filter(
            owner=self.request.user,
            is_active=True
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        project.is_active = False
        project.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def archived(self, request):
        projects = Project.objects.filter(
            owner=request.user,
            is_active=False
        )
        serializer = ProjectListSerializer(projects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        project = Project.objects.get(pk=pk, owner=request.user)

        can_create, msg = Project.can_create_project(request.user)
        if not can_create:
            return Response({"error": msg}, status=400)

        project.is_active = True
        project.save()
        return Response(ProjectSerializer(project).data)

    @action(detail=False, methods=['get'])
    def subscription_status(self, request):
        sub = Subscription.objects.get(user=request.user)

        used = Project.objects.filter(
            owner=request.user,
            is_active=True
        ).count()

        limit = Project.get_plan_limit(sub.plan)

        return Response({
            "plan": sub.plan,
            "projects_used": used,
            "projects_limit": limit,
            "can_create_project": used < limit,
            "expires_at": sub.expires_at
        })
