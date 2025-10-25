from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Avg
from rest_framework import serializers
from .models import Booking, WorkerProfile, Payment, WorkerAvailability, User
from decimal import Decimal
import razorpay
from django.conf import settings
from decimal import Decimal
from rest_framework.response import Response
from rest_framework import status
User = get_user_model()
from .models import *
class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD  # Important: use email instead of username

    def validate(self, attrs):
        # attrs will have 'email' and 'password'
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user with this email.")

        # Add username for the parent validation
        attrs['username'] = user.username
        return super().validate(attrs)






class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=[('user', 'User'), ('worker', 'Worker')])

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # ensures password is hashed
        user.save()
        return user
# ---------------- USER ----------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ["id", "role"]

class WorkerVerificationSerializer(serializers.ModelSerializer):
    worker_profile_verified = serializers.SerializerMethodField()

    class Meta:
        model = WorkerVerificationRequest
        fields = [
            "id", "worker", "full_name", "date_of_birth", "id_document", "selfie",
            "certificates", "portfolio", "additional_info", "verification_fee",
            "payment_transaction_id", "status", "admin_notes", "created_at", "updated_at",
            "worker_profile_verified",
        ]
        read_only_fields = ["status", "admin_notes", "created_at", "updated_at", "worker_profile_verified"]

    def get_worker_profile_verified(self, obj):
        """
        Returns True only if the worker's profile is verified and verification
        has not expired (3 months validity)
        """
        try:
            profile = obj.worker.worker_profile
        except WorkerProfile.DoesNotExist:
            return False

        # Check if there is a verification request and it has a verified_until date
        if obj.status == "approved" and obj.verified_until:
            if timezone.now() <= obj.verified_until:
                return True

        return False

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "location"]
# ---------------- WORKER ----------------
class WorkerCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = WorkerComment
        fields = "__all__"

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    
class PortfolioMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioMedia
        fields = ["id", "file", "is_video"]

# serializers.py

class WorkerPortfolioSerializer(serializers.ModelSerializer):
    comments = WorkerCommentSerializer(many=True, read_only=True)
    media = PortfolioMediaSerializer(many=True, read_only=True)
   

    class Meta:
        model = WorkerPortfolio
        # Exclude worker so it's not required in POST
        exclude = ['worker']

    def validate_video(self, video):
        if video:
            max_size = 20 * 1024 * 1024  # 20 MB
            if video.size > max_size:
                raise serializers.ValidationError("Video must be under 20MB (~3 minutes).")

            valid_mime_types = ["video/mp4", "video/webm", "video/quicktime"]
            if video.content_type not in valid_mime_types:
                raise serializers.ValidationError("Only MP4, WebM, or MOV videos are allowed.")

        return video


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class WorkerProfileSearchSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username')
    user = UserSerializer(read_only=True) 
    categories = CategorySerializer(many=True)

    class Meta:
        model = WorkerProfile
        fields = [
            'id', 'user_name', 'skills', 'rating', 'total_jobs',
            'availability', 'verified', 'categories', 'user'
        ]

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'location', 'phone']

    def create(self, validated_data):
        role = validated_data.get('role', 'user')
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            role=role,
            location=validated_data.get('location'),
            phone=validated_data.get('phone')
        )
        user.set_password(validated_data['password'])
        user.save()

        if role == 'worker':
            WorkerProfile.objects.create(user=user)
        return user
# serializers.py
class WorkerAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerAvailability
        fields = ["id", "date", "is_blocked"]

class WorkerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    portfolios = WorkerPortfolioSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    categories = serializers.StringRelatedField(many=True)
    availabilities = WorkerAvailabilitySerializer(many=True, read_only=True)
    advance_amount = serializers.SerializerMethodField()

    class Meta:
        model = WorkerProfile
        fields = [
            "id", "user", "skills", "availability", "rating", "verified","daily_rate",
            "total_jobs", "portfolios", "reviews", "average_rating", "availabilities","categories","advance_amount"
        ]

    def get_reviews(self, obj):
        return ReviewSerializer(obj.reviews.all(), many=True).data

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews.exists():
            # Option 1: use admin rating as priority
            return round(obj.rating, 2) if obj.rating else round(sum([r.rating for r in reviews])/reviews.count(), 2)
        # fallback
        return round(obj.rating, 2) if obj.rating else 0
    def get_advance_amount(self, obj):
        settings = SiteSettings.objects.first()
        percentage = settings.advance_percentage if settings else 30  # default 30%
        return round(obj.daily_rate * Decimal(percentage) / 100, 2)

