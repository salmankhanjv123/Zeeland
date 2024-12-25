from rest_framework import serializers
from payments.models import (
    IncomingFund,
    OutgoingFund,
    JournalVoucher,
    BankDepositTransactions,
    BankTransaction,
    BankDeposit,
    BankDepositDetail,
)
from booking.models import Token
from rest_framework.exceptions import ValidationError
from plots.models import Plots
from datetime import datetime


class IncomingFundReportSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField(read_only=True)
    plot = serializers.SerializerMethodField(read_only=True)

    def get_customer(self, instance):
        return instance.booking.customer.name

    def get_plot(self, instance):
        plot = instance.booking.plot
        return (
            f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
        )

    class Meta:
        model = IncomingFund
        fields = [
            "project",
            "customer",
            "plot",
            "date",
            "installement_month",
            "amount",
            "remarks",
        ]
        read_only_fields = fields


class OutgoingFundReportSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    reference = serializers.SerializerMethodField(read_only=True)
    customer_name = serializers.CharField(source="payee.name", read_only=True)

    def get_reference(self, instance):
        return "expense"

    class Meta:
        model = OutgoingFund
        fields = "__all__"


class BankDepositTransactionsSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    reference = serializers.SerializerMethodField(read_only=True)
    payment_type = serializers.SerializerMethodField(read_only=True)

    def get_reference(self, instance):
        return "expense"

    def get_payment_type(self, instance):
        return "Cash"

    class Meta:
        model = BankDepositTransactions
        fields = "__all__"


class JournalVoucherReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalVoucher
        fields = ["project", "type", "date", "amount", "remarks"]
        read_only_fields = fields


class PlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)
    block_name = serializers.CharField(source="block.name", read_only=True)  # Added block_name (salman modified)


    def get_plot_size(self, instance):
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    class Meta:
        model = Plots
        exclude = ["parent_plot", "status", "project"]


class BookingPaymentsSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="booking.customer.name", read_only=True
    )
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    plot = serializers.SerializerMethodField(read_only=True)

    def get_plot(self, instance):
        plots = instance.booking.plots.all()
        plot_info = [
            f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
            for plot in plots
        ]
        return plot_info

    class Meta:
        model = IncomingFund
        fields = "__all__"


class TokenPaymentsSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    plot = serializers.SerializerMethodField(read_only=True)
    reference = serializers.SerializerMethodField(read_only=True)

    def get_plot(self, instance):
        plots = instance.plot.all()
        plot_info = [
            f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
            for plot in plots
        ]
        return plot_info

    def get_reference(self, instance):
        return "token"

    class Meta:
        model = Token
        fields = "__all__"


class PaymentDataSerializer(serializers.ModelSerializer):
    date = serializers.DateField()
    credit = serializers.SerializerMethodField()
    debit = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source="booking.customer.name")
    document = serializers.CharField(source="document_number")
    deposit_id = serializers.SerializerMethodField()

    class Meta:
        model = IncomingFund
        fields = [
            "id",
            "date",
            "remarks",
            "reference",
            "booking_id",
            "credit",
            "debit",
            "document",
            "customer_name",
            "deposit_id",
        ]

    def to_representation(self, instance):
        """Ensure the date is serialized correctly."""
        data = super().to_representation(instance)
        if isinstance(data.get("date"), str):
            try:
                data["date"] = datetime.strptime(data["date"], "%Y-%m-%d").date()
            except ValueError:
                pass  # Keep it as string if parsing fails
        return data

    def get_credit(self, obj):
        # Custom logic for credit
        return obj.amount if obj.reference == "refund" else 0.0

    def get_debit(self, obj):
        # Custom logic for debit
        return obj.amount if obj.reference == "payment" else 0.0

    def get_deposit_id(self, obj):
        try:
            bank_transaction = BankTransaction.objects.get(
                related_id=obj.id,
                bank__detail_type="Undeposited_Funds",
                is_deposit=True,
            )
            bank_deposit = BankDeposit.objects.get(details__payment=bank_transaction)
            return bank_deposit.id
        except Exception as e:
            return None


class TokenDataSerializer(serializers.ModelSerializer):
    date = serializers.DateField()
    debit = serializers.FloatField(source="amount")
    credit = serializers.FloatField(default=0.0)
    document = serializers.CharField(source="document_number")
    customer_name = serializers.CharField(source="customer.name")
    reference = serializers.CharField(default="token")
    deposit_id = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = [
            "id",
            "date",
            "remarks",
            "debit",
            "credit",
            "document",
            "customer_name",
            "reference",
            "deposit_id",
        ]

    def to_representation(self, instance):
        """Ensure the date is serialized correctly."""
        data = super().to_representation(instance)
        if isinstance(data.get("date"), str):
            try:
                data["date"] = datetime.strptime(data["date"], "%Y-%m-%d").date()
            except ValueError:
                pass  # Keep it as string if parsing fails
        return data

    def get_deposit_id(self, obj):
        try:
            bank_transaction = BankTransaction.objects.get(
                related_id=obj.id,
                bank__detail_type="Undeposited_Funds",
                is_deposit=True,
            )
            bank_deposit = BankDeposit.objects.get(details__payment=bank_transaction)
            return bank_deposit.id
        except Exception as e:
            return None
