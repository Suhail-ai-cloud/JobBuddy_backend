from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import razorpay
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

# ---------------- USER ----------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ("user", "User"),
        ("worker", "Worker"),
        ("admin", "Admin"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    location = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.username} ({self.role})"

    

# ---------------- WORKER ----------------
class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="worker_profile")
    skills = models.TextField(blank=True, null=True)
    availability = models.BooleanField(default=True)
    rating = models.FloatField(default=0)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    verified = models.BooleanField(default=False)
    total_jobs = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField('Category', related_name='workers', blank=True)
    
    def is_verified_active(self):
        """
        Checks if the verification is still valid (not expired)
        """
        try:
            vr = self.user.verification_request
            if vr.status == "approved" and vr.verified_until:
                if timezone.now() > vr.verified_until:
                    self.verified = False
                    self.save()
                    return False
                return True
            return False
        except WorkerVerificationRequest.DoesNotExist:
            return False

    def __str__(self):
        return f"Worker: {self.user.username}"
    
    
class WorkerAvailability(models.Model):
    worker = models.ForeignKey(
        WorkerProfile, related_name="availabilities", on_delete=models.CASCADE
    )
    date = models.DateField()
    is_blocked = models.BooleanField(default=False)  # True if worker blocks the day manually

    class Meta:
        unique_together = ("worker", "date")  # one record per worker per date

    def __str__(self):
        return f"{self.worker.user.username} - {self.date} ({'Blocked' if self.is_blocked else 'Available'})"


class WorkerPortfolio(models.Model):
    worker = models.ForeignKey(
        WorkerProfile,
        on_delete=models.CASCADE,
        related_name="portfolios"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.worker.user.username} - {self.title}"



class PortfolioMedia(models.Model):
    portfolio = models.ForeignKey(
        WorkerPortfolio,
        on_delete=models.CASCADE,
        related_name="media"
    )
    file = models.FileField(upload_to="portfolio_media/")
    is_video = models.BooleanField(default=False)

    def clean(self):
        if self.is_video:
            validate_video_duration(self.file)


class WorkerVerificationRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    worker = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_request"
    )

    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(blank=True, null=True)

    # Identity verification
    id_document = models.FileField(upload_to="verifications/id_documents/")
    selfie = models.ImageField(upload_to="verifications/selfies/")

    # Professional verification
    certificates = models.FileField(upload_to="verifications/certificates/", blank=True, null=True)
    portfolio = models.FileField(upload_to="verifications/portfolio/", blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)

    # Verification fee (optional)
    verification_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    payment_transaction_id = models.CharField(max_length=255, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    verified_until = models.DateTimeField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.worker.email} - {self.status}"

class WorkerComment(models.Model):
    portfolio = models.ForeignKey(WorkerPortfolio, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.portfolio.title}"

class BookingImage(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='booking_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Booking {self.booking.id}"
# ---------------- BOOKING ----------------
# ---------------- BOOKING ----------------


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("no_show_reported", "No Show Reported"),
        ("investigating", "Under Investigation"),
        ("completed", "Completed"),
        ("paid", "Paid"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    worker = models.ForeignKey("WorkerProfile", on_delete=models.CASCADE, related_name="bookings")
    description = models.TextField(default="No description")
    location = models.TextField(default="Not provided")
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.advance_amount == 0 and self.worker:
            from .models import SiteSettings
            settings_obj = SiteSettings.objects.first()
            advance_percentage = settings_obj.advance_percentage if settings_obj else 30
            self.advance_amount = (self.worker.daily_rate * (advance_percentage / 100))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} - {self.user.username} with {self.worker.user.username}"


class BookingImage(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="images")
    file = models.ImageField(upload_to="bookings/")

    def __str__(self):
        return f"Image for booking {self.booking.id}"


class Proof(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="proofs")
    file = models.FileField(upload_to="booking_proofs/")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Proof {self.id} for booking {self.booking.id}"

    
# ---------------- CART ----------------
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    bookings = models.ManyToManyField(Booking, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.user.username}"


# ---------------- PAYMENT ----------------
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} Wallet - {self.balance}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("held", "Held in Escrow"),
        ("released", "Released"),
        ("refunded", "Refunded"),
        ("failed", "Failed"),
    ]
    PAYMENT_TYPE_CHOICES = [
        ("advance", "Advance"),
        ("balance", "Balance"),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, default="advance")
    method = models.CharField(max_length=50, blank=True, null=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    worker_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_type.capitalize()} Payment {self.id} - {self.booking.id} - {self.status}"

    # --- Payment actions ---
    def hold_in_escrow(self, payment_id=None):
        if payment_id:
            self.razorpay_payment_id = payment_id
        self.status = "held"
        self.save()

    def release_to_worker(self):
        self.status = "released"
        self.save()

    def refund_to_user(self):
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            if self.razorpay_payment_id:
                refund = client.payment.refund(self.razorpay_payment_id, int(self.amount * 100))
                self.status = "refunded"
                self.transaction_id = refund.get("id")
            else:
                self.status = "refunded"
            self.save()
        except Exception as e:
            self.status = "failed"
            self.save()
            print(f"Refund failed: {e}")

