# jobs/notifications.py
from .models import Notification

def create_notification(user, type, message, booking=None):
    Notification.objects.create(
        user=user,
        type=type,           # e.g., "payment", "booking", "review"
        message=message,
        booking=booking
    )
