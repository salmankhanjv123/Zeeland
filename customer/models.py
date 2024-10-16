from django.db import models
from projects.models import Projects
from plots.models import Plots
from django.contrib.auth.models import User

# Create your models here.


class Department(models.Model):
    name = models.CharField(max_length=15)

    class Meta:
        db_table = "departments"


class Customers(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, blank=True, null=True
    )
    reference = models.CharField(max_length=15, default="customer")
    designation = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=30)
    father_name = models.CharField(max_length=30, blank=True, null=True)
    contact = models.CharField(max_length=40)
    cnic = models.CharField(max_length=16, blank=True, null=True)
    address = models.TextField()
    pic = models.ImageField(upload_to="media/customer", blank=True, null=True)
    gender = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)


    def __str__(self):
        return self.name

    class Meta:
        db_table = "customers"


class CustomersDocuments(models.Model):
    customer = models.ForeignKey(
        Customers, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/customer_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers_documents"


class CustomerMessages(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    booking = models.ForeignKey(
        "booking.Booking", on_delete=models.PROTECT, blank=True, null=True
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    follow_up = models.DateField(blank=True, null=True)
    follow_up_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "customers_messages"


class CustomerMessagesDocuments(models.Model):
    message = models.ForeignKey(
        CustomerMessages, related_name="files", on_delete=models.CASCADE
    )
    file = models.FileField(upload_to="media/customer_messages")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers_messages_documents"


class CustomerMessagesReminder(models.Model):
    message = models.ForeignKey(
        CustomerMessages, related_name="reminders", on_delete=models.CASCADE
    )
    date = models.DateField()
    follow_up_message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default="pending")

    class Meta:
        db_table = "customer_messages_reminder"


class Dealers(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    date = models.DateField()
    name = models.CharField(max_length=30)
    contact = models.CharField(max_length=40, blank=True, null=True)
    cnic = models.CharField(max_length=16, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "dealers"


class DealersDocuments(models.Model):
    dealer = models.ForeignKey(Dealers, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/dealer_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dealers_documents"
