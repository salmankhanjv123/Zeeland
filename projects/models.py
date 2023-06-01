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
