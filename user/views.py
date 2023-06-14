# views.py
from django.contrib.auth.models import User, Group, Permission
from rest_framework import generics, viewsets
from projects.models import Projects
from .serializers import UserSerializer, ProjectsSerializer, UserProjectsSerializer, GroupSerializer, PermissionSerializer, AssignGroupSerializer, ListPermissionSerializer, AssignPermissionSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProjectsList(generics.ListAPIView):
    queryset = Projects.objects.values('id', 'name')
    serializer_class = ProjectsSerializer


class UserProjectsList(generics.ListAPIView):
    queryset = User.objects.all().prefetch_related('projects_list')
    serializer_class = UserProjectsSerializer


class UserProjectsDetail(generics.RetrieveAPIView):
    queryset = User.objects.all().prefetch_related('projects_list')
    serializer_class = UserProjectsSerializer
    lookup_field = 'id'


class UserProjectsUpdate(generics.UpdateAPIView):
    queryset = User.objects.all().prefetch_related('projects_list')
    serializer_class = UserProjectsSerializer


class GroupListCreateAPIView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class PermissionListCreateAPIView(generics.ListCreateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        content_type = self.request.query_params.get('content_type')

        if content_type:
            queryset = queryset.filter(content_type=content_type)

        return queryset


class PermissionRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


class UserAssignGroupView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = AssignGroupSerializer


class UserAssignPermissionView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return AssignPermissionSerializer
        else:
            return ListPermissionSerializer


class UsersListPermissionView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = ListPermissionSerializer
