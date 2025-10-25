import razorpay
from decimal import Decimal
from .models import Payment
from .notifications import create_notification
from .audit import log_audit
from django.conf import settings as django_settings

def refund_payment_for_booking(booking):
    """
    Refunds the advance payment for a booking, silently handles exceptions.
    Works for both Razorpay and offline payments.
    """
    payment = Payment.objects.filter(booking=booking, status="pending").first()
    if not payment:
        return  # nothing to refund

    try:
        if payment.razorpay_order_id:
            client = razorpay.Client(auth=(django_settings.RAZORPAY_KEY_ID, django_settings.RAZORPAY_KEY_SECRET))
            refund_amount = int(payment.amount * 100)
            refund = client.payment.refund(payment.razorpay_order_id, refund_amount)

            payment.status = "refunded"
            payment.transaction_id = refund.get("id")
            payment.save()

            create_notification(booking.user, "payment", f"Your payment for booking {booking.id} has been refunded.")
            log_audit("payment_refunded", user=booking.user, booking=booking, payment=payment)
        else:
            payment.status = "refunded"
            payment.save()
            create_notification(booking.user, "payment", f"Your payment for booking {booking.id} has been refunded.")
            log_audit("payment_refunded_offline", user=booking.user, booking=booking, payment=payment)

    except Exception as e:
        log_audit("payment_refund_failed", user=booking.user, booking=booking, payment=payment, details=str(e))
