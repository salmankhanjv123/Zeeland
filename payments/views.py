from django.db.models import Max
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
import datetime
from decimal import Decimal
from rest_framework import viewsets, status
from django.db.models.signals import post_save
from django.dispatch import receiver
from .serializers import (
    IncomingFundSerializer,
    OutgoingFundSerializer,
    ExpenseTypeSerializer,
    JournalVoucherSerializer,
    PaymentReminderSerializer,
    ExpensePersonSerializer,
    BankSerializer,
    BankTransactionSerializer,
    BankDepositSerializer,
    DealerPaymentsSerializer,
)
from .models import (
    IncomingFund,
    OutgoingFund,
    ExpenseType,
    JournalVoucher,
    PaymentReminder,
    ExpensePerson,
    Bank,
    BankTransaction,
    BankDeposit,
    DealerPayments,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import date
from booking.models import Booking, Token
from customer.models import Customers


class BankViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Banks to be viewed or edited.
    """

    serializer_class = BankSerializer

    def get_queryset(self):

        account_type_string = self.request.query_params.get("account_type")
        parent_account = self.request.query_params.get("parent_account")
        query_filters = Q()
        account_type = (
            [str for str in account_type_string.split(",")]
            if account_type_string
            else None
        )
        if account_type:
            query_filters &= Q(account_type__in=account_type)
        if parent_account == "null":
            query_filters &= Q(parent_account__isnull=True)

        queryset = Bank.objects.filter(query_filters)
        return queryset


class BankTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Banks to be viewed or edited.
    """

    serializer_class = BankTransactionSerializer

    def get_queryset(self):
        bank_id = self.request.query_params.get("bank_id")
        account_type = self.request.query_params.get("account_type")
        main_type = self.request.query_params.get("main_type")
        is_deposit=self.request.query_params.get("is_deposit")
        query_filters = Q()
        if bank_id:
            query_filters &= Q(bank_id=bank_id)
        if account_type:
            query_filters &= Q(bank__account_type=account_type)
        if main_type:
            query_filters &= Q(bank__main_type=main_type)
        if is_deposit:
            query_filters &=Q(is_deposit=is_deposit)
        queryset = BankTransaction.objects.filter(query_filters)
        return queryset


class BankTransactionAPIView(APIView):
    def get(self, request, *args, **kwargs):
        bank_id = request.query_params.get("bank_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not bank_id or not start_date or not end_date:
            return Response(
                {"error": "bank_id, start_date, and end_date are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter transactions based on bank_id and date range
        query_filters = Q(bank_id=bank_id)
        transactions = BankTransaction.objects.filter(
            query_filters, transaction_date__range=[start_date, end_date]
        ).order_by("transaction_date", "id")

        # Calculate opening balance before start_date
        opening_balance_data = BankTransaction.objects.filter(
            query_filters, transaction_date__lt=start_date
        ).aggregate(deposit_sum=Sum("deposit"), payment_sum=Sum("payment"))
        opening_balance = (opening_balance_data["deposit_sum"] or 0) - (
            opening_balance_data["payment_sum"] or 0
        )

        # Prepare transaction records with running balance
        transaction_records = []
        current_balance = opening_balance
        for transaction in transactions:
            deposit = transaction.deposit
            payment = transaction.payment
            current_balance += deposit - payment
            transaction_records.append(
                {
                    "id": transaction.id,
                    "bank_id": transaction.bank_id,
                    "bank_name": transaction.bank.name,
                    "transaction_type": transaction.transaction_type,
                    "payment": str(payment),
                    "deposit": str(deposit),
                    "transaction_date": transaction.transaction_date,
                    "related_table": transaction.related_table,
                    "related_id": transaction.related_id,
                    "balance": str(current_balance),
                }
            )

        # Calculate closing balance
        closing_balance = current_balance

        response_data = {
            "opening_balance": str(opening_balance),
            "closing_balance": str(closing_balance),
            "transactions": transaction_records,
        }

        return Response(response_data)


# Ensure to add the URL route for this view in your urls.py


class IncomingFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows IncomingFund to be viewed or edited.
    """

    serializer_class = IncomingFundSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get("project")
        plot_id = self.request.query_params.get("plot_id")
        customer_id = self.request.query_params.get("customer_id")
        booking_id = self.request.query_params.get("booking_id")
        booking_type = self.request.query_params.get("booking_type")
        payment_type = self.request.query_params.get("payment_type")
        bank_id = self.request.query_params.get("bank_id")
        account_detail_type = self.request.query_params.get("account_detail_type")
        reference = self.request.query_params.get("reference")

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if reference:
            query_filters &= Q(reference=reference)
        if booking_type:
            query_filters &= Q(booking__booking_type=booking_type)
        if booking_id:
            query_filters &= Q(booking_id=booking_id)
        if payment_type:
            query_filters &= Q(payment_type=payment_type)
        if bank_id:
            query_filters &= Q(bank_id=bank_id)
        if account_detail_type:
            query_filters &= Q(bank__detail_type=account_detail_type)
            if account_detail_type == "Undeposited_Funds":
                query_filters &= Q(deposit=False)
        if plot_id:
            query_filters &= Q(booking__plot_id=plot_id)
        if customer_id:
            query_filters &= Q(booking__customer_id=customer_id)

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        queryset = (
            IncomingFund.objects.filter(query_filters)
            .select_related("booking", "booking__customer", "booking__plot", "bank")
            .prefetch_related("files")
        )
        return queryset

    def perform_destroy(self, instance):
        amount = instance.amount
        booking = instance.booking
        reference = instance.reference
        if reference == "payment":
            booking.remaining += amount
            booking.total_receiving_amount -= amount
        elif reference == "refund":
            booking.remaining -= amount
            booking.total_receiving_amount += amount
        booking.save()
        return super().perform_destroy(instance)


class OutgoingFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OutgoingFund to be viewed or edited.
    """

    serializer_class = OutgoingFundSerializer

    def get_queryset(self):
        queryset = OutgoingFund.objects.all().select_related(
            "person", "expense_type", "bank"
        )
        project_id = self.request.query_params.get("project")
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
        project_id = self.request.query_params.get("project")
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
        project_id = self.request.query_params.get("project")
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
        project_id = self.request.query_params.get("project")
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
        project_id = self.request.query_params.get("project")
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
        project = request.query_params.get("project")
        today = date.today().day
        current_month = datetime.date.today().replace(day=1)
        active_bookings = Booking.objects.filter(
            status="active", booking_type="installment_payment"
        )

        if project:
            active_bookings = active_bookings.filter(project_id=project)
        defaulter_bookings = []

        for booking in active_bookings:
            latest_payment = IncomingFund.objects.filter(booking=booking).aggregate(
                latest_installement_month=Max("installement_month")
            )
            latest = IncomingFund.objects.filter(booking=booking)
            if latest_payment["latest_installement_month"]:
                latest_payment_obj = IncomingFund.objects.filter(
                    booking=booking,
                    installement_month=latest_payment["latest_installement_month"],
                ).first()
                if (
                    latest_payment_obj.installement_month != current_month
                    and latest_payment_obj.booking.installment_date < today
                ):
                    # Calculate the difference in months
                    month_diff = (
                        current_month.year - latest_payment_obj.installement_month.year
                    ) * 12 + (
                        current_month.month
                        - latest_payment_obj.installement_month.month
                    )

                    # Append the booking object along with the month difference
                    defaulter_bookings.append(
                        {"booking": booking, "month_difference": month_diff}
                    )
            else:
                # If no payments found, add the booking to defaulter_bookings
                month_diff = (current_month.year - booking.booking_date.year) * 12 + (
                    current_month.month - booking.booking_date.month
                )

                defaulter_bookings.append(
                    {"booking": booking, "month_difference": month_diff}
                )
        due_payments = []
        for defaulter_booking in defaulter_bookings:
            booking = defaulter_booking["booking"]
            month_diff = defaulter_booking["month_difference"]
            customer = Customers.objects.get(pk=booking.customer_id)
            plot_info = get_plot_info(booking)
            due_payments.append(
                {
                    "id": booking.id,
                    "booking_id": booking.booking_id,
                    "plot_info": plot_info,
                    "customer_name": customer.name,
                    "customer_contact": customer.contact,
                    "due_date": booking.installment_date,
                    "total_remaining_amount": month_diff
                    * booking.installment_per_month,
                    "month_difference": month_diff,
                }
            )

        return Response({"due_payments": due_payments})


class BankTransactionsAPIView(APIView):

    def get(self, request):
        bank_id = request.query_params.get("bank_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not bank_id:
            return Response(
                {"error": "bank_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bank = get_object_or_404(Bank, pk=bank_id)

        date_filter = Q()

        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            date_filter &= Q(date__gte=start_date)

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            date_filter &= Q(date__lte=end_date)

        payments = bank.payments.filter(date_filter)
        expenses = bank.expenses.filter(date_filter)
        deposits = bank.deposits.filter(date_filter)

        combined = []

        for payment in payments:
            combined.append(
                {
                    "date": payment.date,
                    "reference": "payment",
                    "remarks": payment.remarks,
                    "id": payment.id,
                    "payment": 0,
                    "deposit": payment.amount,
                }
            )
        for payment in deposits:
            combined.append(
                {
                    "date": payment.date,
                    "reference": "deposits",
                    "remarks": payment.remarks,
                    "id": payment.bank_deposit_id,
                    "payment": 0,
                    "deposit": payment.amount,
                }
            )

        for expense in expenses:
            combined.append(
                {
                    "date": expense.date,
                    "reference": "expense",
                    "remarks": expense.remarks,
                    "id": expense.id,
                    "payment": expense.amount,
                    "deposit": 0,
                }
            )

        combined.sort(key=lambda x: x["date"])

        balance = 0
        for entry in combined:
            balance += entry["deposit"] - entry["payment"]
            entry["balance"] = balance

        return Response(combined, status=status.HTTP_200_OK)


class BankDepositViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows IncomingFund to be viewed or edited.
    """

    serializer_class = BankDepositSerializer

    def get_queryset(self):

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        bank_id=self.request.query_params.get("bank_id")

        query_filters = Q()

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        if bank_id:
            query_filters &= Q(deposit_to=bank_id)
            
        queryset = BankDeposit.objects.filter(query_filters).prefetch_related("files")
        return queryset


class DealerPaymentsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows DealerPayments to be viewed or edited.
    """

    serializer_class = DealerPaymentsSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get("project")
        plot_id = self.request.query_params.get("plot_id")
        dealer_id = self.request.query_params.get("dealer_id")
        booking_id = self.request.query_params.get("booking_id")
        booking_type = self.request.query_params.get("booking_type")
        payment_type = self.request.query_params.get("payment_type")
        bank_id = self.request.query_params.get("bank_id")
        account_detail_type = self.request.query_params.get("account_detail_type")
        reference = self.request.query_params.get("reference")

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if reference:
            query_filters &= Q(reference=reference)
        if booking_type:
            query_filters &= Q(booking__booking_type=booking_type)
        if booking_id:
            query_filters &= Q(booking_id=booking_id)
        if payment_type:
            query_filters &= Q(payment_type=payment_type)
        if bank_id:
            query_filters &= Q(bank_id=bank_id)
        if account_detail_type:
            query_filters &= Q(bank__detail_type=account_detail_type)
            if account_detail_type == "Undeposited_Funds":
                query_filters &= Q(deposit=False)
        if plot_id:
            query_filters &= Q(booking__plot_id=plot_id)
        if dealer_id:
            query_filters &= Q(booking__dealer_id=dealer_id)

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        queryset = (
            DealerPayments.objects.filter(query_filters)
            .select_related("booking", "booking__dealer", "booking__plot", "bank")
            .prefetch_related("files")
        )
        return queryset



def create_or_update_transaction(
    instance, related_table, transaction_type, amount_field
):
    bank_field = getattr(instance, "bank", None)
    if bank_field:
        amount = getattr(instance, amount_field, None)
        try:
            # Try to get the existing transaction
            transaction = BankTransaction.objects.get(
                related_table=related_table, related_id=instance.id
            )
            # Update the existing transaction
            transaction.bank = bank_field
            transaction.transaction_type = transaction_type
            if transaction_type == "refund":
                transaction.payment = amount
                transaction.deposit = 0
            else:
                transaction.deposit = amount
                transaction.payment = 0
            transaction.save()
        except BankTransaction.DoesNotExist:
            # If the transaction doesn't exist, create it
            if transaction_type == "refund":
                BankTransaction.objects.create(
                    bank=bank_field,
                    transaction_type=transaction_type,
                    deposit=0,
                    payment=amount,
                    related_table=related_table,
                    related_id=instance.id,
                )
            else:
                BankTransaction.objects.create(
                    bank=bank_field,
                    transaction_type=transaction_type,
                    deposit=amount,
                    payment=0,
                    related_table=related_table,
                    related_id=instance.id,
                )


@receiver(post_save, sender=IncomingFund)
def create_payment_transaction(sender, instance, **kwargs):
    create_or_update_transaction(
        instance, "incoming_funds", instance.reference, "amount"
    )


# @receiver(post_save, sender=Booking)
# def create_booking_transaction(sender, instance, **kwargs):
#     create_or_update_transaction(instance, "booking", "Booking", "advance")


@receiver(post_save, sender=Token)
def create_token_transaction(sender, instance, **kwargs):
    create_or_update_transaction(instance, "token", "Token", "amount")
