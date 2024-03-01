from django.db.models import Max
from django.db.models import Q, Sum
import datetime
from rest_framework import viewsets
from .serializers import IncomingFundSerializer, OutgoingFundSerializer, ExpenseTypeSerializer, JournalVoucherSerializer, PaymentReminderSerializer, ExpensePersonSerializer
from .models import IncomingFund, OutgoingFund, ExpenseType, JournalVoucher, PaymentReminder, ExpensePerson
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
        project_id = self.request.query_params.get('project')
        plot_id = self.request.query_params.get('plot_id')
        customer_id = self.request.query_params.get('customer_id')
        booking_id = self.request.query_params.get('booking_id')

        query_filters=Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if booking_id:
            query_filters &= Q(booking_id=booking_id)
        if plot_id:
            query_filters &= Q(booking__plot_id=plot_id)
        if customer_id:
            query_filters &= Q(booking__customer_id=customer_id)
        queryset = IncomingFund.objects.filter(query_filters).select_related(
            'booking', 'booking__customer', 'booking__plot')
        return queryset

    def perform_destroy(self, instance):
        amount = instance.amount
        booking = instance.booking
        booking.remaining += amount
        booking.total_receiving_amount -= amount
        booking.save()
        return super().perform_destroy(instance)


class OutgoingFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OutgoingFund to be viewed or edited.
    """
    serializer_class = OutgoingFundSerializer

    def get_queryset(self):
        queryset = OutgoingFund.objects.all().select_related('person', 'expense_type')
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


class ExpensePersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ExpensePerson to be viewed or edited.
    """
    serializer_class = ExpensePersonSerializer

    def get_queryset(self):
        queryset = ExpensePerson.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class PaymentReminderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows payments reminders to be viewed or edited.
    """
    serializer_class = PaymentReminderSerializer

    def get_queryset(self):
        queryset = PaymentReminder.objects.all()
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


def get_plot_info(instance):
    plot_number = instance.plot.plot_number
    plot_size = instance.plot.get_plot_size()
    plot_type = instance.plot.get_type_display()
    return f"{plot_number} || {plot_type} || {plot_size}"


class DuePaymentsView(APIView):
    def get(self, request):
        project = request.query_params.get('project')
        today = date.today().day
        current_month = datetime.date.today().replace(day=1)
        active_bookings = Booking.objects.filter(status="active",booking_type="installment_payment")

        if project:
            active_bookings = active_bookings.filter(project_id=project)
        defaulter_bookings = []

        for booking in active_bookings:
            latest_payment = IncomingFund.objects.filter(
                booking=booking).aggregate(latest_installement_month=Max('installement_month'))
            latest = IncomingFund.objects.filter(
                booking=booking)
            if latest_payment['latest_installement_month']:
                latest_payment_obj = IncomingFund.objects.filter(
                    booking=booking, installement_month=latest_payment['latest_installement_month']).first()
                if latest_payment_obj.installement_month != current_month and latest_payment_obj.booking.installment_date < today:
                    # Calculate the difference in months
                    month_diff = (current_month.year - latest_payment_obj.installement_month.year) * 12 + \
                        (current_month.month -
                         latest_payment_obj.installement_month.month)

                    # Append the booking object along with the month difference
                    defaulter_bookings.append({
                        'booking': booking,
                        'month_difference': month_diff
                    })
            else:
                # If no payments found, add the booking to defaulter_bookings
                month_diff = (current_month.year - booking.booking_date.year) * 12 + \
                    (current_month.month - booking.booking_date.month)

                defaulter_bookings.append({
                    'booking': booking,
                    'month_difference': month_diff
                })
        due_payments = []
        for defaulter_booking in defaulter_bookings:
            booking = defaulter_booking['booking']
            month_diff = defaulter_booking['month_difference']
            customer = Customers.objects.get(pk=booking.customer_id)
            plot_info = get_plot_info(booking)
            due_payments.append({
                'id': booking.id,
                'booking_id': booking.booking_id,
                'plot_info': plot_info,
                'customer_name': customer.name,
                'customer_contact': customer.contact,
                'due_date': booking.installment_date,
                'total_remaining_amount': month_diff*booking.installment_per_month,
                'month_difference': month_diff
            })

        return Response({'due_payments': due_payments})
