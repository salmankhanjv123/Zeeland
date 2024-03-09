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

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'projects'


class ProjectsBalanceSheet(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    detail=models.CharField(max_length=100)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BalanceSheetDetail(models.Model):
    balance_sheet=models.ForeignKey(ProjectsBalanceSheet,related_name="payments_detail",on_delete=models.CASCADE)
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    amount=models.FloatField(default=0)