class PayoutSerializer(serializers.ModelSerializer):
    worker_name = serializers.CharField(source="worker.user.username", read_only=True)
    booking_date = serializers.DateField(source="booking.date", read_only=True)

    class Meta:
        model = Payout
        fields = ["id", "worker", "worker_name", "booking", "booking_date", "amount", "status", "transaction_id", "created_at"]
        read_only_fields = ["id", "worker_name", "booking_date", "transaction_id", "created_at"]
# ---------------- BOOKING ----------------
# class BookingSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField(read_only=True)
#     worker = serializers.StringRelatedField(read_only=True)
#     payments = serializers.SerializerMethodField()

#     class Meta:
#         model = Booking
#         fields = "__all__"

#     def get_payments(self, obj):
#         return PaymentSerializer(obj.payments.all(), many=True).data

#     def validate(self, data):
#         worker = data.get("worker")
#         booking_date = data.get("date")

#         if Booking.objects.filter(worker=worker, date=booking_date, status__in=["pending", "accepted"]).exists():
#             raise serializers.ValidationError({"date": "Worker already booked for this date."})

#         if WorkerAvailability.objects.filter(worker=worker, date=booking_date, is_blocked=True).exists():
#             raise serializers.ValidationError({"date": "This date is blocked by worker."})

#         return data

class BookingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingImage
        fields = ["id", "file"]


class BookingWorkerSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = WorkerProfile
        fields = ["id", "username", "profile_image"]

    def get_username(self, obj):
        return obj.user.username if hasattr(obj, 'user') else str(obj)

    def get_profile_image(self, obj):
        return obj.user.profile_image.url if hasattr(obj, 'user') and obj.user.profile_image else None




class ProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proof
        fields = ["id", "file", "submitted_by", "submitted_at"]


class PaymentSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    commission = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    worker_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    payment_type = serializers.CharField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "booking", "amount", "commission", "worker_amount",
            "method", "status", "transaction_id", "created_at", "payment_type"
        ]
        read_only_fields = ["commission", "worker_amount", "status", "transaction_id", "created_at"]

    def create(self, validated_data):
        from .models import SiteSettings
        settings_obj = SiteSettings.objects.first()
        commission_rate = settings_obj.commission_rate if settings_obj else 10.0

        amount = Decimal(validated_data["amount"])
        validated_data["commission"] = amount * Decimal(commission_rate / 100)
        validated_data["worker_amount"] = amount - validated_data["commission"]
        validated_data["status"] = "pending"
        return super().create(validated_data)

    def _refund_payment(self, booking):
        payment = Payment.objects.filter(booking=booking, status="pending").first()
        if not payment:
            return

        try:
            if payment.razorpay_order_id:
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                refund_amount = int(payment.amount * 100)
                refund = client.payment.refund(payment.razorpay_order_id, refund_amount)

                payment.status = "refunded"
                payment.transaction_id = refund.get("id")
                payment.save()
                create_notification(booking.user, "payment", f"Your payment for booking {booking.id} has been refunded.")
                log_audit("payment_refunded", user=booking.user, booking=booking, payment=payment, details="Refund triggered automatically.")
            else:
                payment.status = "refunded"
                payment.save()
                create_notification(booking.user, "payment", f"Your payment for booking {booking.id} has been refunded.")
                log_audit("payment_refunded_offline", user=booking.user, booking=booking, payment=payment, details="Refund marked manually/offline.")
        except Exception as e:
            log_audit("payment_refund_failed", user=booking.user, booking=booking, payment=payment, details=str(e))
            print(f"Payment refund failed: {e}")



