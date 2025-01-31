from django.db import models
from projects.models import Projects
# Create your models here.

class Block(models.Model):
    name= models.CharField(max_length=30)
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)


class Plots(models.Model):
    Types = (
        (1, 'Residential'),
        (2, 'Commercial'),
        (3, ' Main Commercial'),
    )
    project = models.ForeignKey(Projects, on_delete=models.PROTECT)
    plot_number = models.CharField(max_length=30)
    block = models.ForeignKey(Block, on_delete=models.PROTECT,blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    type = models.IntegerField(choices=Types)
    marlas = models.FloatField(default=0)
    square_fts = models.FloatField(default=0)
    rate = models.FloatField(default=0)
    rate_marla = models.FloatField(default=0)
    total=models.FloatField(default=0)
    # is_parent = models.BooleanField(default=False)
    cost_price=models.FloatField(default=0)
    status = models.CharField(max_length=10, default='active')
    parent_plot = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='sub_plots')

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

class PlotsDocuments(models.Model):
    plot = models.ForeignKey(Plots, related_name="files", on_delete=models.CASCADE)
    file = models.FileField(upload_to="media/plot_files")
    description = models.TextField()
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "plots_documents"