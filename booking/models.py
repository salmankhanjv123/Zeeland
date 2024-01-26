from django.db import models
from projects.models import Projects
from plots.models import Plots
from customer.models import Customers
from django.contrib.auth.models import User
# Create your models here.


class Booking(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    plot = models.ForeignKey(
        Plots, related_name="booking_details", on_delete=models.PROTECT)
    customer = models.ForeignKey(Customers, on_delete=models.PROTECT)
    booking_id = models.CharField(max_length=10)
    reference = models.CharField(max_length=30, null=True)
    reference_contact = models.CharField(max_length=20, null=True)
    booking_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    installment_plan = models.IntegerField()
    due_date = models.DateField()
    installment_date = models.IntegerField()
    installment_per_month = models.FloatField()
    remarks = models.TextField(null=True)
    total_amount = models.FloatField()
    advance = models.FloatField()
    remaining = models.FloatField()
    total_receiving_amount = models.FloatField()
    status = models.CharField(max_length=10, default='active')

    def __str__(self):
        return self.booking_id

    class Meta:
        db_table = 'booking'


class Token(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    plot = models.ForeignKey(Plots, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customers, on_delete=models.PROTECT)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expire_date = models.DateField()
    amount = models.FloatField()
    remarks = models.TextField(null=True)


class PlotResale(models.Model):
    booking=models.ForeignKey(Booking,on_delete=models.PROTECT)
    plot=models.ForeignKey(Plots,related_name="resale_plots",on_delete=models.PROTECT)
    entry_type=models.CharField(max_length=10,default="resale")
    old_plot_price=models.FloatField(default=0)
    company_amount_paid=models.FloatField(default=0)
    customer_amount_paid=models.FloatField(default=0)
    new_plot_price=models.FloatField(default=0)
    per_marla_price=models.FloatField(default=0)
    customer_profit=models.FloatField(default=0)
    company_profit=models.FloatField(default=0)
    remarks=models.TextField(blank=True,null=True)