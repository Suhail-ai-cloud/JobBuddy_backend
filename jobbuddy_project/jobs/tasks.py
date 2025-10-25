from celery import shared_task
from django.utils import timezone
from .models import Booking, Payment
from datetime import timedelta

@shared_task
def check_no_show_bookings():
    """
    Check all accepted bookings where scheduled day passed,
    worker didn't mark as complete → mark no-show and hold payment
    """
    today = timezone.now().date()
    bookings = Booking.objects.filter(status="accepted", date__lt=today)

    for booking in bookings:
        # Check if already completed or no-show reported
        if booking.status in ["completed", "no_show_reported"]:
            continue

        booking.status = "no_show_reported"
        booking.save()

        # Hold payment in escrow
        payment = booking.payments.filter(status="pending").first()
        if payment:
            payment.hold_in_escrow()

        # Notify user and worker
        create_notification(booking.user, "booking", f"Worker didn't arrive for booking {booking.id}. Please submit proof if needed.")
        create_notification(booking.worker.user, "booking", f"Booking {booking.id} marked as no-show. Please submit proof if you arrived.")

@shared_task
def auto_resolve_disputes():
    """
    Automatically remind admin for disputes older than 2 days
    """
    threshold = timezone.now() - timedelta(days=2)
    bookings = Booking.objects.filter(status="investigating", updated_at__lte=threshold)

    for booking in bookings:
        # Notify admin
        create_notification(None, "admin", f"Booking {booking.id} has pending dispute for more than 2 days.")