class BookingSerializer(serializers.ModelSerializer):
    user = BookingWorkerSerializer(read_only=True)
    worker = serializers.StringRelatedField(read_only=True)
    images = BookingImageSerializer(many=True, read_only=True)
    advance_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=True
    )
    payments = PaymentSerializer(many=True, read_only=True)

    balance_amount = serializers.SerializerMethodField()


    class Meta:
        model = Booking
        fields = "__all__"

    def validate(self, data):
        worker = data.get("worker")
        booking_date = data.get("date")

        if Booking.objects.filter(worker=worker, date=booking_date, status__in=["pending", "accepted"]).exists():
            raise serializers.ValidationError({"date": "Worker already booked for this date."})

        if WorkerAvailability.objects.filter(worker=worker, date=booking_date, is_blocked=True).exists():
            raise serializers.ValidationError({"date": "This date is blocked by worker."})

        return data
    def get_balance_amount(self, obj):
        total_paid = sum(p.amount for p in obj.payments.filter(status="completed"))
        return max(Decimal(obj.worker.daily_rate) - total_paid, 0)


# ---------------- REVIEW ----------------
# serializers.py


class ReviewMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewMedia
        fields = ['id', 'file']

class ReviewSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    worker = serializers.StringRelatedField(read_only=True)
    media = ReviewMediaSerializer(many=True, read_only=True)  # nested
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "user_id",      # 👈 include
            "user_name",    # 👈 include
            "user",
            "worker",
            "comment",
            "rating",
            "created_at",
            "avg_rating",
            "media",
        ]

    def get_avg_rating(self, obj):
        return Review.objects.filter(worker=obj.worker).aggregate(Avg("rating"))["rating__avg"]

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        worker_id = request.data.get("worker")
        worker = WorkerProfile.objects.get(id=worker_id)

        review = Review.objects.create(user=user, worker=worker, comment=validated_data.get("comment"), rating=validated_data.get("rating"), booking=Booking.objects.filter(worker_id=worker_id, status='completed').first())

        # Handle uploaded files
        files = request.FILES.getlist("mediaFiles")
        for f in files:
            ReviewMedia.objects.create(review=review, file=f)

        return review
    def update(self, instance, validated_data):
        # Update rating/comment
        instance.rating = validated_data.get("rating", instance.rating)
        instance.comment = validated_data.get("comment", instance.comment)
        instance.save()

        # If new files uploaded, add them
        request = self.context.get("request")
        if request and request.FILES:
            files = request.FILES.getlist("mediaFiles")
            for f in files:
                ReviewMedia.objects.create(review=instance, file=f)

        return instance

# ---------------- NOTIFICATION ----------------
# serializers.py
class NotificationSerializer(serializers.ModelSerializer):
    booking_id = serializers.SerializerMethodField()
    worker_id = serializers.SerializerMethodField()
    worker_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id", "message", "type", "read_status", "created_at",
            "booking_id", "worker_id", "worker_name"
        ]

    def get_booking_id(self, obj):
        return obj.booking.id if obj.booking else None

    def get_worker_id(self, obj):
        return obj.booking.worker.id if obj.booking else None

    def get_worker_name(self, obj):
        return obj.booking.worker.user.username if obj.booking and obj.booking.worker else None
    
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=6)

    
class TicketReplySerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = TicketReply
        fields = ['id', 'sender', 'sender_name', 'message', 'timestamp']


class SupportTicketSerializer(serializers.ModelSerializer):
    worker = serializers.HiddenField(default=serializers.CurrentUserDefault())
    worker_name = serializers.CharField(source='worker.username', read_only=True)
    replies = TicketReplySerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = ['id', 'worker', 'worker_name', 'subject', 'description', 'status', 'created_at', 'updated_at', 'replies']

class WorkerReportSerializer(serializers.ModelSerializer):
    worker_username = serializers.CharField(source='worker.user.username', read_only=True)
    reported_by_username = serializers.CharField(source='reported_by.username', read_only=True)

    class Meta:
        model = WorkerReport
        fields = [
            "id",
            "worker",
            "worker_username",
            "booking",
            "reported_by",
            "reported_by_username",
            "report_type",
            "description",
            "evidence",
            "status",
            "admin_notes",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = ["created_at", "updated_at", "resolved_at"]

