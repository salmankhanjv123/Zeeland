from django.db import models
from projects.models import Projects
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
