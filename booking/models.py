from django.db import models
from projects.models import Projects
from plots.models import Plots
from customer.models import Customers, Dealers
from django.contrib.auth.models import User

# Create your models here.


class Booking(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    plot = models.ForeignKey(
        Plots, related_name="booking_details", on_delete=models.PROTECT
    )

    customer = models.ForeignKey(
        Customers, related_name="bookings", on_delete=models.PROTECT
    )

    booking_id = models.CharField(max_length=10)
    booking_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    booking_type = models.CharField(max_length=20)
    follow_up_date = models.DateField(blank=True, null=True)

    installment_plan = models.IntegerField()
    due_date = models.DateField(blank=True, null=True)
    installment_date = models.IntegerField()
    installment_per_month = models.FloatField()

    remarks = models.TextField(null=True)
    total_amount = models.FloatField()
    advance = models.FloatField()
    payment_type = models.CharField(max_length=20, default="cash")
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    bank = models.ForeignKey(
        "payments.Bank",
        related_name="advance_payments",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    remaining = models.FloatField()
    total_receiving_amount = models.FloatField()

    dealer = models.ForeignKey(
        Dealers,
        on_delete=models.PROTECT,
        related_name="bookings",
        blank=True,
        null=True,
    )
    comission_type = models.CharField(
        max_length=20, default="percentage", blank=True, null=True
    )
    dealer_per_marla_comission = models.FloatField(default=0)
    dealer_comission_percentage = models.FloatField(default=0)
    dealer_comission_amount = models.FloatField(default=0)
    status = models.CharField(max_length=10, default="active")
    token = models.ForeignKey("Token", on_delete=models.PROTECT,related_name="booking", blank=True, null=True)

    def __str__(self):
        return self.booking_id

    class Meta:
        db_table = "booking"


class BookingDocuments(models.Model):
    booking = models.ForeignKey(Booking, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/booking_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Token(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    plot = models.ForeignKey(Plots, on_delete=models.PROTECT)
    plot_amount=models.FloatField(default=0)
    customer = models.ForeignKey(Customers, on_delete=models.PROTECT)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expire_date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(null=True)
    payment_type = models.CharField(max_length=20, default="cash")
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    bank = models.ForeignKey(
        "payments.Bank",
        related_name="token_payments",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=10, default="pending")

    class Meta:
        db_table = "token"


class TokenDocuments(models.Model):
    token = models.ForeignKey(Token, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/booking_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PlotResale(models.Model):
    date = models.DateField()
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    remaining = models.FloatField(default=0)
    amount_received = models.FloatField(default=0)
    company_amount_paid = models.FloatField(default=0)
    customer_profit = models.FloatField(default=0)
    company_profit = models.FloatField(default=0)
    remarks = models.TextField(blank=True, null=True)
