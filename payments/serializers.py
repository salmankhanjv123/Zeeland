from rest_framework import serializers
from booking.models import Booking,Token
from plots.models import Plots
from customer.models import Customers, Dealers
from payments.models import IncomingFund
from .models import (
    ExpenseType,
    IncomingFund,
    IncomingFundDocuments,
    OutgoingFund,
    OutgoingFundDetails,
    OutgoingFundDocuments,
    JournalVoucher,
    PaymentReminder,
    ExpensePerson,
    Bank,
    BankTransaction,
    BankDeposit,
    BankDepositTransactions,
    BankDepositDetail,
    BankDepositDocuments,
    DealerPayments,
    DealerPaymentsDocuments,
    JournalEntry,
    JournalEntryLine,
    JournalEntryDocuments,
    BankTransfer,
    BankTransferDocuments,
    
)
import datetime
from django.db import transaction
from rest_framework.exceptions import ValidationError


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


class BankTransactionSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    customer_name = serializers.SerializerMethodField()
    plot_number = serializers.SerializerMethodField()

    class Meta:
        model = BankTransaction
        fields = "__all__"

    def get_customer_name(self, obj):
        if obj.related_table == 'incoming_funds':
            try:
                related_instance = IncomingFund.objects.get(pk=obj.related_id)
                return related_instance.booking.customer.name
            except IncomingFund.DoesNotExist:
                return None
        elif obj.related_table == 'token':
            try:
                related_instance = Token.objects.get(pk=obj.related_id)
                return related_instance.customer.name
            except Token.DoesNotExist:
                return None
        return None

    def get_plot_number(self, obj):
        if obj.related_table == 'incoming_funds':
            try:
                related_instance = IncomingFund.objects.get(pk=obj.related_id)
                booking=related_instance.booking
                return f"{booking.plot.plot_number} || {booking.plot.get_plot_size()} || {booking.plot.get_type_display()}" 
            except IncomingFund.DoesNotExist:
                return None
        elif obj.related_table == 'token':
            try:
                related_instance = Token.objects.get(pk=obj.related_id)
                return f"{related_instance.plot.plot_number} || {related_instance.plot.get_plot_size()} || {related_instance.plot.get_type_display()}"  
            except Token.DoesNotExist:
                return None
        return None


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

class PlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)

    def get_plot_size(self, instance):
        # Update this method according to your requirement
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    class Meta:
        model = Plots
        fields = "__all__"  # or specify specific fields

class BookingSerializer(serializers.ModelSerializer):
    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_plot_info(self, instance):
        plot_number = instance.plot.plot_number
        plot_size = instance.plot.get_plot_size()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"


    class Meta:
        model = Booking
        fields = ["plot_info","total_amount", "remaining", "total_receiving_amount"]
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
    installement_month = MonthField(required=False)
    booking_info = BookingSerializer(source="booking", read_only=True)
    plot_info = PlotsSerializer(source="booking.plot",read_only=True)
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
        elif reference == "refund":
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
                booking.save()
            elif reference == "refund":
                booking.total_receiving_amount -= new_amount - old_amount
                booking.remaining += new_amount - old_amount
                booking.save()
            else:
                raise ValueError(f"Invalid reference type: {reference}")

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

