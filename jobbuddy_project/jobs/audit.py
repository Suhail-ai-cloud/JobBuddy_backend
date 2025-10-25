# jobs/audit.py
from .models import AuditLog

def log_audit(action, user=None, booking=None, payment=None, details=""):
    AuditLog.objects.create(
        action=action,
        user=user,
        booking=booking,
        payment=payment,
        details=details
    )
