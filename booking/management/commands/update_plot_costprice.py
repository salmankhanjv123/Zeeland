from django.core.management.base import BaseCommand
from plots.models import Plots

class Command(BaseCommand):
    help = 'Update cost_price for all plots'

    def handle(self, *args, **kwargs):
        plots = Plots.objects.filter(project_id=6)
        for plot in plots:
            # Calculate cost price
            marla_cost = plot.marlas * 299618
            square_ft_cost = (plot.square_fts) * (299618 / 225)
            total_cost = marla_cost + square_ft_cost

            # Update cost_price field
            plot.cost_price = round(total_cost)
            plot.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated cost_price for all plots'))
