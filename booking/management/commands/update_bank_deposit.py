from django.core.management.base import BaseCommand
from payments.models import BankDeposit, BankTransaction


class Command(BaseCommand):
    help = "Update payment_amount for all BankDeposit records"

    def handle(self, *args, **kwargs):
        deposits = BankDeposit.objects.prefetch_related("details__payment").all()

        for deposit in deposits:
            total_payment = sum(
                detail.payment.deposit - detail.payment.payment
                for detail in deposit.details.all()
                if detail.payment
            )
            deposit.payment_amount = total_payment
            deposit.save(update_fields=["payment_amount"])
            try:
                bank_transaction = BankTransaction.objects.get(
                    bank_id=15,
                    related_table="bank_deposits",
                    related_id=deposit.id,
                )
                # Update the BankTransaction entry
                bank_transaction.deposit = 0
                bank_transaction.payment = total_payment
                bank_transaction.save(update_fields=["deposit", "payment"])
            except BankTransaction.DoesNotExist:
                self.stderr.write(
                    self.style.WARNING(
                        f"No BankTransaction found for BankDeposit ID {deposit.id}. Skipping..."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS("Successfully updated all payment_amount fields")
        )
