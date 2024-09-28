from django.db import models
from projects.models import Projects
from booking.models import Booking
from customer.models import Customers


class Bank(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    main_type = models.CharField(max_length=100, default="asset")
    account_type = models.CharField(max_length=100)
    detail_type = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    balance = models.FloatField(default=0)
    parent_account = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_accounts",
    )

    class Meta:
        db_table = "banks"

class BankTransaction(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50)
    payment = models.FloatField(default=0)
    deposit = models.FloatField(default=0)
    transaction_date = models.DateField()
    related_table = models.CharField(max_length=50)
    related_id = models.IntegerField()
    is_deposit = models.BooleanField(default=True)
    is_cheque_clear=models.BooleanField(default=True)

    class Meta:
        db_table = "bank_transactions"

class MonthField(models.DateField):
    def to_python(self, value):
        if isinstance(value, str):
            # Convert the string value to a Python datetime object
            value += "-01"  # Append day and convert to a complete date
            value = super().to_python(value)
            if value is not None:
                return value.strftime("%Y-%m")  # Format as YYYY-MM
        return value

    def get_prep_value(self, value):
        if isinstance(value, str):
            # Ensure the value is in the correct format
            return value[:7]  # Extract only the first 7 characters (YYYY-MM)
        return value


class IncomingFund(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    reference = models.CharField(max_length=10, default="payment")
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)
    date = models.DateField()
    installement_month = MonthField(blank=True, null=True)
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    advance_payment = models.BooleanField(default=False)
    payment_type = models.CharField(max_length=20, default="cash")
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    bank = models.ForeignKey(
        Bank, related_name="payments", on_delete=models.PROTECT, blank=True, null=True
    )

    class Meta:
        db_table = "incoming_funds"


class IncomingFundDocuments(models.Model):
    incoming_fund = models.ForeignKey(
        IncomingFund, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/payments_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "incoming_funds_documents"

class ExpenseType(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "expense_type"



class ExpensePerson(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    name = models.CharField(max_length=30)
    balance = models.FloatField(default=0)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "expense_persons"


class OutgoingFund(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    payee = models.ForeignKey(Customers, on_delete=models.PROTECT,blank=True, null=True)
    date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    payment_type = models.CharField(max_length=20, default="cash")
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    bank = models.ForeignKey(
        Bank, related_name="expenses", on_delete=models.PROTECT, blank=True, null=True
    )

    class Meta:
        db_table = "outgoing_funds"


class OutgoingFundDetails(models.Model):
    outgoing_fund = models.ForeignKey(
        OutgoingFund, related_name="details", on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Bank, related_name="expenses_details", on_delete=models.PROTECT
    )
    description=models.CharField(max_length=100,blank=True,null=True)
    amount=models.FloatField(default=0)

    class Meta:
        db_table = "outgoing_funds_details"

class OutgoingFundDocuments(models.Model):
    outgoing_fund = models.ForeignKey(
        OutgoingFund, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/dealer_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "outgoing_funds_documents"

class JournalVoucher(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    type = models.CharField(max_length=10)
    date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "journal_voucher"


class PaymentReminder(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)
    remarks = models.TextField(blank=True, null=True)
    reminder_date = models.DateField()

    class Meta:
        db_table = "payments_reminder"


class BankDeposit(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    deposit_to = models.ForeignKey(Bank, on_delete=models.PROTECT)
    amount = models.FloatField(default=0)
    date = models.DateField()

    class Meta:
        db_table = "bank_deposits"


class BankDepositDetail(models.Model):
    bank_deposit = models.ForeignKey(
        BankDeposit, related_name="details", on_delete=models.CASCADE
    )
    payment = models.ForeignKey(BankTransaction, on_delete=models.PROTECT)


    class Meta:
        db_table = "bank_deposits_details"

class BankDepositTransactions(models.Model):
    bank_deposit = models.ForeignKey(
        BankDeposit, related_name="transactions", on_delete=models.CASCADE
    )
    customer = models.ForeignKey(
        Customers, on_delete=models.PROTECT, blank=True, null=True
    )
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    bank = models.ForeignKey(
        Bank, related_name="deposits", on_delete=models.PROTECT, blank=True, null=True
    )

    class Meta:
        db_table = "bank_deposits_transactions"

class BankDepositDocuments(models.Model):
    bank_deposit = models.ForeignKey(
        BankDeposit, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/payments_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_deposits_documents"

class DealerPayments(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    reference = models.CharField(max_length=10, default="payment")
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)
    date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    payment_type = models.CharField(max_length=20, default="cash")
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    bank = models.ForeignKey(
        Bank,
        related_name="dealer_payments",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "dealer_payments"


class DealerPaymentsDocuments(models.Model):
    payment = models.ForeignKey(
        DealerPayments, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/dealer_payments_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dealer_payments_documents"

class JournalEntry(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "journal_entry"

class JournalEntryLine(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry, related_name="details", on_delete=models.CASCADE
    )
    account = models.ForeignKey(Bank, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True, null=True)
    debit = models.FloatField(default=0)
    credit = models.FloatField(default=0)
    person = models.ForeignKey(
        Customers, related_name="journal_entries", on_delete=models.PROTECT,blank=True, null=True
    )

    class Meta:
        db_table = "journal_entry_details"

class JournalEntryDocuments(models.Model):
    journal_entry = models.ForeignKey(
        JournalEntry, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/journal_entries_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "journal_entry_documents"

class BankTransfer(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    date = models.DateField()
    transfer_from = models.ForeignKey(
        Bank, on_delete=models.PROTECT, related_name="bank_transfer"
    )
    transfer_to = models.ForeignKey(
        Bank, on_delete=models.PROTECT, related_name="bank_received"
    )
    amount = models.FloatField(default=0)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_transfer"

class BankTransferDocuments(models.Model):
    bank_transfer = models.ForeignKey(
        BankTransfer, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/bank_transfer_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_transfer_documents"


class ChequeClearance(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "cheque_clearance"

class ChequeClearanceDetail(models.Model):
    cheque_clearance = models.ForeignKey(
        ChequeClearance, related_name="details", on_delete=models.CASCADE
    )
    expense = models.ForeignKey(BankTransaction, on_delete=models.PROTECT)

    class Meta:
        db_table = "cheque_clearance_details"

class ChequeClearanceDocuments(models.Model):
    cheque_clearance = models.ForeignKey(
        ChequeClearance, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/cheque_clearance_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cheque_clearance_documents"