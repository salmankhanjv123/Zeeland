from rest_framework import serializers
from booking.models import Booking
from customer.models import Customers
from .models import (
    ExpenseType,
    IncomingFund,
    IncomingFundDocuments,
    OutgoingFund,
    OutgoingFundDocuments,
    JournalVoucher,
    PaymentReminder,
    ExpensePerson,
    Bank,
    BankDeposit,
    BankDepositDetail,
    BankDepositDocuments,
)
import datetime


class SubAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ["id", "name", "account_type", "detail_type", "description", "balance"]


class BankSerializer(serializers.ModelSerializer):
    sub_accounts = SubAccountSerializer(many=True, read_only=True)
    parent_account_name = serializers.CharField(
        source="parent_account.name", read_only=True
    )

    class Meta:
        model = Bank
        fields = "__all__"


class MonthField(serializers.Field):
    def to_internal_value(self, data):
        # Validate the month string and return a datetime object with day set to 1
        try:
            year, month = data.split("-")
            return datetime.datetime(int(year), int(month), 1).date()
        except (ValueError, AttributeError):
            raise serializers.ValidationError("Invalid month format. Use 'YYYY-MM'.")

    def to_representation(self, value):
        # Convert the datetime object to a month string in the format 'YYYY-MM'
        if value is not None:
            return value.strftime("%Y-%m")
        return value


class BookingSerializer(serializers.ModelSerializer):
    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_plot_info(self, instance):
        plot_number = instance.plot.plot_number
        plot_size = instance.plot.get_plot_size()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"

    class Meta:
        model = Booking
        fields = ["plot_info", "total_amount", "remaining", "total_receiving_amount"]
        read_only_fields = fields


class CustomersSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customers
        fields = ["name", "father_name", "contact", "cnic"]


class IncomingFundDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomingFundDocuments
        exclude = ["incoming_fund"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class IncomingFundSerializer(serializers.ModelSerializer):
    installement_month = MonthField()
    booking_info = BookingSerializer(source="booking", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    account_type = serializers.CharField(source="bank.account_type", read_only=True)
    customer = CustomersSerializer(source="booking.customer", read_only=True)
    files = IncomingFundDocumentsSerializer(many=True, required=False)

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        reference = validated_data["reference"]
        booking = validated_data["booking"]
        amount = validated_data["amount"]
        if reference == "payment":
            booking.total_receiving_amount += amount
            booking.remaining -= amount
        elif reference == "return":
            booking.total_receiving_amount -= amount
            booking.remaining += amount
        else:
            raise ValueError("Invalid reference type")

        booking.save()
        incoming_fund = IncomingFund.objects.create(**validated_data)
        for file_data in files_data:
            IncomingFundDocuments.objects.create(
                incoming_fund=incoming_fund, **file_data
            )
        return incoming_fund

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        reference = validated_data.get("reference", instance.reference)
        booking = instance.booking
        new_amount = validated_data.get("amount", instance.amount)
        old_amount = instance.amount
        
        if new_amount != old_amount:
            if reference == "payment":
                booking.total_receiving_amount += new_amount - old_amount
                booking.remaining -= new_amount - old_amount
            elif reference == "return":
                booking.total_receiving_amount -= new_amount - old_amount
                booking.remaining += new_amount - old_amount
            else:
                raise ValueError(f"Invalid reference type: {reference}")
            booking.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        for file_data in files_data:
            file_id = file_data.get("id", None)
            if file_id:
                file = IncomingFundDocuments.objects.get(
                    id=file_id, incoming_fund=instance
                )
                file.description = file_data.get("description", file.description)
                file.type = file_data.get("type", file.type)
                if "file" in file_data:
                    file.file = file_data.get("file", file.file)
                file.save()
            else:
                IncomingFundDocuments.objects.create(
                    incoming_fund=instance, **file_data
                )
        return instance

    class Meta:
        model = IncomingFund
        fields = "__all__"


class OutgoingFundDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutgoingFundDocuments
        exclude = ["outgoing_fund"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class OutgoingFundSerializer(serializers.ModelSerializer):
    expense_type_name = serializers.CharField(
        source="expense_type.name", read_only=True
    )
    person_name = serializers.CharField(source="person.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    account_type = serializers.CharField(source="bank.account_type", read_only=True)
    files = OutgoingFundDocumentsSerializer(many=True, required=False)

    class Meta:
        model = OutgoingFund
        fields = "__all__"

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        amount = validated_data.get("amount", 0)
        person = validated_data.get("person")
        person.balance -= amount
        person.save()
        outgoing_fund = OutgoingFund.objects.create(**validated_data)
        for file_data in files_data:
            OutgoingFund.objects.create(outgoing_fund=outgoing_fund, **file_data)
        return outgoing_fund

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        amount = validated_data.get("amount")
        if amount is not None:
            difference = amount - instance.amount
            person = instance.person
            person.balance -= difference
            person.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        for file_data in files_data:
            file_id = file_data.get("id", None)
            if file_id:
                file = OutgoingFundDocuments.objects.get(
                    id=file_id, outgoing_fund=instance
                )
                file.description = file_data.get("description", file.description)
                file.type = file_data.get("type", file.type)
                if "file" in file_data:
                    file.file = file_data.get("file", file.file)
                file.save()
            else:
                OutgoingFundDocuments.objects.create(
                    outgoing_fund=instance, **file_data
                )
        return instance


class ExpenseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseType
        fields = "__all__"


class JournalVoucherSerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalVoucher
        fields = "__all__"


class PaymentReminderSerializer(serializers.ModelSerializer):
    plot_info = serializers.SerializerMethodField(read_only=True)
    customer_info = CustomersSerializer(source="booking.customer", read_only=True)

    def get_plot_info(self, instance):
        plot_number = instance.booking.plot.plot_number
        plot_size = instance.booking.plot.get_plot_size()
        plot_type = instance.booking.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"

    class Meta:
        model = PaymentReminder
        fields = "__all__"


class ExpensePersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExpensePerson
        fields = "__all__"

    def update(self, instance, validated_data):
        added_balance = validated_data.pop("balance", 0)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.balance += added_balance
        instance.save()
        return instance


class BankDepositDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDepositDocuments
        exclude = ["bank_deposit"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class BankDepositDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDepositDetail
        exclude = ["bank_deposit"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class BankDepositSerializer(serializers.ModelSerializer):
    files = BankDepositDocumentsSerializer(many=True, required=False)
    details = BankDepositDetailSerializer(many=True, required=False)

    class Meta:
        model = BankDeposit
        fields = "__all__"

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        details_data = validated_data.pop("details", [])
        bank_deposit = BankDeposit.objects.create(**validated_data)
        for data in details_data:
            BankDepositDetail.objects.create(bank_deposit=bank_deposit, **data)
        for file_data in files_data:
            BankDepositDocuments.objects.create(bank_deposit=bank_deposit, **file_data)
        return bank_deposit
