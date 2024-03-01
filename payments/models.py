from django.db import models
from projects.models import Projects
from booking.models import Booking


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
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT)
    date = models.DateField()
    installement_month = MonthField()
    amount = models.FloatField()
    remarks = models.TextField(blank=True, null=True)
    advance_payment=models.BooleanField(default=False)

    class Meta:
        db_table = 'incoming_funds'


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

    class Meta:
        db_table = 'outgoing_funds'


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