class OutgoingFundDetailsSerializer(serializers.ModelSerializer):
    category_name=serializers.CharField(source="category.name", read_only=True)
    person_name=serializers.CharField(source="person.name", read_only=True)
    class Meta:
        model = OutgoingFundDetails
        exclude = ["outgoing_fund"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data

class OutgoingFundSerializer(serializers.ModelSerializer):
    payee_name = serializers.CharField(source="payee.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    account_type = serializers.CharField(source="bank.account_type", read_only=True)
    files = OutgoingFundDocumentsSerializer(many=True, required=False)
    details=OutgoingFundDetailsSerializer(many=True)

    class Meta:
        model = OutgoingFund
        fields = "__all__"

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        detail_data = validated_data.pop("details", [])

        outgoing_fund = OutgoingFund.objects.create(**validated_data)
        
        for file_data in files_data:
            OutgoingFundDocuments.objects.create(outgoing_fund=outgoing_fund, **file_data)
        for data in detail_data:
            OutgoingFundDetails.objects.create(outgoing_fund=outgoing_fund, **data)
        return outgoing_fund

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        detail_data = validated_data.pop("details", [])


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
    payment_detail = BankTransactionSerializer(source="payment", read_only=True)

    class Meta:
        model = BankDepositDetail
        exclude = ["bank_deposit"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class BankDepositTransactionsSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)

    class Meta:
        model = BankDepositTransactions
        exclude = ["bank_deposit"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class BankDepositSerializer(serializers.ModelSerializer):
    files = BankDepositDocumentsSerializer(many=True, required=False)
    details = BankDepositDetailSerializer(many=True, required=False)
    transactions = BankDepositTransactionsSerializer(many=True, required=False)
    deposit_to_name = serializers.CharField(source="deposit_to.name", read_only=True)

    class Meta:
        model = BankDeposit
        fields = "__all__"

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        details_data = validated_data.pop("details", [])
        transactions_data = validated_data.pop("transactions", [])

        date = validated_data.get("date")
        amount = validated_data.get("amount")
        bank = validated_data.get("deposit_to")

        try:
            with transaction.atomic():
                bank_deposit = BankDeposit.objects.create(**validated_data)
                BankTransaction.objects.create(
                    bank=bank,
                    transaction_date=date,
                    deposit=amount,
                    payment=0,
                    transaction_type="deposit",
                    related_table="bank_deposits",
                    related_id=bank_deposit.id,
                )
                for detail_data in details_data:
                    payment = detail_data.get("payment")
                    undeposit_bank = payment.bank
                    payment.is_deposit = True
                    payment.save()
                    BankDepositDetail.objects.create(
                        bank_deposit=bank_deposit, **detail_data
                    )
                BankTransaction.objects.create(
                    bank=undeposit_bank,
                    transaction_date=date,
                    deposit=0,
                    payment=amount,
                    transaction_type="deposit",
                    related_table="bank_deposits",
                    related_id=bank_deposit.id,
                )
                for data in transactions_data:
                    date = data.get("date")
                    amount = abs(data.get("amount"))
                    bank = data.get("bank")
                    BankDepositTransactions.objects.create(
                        bank_deposit=bank_deposit, **data
                    )
                    BankTransaction.objects.create(
                        bank=bank,
                        transaction_date=date,
                        payment=amount,
                        deposit=0,
                        transaction_type="deposit",
                        related_table="bank_deposits",
                        related_id=bank_deposit.id,
                    )
                for file_data in files_data:
                    BankDepositDocuments.objects.create(
                        bank_deposit=bank_deposit, **file_data
                    )
                return bank_deposit
        except Exception as e:
            raise ValidationError({"error": str(e)})

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        details_data = validated_data.pop("details", [])
        transactions_data = validated_data.pop("transactions", [])

        date = validated_data.get("date", instance.date)
        amount = validated_data.get("amount", instance.amount)
        bank = validated_data.get("deposit_to", instance.deposit_to)

        try:
            with transaction.atomic():
                instance.date = date
                instance.amount = amount
                instance.deposit_to = bank
                instance.save()

                # Update or create BankTransaction
                BankTransaction.objects.filter(
                    related_table="bank_deposits", related_id=instance.id
                ).update(bank=bank, transaction_date=date, deposit=amount)

                # Update or create BankDepositDetails
                BankDepositDetail.objects.filter(bank_deposit=instance).delete()
                for detail_data in details_data:
                    payment = detail_data.get("payment")
                    undeposit_bank = payment.bank
                    payment.is_deposit = True
                    payment.save()
                    BankDepositDetail.objects.create(
                        bank_deposit=instance, **detail_data
                    )
                    BankTransaction.objects.create(
                        bank=undeposit_bank,
                        transaction_date=date,
                        deposit=0,
                        payment=amount,
                        transaction_type="deposit",
                        related_table="bank_deposits",
                        related_id=instance.id,
                    )

                # Update or create BankDepositTransactions
                BankDepositTransactions.objects.filter(bank_deposit=instance).delete()
                for data in transactions_data:
                    BankDepositTransactions.objects.create(
                        bank_deposit=instance, **data
                    )
                    BankTransaction.objects.create(
                        bank=data.get("bank"),
                        transaction_date=data.get("date"),
                        payment=abs(data.get("amount")),
                        deposit=0,
                        transaction_type="deposit",
                        related_table="bank_deposits",
                        related_id=instance.id,
                    )

                # Update or create BankDepositDocuments
                BankDepositDocuments.objects.filter(bank_deposit=instance).delete()
                for file_data in files_data:
                    BankDepositDocuments.objects.create(
                        bank_deposit=instance, **file_data
                    )

                return instance

        except Exception as e:
            raise ValidationError({"error": str(e)})
class DealersSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dealers
        fields = ["name", "contact", "cnic", "address"]


class DealerPaymentsDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealerPaymentsDocuments
        exclude = ["payment"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class DealerPaymentsSerializer(serializers.ModelSerializer):
    files = DealerPaymentsDocumentsSerializer(many=True, required=False)
    booking_info = BookingSerializer(source="booking", read_only=True)
    dealer = DealersSerializer(source="booking.dealer", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    account_type = serializers.CharField(source="bank.account_type", read_only=True)

    class Meta:
        model = DealerPayments
        fields = "__all__"

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        payment = DealerPayments.objects.create(**validated_data)
        for file_data in files_data:
            DealerPaymentsDocuments.objects.create(payment=payment, **file_data)
        return payment

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        for file_data in files_data:
            file_id = file_data.get("id", None)
            if file_id:
                file = DealerPaymentsDocuments.objects.get(id=file_id, payment=instance)
                file.description = file_data.get("description", file.description)
                file.type = file_data.get("type", file.type)
                if "file" in file_data:
                    file.file = file_data.get("file", file.file)
                file.save()
            else:
                DealerPaymentsDocuments.objects.create(payment=instance, **file_data)
        return instance


class JournalEntryDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntryDocuments
        exclude = ["journal_entry"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class JournalEntryLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntryLine
        exclude = ["journal_entry"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data

class JournalEntrySerializer(serializers.ModelSerializer):
    details = JournalEntryLineSerializer(many=True)
    files = JournalEntryDocumentsSerializer(many=True, required=False)

    class Meta:
        model = JournalEntry
        fields = "__all__"

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        files_data = validated_data.pop('files', [])

        journal_entry = JournalEntry.objects.create(**validated_data)

        for detail_data in details_data:
            JournalEntryLine.objects.create(journal_entry=journal_entry, **detail_data)

        for file_data in files_data:
            JournalEntryDocuments.objects.create(journal_entry=journal_entry, **file_data)

        return journal_entry

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details')
        files_data = validated_data.pop('files', [])
        
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        
        instance.details.all().delete()
        for detail_data in details_data:
            JournalEntryLine.objects.create(journal_entry=instance, **detail_data)

        instance.files.all().delete()
        for file_data in files_data:
            JournalEntryDocuments.objects.create(journal_entry=instance, **file_data)

        return instance



class BankTransferDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransferDocuments
        exclude = ["bank_transfer"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data



class BankTransferSerializer(serializers.ModelSerializer):
    files = BankDepositDocumentsSerializer(many=True, required=False)
    transfer_from_name=serializers.CharField(source="transfer_from.name",read_only=True)
    transfer_to_name=serializers.CharField(source="transfer_to.name",read_only=True)

    class Meta:
        model = BankTransfer
        fields = "__all__"

    def create(self, validated_data):
        files_data = validated_data.pop('files', [])
        
        bank_transfer = BankTransfer.objects.create(**validated_data)
        for file_data in files_data:
            BankTransferDocuments.objects.create(bank_transfer=bank_transfer, **file_data)

        return bank_transfer


    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        for file_data in files_data:
            file_id = file_data.get("id", None)
            if file_id:
                file = BankTransferDocuments.objects.get(id=file_id, payment=instance)
                file.description = file_data.get("description", file.description)
                file.type = file_data.get("type", file.type)
                if "file" in file_data:
                    file.file = file_data.get("file", file.file)
                file.save()
            else:
                BankTransferDocuments.objects.create(payment=instance, **file_data)
        return instance

