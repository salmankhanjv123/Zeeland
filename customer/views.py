from rest_framework import viewsets
from rest_framework import generics
from django.db.models import Q
from .serializers import (
    CustomersSerializer,
    CustomerMessagesSerializer,
    CustomerMessagesReminderSerializer,
    DealersSerializer,
    DepartmentSerializer,
)
from .models import Customers, CustomerMessages, CustomerMessagesReminder, Dealers,Department
from booking.models import Booking


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer



class CustomersViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Customers to be viewed or edited.
    """

    serializer_class = CustomersSerializer

    def get_queryset(self):
        queryset = Customers.objects.all().prefetch_related("files")
        project_id = self.request.query_params.get("project")
        department_id = self.request.query_params.get("department_id")
        reference_string = self.request.query_params.get("reference")
        reference = (
            [str for str in reference_string.split(",")]
            if reference_string
            else []
        )
        print(reference)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if reference:
            queryset = queryset.filter(reference__in=reference)
        return queryset


class CustomerMessagesReminderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Customers Reminders to be viewed or edited.
    """

    serializer_class = CustomerMessagesReminderSerializer

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        status = self.request.query_params.get("status")
        date = self.request.query_params.get("date")
        query_filters = Q()
        if user_id:
            query_filters &= Q(message__user_id=user_id)
        if status:
            query_filters &= Q(status=status)
        if date:
            query_filters &= Q(date__lte=date)

        queryset = CustomerMessagesReminder.objects.filter(
            query_filters
        ).select_related("message__booking__plot", "message__booking__customer")
        return queryset


class CustomerMessagesListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerMessagesSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get("project")
        booking_id = self.request.query_params.get("booking_id")
        user_id = self.request.query_params.get("user_id")

        query_filters = Q()
        if project_id:
            query_filters &= Q(booking__project_id=project_id)
        if user_id:
            query_filters &= Q(user_id=user_id)
        if booking_id:
            query_filters &= Q(booking_id=booking_id)
        # Add filter for booking not null
        query_filters &= Q(booking__isnull=False)
        queryset = (
            CustomerMessages.objects.filter(query_filters)
            .select_related("booking__customer", "booking__plot", "user")
            .prefetch_related("files")
        )

        return queryset


class CustomerMessagesDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomerMessages.objects.all()
    serializer_class = CustomerMessagesSerializer


class DealerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Dealers to be viewed or edited.
    """

    serializer_class = DealersSerializer

    def get_queryset(self):

        project_id = self.request.query_params.get("project")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        queryset = Dealers.objects.filter(query_filters).prefetch_related("files")
        return queryset
