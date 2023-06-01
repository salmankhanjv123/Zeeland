from django.db import models
from projects.models import Projects
# Create your models here.


class Plots(models.Model):
    Types = (
        (1, 'Residential'),
        (2, 'Commercial'),
        (3, ' Main Commercial'),
    )
    Size = (
        (1, 'sq ft'),
        (2, 'Marla'),
    )
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    plot_number = models.CharField(max_length=30)
    address = models.TextField(blank=True, null=True)
    type = models.IntegerField(choices=Types)
    size_type = models.IntegerField(choices=Size)
    size = models.FloatField()
    rate = models.FloatField()
    pic = models.ImageField(upload_to='media/plots', blank=True, null=True)

    def __str__(self):
        return self.plot_number

    class Meta:
        db_table = 'plots'
