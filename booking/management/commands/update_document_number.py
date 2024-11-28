from django.core.management.base import BaseCommand
from booking.models import Token
from payments.models import IncomingFund

class Command(BaseCommand):
    help = "Populate document_number for existing Token records."

    def handle(self, *args, **kwargs):
        projects = Token.objects.values_list('project', flat=True).distinct()

        for project_id in projects:
            tokens = Token.objects.filter(project_id=project_id).order_by('created_at')
            document_number = 1

            for token in tokens:
                token.document_number = f"{document_number:03}"
                token.save(update_fields=['document_number'])
                document_number += 1
        
        projects = IncomingFund.objects.values_list('project', flat=True).distinct()
        for project_id in projects:
            payments = IncomingFund.objects.filter(project_id=project_id).order_by('id')
            document_number = 1

            for payment in payments:
                payment.document_number = f"{document_number:03}"
                payment.save(update_fields=['document_number'])
                document_number += 1

        self.stdout.write(self.style.SUCCESS("Document numbers have been updated successfully."))
