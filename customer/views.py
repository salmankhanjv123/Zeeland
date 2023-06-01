from rest_framework import viewsets
from .serializers import CustomersSerializer
from .models import Customers


class CustomersViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Customers to be viewed or edited.
    """
    serializer_class = CustomersSerializer

    def get_queryset(self):
        queryset = Customers.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
