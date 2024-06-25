from django.db import models
from projects.models import Projects
from booking.models import Booking
from customer.models import Customers



class Bank(models.Model):
    name=models.CharField(max_length=50)
    main_type=models.CharField(max_length=100,default="asset")
    account_type=models.CharField(max_length=100)
    detail_type=models.CharField(max_length=100)
    description=models.TextField(blank=True,null=True)
    balance=models.FloatField(default=0)
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_accounts')




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
    reference=models.CharField(max_length=10,default="payment")
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)
    date = models.DateField()
    installement_month = MonthField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    advance_payment=models.BooleanField(default=False)
    payment_type=models.CharField(max_length=20,default="cash")
    bank=models.ForeignKey(Bank,related_name="payments", on_delete=models.PROTECT,blank=True, null=True)
    

    class Meta:
        db_table = 'incoming_funds'


class IncomingFundDocuments(models.Model):
    incoming_fund = models.ForeignKey(IncomingFund, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/payments_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ExpenseType(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'expense_type'

    def __str__(self):
        return self.name


class ExpensePerson(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    name = models.CharField(max_length=30)
    balance = models.FloatField(default=0)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'expense_persons'


class OutgoingFund(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    person = models.ForeignKey(ExpensePerson, on_delete=models.PROTECT)
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.PROTECT)
    date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    payment_type=models.CharField(max_length=20,default="cash")
    bank=models.ForeignKey(Bank,related_name="expenses", on_delete=models.PROTECT,blank=True, null=True)
    class Meta:
        db_table = 'outgoing_funds'


class OutgoingFundDocuments(models.Model):
    outgoing_fund = models.ForeignKey(OutgoingFund, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/dealer_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class JournalVoucher(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    type = models.CharField(max_length=10)
    date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'journal_voucher'


class PaymentReminder(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)
    remarks = models.TextField(blank=True, null=True)
    reminder_date = models.DateField()

    class Meta:
        db_table = 'payments_reminder'


class BankDeposit(models.Model):
    deposit_to=models.ForeignKey(Bank,on_delete=models.PROTECT)
    amount=models.FloatField(default=0)
    date=models.DateField()

class BankDepositDetail(models.Model):
    bank_deposit=models.ForeignKey(BankDeposit,related_name="details",on_delete=models.CASCADE)
    payment=models.ForeignKey(IncomingFund,on_delete=models.PROTECT)

class BankDepositTransactions(models.Model):
    bank_deposit=models.ForeignKey(BankDeposit,related_name="transactions",on_delete=models.CASCADE)
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    reference=models.CharField(max_length=10,default="payment")
    customer = models.ForeignKey(Customers, on_delete=models.PROTECT)
    date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    payment_type=models.CharField(max_length=20,default="cash")
    bank=models.ForeignKey(Bank,related_name="deposits", on_delete=models.PROTECT,blank=True, null=True)    

class BankDepositDocuments(models.Model):
    bank_deposit = models.ForeignKey(BankDeposit, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/payments_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)