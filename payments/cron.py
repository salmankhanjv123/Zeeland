from django_cron import CronJobBase, Schedule
from django.utils.timezone import now
from booking.models import Booking
from .models import PaymentReminder
from django.db import transaction
from django.contrib.auth.models import User
import logging
logger = logging.getLogger(__name__)



class GeneratePaymentReminders(CronJobBase):
    RUN_EVERY_MINS = 1  # Runs daily (adjust as needed)
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'payments.generate_payment_reminders'  # Unique identifier

    def do(self):
        today = now()
        with transaction.atomic():
            logger.info(f"Running payment reminder cron job for {today}")
            day_of_month = today.day
            bookings = Booking.objects.filter(booking_type="installment_payment", project_id=6, installment_date= day_of_month, status="active")
            logger.info(f"Found {len(bookings)} active installment bookings")

            for booking in bookings:
                logger.info(f"Processing booking {booking.booking_id}")
                token_amount_received = 0.0
                if booking.token:
                    if booking.token.status!="refunded":
                        token_amount_received=booking.token.amount

                booking_received_amount = booking.total_receiving_amount
                reminder_date = today.date()  # Store a proper date
                booking_date=booking.booking_date

                booking_months_count = (today.year - booking_date.year) * 12 + (today.month - booking_date.month)
                booking_payments_total= booking_months_count * booking.installment_per_month + token_amount_received
                logger.info(f"Processing booking_payments_total {booking_payments_total}")
                logger.info(f"Processing booking_received_amount {booking_received_amount}")
                
                if booking_payments_total > booking_received_amount:
                    # deleted_count, _ = PaymentReminder.objects.filter(
                    #     booking=booking,
                    #     remarks__startswith=f"Payment not recieved for booking {booking.booking_id}"
                    # ).delete()
                    
                    # logger.info(f"Deleted {deleted_count} old payment reminders for booking {booking.booking_id}")
                    admin_user = User.objects.get(pk=1)  # Fetch the user instance
                    PaymentReminder.objects.create(
                        project=booking.project,
                        booking=booking,
                        reminder_date=reminder_date,
                        user=admin_user,
                        contact=booking.customer.contact,
                        worked_on=False,
                        created_at=today,
                        updated_at=today,
                        remarks=f"Payment not recieved for booking {booking.booking_id} outstanding amount: {float(booking_payments_total)-float(booking_received_amount)}"
                    )