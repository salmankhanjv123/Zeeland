from django.core.management.base import BaseCommand
from payments.models import IncomingFund, BankTransaction, Bank

class Command(BaseCommand):
    help = 'Update all existing payment transactions'

    def handle(self, *args, **kwargs):
        # Get all IncomingFunds with reference as 'payment'
        incoming_funds = IncomingFund.objects.filter(reference='payment')
        
        for fund in incoming_funds:
            try:
                # Update bank transactions logic for each payment
                self.update_bank_transactions(fund)
                self.stdout.write(self.style.SUCCESS(f'Successfully updated transactions for IncomingFund ID {fund.id}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing IncomingFund ID {fund.id}: {str(e)}'))

    def update_bank_transactions(self, fund):
        """Update bank transactions for the given IncomingFund."""
        project = fund.project
        date = fund.date
        reference = fund.reference
        amount = fund.amount
        bank = fund.bank
        payment_type = fund.payment_type
        is_deposit = bank.detail_type != "Undeposited_Funds"
        is_cheque_clear = payment_type != "Cheque"

        # Determine transaction type and amounts
        transaction_type = "Customer_Payment" if reference == "payment" else "Customer_Refund"
        payment_amount = amount if reference == "payment" else 0
        deposit_amount = 0 if reference == "payment" else amount

        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()

        # Update or create the transaction for the account receivable bank
        BankTransaction.objects.create(
            project=project,
            bank=account_receivable_bank,
            transaction_type=transaction_type,
            payment=payment_amount,
            deposit=deposit_amount,
            transaction_date=date,
            related_table="incoming_funds",
            related_id=fund.id,
        )


