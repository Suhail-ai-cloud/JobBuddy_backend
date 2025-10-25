
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils import timezone
from datetime import timedelta
from .models import (
    Booking, Notification, Review, Cart, WorkerProfile, Analytics, Payment,
    Wallet, WalletTransaction, AuditLog,WorkerVerificationRequest, WorkerProfile
)
from decimal import Decimal

# ---------------- Helper Functions ----------------

@receiver(post_save, sender=WorkerVerificationRequest)
def update_worker_profile_on_status_change(sender, instance, created, **kwargs):
    """
    Automatically updates the worker profile's verified status.
    Approved = verified = True + sets 3 months validity
    Rejected = verified = False + clears validity
    """
    try:
        profile = instance.worker.worker_profile
    except WorkerProfile.DoesNotExist:
        return

    # Only update profile
    if instance.status == "approved":
        if not profile.verified:
            profile.verified = True
            profile.save(update_fields=["verified"])
        # Set verified_until if not already set
        if not instance.verified_until:
            WorkerVerificationRequest.objects.filter(pk=instance.pk).update(
                verified_until=timezone.now() + timedelta(days=90)
            )
    elif instance.status == "rejected":
        if profile.verified:
            profile.verified = False
            profile.save(update_fields=["verified"])
        if instance.verified_until is not None:
            WorkerVerificationRequest.objects.filter(pk=instance.pk).update(
                verified_until=None
            )

def create_notification(user, type, message, booking=None):
    try:
        Notification.objects.create(user=user, type=type, message=message, booking=booking)
    except Exception as e:
        # log the error if needed
        print(f"Notification error: {e}")

def log_audit(action, user=None, booking=None, payment=None, review=None, details=None):
    try:
        AuditLog.objects.create(
            action=action,
            user=user,
            booking=booking,
            payment=payment,
            review=review,
            details=details
        )
    except Exception as e:
        print(f"Audit log error: {e}")

# ---------------- BOOKING SIGNALS ----------------
@receiver(post_save, sender=Booking)
def booking_status_update(sender, instance, created, **kwargs):
    """
    Update user's cart and send notifications when booking status changes.
    Also triggers a review notification when booking is completed.
    """
    try:
        cart, _ = Cart.objects.get_or_create(user=instance.user)

        if not created:
            # Accepted Booking
            if instance.status == "accepted":
                cart.bookings.add(instance)
                create_notification(instance.user, "booking", f"Your booking with {instance.worker.user.username} is accepted.")
                log_audit("booking_accepted", user=instance.user, booking=instance, details="Booking accepted.")

            # Rejected Booking
            elif instance.status == "rejected":
                cart.bookings.remove(instance)
                create_notification(instance.user, "booking", f"Your booking with {instance.worker.user.username} has been rejected.")
                log_audit("booking_rejected", user=instance.user, booking=instance, details="Booking rejected.")

            # Completed Booking
            elif instance.status == "completed":
                cart.bookings.remove(instance)
                if instance.worker and instance.worker.user:
                    create_notification(
                        instance.user,
                        "review",
                        f"Your booking with {instance.worker.user.username} has been completed. Please leave a review!",
                        booking=instance
                    )
                log_audit("booking_completed", user=instance.user, booking=instance, details="Booking completed.")

    except Exception as e:
        print(f"Booking signal error: {e}")


# ---------------- REVIEW SIGNALS ----------------
@receiver(post_save, sender=Review)
def update_worker_rating(sender, instance, created, **kwargs):
    """
    Update worker's average rating and analytics when a new review is added.
    Notify worker of new review.
    """
    try:
        worker = instance.worker
        all_reviews = worker.reviews.all()
        worker.rating = round(sum([r.rating for r in all_reviews]) / len(all_reviews), 2)
        worker.total_jobs = len(all_reviews)
        worker.save()

        # Update analytics
        analytics, _ = Analytics.objects.get_or_create(worker=worker)
        analytics.total_jobs = worker.total_jobs
        analytics.ratings = worker.rating
        analytics.save()

        create_notification(worker.user, "review", f"You received a new review from {instance.user.username}.")
        log_audit("review_created", user=instance.user, review=instance, booking=instance.booking, details="New review added.")

    except Exception as e:
        print(f"Review signal error: {e}")


# ---------------- PAYMENT SIGNALS ----------------
@receiver(post_save, sender=Payment)
def payment_notification(sender, instance, created, **kwargs):
    try:
        if instance.status == "completed":
            booking = instance.booking
            create_notification(
                booking.user,
                "payment",
                f"Your payment of ₹{instance.amount} for your booking with {booking.worker.user.username} on {booking.date} has been successful."
            )
            log_audit("payment_completed", user=booking.user, payment=instance, booking=booking, details="Payment completed.")

            # Update worker wallet
            worker_user = booking.worker.user
            wallet, _ = Wallet.objects.get_or_create(user=worker_user)
            wallet.balance += Decimal(instance.worker_amount)
            wallet.save()

            WalletTransaction.objects.create(
                user=worker_user,
                amount=instance.worker_amount,
                transaction_type="credit",
                booking=booking,
                payment=instance,
                details="Payment released from completed booking."
            )

    except Exception as e:
        print(f"Payment signal error: {e}")


# ---------------- BOOKING DELETE SIGNAL ----------------
@receiver(post_delete, sender=Booking)
def remove_booking_from_cart(sender, instance, **kwargs):
    """
    Remove deleted booking from any carts automatically
    """
    try:
        carts = Cart.objects.filter(bookings=instance)
        for cart in carts:
            cart.bookings.remove(instance)
        log_audit("booking_deleted", booking=instance, details="Booking removed from carts due to deletion.")
    except Exception as e:
        print(f"Booking delete signal error: {e}")