# ---------------- REVIEW ----------------

class ReviewMedia(models.Model):
    review = models.ForeignKey('Review', on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='reviews/')

class Review(models.Model):
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, related_name="reviews", null=True, blank=True)
    rating = models.PositiveIntegerField(default=1)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.worker.user.username}"


# ---------------- NOTIFICATIONS ----------------
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("booking", "Booking"),
        ("payment", "Payment"),
        ("comment", "Comment"),
        ("review", "Review"),
        ("system", "System"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default="system")
    message = models.TextField()
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.CASCADE)
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.type}"
# ------------------------- 
# 7. CATEGORY
# -------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


# ------------------------- 
# 8. EVENTS & PROMOTIONS
# -------------------------
class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    pricing = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Promotion(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class EventPackage(models.Model):
    name = models.CharField(max_length=255, default="General Package")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    features = models.JSONField(default=list)  # list of package features
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PromotionTicket(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name="tickets")
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="promotion_tickets")
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket for {self.user.username} - {self.promotion.title}"


# ------------------------- 
# 9. ANALYTICS
# -------------------------
class Analytics(models.Model):
    worker = models.OneToOneField('WorkerProfile', on_delete=models.CASCADE, related_name="analytics")
    total_jobs = models.PositiveIntegerField(default=0)
    ratings = models.FloatField(default=0)
    earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    portfolio_views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics - {self.worker.user.username}"
class SiteSettings(models.Model):
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    advance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30.0)  # %
    currency = models.CharField(max_length=10, default="INR")

    def __str__(self):
        return f"Settings - {self.commission_rate}%"
class Payout(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    worker = models.ForeignKey("WorkerProfile", on_delete=models.CASCADE, related_name="payouts")
    booking = models.OneToOneField("Booking", on_delete=models.CASCADE, related_name="payout")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # Razorpay payout ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout {self.id} - {self.worker.user.username} - {self.status}"
    
class AuditLog(models.Model):
    action = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.SET_NULL)
    payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=[("credit", "Credit"), ("debit", "Debit")])
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount} for {self.wallet.user.username}"
    
class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject} - {self.worker.username}"


class TicketReply(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.sender.username}"

class WorkerReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ("performance", "Performance Issue"),
        ("payment", "Payment Issue"),
        ("behavior", "Behavior Issue"),
        ("no_show", "No Show"),
        ("customer_complaint", "Customer Complaint"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    worker = models.ForeignKey("WorkerProfile", on_delete=models.CASCADE, related_name="reports")
    booking = models.ForeignKey("Booking", on_delete=models.SET_NULL, null=True, blank=True, related_name="worker_reports")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="submitted_worker_reports")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES, default="other")
    description = models.TextField(help_text="Detailed description of the issue")
    evidence = models.FileField(upload_to="worker_reports/evidence/", blank=True, null=True, help_text="Optional: Image, video, or document evidence")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin review")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Worker Report"
        verbose_name_plural = "Worker Reports"
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.id} - {self.worker.user.username} ({self.report_type})"

    def mark_resolved(self):
        self.status = "resolved"
        self.resolved_at = timezone.now()
        self.save()