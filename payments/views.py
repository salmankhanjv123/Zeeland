from django.db.models import Max
from django.db.models import Q, Sum,Prefetch
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
    JournalEntrySerializer,
    BankTransferSerializer,
    ChequeClearanceSerializer,
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
    BankDepositDetail,
    BankDepositTransactions,
    BankDepositDocuments,
    DealerPayments,
    JournalEntry,
    BankTransfer,
    ChequeClearance,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from datetime import date
from booking.models import Booking, Token
from customer.models import Customers


class BankViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Banks to be viewed or edited.
    """

    serializer_class = BankSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get("project")
        account_type_string = self.request.query_params.get("account_type")
        parent_account = self.request.query_params.get("parent_account")
        query_filters = Q()

        account_type = (
            [str for str in account_type_string.split(",")]
            if account_type_string
            else None
        )

        if project_id:
            query_filters &= Q(project_id=project_id)
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
        project_id = self.request.query_params.get("project")
        bank_id = self.request.query_params.get("bank_id")
        account_type = self.request.query_params.get("account_type")
        main_type = self.request.query_params.get("main_type")
        is_deposit = self.request.query_params.get("is_deposit")
        is_cheque_clear = self.request.query_params.get("is_cheque_clear")

        query_filters = Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if bank_id:
            query_filters &= Q(bank_id=bank_id)
        if account_type:
            query_filters &= Q(bank__account_type=account_type)
        if main_type:
            query_filters &= Q(bank__main_type=main_type)
        if is_deposit:
            query_filters &= Q(is_deposit=is_deposit)
        if is_cheque_clear:
            query_filters &= Q(is_cheque_clear=is_cheque_clear)
        queryset = BankTransaction.objects.filter(query_filters)
        queryset = queryset.exclude(bank__name="Discount Given")

        return queryset


class BankTransactionAPIView(APIView):
    def get(self, request, *args, **kwargs):
        project_id = self.request.query_params.get("project")
        bank_id = request.query_params.get("bank_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not bank_id or not start_date or not end_date or not project_id:
            return Response(
                {"error": "bank_id, start_date, and end_date,project_id are required"},
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
        query_filters = Q(bank_id=bank_id, project_id=project_id, is_cheque_clear=True)
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
            query_filters &= Q(booking__plots=plot_id)
        if customer_id:
            query_filters &= Q(booking__customer_id=customer_id)

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        queryset = (
            IncomingFund.objects.filter(query_filters)
            .select_related("booking", "booking__customer", "bank")
            .prefetch_related("files")
        )
        return queryset
  
    def perform_destroy(self, instance):
         # Handle discount instance and related transactions
        try:
            discount_instance = IncomingFund.objects.get(document_number=f"D-{instance.document_number}")
            
            # Delete all bank transactions related to the discount instance
            BankTransaction.objects.filter(
                related_table="incoming_funds",
                related_id=discount_instance.id
            ).delete()
            
            # Delete the discount instance
            discount_instance.delete()
        except IncomingFund.DoesNotExist:
            pass  # No discount instance exists, continue deletion of the main payment
        # Check for existing related bank transaction entries
        related_bank_transactions = BankTransaction.objects.filter(
            related_table="incoming_funds",
            related_id=instance.id,
            is_deposit=True,
            bank__detail_type="Undeposited_Funds",
        )
        if related_bank_transactions.exists():
            raise ValidationError(
                {
                    "error": "Cannot delete this entry as related bank transactions exist."
                }
            )

        BankTransaction.objects.filter(
            related_table="incoming_funds", related_id=instance.id
        ).delete()

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


class LatestPaymentView(APIView):
    
    def get(self, request):
        project_id = request.query_params.get("project_id")
        print(f"Project ID: {project_id}")

        if not project_id:
            return Response({'error': 'Project ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            filtered_payments = IncomingFund.objects.filter(project_id=project_id, reference="payment")
            print(f"Filtered Payments Count: {filtered_payments.count()}")

            if not filtered_payments.exists():
                return Response({'error': 'No payments found for this project'}, status=status.HTTP_404_NOT_FOUND)

            latest_payment = filtered_payments.latest('created_at')
            print(f"Latest Payment: {latest_payment}")
            
            serializer = IncomingFundSerializer(latest_payment)
            return Response(serializer.data)
        except Exception as e:
            print(f"Error: {e}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OutgoingFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OutgoingFund to be viewed or edited.
    """

    serializer_class = OutgoingFundSerializer

    def get_queryset(self):
        queryset = OutgoingFund.objects.all().select_related("bank")
        project_id = self.request.query_params.get("project")
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_destroy(self, instance):
        # Delete related bank transactions before deleting the OutgoingFund instance
        BankTransaction.objects.filter(
            related_table="OutgoingFund", related_id=instance.id
        ).delete()
        # Now delete the OutgoingFund instance
        instance.delete()


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


def get_plot_info(booking):
    return [
        f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
        for plot in booking.plots.all()
    ]


class DuePaymentsView(APIView):
    def get(self, request):
        project_id = request.query_params.get("project")
        today_day = date.today().day
        current_month = date.today().replace(day=1)

        # Filter active bookings
        active_bookings = Booking.objects.filter(
            status="active", booking_type="installment_payment"
        )
        
        if project_id:
            active_bookings = active_bookings.filter(project_id=project_id)

        due_payments = []

        for booking in active_bookings.prefetch_related('customer', 'plots'):
            # Get the latest installment month
            latest_payment = IncomingFund.objects.filter(booking=booking).aggregate(
                latest_installement_month=Max("installement_month")
            )

            latest_payment_obj = None
            if latest_payment["latest_installement_month"]:
                latest_payment_obj = IncomingFund.objects.filter(
                    booking=booking,
                    installement_month=latest_payment["latest_installement_month"],
                ).first()

            # Determine month difference based on the latest payment or booking date
            if latest_payment_obj:
                last_payment_month = latest_payment_obj.installement_month
            else:
                # If no payments made, use booking date as the reference
                last_payment_month = booking.booking_date

            # Calculate the month difference between last_payment_month and current_month
            month_diff = (current_month.year - last_payment_month.year) * 12 + (current_month.month - last_payment_month.month)

            # Check if installment is due this month by comparing with installment date
            if latest_payment_obj and today_day < booking.installment_date:
                month_diff -= 1  # Reduce by one month if payment was received this month
            
            if month_diff < 1:
                continue
            # Construct due payment entry
            customer = booking.customer  # Prefetch customer to avoid extra query
            plot_info = get_plot_info(booking)
            due_payments.append({
                "id": booking.id,
                "booking_id": booking.booking_id,
                "plot_info": plot_info,
                "customer_name": customer.name,
                "customer_contact": customer.contact,
                "due_date": booking.installment_date,
                "total_remaining_amount": month_diff * booking.installment_per_month,
                "month_difference": month_diff,
            })

        return Response({"due_payments": due_payments})

class BankDepositViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows IncomingFund to be viewed or edited.
    """

    serializer_class = BankDepositSerializer

    def get_queryset(self):

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        bank_id = self.request.query_params.get("bank_id")
        project_id = self.request.query_params.get("project")

        query_filters = Q()

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        if bank_id:
            query_filters &= Q(deposit_to=bank_id)
        if project_id:
            query_filters &= Q(project_id=project_id)

        queryset = BankDeposit.objects.filter(query_filters).select_related("deposit_to").prefetch_related(
        Prefetch("details", queryset=BankDepositDetail.objects.all().select_related("payment__bank")),
        Prefetch("transactions", queryset=BankDepositTransactions.objects.all().select_related("customer","bank")),
        Prefetch("files", queryset=BankDepositDocuments.objects.all())
    )

        return queryset

    def perform_destroy(self, instance):
        # Delete all related bank transactions
        BankTransaction.objects.filter(
            related_table="bank_deposits", related_id=instance.id
        ).delete()

        # Update BankDepositDetail to set is_deposit=False
        for detail in instance.details.all():
            payment = detail.payment
            payment.is_deposit = False
            payment.save()

        # Delete the BankDeposit instance
        super().perform_destroy(instance)


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

        if plot_id:
            query_filters &= Q(booking__plot_id=plot_id)
        if dealer_id:
            query_filters &= Q(booking__dealer_id=dealer_id)

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        queryset = (
            DealerPayments.objects.filter(query_filters)
            .select_related("booking", "booking__dealer", "bank")
            .prefetch_related("files", "booking__plots")
        )
        return queryset

    def perform_destroy(self, instance):
        # Delete all related bank transactions
        BankTransaction.objects.filter(
            related_table="dealer_payments", related_id=instance.id
        ).delete()

        # Then delete the journal entry
        instance.delete()


class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows IncomingFund to be viewed or edited.
    """

    serializer_class = JournalEntrySerializer

    def get_queryset(self):

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        project_id = self.request.query_params.get("project")

        query_filters = Q()

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        if project_id:
            query_filters &= Q(project_id=project_id)

        queryset = JournalEntry.objects.filter(query_filters).prefetch_related("files")
        return queryset

    def perform_destroy(self, instance):
        # Delete all related bank transactions
        BankTransaction.objects.filter(
            related_table="JournalEntry", related_id=instance.id
        ).delete()

        # Then delete the journal entry
        instance.delete()


class BankTransferViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows IncomingFund to be viewed or edited.
    """

    serializer_class = BankTransferSerializer

    def get_queryset(self):

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        project_id = self.request.query_params.get("project")

        query_filters = Q()

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        if project_id:
            query_filters &= Q(project_id=project_id)

        queryset = BankTransfer.objects.filter(query_filters).prefetch_related("files")
        return queryset

    def perform_destroy(self, instance):
        # Delete all related bank transactions
        BankTransaction.objects.filter(
            related_table="BankTransfer", related_id=instance.id
        ).delete()

        # Then delete the journal entry
        instance.delete()


class ChequeClearanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows IncomingFund to be viewed or edited.
    """

    serializer_class = ChequeClearanceSerializer

    def get_queryset(self):

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        project_id = self.request.query_params.get("project")
        query_filters = Q()

        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        if project_id:
            query_filters &= Q(project_id=project_id)
        queryset = ChequeClearance.objects.filter(query_filters).prefetch_related(
            "files"
        )
        return queryset

    def perform_destroy(self, instance):

        # Update BankDepositDetail to set is_deposit=False
        for detail in instance.details.all():
            expense = detail.expense
            expense.is_cheque_clear = False
            expense.save()

        # Delete the BankDeposit instance
        super().perform_destroy(instance)
