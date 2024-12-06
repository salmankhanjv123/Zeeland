# views.py
from rest_framework import generics
from payments.models import (
    IncomingFund,
    OutgoingFund,
    OutgoingFundDetails,
    JournalVoucher,
    BankTransaction,
    DealerPayments,
    BankDepositTransactions,
    JournalEntryLine,
)
from customer.models import Customers, CustomerMessages, Dealers
from plots.models import Plots
from booking.models import Booking, Token, PlotResale
from .serializers import (
    IncomingFundReportSerializer,
    OutgoingFundReportSerializer,
    JournalVoucherReportSerializer,
    PlotsSerializer,
    BookingPaymentsSerializer,
    TokenPaymentsSerializer,
    PaymentDataSerializer,
    BankDepositTransactionsSerializer,
    TokenDataSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import (
    Count,
    Sum,
    functions,
    Q,
    F,
    Value,
    CharField,
    FloatField,
    Case,
    When,
)
from django.db.models.functions import Coalesce, Abs
from rest_framework.exceptions import ValidationError
from itertools import groupby
from operator import itemgetter

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
            .annotate(booking_count=Count("booking"))
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


# new reports


class DealerLedgerView(APIView):
    def get(self, request):
        project_id = request.query_params.get("project_id")
        dealer_id = request.query_params.get("dealer_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not project_id or not dealer_id or not start_date or not end_date:
            return Response(
                {
                    "error": "project_id, dealer_id, start_date, and end_date are required"
                },
                status=400,
            )

        booking_query_filters = Q(dealer_id=dealer_id)
        payment_query_filters = Q(booking__dealer_id=dealer_id)

        if project_id:
            booking_query_filters &= Q(project_id=project_id)
            payment_query_filters &= Q(project_id=project_id)

        if start_date and end_date:
            booking_query_filters &= Q(booking_date__gte=start_date) & Q(
                booking_date__lte=end_date
            )
            payment_query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        try:
            bookings = Booking.objects.filter(dealer_id=dealer_id).values(
                "id",
                "status",
                document=F("booking_id"),
            )

            booking_data = (
                Booking.objects.filter(booking_query_filters)
                .select_related("dealer")
                .values(
                    "id",
                    "remarks",
                    document=F("booking_id"),
                    credit=F("dealer_comission_amount"),
                    debit=Value(0.0),
                    date=F("booking_date"),
                    dealer_name=F("dealer__name"),
                    reference=Value("booking", output_field=CharField()),
                )
            )

            payment_data = (
                DealerPayments.objects.filter(payment_query_filters)
                .select_related("booking__dealer")
                .values(
                    "id",
                    "date",
                    "remarks",
                    "reference",
                    credit=Case(
                        When(reference="refund", then=F("amount")),
                        default=Value(0),
                        output_field=FloatField(),
                    ),
                    debit=Case(
                        When(reference="payment", then=F("amount")),
                        default=Value(0),
                        output_field=FloatField(),
                    ),
                    document=F("id"),
                    dealer_name=F("booking__dealer__name"),
                )
            )

            combined_data = sorted(
                list(booking_data) + list(payment_data), key=lambda x: x["date"]
            )

            comission_amount = (
                Booking.objects.filter(
                    dealer_id=dealer_id, booking_date__lt=start_date
                ).aggregate(
                    total_amount=Coalesce(
                        Sum("dealer_comission_amount"),
                        Value(0, output_field=FloatField()),
                    )
                )[
                    "total_amount"
                ]
                or 0.0
            )

            paid_amount = (
                DealerPayments.objects.filter(
                    booking__dealer_id=dealer_id, date__lt=start_date
                ).aggregate(
                    total_amount=Sum(
                        Case(
                            When(reference="payment", then=F("amount")),
                            When(reference="refund", then=-F("amount")),
                            default=Value(0),
                            output_field=FloatField(),
                        )
                    )
                )[
                    "total_amount"
                ]
                or 0.0
            )

            opening_balance = round((comission_amount - paid_amount), 2)
            current_balance = opening_balance

            for entry in combined_data:
                current_balance += entry["credit"] - entry["debit"]
                entry["balance"] = current_balance

            dealer_info = (
                Customers.objects.filter(id=dealer_id)
                .values("id", "name", "contact", "address")
                .first()
            )

            plot_query = Plots.objects.filter(booking__dealer=dealer_id)
            plot_serializer = PlotsSerializer(plot_query, many=True)

            total_amount = (
                Booking.objects.filter(dealer_id=dealer_id).aggregate(
                    total_amount=Coalesce(
                        Sum("dealer_comission_amount"),
                        Value(0, output_field=FloatField()),
                    )
                )["total_amount"]
                or 0.0
            )

            paid_amount = (
                DealerPayments.objects.filter(booking__dealer_id=dealer_id).aggregate(
                    total_amount=Sum(
                        Case(
                            When(reference="payment", then=F("amount")),
                            When(reference="refund", then=-F("amount")),
                            default=Value(0),
                            output_field=FloatField(),
                        )
                    )
                )["total_amount"]
                or 0.0
            )

            total_amount = round(total_amount, 2)
            remaining_amount = round(total_amount - paid_amount, 2)
            response_data = {
                "dealer_info": dealer_info,
                "booking_data": list(bookings),
                "plot_data": plot_serializer.data,
                "opening_balance": opening_balance,
                "closing_balance": current_balance,
                "total_amount": total_amount,
                "remaining_amount": remaining_amount,
                "transactions": combined_data,
            }

            return Response(response_data)
        except Exception as e:
            return Response(
                {"error": "Internal server error", "details": str(e)}, status=500
            )


class CustomerLedgerView(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        customer_id = self.request.query_params.get("customer_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        plot_id = self.request.query_params.get("plot_id")

        booking_query_filters = Q()
        token_query_filters = Q()
        payment_query_filters = Q()
        resale_query_filters = Q()

        if project_id:
            booking_query_filters &= Q(project_id=project_id)
            token_query_filters &= Q(project_id=project_id)
            payment_query_filters &= Q(project_id=project_id)
            resale_query_filters &= Q(project_id=project_id)

        if plot_id:
            booking_query_filters &= Q(plot_id=plot_id)
            token_query_filters &= Q(plot_id=plot_id)
            payment_query_filters &= Q(booking__plot_id=plot_id)
            resale_query_filters &= Q(booking__plot_id=plot_id)

        if start_date and end_date:
            booking_query_filters &= Q(booking_date__gte=start_date) & Q(
                booking_date__lte=end_date
            )
            token_query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
            payment_query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
            resale_query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        bookings = Booking.objects.filter(customer_id=customer_id).values(
            "id",
            "status",
            document=F("booking_id"),
        )

        dealers = (
            Booking.objects.filter(customer_id=customer_id)
            .exclude(dealer_id__isnull=True)
            .select_related("dealer")
            .values("dealer_id", "dealer__name")
        )

        booking_data = (
            Booking.objects.filter(booking_query_filters, customer_id=customer_id)
            .select_related("customer")
            .values(
                "id",
                "remarks",
                document=F("booking_id"),
                credit=F("total_amount"),
                debit=Value(0.0),
                date=F("booking_date"),
                customer_name=F("customer__name"),
                reference=Value("booking", output_field=CharField()),
            )
        )
        expense_data = (
            OutgoingFund.objects.filter(payee=customer_id)
            .select_related("payee")
            .values(
                "id",
                "date",
                "remarks",
                document=F("id"),
                credit=F("amount"),
                debit=Value(0.0),
                customer_name=F("payee__name"),
                reference=Value("Expenses", output_field=CharField()),
            )
        )
        bank_deposit_data = (
            BankDepositTransactions.objects.filter(customer_id=customer_id)
            .select_related("customer")
            .values(
                "id",
                "remarks",
                "date",
                document=F("id"),
                credit=F("amount"),
                debit=Value(0.0),
                customer_name=F("customer__name"),
                reference=Value("Deposits", output_field=CharField()),
            )
        )
        payment_data_query = IncomingFund.objects.filter(
            payment_query_filters, booking__customer_id=customer_id
        ).select_related("booking__customer")
        payment_data = PaymentDataSerializer(payment_data_query, many=True).data

        token_data_query = Token.objects.filter(
            token_query_filters, customer_id=customer_id
        ).select_related("customer")
        token_data = TokenDataSerializer(token_data_query, many=True).data

        resale_data = (
            PlotResale.objects.filter(
                resale_query_filters, booking__customer_id=customer_id
            )
            .select_related("customer")
            .values(
                "id",
                "date",
                "remarks",
                credit=F("amount_received"),
                debit=F("booking__total_amount"),
                document=F("id"),
                customer_name=F("booking__customer__name"),
                reference=Value("close booking", output_field=CharField()),
            )
        )
        resale_data_extra = (
            PlotResale.objects.filter(
                resale_query_filters, booking__customer_id=customer_id
            )
            .select_related("customer")
            .values(
                "id",
                "date",
                "remarks",
                debit=F("company_amount_paid"),
                credit=Value(0.0),
                document=F("id"),
                customer_name=F("booking__customer__name"),
                reference=Value("close booking", output_field=CharField()),
            )
        )
        # Combine and sort by date
        combined_data = sorted(
            list(booking_data)
            + list(payment_data)
            + list(token_data)
            + list(expense_data)
            + list(bank_deposit_data)
            + list(resale_data)
            + list(resale_data_extra),
            key=lambda x: x["date"],
        )

        booking_amount = (
            Booking.objects.filter(
                customer_id=customer_id, booking_date__lt=start_date
            ).aggregate(
                total_amount=Coalesce(
                    Sum("total_amount"), Value(0, output_field=FloatField())
                )
            )[
                "total_amount"
            ]
            or 0.0
        )
        paid_amount = (
            IncomingFund.objects.filter(
                booking__customer_id=customer_id, date__lt=start_date
            ).aggregate(
                total_amount=Sum(
                    Case(
                        When(reference="payment", then=F("amount")),
                        When(reference="refund", then=-F("amount")),
                        default=Value(0),
                        output_field=FloatField(),
                    )
                )
            )[
                "total_amount"
            ]
            or 0.0
        )
        token_amount = (
            Token.objects.filter(
                customer_id=customer_id, date__lt=start_date
            ).aggregate(
                total_amount=Coalesce(
                    Sum("amount"), Value(0, output_field=FloatField())
                )
            )[
                "total_amount"
            ]
            or 0.0
        )

        opening_balance = round(booking_amount - paid_amount - token_amount, 2)
        current_balance = opening_balance

        for entry in combined_data:
            current_balance += entry["credit"] - entry["debit"]
            entry["balance"] = current_balance
        # Fetch customer information
        customer_info = (
            Customers.objects.filter(id=customer_id)
            .values("id", "name", "father_name", "contact", "address")
            .first()
        )
        plot_query = Plots.objects.filter(booking__customer_id=customer_id)
        plot_serializer = PlotsSerializer(plot_query, many=True)
        customer_messages = CustomerMessages.objects.filter(
            booking__customer_id=customer_id
        ).prefetch_related("files")
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
                ],
            }
            for message in customer_messages
        ]

        booking_amount = (
            Booking.objects.filter(customer_id=customer_id).aggregate(
                total_amount=Coalesce(
                    Sum("total_amount"), Value(0, output_field=FloatField())
                )
            )["total_amount"]
            or 0.0
        )
        paid_amount = (
            IncomingFund.objects.filter(booking__customer_id=customer_id).aggregate(
                total_amount=Sum(
                    Case(
                        When(reference="payment", then=F("amount")),
                        When(reference="refund", then=-F("amount")),
                        default=Value(0),
                        output_field=FloatField(),
                    )
                )
            )["total_amount"]
            or 0.0
        )
        token_amount = (
            Token.objects.filter(customer_id=customer_id).aggregate(
                total_amount=Coalesce(
                    Sum("amount"), Value(0, output_field=FloatField())
                )
            )["total_amount"]
            or 0.0
        )

        total_amount = round(booking_amount, 2)
        remaining_amount = round(booking_amount - paid_amount - token_amount, 2)

        response_data = {
            "customer_info": customer_info,
            "booking_data": list(bookings),
            "plot_data": plot_serializer.data,
            "dealer_data": list(dealers),
            "customer_messages": customer_messages_data,
            "opening_balance": opening_balance,
            "total_amount": total_amount,
            "remaining_amount": remaining_amount,
            "transactions": combined_data,
        }

        return Response(response_data)


class VendorLedgerView(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        vendor_id = self.request.query_params.get("vendor_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        journal_filters = Q()
        query_filters = Q()

        if start_date and end_date:
            journal_filters &= Q(journal_entry__date__gte=start_date) & Q(
                journal_entry__date__lte=end_date
            )
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        outgoing_fund_debit = (
            OutgoingFund.objects.filter(payee=vendor_id, date__lt=start_date)
            .aggregate(total_debit=Sum("amount", output_field=FloatField()))
            .get("total_debit", 0.0)
            or 0.0
        )
        bank_deposit_debit = (
            BankDepositTransactions.objects.filter(
                customer_id=vendor_id, date__lt=start_date
            )
            .aggregate(total_debit=Sum(Abs(F("amount")), output_field=FloatField()))
            .get("total_debit", 0.0)
            or 0.0
        )
        journal_data = JournalEntryLine.objects.filter(
            person_id=vendor_id, journal_entry__date__lt=start_date
        ).aggregate(
            total_credit=Sum("credit", output_field=FloatField()),
            total_debit=Sum("debit", output_field=FloatField()),
        )
        journal_credit = journal_data.get("total_credit", 0.0) or 0.0
        journal_debit = journal_data.get("total_debit", 0.0) or 0.0
        journal_balance = journal_credit - journal_debit
        opening_balance = journal_balance - bank_deposit_debit - outgoing_fund_debit

        expense_data = (
            OutgoingFund.objects.filter(query_filters, payee=vendor_id)
            .select_related("payee")
            .values(
                "id",
                "date",
                "remarks",
                document=F("id"),
                debit=F("amount"),
                credit=Value(0.0),
                customer_name=F("payee__name"),
                reference=Value("Expenses", output_field=CharField()),
            )
        )

        bank_deposit_data = (
            BankDepositTransactions.objects.filter(query_filters, customer_id=vendor_id)
            .select_related("customer")
            .values(
                "id",
                "remarks",
                "date",
                document=F("bank_deposit"),
                debit=Abs(F("amount")),
                credit=Value(0.0),
                customer_name=F("customer__name"),
                reference=Value("Deposits", output_field=CharField()),
            )
        )

        journal_data = (
            JournalEntryLine.objects.filter(journal_filters, person_id=vendor_id)
            .select_related("person")
            .values(
                "id",
                "credit",
                "debit",
                remarks=F("description"),
                document=F("journal_entry"),
                date=F("journal_entry__date"),
                customer_name=F("person__name"),
                reference=Value("Journal", output_field=CharField()),
            )
        )

        # Combine and sort by date
        combined_data = sorted(
            list(expense_data) + list(bank_deposit_data) + list(journal_data),
            key=lambda x: x["date"],
        )

        current_balance = opening_balance

        for entry in combined_data:
            current_balance += entry["credit"] - entry["debit"]
            entry["balance"] = current_balance
        # Fetch customer information
        customer_info = (
            Customers.objects.filter(id=vendor_id)
            .values("id", "name", "father_name", "contact", "address")
            .first()
        )

        response_data = {
            "customer_info": customer_info,
            "opening_balance": opening_balance,
            "closing_balance": current_balance,
            "transactions": combined_data,
        }

        return Response(response_data)


class EmployeeLedgerView(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        vendor_id = self.request.query_params.get("employee_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        journal_filters = Q()
        query_filters = Q()

        if start_date and end_date:
            journal_filters &= Q(journal_entry__date__gte=start_date) & Q(
                journal_entry__date__lte=end_date
            )
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        outgoing_fund_debit = (
            OutgoingFund.objects.filter(payee=vendor_id, date__lt=start_date)
            .aggregate(total_debit=Sum("amount", output_field=FloatField()))
            .get("total_debit", 0.0)
            or 0.0
        )
        bank_deposit_debit = (
            BankDepositTransactions.objects.filter(
                customer_id=vendor_id, date__lt=start_date
            )
            .aggregate(total_debit=Sum(Abs(F("amount")), output_field=FloatField()))
            .get("total_debit", 0.0)
            or 0.0
        )
        journal_data = JournalEntryLine.objects.filter(
            person_id=vendor_id, journal_entry__date__lt=start_date
        ).aggregate(
            total_credit=Sum("credit", output_field=FloatField()),
            total_debit=Sum("debit", output_field=FloatField()),
        )
        journal_credit = journal_data.get("total_credit", 0.0) or 0.0
        journal_debit = journal_data.get("total_debit", 0.0) or 0.0
        journal_balance = journal_credit - journal_debit
        opening_balance = journal_balance - bank_deposit_debit - outgoing_fund_debit

        expense_data = (
            OutgoingFund.objects.filter(query_filters, payee=vendor_id)
            .select_related("payee")
            .values(
                "id",
                "date",
                "remarks",
                document=F("id"),
                debit=F("amount"),
                credit=Value(0.0),
                customer_name=F("payee__name"),
                reference=Value("Expenses", output_field=CharField()),
            )
        )

        bank_deposit_data = (
            BankDepositTransactions.objects.filter(query_filters, customer_id=vendor_id)
            .select_related("customer")
            .values(
                "id",
                "remarks",
                "date",
                document=F("id"),
                debit=Abs(F("amount")),
                credit=Value(0.0),
                customer_name=F("customer__name"),
                reference=Value("Deposits", output_field=CharField()),
            )
        )

        journal_data = (
            JournalEntryLine.objects.filter(journal_filters, person_id=vendor_id)
            .select_related("person")
            .values(
                "id",
                "credit",
                "debit",
                remarks=F("description"),
                document=F("journal_entry"),
                date=F("journal_entry__date"),
                customer_name=F("person__name"),
                reference=Value("Journal", output_field=CharField()),
            )
        )

        # Combine and sort by date
        combined_data = sorted(
            list(expense_data) + list(bank_deposit_data) + list(journal_data),
            key=lambda x: x["date"],
        )

        current_balance = opening_balance

        for entry in combined_data:
            current_balance += entry["credit"] - entry["debit"]
            entry["balance"] = current_balance
        # Fetch customer information
        customer_info = (
            Customers.objects.filter(id=vendor_id)
            .values("id", "name", "father_name", "contact", "designation", "address")
            .first()
        )

        response_data = {
            "customer_info": customer_info,
            "opening_balance": opening_balance,
            "closing_balance": current_balance,
            "transactions": combined_data,
        }

        return Response(response_data)


class PlotLedgerView(APIView):
    def get(self, request):
        plot_id = self.request.query_params.get("plot_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if not plot_id:
            return Response({"error": "plot_id parameter is required"}, status=400)

        try:
            parent_plot = Plots.objects.filter(id=plot_id).first()
            child_plots = Plots.objects.filter(parent_plot_id=plot_id)
            plots = [parent_plot] + list(child_plots)
            plot_ids = [plot.id for plot in plots]
            result = []

            for plot_id in plot_ids:
                bookings = Booking.objects.filter(plots=plot_id)

                if bookings.exists():
                    for booking in bookings:
                        booking_id = booking.id

                        booking_data = (
                            Booking.objects.filter(
                                id=booking_id,
                                booking_date__gte=start_date,
                                booking_date__lte=end_date,
                            )
                            .select_related("customer")
                            .values(
                                "id",
                                "remarks",
                                "status",
                                document=F("booking_id"),
                                credit=F("total_amount"),
                                debit=Value(0.0),
                                date=F("booking_date"),
                                customer_name=F("customer__name"),
                                reference=Value("booking", output_field=CharField()),
                            )
                        )

                        payment_data = (
                            IncomingFund.objects.filter(
                                booking_id=booking_id,
                                reference_plot=plot_id,
                                date__gte=start_date,
                                date__lte=end_date,
                            )
                            .select_related("booking__customer")
                            .values(
                                "id",
                                "date",
                                "remarks",
                                "reference",
                                "booking_id",
                                credit=Case(
                                    When(reference="refund", then=F("amount")),
                                    default=Value(0),
                                    output_field=FloatField(),
                                ),
                                debit=Case(
                                    When(reference="payment", then=F("amount")),
                                    default=Value(0),
                                    output_field=FloatField(),
                                ),
                                document=F("document_number"),
                                customer_name=F("booking__customer__name"),
                            )
                        )

                        token_data = (
                            Token.objects.filter(
                                plot=plot_id,
                                booking=booking_id,
                                date__gte=start_date,
                                date__lte=end_date,
                            )
                            .select_related("customer")
                            .values(
                                "id",
                                "date",
                                "remarks",
                                debit=F("amount"),
                                credit=Value(0.0),
                                document=F("document_number"),
                                customer_name=F("customer__name"),
                                reference=Value("token", output_field=CharField()),
                            )
                        )

                        resale_data = (
                            PlotResale.objects.filter(
                                booking=booking_id,
                                date__gte=start_date,
                                date__lte=end_date,
                            )
                            .select_related("customer")
                            .values(
                                "id",
                                "date",
                                "remarks",
                                debit=F("company_amount_paid"),
                                credit=Value(0.0),
                                document=F("id"),
                                customer_name=F("booking__customer__name"),
                                reference=Value(
                                    "close booking", output_field=CharField()
                                ),
                            )
                        )

                        combined_data = sorted(
                            list(token_data)
                            + list(booking_data)
                            + list(payment_data)
                            + list(resale_data),
                            key=lambda x: x["date"],
                        )

                        booking_amount = (
                            Booking.objects.filter(
                                id=booking_id, booking_date__lt=start_date
                            ).aggregate(
                                total_amount=Coalesce(
                                    Sum("total_amount"),
                                    Value(0, output_field=FloatField()),
                                )
                            )[
                                "total_amount"
                            ]
                            or 0.0
                        )

                        paid_amount = (
                            IncomingFund.objects.filter(
                                booking_id=booking_id,
                                reference_plot=plot_id,
                                date__lt=start_date,
                            ).aggregate(
                                total_amount=Sum(
                                    Case(
                                        When(reference="payment", then=F("amount")),
                                        When(reference="refund", then=-F("amount")),
                                        default=Value(0),
                                        output_field=FloatField(),
                                    )
                                )
                            )[
                                "total_amount"
                            ]
                            or 0.0
                        )

                        token_amount = (
                            Token.objects.filter(
                                booking=booking_id, date__lt=start_date
                            ).aggregate(
                                total_amount=Coalesce(
                                    Sum("amount"), Value(0, output_field=FloatField())
                                )
                            )[
                                "total_amount"
                            ]
                            or 0.0
                        )

                        resale_amount = (
                            PlotResale.objects.filter(
                                booking=booking_id, date__lt=start_date
                            ).aggregate(
                                total_amount=Coalesce(
                                    Sum("company_amount_paid"),
                                    Value(0, output_field=FloatField()),
                                )
                            )[
                                "total_amount"
                            ]
                            or 0.0
                        )

                        opening_balance = (
                            booking_amount - paid_amount - token_amount - resale_amount
                        )
                        current_balance = opening_balance

                        for entry in combined_data:
                            current_balance += entry["credit"] - entry["debit"]
                            entry["balance"] = current_balance

                        customer_info = Customers.objects.filter(
                            bookings__id=booking_id
                        ).values("id", "name", "father_name", "contact", "address")

                        plot_query = Plots.objects.get(id=plot_id)
                        plot_serializer = PlotsSerializer(plot_query)

                        customer_messages = CustomerMessages.objects.filter(
                            booking_id=booking_id
                        ).prefetch_related("files")
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
                                ],
                            }
                            for message in customer_messages
                        ]

                        dealer_info = (
                            Booking.objects.filter(id=booking_id)
                            .exclude(dealer_id__isnull=True)
                            .select_related("dealer")
                            .values("dealer_id", "dealer__name")
                        )

                        plot_data = plot_serializer.data
                        plot_amount = (
                            Booking.objects.filter(id=booking_id).aggregate(
                                total_amount=Coalesce(
                                    Sum("total_amount"),
                                    Value(0, output_field=FloatField()),
                                )
                            )["total_amount"]
                            or 0.0
                        )
                        paid_amount = (
                            IncomingFund.objects.filter(
                                booking_id=booking_id,
                                reference_plot=plot_id,
                            ).aggregate(
                                total_amount=Sum(
                                    Case(
                                        When(reference="payment", then=F("amount")),
                                        When(reference="refund", then=-F("amount")),
                                        default=Value(0),
                                        output_field=FloatField(),
                                    )
                                )
                            )[
                                "total_amount"
                            ]
                            or 0.0
                        )

                        token_amount = (
                            Token.objects.filter(booking=booking_id).aggregate(
                                total_amount=Coalesce(
                                    Sum("amount"), Value(0, output_field=FloatField())
                                )
                            )["total_amount"]
                            or 0.0
                        )

                        resale_amount = (
                            PlotResale.objects.filter(booking=booking_id).aggregate(
                                total_amount=Coalesce(
                                    Sum("company_amount_paid"),
                                    Value(0, output_field=FloatField()),
                                )
                            )["total_amount"]
                            or 0.0
                        )

                        remaining_amount = (
                            plot_amount - token_amount - paid_amount - resale_amount
                        )

                        response_data = {
                            "plot_data": plot_data,
                            "customer_info": list(customer_info),
                            "booking_data": list(booking_data),
                            "dealer_info": list(dealer_info),
                            "customer_messages": customer_messages_data,
                            "total_amount": plot_amount,
                            "remaining_amount": remaining_amount,
                            "opening_balance": opening_balance,
                            "closing_balance": current_balance,
                            "transactions": combined_data,
                        }
                        result.append(response_data)

                token_data_no_booking = (
                    Token.objects.filter(plot=plot_id, booking__isnull=True)
                    .select_related("customer")
                    .values(
                        "id",
                        "date",
                        "remarks",
                        debit=F("amount"),
                        credit=Value(0.0),
                        document=F("document_number"),
                        customer_name=F("customer__name"),
                        reference=Value("token", output_field=CharField()),
                    )
                )

                if token_data_no_booking.exists():
                    for token in token_data_no_booking:
                        token_id = token["id"]
                        plot_query = Plots.objects.get(id=plot_id)
                        plot_serializer = PlotsSerializer(plot_query)
                        plot_data = plot_serializer.data
                        plot_amount = plot_data.get("total")

                        token_amount = (
                            Token.objects.filter(id=token_id).aggregate(
                                total_amount=Coalesce(
                                    Sum("amount"), Value(0, output_field=FloatField())
                                )
                            )["total_amount"]
                            or 0.0
                        )
                        remaining_amount = plot_amount - token_amount

                        token_data = (
                            Token.objects.filter(id=token_id)
                            .select_related("customer")
                            .values(
                                "id",
                                "date",
                                "remarks",
                                debit=F("amount"),
                                credit=Value(0.0),
                                document=F("document_number"),
                                customer_name=F("customer__name"),
                                reference=Value("token", output_field=CharField()),
                            )
                        )

                        combined_data = sorted(
                            list(token_data), key=lambda x: x["date"]
                        )

                        opening_balance = plot_amount
                        current_balance = opening_balance

                        for entry in combined_data:
                            current_balance += entry["credit"] - entry["debit"]
                            entry["balance"] = current_balance

                        customer_info = Customers.objects.filter(
                            token__id=token_id
                        ).values("id", "name", "father_name", "contact", "address")

                        response_data = {
                            "plot_data": plot_data,
                            "customer_info": list(customer_info),
                            "booking_data": [],
                            "dealer_info": [],
                            "customer_messages": [],
                            "total_amount": plot_amount,
                            "remaining_amount": remaining_amount,
                            "opening_balance": opening_balance,
                            "closing_balance": current_balance,
                            "transactions": combined_data,
                        }
                        result.append(response_data)

                if not result:
                    plot_query = Plots.objects.get(id=plot_id)
                    plot_serializer = PlotsSerializer(plot_query)
                    plot_data = plot_serializer.data
                    plot_amount = plot_data.get("total")

                    response_data = {
                        "plot_data": plot_data,
                        "customer_info": [],
                        "booking_data": [],
                        "dealer_info": [],
                        "customer_messages": [],
                        "total_amount": plot_amount,
                        "remaining_amount": plot_amount,
                        "opening_balance": plot_amount,
                        "closing_balance": plot_amount,
                        "transactions": [],
                    }
                    result.append(response_data)

            return Response(result)

        except ValidationError as e:
            return Response({"error": str(e)}, status=400)


class BalanceSheetView(APIView):

    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)

        if start_date and end_date:
            query_filters &= Q(transaction_date__gte=start_date) & Q(
                transaction_date__lte=end_date
            )

        banks = Bank.objects.filter(
            main_type__in=["Asset", "Liabilities", "Equity"], project_id=project_id
        )

        main_type_dict = defaultdict(
            lambda: {
                "total": 0,
                "account_types": defaultdict(lambda: {"total": 0, "accounts": {}}),
            }
        )

        for bank in banks:
            main_type = bank.main_type
            account_type = bank.account_type
            bank_name = bank.name
            bank_id = bank.id
            parent_bank = bank.parent_account

            # Calculate balance
            transactions = BankTransaction.objects.filter(query_filters, bank=bank)
            balance = sum(t.deposit for t in transactions) - sum(
                t.payment for t in transactions
            )

            # Aggregate balances
            main_type_dict[main_type]["total"] += balance
            main_type_dict[main_type]["account_types"][account_type]["total"] += balance

            # Create account entry if it doesn't exist
            if (
                bank.id
                not in main_type_dict[main_type]["account_types"][account_type][
                    "accounts"
                ]
            ):
                main_type_dict[main_type]["account_types"][account_type]["accounts"][
                    bank.id
                ] = {
                    "bank_name": bank_name,
                    "bank_id": bank_id,
                    "balance": balance,
                    "sub_accounts": [],
                }
            else:
                # Update balance if account already exists (e.g., as a sub-account added earlier)
                main_type_dict[main_type]["account_types"][account_type]["accounts"][
                    bank.id
                ]["balance"] += balance

            # If the bank has a parent, add it as a sub-account
            if parent_bank:
                parent_account_type = parent_bank.account_type
                parent_main_type = parent_bank.main_type
                if (
                    parent_bank.id
                    not in main_type_dict[parent_main_type]["account_types"][
                        parent_account_type
                    ]["accounts"]
                ):
                    main_type_dict[parent_main_type]["account_types"][
                        parent_account_type
                    ]["accounts"][parent_bank.id] = {
                        "bank_name": parent_bank.name,
                        "balance": 0,  # Initial balance is 0 since it will be updated by its own entry
                        "sub_accounts": [],
                    }
                main_type_dict[parent_main_type]["account_types"][parent_account_type][
                    "accounts"
                ][parent_bank.id]["sub_accounts"].append(
                    main_type_dict[main_type]["account_types"][account_type][
                        "accounts"
                    ][bank.id]
                )
                # Remove the sub-account from the main list to avoid duplication
                del main_type_dict[main_type]["account_types"][account_type][
                    "accounts"
                ][bank.id]

        # Convert to the desired output format
        result = []
        for main_type, main_data in main_type_dict.items():
            account_types_list = []
            for account_type, account_data in main_data["account_types"].items():
                accounts_list = list(account_data["accounts"].values())
                account_types_list.append(
                    {
                        "account_type": account_type,
                        "total": account_data["total"],
                        "accounts": accounts_list,
                    }
                )
            result.append(
                {
                    "main_type": main_type,
                    "total": main_data["total"],
                    "account_types": account_types_list,
                }
            )

        return Response(result)


class ProfitReportView(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        # Define the allowed account types
        allowed_account_types = [
            "Income",
            "Other_Income",
            "Expenses",
            "Cost_of_goods_sold",
            "Other_Expenses",
        ]

        # Apply query filters for transactions
        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if start_date and end_date:
            query_filters &= Q(transaction_date__gte=start_date) & Q(
                transaction_date__lte=end_date
            )

        # Filter banks based on allowed account types
        banks = Bank.objects.filter(
            account_type__in=allowed_account_types, project_id=project_id
        )

        # Initialize the structure for account types
        account_type_dict = defaultdict(lambda: {"total": 0, "accounts": []})

        for bank in banks:
            account_type = bank.account_type
            bank_name = bank.name
            bank_id = bank.id
            parent_bank = bank.parent_account

            # Calculate balance for each bank
            transactions = BankTransaction.objects.filter(query_filters, bank=bank)
            balance = int(
                sum(t.deposit for t in transactions)
                - sum(t.payment for t in transactions)
            )
            # Create account entry
            account_entry = {
                "bank_name": bank_name,
                "bank_id": bank_id,
                "balance": balance,
                "sub_accounts": [],
            }

            # If the bank has a parent, add it as a sub-account to the parent entry
            if parent_bank:
                parent_entry = next(
                    (
                        acc
                        for acc in account_type_dict[parent_bank.account_type][
                            "accounts"
                        ]
                        if acc["bank_id"] == parent_bank.id
                    ),
                    None,
                )
                if not parent_entry:
                    # Create parent entry if it doesn't exist
                    parent_entry = {
                        "bank_name": parent_bank.name,
                        "bank_id": parent_bank.id,
                        "balance": 0,
                        "sub_accounts": [],
                    }
                    account_type_dict[parent_bank.account_type]["accounts"].append(
                        parent_entry
                    )
                # Append current bank as a sub-account
                parent_entry["sub_accounts"].append(account_entry)
            else:
                # Directly add the account if there's no parent
                account_type_dict[account_type]["accounts"].append(account_entry)

            # Update the total balance for the account type
            account_type_dict[account_type]["total"] += balance

        # Convert defaultdict to list format for final response
        result = [
            {
                "account_type": account_type,
                "total": int(account_data["total"]),
                "accounts": account_data["accounts"],
            }
            for account_type, account_data in account_type_dict.items()
        ]

        return Response(result)


class IncomingPaymentsReport(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        payment_type = self.request.query_params.get("payment_type")

        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)

        if payment_type:
            query_filters &= Q(payment_type=payment_type)

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        booking_payments = (
            IncomingFund.objects.filter(query_filters, reference="payment")
            .select_related("booking__customer", "bank")
            .prefetch_related("booking__plots")
        )
        token_payments = (
            Token.objects.filter(query_filters)
            .select_related("customer", "bank")
            .prefetch_related("plot")
        )

        booking_payments_serialized = BookingPaymentsSerializer(
            booking_payments, many=True
        ).data
        token_payments_serialized = TokenPaymentsSerializer(
            token_payments, many=True
        ).data

        combined_payments = sorted(
            booking_payments_serialized + token_payments_serialized,
            key=lambda x: x["date"],
        )

        payment_types = ["Cash", "Cheque", "Bank_Transfer"]
        grouped_payments = {
            ptype: {"total_amount": 0, "payments": []} for ptype in payment_types
        }

        for payment in combined_payments:
            payment_type = payment["payment_type"]
            if payment_type in grouped_payments:
                grouped_payments[payment_type]["total_amount"] += payment["amount"]
                grouped_payments[payment_type]["payments"].append(payment)

        response_data = [
            {
                "payment_type": ptype,
                "total_amount": data["total_amount"],
                "payments": data["payments"],
            }
            for ptype, data in grouped_payments.items()
        ]

        return Response(response_data)


class OutgoingPaymentsReport(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        payment_type = self.request.query_params.get("payment_type")

        query_filters = Q()
        deposit_query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
            deposit_query_filters &= Q(bank_deposit__project_id=project_id)

        if payment_type:
            query_filters &= Q(payment_type=payment_type)

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
            deposit_query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        booking_payments = (
            IncomingFund.objects.filter(query_filters, reference="refund")
            .select_related("booking__customer", "bank")
            .prefetch_related("booking__plots")
        )
        expense_payments = OutgoingFund.objects.filter(query_filters).select_related(
            "bank"
        )
        bank_deposit_payments = BankDepositTransactions.objects.filter(
            deposit_query_filters
        ).select_related("customer", "bank")

        booking_payments_serialized = BookingPaymentsSerializer(
            booking_payments, many=True
        ).data

        expense_payment_serialized = OutgoingFundReportSerializer(
            expense_payments, many=True
        ).data

        bank_deposit_payments_serialized = BankDepositTransactionsSerializer(
            bank_deposit_payments, many=True
        ).data

        combined_payments = sorted(
            booking_payments_serialized
            + expense_payment_serialized
            + bank_deposit_payments_serialized,
            key=lambda x: x["date"],
        )

        payment_types = ["Cash", "Cheque", "Bank_Transfer"]
        grouped_payments = {
            ptype: {"total_amount": 0, "payments": []} for ptype in payment_types
        }

        for payment in combined_payments:
            payment_type = payment["payment_type"]
            amount = abs(payment["amount"])
            if payment_type in grouped_payments:
                grouped_payments[payment_type]["total_amount"] += amount
                payment["amount"] = amount
                grouped_payments[payment_type]["payments"].append(payment)

        response_data = [
            {
                "payment_type": ptype,
                "total_amount": data["total_amount"],
                "payments": data["payments"],
            }
            for ptype, data in grouped_payments.items()
        ]

        return Response(response_data)


class IncomingChequeReport(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        bank_id = self.request.query_params.get("bank_id")
        plot_id = self.request.query_params.get("plot_id")
        customer_id = self.request.query_params.get("customer_id")

        payment_filters = Q()
        token_filters = Q()
        if project_id:
            token_filters &= Q(project_id=project_id)
            payment_filters &= Q(project_id=project_id)
        if bank_id:
            token_filters &= Q(bank_id=bank_id)
            payment_filters &= Q(bank_id=bank_id)
        if plot_id:
            token_filters &= Q(plot_id=plot_id)
            payment_filters &= Q(booking__plot_id=plot_id)
        if customer_id:
            token_filters &= Q(customer_id=customer_id)
            payment_filters &= Q(booking__customer_id=customer_id)

        if start_date and end_date:
            token_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        booking_payments = (
            IncomingFund.objects.filter(
                payment_filters, reference="payment", payment_type="Cheque"
            )
            .select_related("booking__customer", "bank")
            .prefetch_related("booking__plots")
        )

        token_payments = (
            Token.objects.filter(token_filters, payment_type="Cheque")
            .select_related("customer", "bank")
            .prefetch_related("plot")
        )

        booking_payments_serialized = BookingPaymentsSerializer(
            booking_payments, many=True
        ).data
        token_payments_serialized = TokenPaymentsSerializer(
            token_payments, many=True
        ).data

        combined_payments = sorted(
            booking_payments_serialized + token_payments_serialized,
            key=lambda x: x["date"],
        )

        return Response(combined_payments)


class OutgoingChequeReport(APIView):
    def get(self, request):
        project_id = self.request.query_params.get("project_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        bank_id = self.request.query_params.get("bank_id")

        payment_filters = Q()
        expense_filters = Q()
        if project_id:
            expense_filters &= Q(project_id=project_id)
            payment_filters &= Q(project_id=project_id)

        if bank_id:
            expense_filters &= Q(bank_id=bank_id)
            payment_filters &= Q(bank_id=bank_id)

        if start_date and end_date:
            expense_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
            payment_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)

        booking_payments = (
            IncomingFund.objects.filter(
                payment_filters, reference="refund", payment_type="Cheque"
            )
            .select_related("booking__customer", "bank")
            .prefetch_related("booking__plot")
        )

        outgoing_payments = OutgoingFund.objects.filter(
            expense_filters, payment_type="Cheque"
        ).select_related("bank")

        booking_payments_serialized = BookingPaymentsSerializer(
            booking_payments, many=True
        ).data

        outgoing_payments_serialized = OutgoingFundReportSerializer(
            outgoing_payments, many=True
        ).data

        combined_payments = sorted(
            booking_payments_serialized + outgoing_payments_serialized,
            key=lambda x: x["date"],
        )

        return Response(combined_payments)
