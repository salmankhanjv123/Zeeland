# views.py
from rest_framework import generics
from payments.models import IncomingFund, OutgoingFund, JournalVoucher
from customer.models import Customers
from plots.models import Plots
from booking.models import Booking, Token
from .serializers import IncomingFundReportSerializer, OutgoingFundReportSerializer, JournalVoucherReportSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, functions,Q
from datetime import date, datetime, timedelta
import calendar


class IncomingFundReportView(generics.ListAPIView):
    serializer_class = IncomingFundReportSerializer

    def get_queryset(self):
        queryset = IncomingFund.objects.all().select_related(
            'booking__customer', 'booking__plot')
        project_id = self.request.query_params.get('project_id')
        booking_id = self.request.query_params.get('booking_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if booking_id:
            queryset = queryset.filter(booking_id=booking_id)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset


class OutgoingFundReportView(generics.ListAPIView):
    serializer_class = OutgoingFundReportSerializer

    def get_queryset(self):
        queryset = OutgoingFund.objects.all()
        project_id = self.request.query_params.get('project_id')
        expense_type = self.request.query_params.get('expense_type')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if expense_type:
            queryset = queryset.filter(expense_type=expense_type)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset


class JournalVoucherReportView(generics.ListAPIView):
    serializer_class = JournalVoucherReportSerializer

    def get_queryset(self):
        queryset = JournalVoucher.objects.all()
        project_id = self.request.query_params.get('project_id')
        type = self.request.query_params.get('type')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if type:
            queryset = queryset.filter(type=type)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset


class TotalCountView(APIView):
    def get(self, request):
        project_id = request.GET.get('project_id')
        today = date.today()
        customer_count = Customers.objects.filter(
            project_id=project_id).count()
        active_plots_count = Plots.objects.filter(
            project_id=project_id, status='active').count()
        sold_plots_count = Plots.objects.filter(
            project_id=project_id, status='sold').count()
        resale_plots_count = Plots.objects.filter(project_id=project_id).annotate(
            booking_count=Count('booking_details')).filter(booking_count__gt=1).count()
        booking_count = Booking.objects.filter(project_id=project_id).count()
        non_expired_tokens_count = Token.objects.filter(
            project_id=project_id, expire_date__gte=today).count()

        data = {
            'customer_count': customer_count,
            'active_plots_count': active_plots_count,
            'sold_plots_count': sold_plots_count,
            'resale_plots_count': resale_plots_count,
            'booking_count': booking_count,
            'non_expired_tokens_count': non_expired_tokens_count,
        }

        return Response(data)


class TotalAmountView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        project_id = request.GET.get('project_id')

        # Calculate total incoming amount
        incoming_amount = IncomingFund.objects.filter(
            project=project_id
        ).aggregate(total_amount=Sum('amount'))['total_amount']

        # Calculate total outgoing amount
        outgoing_amount = OutgoingFund.objects.filter(
            project=project_id
        ).aggregate(total_amount=Sum('amount'))['total_amount']

        # Calculate total journal voucher amount
        journal_voucher_in_amount = JournalVoucher.objects.filter(
            project=project_id, type='in'
        ).aggregate(total_amount=Sum('amount'))['total_amount']

        journal_voucher_out_amount = JournalVoucher.objects.filter(
            project=project_id, type='out'
        ).aggregate(total_amount=Sum('amount'))['total_amount']

        # Prepare response
        response_data = {
            'incoming_amount': incoming_amount or 0,
            'outgoing_amount': outgoing_amount or 0,
            'journal_voucher_in_amount': journal_voucher_in_amount or 0,
            'journal_voucher_out_amount': journal_voucher_out_amount or 0
        }

        return Response(response_data)


class MonthlyIncomingFundGraphView(APIView):
    def get(self, request):
        project_id = request.GET.get('project_id')
        current_date = datetime.now().date()
        start_date = current_date.replace(day=1)
        end_date = start_date + timedelta(days=32)
        end_date = end_date.replace(day=1)

        incoming_funds_by_day = IncomingFund.objects \
            .filter(date__gte=start_date, date__lt=end_date, project=project_id) \
            .annotate(day=functions.TruncDay('date')) \
            .values('day') \
            .annotate(total_amount=Sum('amount')) \
            .order_by('day')

        outgoing_funds_by_day = OutgoingFund.objects \
            .filter(date__gte=start_date, date__lt=end_date, project=project_id) \
            .annotate(day=functions.TruncDay('date')) \
            .values('day') \
            .annotate(total_amount=Sum('amount')) \
            .order_by('day')

        incoming_report_data = [
            {'day': fund['day'].strftime(
                '%Y-%m-%d'), 'total_amount': fund['total_amount'] or 0}
            for fund in incoming_funds_by_day
        ]

        outgoing_report_data = [
            {'day': fund['day'].strftime(
                '%Y-%m-%d'), 'total_amount': fund['total_amount'] or 0}
            for fund in outgoing_funds_by_day
        ]

        current_day = start_date
        while current_day < end_date:
            current_day_str = current_day.strftime('%Y-%m-%d')

            if not any(d['day'] == current_day_str for d in incoming_report_data):
                incoming_report_data.append(
                    {'day': current_day_str, 'total_amount': 0})

            if not any(d['day'] == current_day_str for d in outgoing_report_data):
                outgoing_report_data.append(
                    {'day': current_day_str, 'total_amount': 0})

            current_day += timedelta(days=1)

        sorted_incoming_report_data = sorted(
            incoming_report_data, key=lambda x: x['day'])
        sorted_outgoing_report_data = sorted(
            outgoing_report_data, key=lambda x: x['day'])

        result = {
            'incoming_funds': sorted_incoming_report_data,
            'outgoing_funds': sorted_outgoing_report_data
        }

        return Response(result)


class AnnualIncomingFundGraphView(APIView):
    def get(self, request):
        project_id = request.GET.get('project_id')
        current_year = datetime.now().year
        start_date = datetime(current_year, 1, 1)
        end_date = datetime(current_year + 1, 1, 1)

        incoming_funds_by_month = IncomingFund.objects \
            .filter(date__gte=start_date, date__lt=end_date, project=project_id) \
            .annotate(month=functions.TruncMonth('date')) \
            .values('month') \
            .annotate(total_amount=Sum('amount')) \
            .order_by('month')

        outgoing_funds_by_month = OutgoingFund.objects \
            .filter(date__gte=start_date, date__lt=end_date, project=project_id) \
            .annotate(month=functions.TruncMonth('date')) \
            .values('month') \
            .annotate(total_amount=Sum('amount')) \
            .order_by('month')

        incoming_report_data = [
            {'month': fund['month'].strftime(
                '%Y-%m'), 'total_amount': fund['total_amount'] or 0}
            for fund in incoming_funds_by_month
        ]

        outgoing_report_data = [
            {'month': fund['month'].strftime(
                '%Y-%m'), 'total_amount': fund['total_amount'] or 0}
            for fund in outgoing_funds_by_month
        ]

        for month in range(1, 13):
            current_month_str = datetime(
                current_year, month, 1).strftime('%Y-%m')

            if not any(d['month'] == current_month_str for d in incoming_report_data):
                incoming_report_data.append(
                    {'month': current_month_str, 'total_amount': 0})

            if not any(d['month'] == current_month_str for d in outgoing_report_data):
                outgoing_report_data.append(
                    {'month': current_month_str, 'total_amount': 0})

        sorted_incoming_report_data = sorted(
            incoming_report_data, key=lambda x: x['month'])
        sorted_outgoing_report_data = sorted(
            outgoing_report_data, key=lambda x: x['month'])

        result = {
            'incoming_funds': sorted_incoming_report_data,
            'outgoing_funds': sorted_outgoing_report_data
        }
        # Return the result with month names
        result_with_month_names = {
            'incoming_funds': [{'month': calendar.month_abbr[int(data['month'].split('-')[1])], 'total_amount': data['total_amount']} for data in sorted_incoming_report_data],
            'outgoing_funds': [{'month': calendar.month_abbr[int(data['month'].split('-')[1])], 'total_amount': data['total_amount']} for data in sorted_outgoing_report_data]
        }

        return Response(result_with_month_names)



class DealerLedgerView(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        dealer_id = self.request.query_params.get("dealer_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if dealer_id:
            query_filters &= Q(dealer_id=dealer_id)
        if start_date and end_date:
            query_filters &= Q(booking_date__gte=start_date) & Q(booking_date__lte=end_date)

        # Calculate total incoming amount
        booking_data = Booking.objects.filter(
            query_filters
        ).values("id","booking_date","booking_id","dealer__name","dealer__contact","dealer__address","dealer_per_marla_comission","dealer_comission_percentage","dealer_comission_amount")


        return Response(booking_data)
