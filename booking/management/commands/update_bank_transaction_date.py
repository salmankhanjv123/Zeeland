from django.core.management.base import BaseCommand
from payments.models import BankDeposit, BankDepositTransactions

class Command(BaseCommand):
    help = 'Update BankDepositTransactions.date with the corresponding BankDeposit.date'

    def handle(self, *args, **kwargs):
        transactions = BankDepositTransactions.objects.select_related('bank_deposit').all()

        updated_count = 0
        for transaction in transactions:
            if transaction.bank_deposit and transaction.date != transaction.bank_deposit.date:
                transaction.date = transaction.bank_deposit.date
                transaction.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} transactions.'))
