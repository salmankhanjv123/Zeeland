from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from .models import BankTransaction, Bank


def create_or_update_bank_transaction(instance, created, related_table):
    bank_field = getattr(instance, "bank", None)
    if bank_field:
        transaction_type = "test"
        if created:
            # Create new BankTransaction
            BankTransaction.objects.create(
                bank=bank_field,
                transaction_type=transaction_type,
                amount=instance.amount,
                related_table=related_table,
                related_id=instance.id,
            )
        else:
            # Update existing BankTransaction
            try:
                transaction = BankTransaction.objects.get(
                    related_table=related_table, related_id=instance.id
                )
                transaction.bank = bank_field
                transaction.transaction_type = transaction_type
                transaction.amount = instance.amount
                transaction.save()
            except BankTransaction.DoesNotExist:
                # If the transaction doesn't exist, create it
                BankTransaction.objects.create(
                    bank=bank_field,
                    transaction_type=transaction_type,
                    amount=instance.amount,
                    related_table=related_table,
                    related_id=instance.id,
                )


@receiver(post_save, sender=apps.get_model("your_app_name", "Booking"))
def create_booking_transaction(sender, instance, created, **kwargs):
    create_or_update_bank_transaction(instance, created, "Booking")


@receiver(post_save, sender=apps.get_model("your_app_name", "Invoice"))
def create_invoice_transaction(sender, instance, created, **kwargs):
    create_or_update_bank_transaction(instance, created, "Invoice")


@receiver(post_save, sender=apps.get_model("your_app_name", "Payments"))
def create_payment_transaction(sender, instance, created, **kwargs):
    create_or_update_bank_transaction(instance, created, "Payments")


@receiver(post_save, sender=apps.get_model("your_app_name", "Refund"))
def create_refund_transaction(sender, instance, created, **kwargs):
    create_or_update_bank_transaction(instance, created, "Refund")


@receiver(post_save, sender=apps.get_model("your_app_name", "BankDeposit"))
def create_bank_deposit_transaction(sender, instance, created, **kwargs):
    create_or_update_bank_transaction(instance, created, "BankDeposit")
