from rest_framework import viewsets
from .serializers import PlotsSerializer
from .models import Plots


class PlotsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Plots to be viewed or edited.
    """
    serializer_class = PlotsSerializer

    def get_queryset(self):
        queryset = Plots.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
