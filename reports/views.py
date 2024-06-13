# views.py
from rest_framework import generics
from payments.models import IncomingFund, OutgoingFund, JournalVoucher
from customer.models import Customers,CustomerMessages
from plots.models import Plots
from booking.models import Booking, Token
from .serializers import (
    IncomingFundReportSerializer,
    OutgoingFundReportSerializer,
    JournalVoucherReportSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Sum, functions, Q,F,Value,CharField
from datetime import date, datetime, timedelta
import calendar
# views.py

from payments.models import Bank
from payments.serializers import BankSerializer
from collections import defaultdict

class IncomingFundReportView(generics.ListAPIView):
    serializer_class = IncomingFundReportSerializer

    def get_queryset(self):
        queryset = IncomingFund.objects.all().select_related(
            "booking__customer", "booking__plot"
        )
        project_id = self.request.query_params.get("project_id")
        booking_id = self.request.query_params.get("booking_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

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
        project_id = self.request.query_params.get("project_id")
        expense_type = self.request.query_params.get("expense_type")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

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
        project_id = self.request.query_params.get("project_id")
        type = self.request.query_params.get("type")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

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
        project_id = request.GET.get("project_id")
        today = date.today()
        customer_count = Customers.objects.filter(project_id=project_id).count()
        active_plots_count = Plots.objects.filter(
            project_id=project_id, status="active"
        ).count()
        sold_plots_count = Plots.objects.filter(
            project_id=project_id, status="sold"
        ).count()
        resale_plots_count = (
            Plots.objects.filter(project_id=project_id)
            .annotate(booking_count=Count("booking_details"))
            .filter(booking_count__gt=1)
            .count()
        )
        booking_count = Booking.objects.filter(project_id=project_id).count()
        non_expired_tokens_count = Token.objects.filter(
            project_id=project_id, expire_date__gte=today
        ).count()

        data = {
            "customer_count": customer_count,
            "active_plots_count": active_plots_count,
            "sold_plots_count": sold_plots_count,
            "resale_plots_count": resale_plots_count,
            "booking_count": booking_count,
            "non_expired_tokens_count": non_expired_tokens_count,
        }

        return Response(data)


class TotalAmountView(APIView):
    def get(self, request):
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        project_id = request.GET.get("project_id")

        # Calculate total incoming amount
        incoming_amount = IncomingFund.objects.filter(project=project_id).aggregate(
            total_amount=Sum("amount")
        )["total_amount"]

        # Calculate total outgoing amount
        outgoing_amount = OutgoingFund.objects.filter(project=project_id).aggregate(
            total_amount=Sum("amount")
        )["total_amount"]

        # Calculate total journal voucher amount
        journal_voucher_in_amount = JournalVoucher.objects.filter(
            project=project_id, type="in"
        ).aggregate(total_amount=Sum("amount"))["total_amount"]

        journal_voucher_out_amount = JournalVoucher.objects.filter(
            project=project_id, type="out"
        ).aggregate(total_amount=Sum("amount"))["total_amount"]

        # Prepare response
        response_data = {
            "incoming_amount": incoming_amount or 0,
            "outgoing_amount": outgoing_amount or 0,
            "journal_voucher_in_amount": journal_voucher_in_amount or 0,
            "journal_voucher_out_amount": journal_voucher_out_amount or 0,
        }

        return Response(response_data)


class MonthlyIncomingFundGraphView(APIView):
    def get(self, request):
        project_id = request.GET.get("project_id")
        current_date = datetime.now().date()
        start_date = current_date.replace(day=1)
        end_date = start_date + timedelta(days=32)
        end_date = end_date.replace(day=1)

        incoming_funds_by_day = (
            IncomingFund.objects.filter(
                date__gte=start_date, date__lt=end_date, project=project_id
            )
            .annotate(day=functions.TruncDay("date"))
            .values("day")
            .annotate(total_amount=Sum("amount"))
            .order_by("day")
        )

        outgoing_funds_by_day = (
            OutgoingFund.objects.filter(
                date__gte=start_date, date__lt=end_date, project=project_id
            )
            .annotate(day=functions.TruncDay("date"))
            .values("day")
            .annotate(total_amount=Sum("amount"))
            .order_by("day")
        )

        incoming_report_data = [
            {
                "day": fund["day"].strftime("%Y-%m-%d"),
                "total_amount": fund["total_amount"] or 0,
            }
            for fund in incoming_funds_by_day
        ]

        outgoing_report_data = [
            {
                "day": fund["day"].strftime("%Y-%m-%d"),
                "total_amount": fund["total_amount"] or 0,
            }
            for fund in outgoing_funds_by_day
        ]

        current_day = start_date
        while current_day < end_date:
            current_day_str = current_day.strftime("%Y-%m-%d")

            if not any(d["day"] == current_day_str for d in incoming_report_data):
                incoming_report_data.append({"day": current_day_str, "total_amount": 0})

            if not any(d["day"] == current_day_str for d in outgoing_report_data):
                outgoing_report_data.append({"day": current_day_str, "total_amount": 0})

            current_day += timedelta(days=1)

        sorted_incoming_report_data = sorted(
            incoming_report_data, key=lambda x: x["day"]
        )
        sorted_outgoing_report_data = sorted(
            outgoing_report_data, key=lambda x: x["day"]
        )

        result = {
            "incoming_funds": sorted_incoming_report_data,
            "outgoing_funds": sorted_outgoing_report_data,
        }

        return Response(result)


class AnnualIncomingFundGraphView(APIView):
    def get(self, request):
        project_id = request.GET.get("project_id")
        current_year = datetime.now().year
        start_date = datetime(current_year, 1, 1)
        end_date = datetime(current_year + 1, 1, 1)

        incoming_funds_by_month = (
            IncomingFund.objects.filter(
                date__gte=start_date, date__lt=end_date, project=project_id
            )
            .annotate(month=functions.TruncMonth("date"))
            .values("month")
            .annotate(total_amount=Sum("amount"))
            .order_by("month")
        )

        outgoing_funds_by_month = (
            OutgoingFund.objects.filter(
                date__gte=start_date, date__lt=end_date, project=project_id
            )
            .annotate(month=functions.TruncMonth("date"))
            .values("month")
            .annotate(total_amount=Sum("amount"))
            .order_by("month")
        )

        incoming_report_data = [
            {
                "month": fund["month"].strftime("%Y-%m"),
                "total_amount": fund["total_amount"] or 0,
            }
            for fund in incoming_funds_by_month
        ]

        outgoing_report_data = [
            {
                "month": fund["month"].strftime("%Y-%m"),
                "total_amount": fund["total_amount"] or 0,
            }
            for fund in outgoing_funds_by_month
        ]

        for month in range(1, 13):
            current_month_str = datetime(current_year, month, 1).strftime("%Y-%m")

            if not any(d["month"] == current_month_str for d in incoming_report_data):
                incoming_report_data.append(
                    {"month": current_month_str, "total_amount": 0}
                )

            if not any(d["month"] == current_month_str for d in outgoing_report_data):
                outgoing_report_data.append(
                    {"month": current_month_str, "total_amount": 0}
                )

        sorted_incoming_report_data = sorted(
            incoming_report_data, key=lambda x: x["month"]
        )
        sorted_outgoing_report_data = sorted(
            outgoing_report_data, key=lambda x: x["month"]
        )

        result = {
            "incoming_funds": sorted_incoming_report_data,
            "outgoing_funds": sorted_outgoing_report_data,
        }
        # Return the result with month names
        result_with_month_names = {
            "incoming_funds": [
                {
                    "month": calendar.month_abbr[int(data["month"].split("-")[1])],
                    "total_amount": data["total_amount"],
                }
                for data in sorted_incoming_report_data
            ],
            "outgoing_funds": [
                {
                    "month": calendar.month_abbr[int(data["month"].split("-")[1])],
                    "total_amount": data["total_amount"],
                }
                for data in sorted_outgoing_report_data
            ],
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
            query_filters &= Q(booking_date__gte=start_date) & Q(
                booking_date__lte=end_date
            )

        # Calculate total incoming amount
        booking_data = Booking.objects.filter(query_filters).values(
            "id",
            "booking_date",
            "booking_id",
            "dealer__name",
            "dealer__contact",
            "dealer__address",
            "dealer_per_marla_comission",
            "dealer_comission_percentage",
            "dealer_comission_amount",
        )

        return Response(booking_data)



class CustomerLedgerView(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        customer_id = self.request.query_params.get("customer_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        booking_data = Booking.objects.filter(query_filters, customer_id=customer_id).select_related('customer').values(
            "id",
            "remarks",
            document=F("booking_id"),
            amount=F("total_amount"),
            date=F("booking_date"),
            customer_name=F("customer__name"),
            reference=Value("booking", output_field=CharField())
        )
        
        payment_data = IncomingFund.objects.filter(query_filters, booking__customer_id=customer_id).select_related('booking__customer').values(
            "id",
            "date",
            "amount",
            "remarks",
            "reference",
            document=F("id"),
            customer_name=F("booking__customer__name"),
        )
        token_data = Token.objects.filter(query_filters, customer_id=customer_id).select_related('customer').values(
            "id",
            "date",
            "amount",
            "remarks",
            document=F("id"),
            customer_name=F("customer__name"),
            reference=Value("token", output_field=CharField())
        )

        # Combine and sort by date
        combined_data = sorted(
            list(booking_data) + list(payment_data)+ list(token_data),
            key=lambda x: x["date"]
        )

        # Fetch customer information
        customer_info = Customers.objects.filter(id=customer_id).values(
            "id",
            "name",
            "father_name",
            "contact",
            "address"
        ).first()
        plot_data = Plots.objects.filter(booking_details__customer_id=customer_id).values(
            "id", "plot_number", "address"
        )
        customer_messages = CustomerMessages.objects.filter(booking__customer_id=customer_id).prefetch_related('files')
        customer_messages_data = [
            {
                "id": message.id,
                "user": message.user_id,
                "booking": message.booking_id,
                "date": message.date,
                "created_at": message.created_at,
                "updated_at": message.updated_at,
                "notes": message.notes,
                "follow_up": message.follow_up,
                "follow_up_message": message.follow_up_message,
                "files": [
                    {
                        "id": file.id,
                        "file": file.file.url,
                        "description": file.description,
                        "type": file.type,
                        "created_at": file.created_at,
                        "updated_at": file.updated_at,
                    }
                    for file in message.files.all()
                ]
            }
            for message in customer_messages
        ]

        # Calculate opening and closing balances
        # opening_balance = Booking.objects.filter(customer_id=customer_id, booking_date__lt=start_date).aggregate(total=Sum('total_amount'))['total'] or 0
        # opening_balance -= IncomingFund.objects.filter(booking__customer_id=customer_id, date__lt=start_date).aggregate(total=Sum('amount'))['total'] or 0

        # closing_balance = opening_balance
        # for entry in combined_data:
        #     if entry['reference'] == 'booking':
        #         closing_balance += entry['amount']
        #     elif entry['reference'] == 'payment':
        #         closing_balance -= entry['amount']

        response_data = {
            "customer_info": customer_info,
            "booking_data": list(booking_data),
            "plot_data": list(plot_data),
            "customer_messages": customer_messages_data,
            "opening_balance": 0,
            "closing_balance": 0,
            "transactions": combined_data
        }

        return Response(response_data)





class BalanceSheetView(APIView):

    def get(self, request):
        banks = Bank.objects.all()
        main_type_dict = defaultdict(lambda: {'total': 0, 'account_types': defaultdict(lambda: {'total': 0, 'accounts': []})})
        
        for bank in banks:
            main_type = bank.main_type
            account_type = bank.account_type
            bank_name = bank.name
            
            # Aggregate balances
            main_type_dict[main_type]['total'] += bank.balance
            main_type_dict[main_type]['account_types'][account_type]['total'] += bank.balance
            
            # Format the sub-account
            sub_account = {
                'bank_name': bank_name,
                'balance': bank.balance
            }
            main_type_dict[main_type]['account_types'][account_type]['accounts'].append(sub_account)

        # Convert to the desired output format
        result = []
        for main_type, main_data in main_type_dict.items():
            account_types_list = []
            for account_type, account_data in main_data['account_types'].items():
                account_types_list.append({
                    'account_type': account_type,
                    'total': account_data['total'],
                    'accounts': account_data['accounts']
                })
            result.append({
                'main_type': main_type,
                'total': main_data['total'],
                'account_types': account_types_list
            })
        
        return Response(result)
