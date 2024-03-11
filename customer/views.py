from rest_framework import viewsets
from rest_framework import generics
from django.db.models import Q,Prefetch, OuterRef, Subquery
from .serializers import CustomersSerializer,CustomerMessagesSerializer,CustomerMessagesReminderSerializer
from .models import Customers,CustomerMessages,CustomerMessagesReminder
from booking.models import Booking

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

class CustomerMessagesReminderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Customers Reminders to be viewed or edited.
    """
    serializer_class = CustomerMessagesReminderSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        status  = self.request.query_params.get('status')
        date  = self.request.query_params.get('date')
        query_filters=Q()
        if user_id:
            query_filters &= Q(message__user_id=user_id)
        if status:
            query_filters &= Q(status=status)
        if date:
            query_filters &= Q(date__lte=date)

        queryset = CustomerMessagesReminder.objects.filter(query_filters).select_related("message__booking__plot","message__booking__customer")
        return queryset

class CustomerMessagesListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerMessagesSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        plot_id = self.request.query_params.get('plot_id')
        user_id= self.request.query_params.get('user_id')

        query_filters=Q()
        if project_id:
            query_filters&=Q(plot__project_id=project_id)
        if user_id:
            query_filters&=Q(user_id=user_id)
        if plot_id:
            query_filters&=Q(plot_id=plot_id)

        queryset = CustomerMessages.objects.filter(query_filters).select_related("booking__customer","booking__plot","user").prefetch_related('files')

        return queryset

class CustomerMessagesDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerMessages.objects.all()
    serializer_class = CustomerMessagesSerializer
