from django.db import models
from projects.models import Projects
# Create your models here.


class Plots(models.Model):
    Types = (
        (1, 'Residential'),
        (2, 'Commercial'),
        (3, ' Main Commercial'),
    )
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    plot_number = models.CharField(max_length=30)
    address = models.TextField(blank=True, null=True)
    type = models.IntegerField(choices=Types)
    marlas = models.FloatField(default=0)
    square_fts = models.FloatField(default=0)
    rate = models.FloatField()
    pic = models.ImageField(upload_to='media/plots', blank=True, null=True)

    def __str__(self):
        return self.plot_number

    def get_plot_size(self):
        marlas = self.marlas
        square_feets = self.square_fts
        size_str = ""
        if marlas > 0:
            size_str = str(marlas) + " marlas"
        if square_feets > 0:
            size_str += " " + str(square_feets) + " sq ft"
        return size_str

    class Meta:
        db_table = 'plots'
