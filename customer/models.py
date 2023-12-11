from django.db import models
from projects.models import Projects
from plots.models import Plots
# Create your models here.


class Customers(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    name = models.CharField(max_length=30)
    father_name = models.CharField(max_length=30)
    contact = models.CharField(max_length=40)
    cnic = models.CharField(max_length=16, blank=True, null=True)
    address = models.TextField()
    pic = models.ImageField(upload_to='media/customer', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'customers'


class CustomerMessages(models.Model):
    plot=models.ForeignKey(Plots,on_delete=models.PROTECT)
    date=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    notes=models.TextField(blank=True,null=True)

class CustomerMessagesDocuments(models.Model):
    message=models.ForeignKey(CustomerMessages,related_name="files",on_delete=models.CASCADE)
    file=models.FileField(upload_to='media/customer_messages')
    description=models.TextField()
    type=models.CharField(max_length=20)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)