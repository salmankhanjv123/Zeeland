# views.py
from rest_framework import generics
from payments.models import IncomingFund, OutgoingFund, JournalVoucher
from .serializers import IncomingFundReportSerializer, OutgoingFundReportSerializer, JournalVoucherReportSerializer


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
