from rest_framework import viewsets
from .serializers import ProjectsSerializer
from .models import Projects


class ProjectsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Projects to be viewed or edited.
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer




