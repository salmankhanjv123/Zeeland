from django.core.management.base import BaseCommand
from payments.models import IncomingFund, Booking

class Command(BaseCommand):
    help = "Sets the reference_plot field for IncomingFund instances."

    def handle(self, *args, **kwargs):
        funds_updated = 0
        funds_with_no_plots = 0

        for fund in IncomingFund.objects.all():
            booking = fund.booking
            first_plot = booking.plots.first()

            if first_plot:
                fund.reference_plot = first_plot
                fund.save()
                funds_updated += 1
            else:
                funds_with_no_plots += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"{funds_updated} IncomingFund records updated successfully."
        ))
        self.stdout.write(self.style.WARNING(
            f"{funds_with_no_plots} IncomingFund records had no plots associated with their bookings."
        ))
