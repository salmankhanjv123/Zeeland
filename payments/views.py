from django.db.models import Q, Sum
import datetime
from rest_framework import viewsets
from .serializers import IncomingFundSerializer, OutgoingFundSerializer, ExpenseTypeSerializer, JournalVoucherSerializer
from .models import IncomingFund, OutgoingFund, ExpenseType, JournalVoucher
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import date
from booking.models import Booking
from customer.models import Customers


class IncomingFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows IncomingFund to be viewed or edited.
    """
    serializer_class = IncomingFundSerializer

    def get_queryset(self):
        queryset = IncomingFund.objects.all().select_related(
            'booking', 'booking__customer', 'booking__plot')

        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class OutgoingFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OutgoingFund to be viewed or edited.
    """
    serializer_class = OutgoingFundSerializer

    def get_queryset(self):
        queryset = OutgoingFund.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class JournalVoucherViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows JournalVoucher to be viewed or edited.
    """
    serializer_class = JournalVoucherSerializer

    def get_queryset(self):
        queryset = JournalVoucher.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class ExpenseTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ExpenseType to be viewed or edited.
    """
    serializer_class = ExpenseTypeSerializer

    def get_queryset(self):
        queryset = ExpenseType.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class DuePaymentsView(APIView):
    def get(self, request):
        today = date.today()
        overdue_bookings = Booking.objects.filter(
            due_date__lt=today, total_remaining_amount__gt=0)
        current_month = datetime.date.today().replace(day=1)
        due_payments = []
        for booking in overdue_bookings:
            # Check if there are any payments for the booking in the current month
            has_payment = IncomingFund.objects.filter(
                booking=booking, installement_month=current_month).exists()

            if not has_payment:
                customer = Customers.objects.get(pk=booking.customer_id)
                due_payments.append({
                    'booking_id': booking.booking_id,
                    'customer_name': customer.name,
                    'customer_contact': customer.contact,
                    'due_date': booking.due_date,
                    'total_remaining_amount': booking.total_remaining_amount,
                })
            else:
                # If there is a payment, exclude the booking from the overdue_bookings queryset
                overdue_bookings = overdue_bookings.exclude(pk=booking.pk)

        return Response({'due_payments': due_payments})

# class DuePaymentsView(APIView):
#     def get(self, request):
#         today = date.today()
#         overdue_bookings = Booking.objects.filter(due_date__lt=today, total_remaining_amount__gt=0)
#         overdue_customers = overdue_bookings.values('customer').distinct()

#         due_payments = []
#         for booking in overdue_bookings:
#             customer = Customers.objects.get(pk=booking.customer_id)

#             # Retrieve the installments that are due for specific months
#             due_installments = IncomingFund.objects.filter(
#                 booking=booking,
#                 installement_month__lt=today.month,
#                 amount__gt=0
#             )

#             # Append the details of due installments to the list
#             for installment in due_installments:
#                 due_payments.append({
#                     'booking_id': booking.booking_id,
#                     'customer_name': customer.name,
#                     'customer_email': customer.email,
#                     'customer_phone': customer.phone,
#                     'due_date': booking.due_date,
#                     'installment_month': installment.installement_month,
#                     'installment_amount': installment.amount,
#                 })

#         return Response({'due_payments': due_payments})
