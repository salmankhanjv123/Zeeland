from django.core.management.base import BaseCommand
from django.db import transaction
from booking.models import Booking
from payments.models import BankTransaction, Bank

class Command(BaseCommand):
    help = 'Generate bank transactions for all existing bookings'

    def handle(self, *args, **kwargs):
        bookings = Booking.objects.all()
        
        for booking in bookings:
            try:
                self.stdout.write(f"Processing booking: {booking.id}")
                self.create_bank_transactions(booking)
                self.stdout.write(self.style.SUCCESS(f"Successfully processed booking {booking.id}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing booking {booking.id}: {e}"))

    def create_bank_transactions(self, booking):
        """Create or update bank transactions for a booking."""
        project = booking.project
        booking_date = booking.booking_date
        booking_amount = booking.total_amount or 0
        advance_amount = booking.advance or 0
        dealer_comission_amount = booking.dealer_comission_amount or 0
        plot_cost = sum(plot.cost_price for plot in booking.plots.all())


        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()
        if account_receivable_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_receivable_bank,
                transaction_type="Booking",
                payment=0,
                deposit=booking_amount,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )


        sale_bank = Bank.objects.filter(
            used_for="Sale_Account", project=project
        ).first()
        if sale_bank:
            BankTransaction.objects.create(
                project=project,
                bank=sale_bank,
                transaction_type="Booking",
                deposit=booking_amount,
                payment=0,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

        cogs_bank = Bank.objects.filter(
            used_for="Cost_of_Good_Sold", project=project
        ).first()
        if cogs_bank:
            BankTransaction.objects.create(
                project=project,
                bank=cogs_bank,
                transaction_type="Booking",
                payment=0,
                deposit=plot_cost,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )


        land_inventory_bank = Bank.objects.filter(
            used_for="Land_Inventory", project=project
        ).first()
        if land_inventory_bank:
            BankTransaction.objects.create(
                project=project,
                bank=land_inventory_bank,
                transaction_type="Booking",
                deposit=0,
                payment=plot_cost,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

        # Advance payment (credit - account receivable) (debit - bank)
        if advance_amount > 0:
            account_receivable_bank = Bank.objects.filter(
                used_for="Account_Receivable", project=project
            ).first()
            if account_receivable_bank:
                BankTransaction.objects.create(
                    project=project,
                    bank=account_receivable_bank,
                    transaction_type="Booking_Advance",
                    payment=advance_amount,
                    deposit=0,
                    transaction_date=booking_date,
                    related_table="Booking",
                    related_id=booking.id,
                )


        # Dealer Comission (credit - account payable) (debit - dealer expense)
        account_payable_bank = Bank.objects.filter(
            used_for="Account_Payable", project=project
        ).first()
        dealer_expense_bank = Bank.objects.filter(
            used_for="Dealer_Expense", project=project
        ).first()
        if dealer_comission_amount > 0 and account_payable_bank and dealer_expense_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_payable_bank,
                transaction_type="Dealer_Comission",
                payment=0,
                deposit=dealer_comission_amount,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

            BankTransaction.objects.create(
                project=project,
                bank=dealer_expense_bank,
                transaction_type="Dealer_Comission",
                payment=0,
                deposit=dealer_comission_amount,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )
