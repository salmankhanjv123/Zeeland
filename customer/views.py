from rest_framework import viewsets
from rest_framework import generics
from django.db.models import Q
from .serializers import CustomersSerializer,CustomerMessagesSerializer, CustomerMessagesDocumentsSerializer
from .models import Customers,CustomerMessages, CustomerMessagesDocuments


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


class CustomerMessagesListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerMessagesSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        plot_id = self.request.query_params.get('plot_id')
        query_filters=Q()
        if project_id:
            query_filters&=Q(customer__project_id=project_id)
        if plot_id:
            query_filters&=Q(plot_id=plot_id)
        queryset = CustomerMessages.objects.filter(query_filters)
        return queryset

class CustomerMessagesDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerMessages.objects.all()
    serializer_class = CustomerMessagesSerializer
