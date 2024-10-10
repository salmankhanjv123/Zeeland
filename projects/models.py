from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Projects(models.Model):
    user = models.ManyToManyField(
        User, related_name="projects_list", blank=True)
    name = models.CharField(max_length=50)
    contact = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    social_links = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='media/projects', blank=True, null=True)
    cost_per_marla=models.FloatField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'projects'


class BalanceSheet(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BalanceSheetDetails(models.Model):
    balance_sheet=models.ForeignKey(BalanceSheet,related_name="details",on_delete=models.CASCADE)
    detail=models.CharField(max_length=100)


class BalanceSheetAmountDetails(models.Model):
    detail=models.ForeignKey(BalanceSheetDetails,related_name="amount_details",on_delete=models.CASCADE)
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    amount=models.FloatField(default=0)

