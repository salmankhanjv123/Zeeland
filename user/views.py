# views.py
from django.contrib.auth.models import User
from rest_framework import generics, viewsets
from projects.models import Projects
from .serializers import UserSerializer, ProjectsSerializer, UserProjectsSerializer


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
