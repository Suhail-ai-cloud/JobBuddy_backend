from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.contrib.auth.tokens import default_token_generator as token_generator
from .models import User
from .serializers import ForgotPasswordSerializer

from rest_framework.response import Response
from django.db.models import Sum
from .models import User, WorkerProfile, Booking, Payment, Payout
from .serializers import UserSerializer, WorkerProfileSerializer
from rest_framework.exceptions import NotFound
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from jobs.models import User
from .serializers import ForgotPasswordSerializer, ResetPasswordSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from jobs.models import User, WorkerProfile
from .serializers import UserSignupSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from jobs.models import User, WorkerProfile
from .serializers import UserSignupSerializer
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend
from datetime import date
from .models import WorkerPortfolio,PortfolioMedia
import razorpay
import logging
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import *
from .models import Payout
from .serializers import*



class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
# ---------------- USER ----------------

GOOGLE_CLIENT_ID = "491438380222-32o93ps0fj5tn7lnmg8akhncqgutb28h.apps.googleusercontent.com"

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    """
    Returns the currently logged-in user info, including worker profile if exists
    """
    user_data = UserSerializer(request.user).data
    if hasattr(request.user, "worker_profile"):
        user_data["worker_profile"] = WorkerProfileSerializer(request.user.worker_profile).data
    return Response(user_data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


    @action(detail=False, methods=["patch"])
    def update_me(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=["post"],
        url_path="update-profile-image",
        parser_classes=[MultiPartParser, FormParser]
    )
    def update_profile_image(self, request):
        user = request.user
        profile_image = request.FILES.get("profile_image")
        if not profile_image:
            return Response({"error": "No image provided"}, status=400)
        user.profile_image = profile_image
        user.save()
        
        absolute_url = request.build_absolute_uri(user.profile_image.url)
        return Response({"success": True, "profile_image": absolute_url})

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_current_user(request):
    user = request.user
    serializer = UpdateUserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_verification_payment(request):
    amount = 9900  # ₹99.00 in paise
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1",
        "notes": {"purpose": "Worker Verification"}
    })

    return Response({
        "order_id": payment["id"],
        "amount": payment["amount"],
        "currency": payment["currency"],
        "key": settings.RAZORPAY_KEY_ID,
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def confirm_verification_payment(request):
    data = request.data
    payment_id = data.get("payment_id")
    order_id = data.get("order_id")
    signature = data.get("signature")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
    except razorpay.errors.SignatureVerificationError:
        return Response({"error": "Invalid payment signature"}, status=400)

    obj, created = WorkerVerificationRequest.objects.get_or_create(worker=request.user)
    obj.verification_fee = 99
    obj.payment_transaction_id = payment_id
    obj.save()

    return Response({"success": True, "message": "Payment verified successfully"})

class WorkerVerificationRequestView(generics.RetrieveUpdateAPIView):
    serializer_class = WorkerVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj, created = WorkerVerificationRequest.objects.get_or_create(worker=self.request.user)
        return obj

class AdminVerificationListView(generics.ListAPIView):
    serializer_class = WorkerVerificationSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = WorkerVerificationRequest.objects.all()
    
class WorkerProfileViewSet(viewsets.ModelViewSet):
    queryset = WorkerProfile.objects.all()
    serializer_class = WorkerProfileSerializer
    filterset_fields = ['availability', 'verified', 'skills']
    search_fields = ['user__username', 'skills']
    ordering_fields = ['rating', 'total_jobs']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'me_availability', 'reviews']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def partial_update(self, request, *args, **kwargs):
        worker = self.get_object()
        user = worker.user
        worker_fields = ["skills", "availability", "verified", "daily_rate"]
        for field in worker_fields:
            if field in request.data:
                setattr(worker, field, request.data[field])
        categories = request.data.get("categories")
        if categories is not None:
            worker.categories.set([c for c in categories if c is not None])

        worker.save()
        user_fields = ["username", "email", "phone", "location", "profile_image"]
        for field in user_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        serializer = self.get_serializer(worker)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="availability")
    def availability(self, request, pk=None):
        """
        Get worker availability for any user (blocks already booked and blocked dates)
        """
        worker = self.get_object()
        availability_records = worker.availabilities.all()
        booked_dates = Booking.objects.filter(worker=worker, status__in=["accepted", "pending"]).values_list("date", flat=True)
        blocked_dates = availability_records.filter(is_blocked=True).values_list("date", flat=True)
        available_dates = availability_records.filter(is_blocked=False).exclude(date__in=booked_dates).values_list("date", flat=True)

        return Response({
            "available_dates": [str(d) for d in available_dates],
            "booked_dates": [str(d) for d in booked_dates],
            "blocked_dates": [str(d) for d in blocked_dates],
        })
    @action(detail=False, methods=["get", "post"], url_path="me/availability")
    def me_availability(self, request):
        try:
            worker = WorkerProfile.objects.get(user=request.user)
        except WorkerProfile.DoesNotExist:
            raise NotFound({"detail": "Worker profile does not exist for this user."})

        if request.method == "GET":
            availability_records = worker.availabilities.all()
            booked_dates = Booking.objects.filter(worker=worker, status__in=["accepted","pending"]).values_list("date", flat=True)
            blocked_dates = availability_records.filter(is_blocked=True).values_list("date", flat=True)
            available_dates = availability_records.filter(is_blocked=False).values_list("date", flat=True)
            return Response({
                "available_dates": [str(d) for d in available_dates if str(d) not in booked_dates],
                "booked_dates": [str(d) for d in booked_dates],
                "blocked_dates": [str(d) for d in blocked_dates],
            })

        elif request.method == "POST":
            dates = request.data.get("dates", [])
            type_ = request.data.get("type")
            for date_str in dates:
                availability_obj, _ = WorkerAvailability.objects.get_or_create(worker=worker, date=date_str)
                availability_obj.is_blocked = type_ == "blocked"
                availability_obj.save()
            return Response({"success": True, "dates": dates, "type": type_})

    @action(detail=True, methods=["get"])
    def reviews(self, request, pk=None):
        worker = self.get_object()
        serializer = ReviewSerializer(worker.reviews.all(), many=True)
        return Response(serializer.data)


class IsWorkerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True  # anyone can view
        return request.user.is_authenticated and request.user.role == "worker"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.worker.user == request.user
    
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class WorkerSearchView(generics.ListAPIView):
    serializer_class = WorkerProfileSearchSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = WorkerProfile.objects.all()
        q = self.request.query_params.get('q')
        category = self.request.query_params.get('category')
        location = self.request.query_params.get('location')
        sort = self.request.query_params.get('sort')

        # Multi-word search
        if q:
            words = q.split()
            search_query = Q()
            for word in words:
                search_query |= (
                    Q(user__username__icontains=word) |
                    Q(user__first_name__icontains=word) |
                    Q(user__last_name__icontains=word) |
                    Q(skills__icontains=word) |
                    Q(portfolios__title__icontains=word) |
                    Q(portfolios__description__icontains=word)
                )
            queryset = queryset.filter(search_query).distinct()

        if category:
            queryset = queryset.filter(categories__id=category)

      
        if location:
            queryset = queryset.filter(user__location__icontains=location)

        
        if sort in ['rating', 'total_jobs']:
            queryset = queryset.order_by(f'-{sort}')

        return queryset

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        user = authenticate(request, email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user_id": str(user.id),
                "role": user.role
            })

        return Response({"error": "Invalid credentials"}, status=401)




class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If this email exists, a reset link has been sent.'})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Use frontend URL from settings
        frontend_url = settings.FRONTEND_URL
        reset_link = f"{frontend_url}/reset-password/{uid}/{token}/"

        subject = "JobBuddy Password Reset"
        from_email = settings.EMAIL_HOST_USER
        to_email = [email]

        html_content = render_to_string("emails/reset_password.html", {
            "reset_link": reset_link,
            "user": user,
            "frontend_url": frontend_url
        })

        msg = EmailMultiAlternatives(
            subject=subject,
            body=f"Use this link to reset your password: {reset_link}",
            from_email=from_email,
            to=to_email
        )
        msg.attach_alternative(html_content, "text/html")

        try:
            msg.send(fail_silently=False)
        except Exception as e:
            print("Email send error:", e)
            return Response({'detail': 'Error sending email.'}, status=500)

        return Response({'detail': 'Password reset email sent successfully.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'error': 'Invalid token.'}, status=400)

        if not token_generator.check_token(user, token):
            return Response({'error': 'Token invalid or expired.'}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password reset successful.'})


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)
            email = idinfo.get("email")
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": email}
            )

            return Response({"user_id": user.id, "email": user.email})

        except ValueError:
            return Response({"error": "Invalid token"}, status=400)
        
class GoogleRoleSelectionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get("user_id")
        role = request.data.get("role")

        if not user_id:
            return Response({"error": "user_id missing in request"}, status=400)

        if role not in ["user", "worker"]:
            return Response({"error": "Invalid role"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.role = role
        user.save()

        if role == "worker" and not hasattr(user, "worker_profile"):
            WorkerProfile.objects.create(user=user)

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Role set successfully",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": str(user.id),
            "role": user.role
        })
class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("=== SignupView Called ===")
        print("Incoming request data:", request.data)

        serializer = UserSignupSerializer(data=request.data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        print(f"User created: {user.email}, role: {user.role}")

        refresh = RefreshToken.for_user(user)
        print("Tokens generated:", refresh, refresh.access_token)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': str(user.id),
            'role': user.role
        }, status=status.HTTP_201_CREATED)
    
class BecomeWorkerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role == 'worker' and hasattr(user, 'worker_profile'):
            return Response({"error": "Already a worker"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        user.role = 'worker'
        user.save()
        worker_profile, created = WorkerProfile.objects.get_or_create(user=user)
        serializer = WorkerProfileSerializer(worker_profile, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Successfully became a worker",
                "user": {"id": user.id, "email": user.email, "role": user.role},
                "worker_profile": serializer.data
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class WorkerPortfolioViewSet(viewsets.ModelViewSet):
    queryset = WorkerPortfolio.objects.all()
    serializer_class = WorkerPortfolioSerializer
    permission_classes = [IsWorkerOrReadOnly]

    def get_queryset(self):
        worker_id = self.request.query_params.get("worker_id")
        if worker_id:
            return WorkerPortfolio.objects.filter(worker_id=worker_id)
        
        if self.request.user.is_authenticated and self.request.user.role == "worker":
            return WorkerPortfolio.objects.filter(worker__user=self.request.user)
   
        return WorkerPortfolio.objects.none()


    def perform_create(self, serializer):
        worker_profile = WorkerProfile.objects.get(user=self.request.user)
        serializer.save(worker=worker_profile)

    @action(detail=True, methods=["post"])
    def add_media(self, request, pk=None):
        portfolio = self.get_object()
        files = request.FILES.getlist("media")
        for f in files:
            PortfolioMedia.objects.create(portfolio=portfolio, file=f)
        return Response({"success": True})

    @action(detail=True, methods=["delete"], url_path="delete-media/(?P<media_id>[^/.]+)")
    def delete_media(self, request, pk=None, media_id=None):
        portfolio = self.get_object()
        media = portfolio.media.filter(id=media_id).first()
        if media:
            media.delete()
            return Response({"success": True})
        return Response({"error": "Media not found"}, status=404)



class WorkerCommentViewSet(viewsets.ModelViewSet):
    queryset = WorkerComment.objects.all()
    serializer_class = WorkerCommentSerializer
    permission_classes = [IsAuthenticated]



class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'worker', 'user', 'date']
    search_fields = ['worker__user__username', 'user__username']
    ordering_fields = ['date', 'status']

    def get_queryset(self):
        user = self.request.user
        my_bookings = self.request.query_params.get("my_bookings")
        if my_bookings == "worker":
            return Booking.objects.filter(worker__user=user)
        elif my_bookings == "user":
            return Booking.objects.filter(user=user)
        return super().get_queryset()

    def perform_create(self, serializer):
        worker_id = self.request.data.get("worker")
        booking_date = self.request.data.get("date")
        advance_amount = Decimal(self.request.data.get("advance_amount", 0))

        if not worker_id or not booking_date:
            raise ValidationError({"error": "Worker and date are required."})

        worker = WorkerProfile.objects.get(id=worker_id)

        if Booking.objects.filter(worker=worker, date=booking_date, status__in=["pending","accepted"]).exists():
            raise ValidationError({"date": "Worker already booked for this date."})

        if WorkerAvailability.objects.filter(worker=worker, date=booking_date, is_blocked=True).exists():
            raise ValidationError({"date": "This date is blocked by worker."})

        booking = serializer.save(user=self.request.user, worker=worker, advance_amount=advance_amount)

        
        images = self.request.FILES.getlist("images")
        for img in images:
            BookingImage.objects.create(booking=booking, file=img)

       
        settings_obj = SiteSettings.objects.first()
        commission_rate = settings_obj.commission_rate if settings_obj else 10.0
        commission = advance_amount * Decimal(commission_rate / 100)
        worker_amount = advance_amount - commission

        Payment.objects.create(
            booking=booking,
            amount=advance_amount,
            commission=commission,
            worker_amount=worker_amount,
            status="pending",
            payment_type="advance"
        )

   
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        booking = self.get_object()
        if booking.status != "pending":
            return Response({"error": "Booking cannot be accepted."}, status=400)

        booking.status = "accepted"
        booking.save()

        availability, _ = WorkerAvailability.objects.get_or_create(worker=booking.worker, date=booking.date)
        availability.is_blocked = True
        availability.save()

        return Response({"status": "Booking accepted", "booking_id": booking.id})

   
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        booking = self.get_object()
        if booking.status not in ["pending", "accepted"]:
            return Response({"error": "Only pending or accepted bookings can be canceled."}, status=400)

        if booking.status == "accepted":
            availability = WorkerAvailability.objects.filter(worker=booking.worker, date=booking.date).first()
            if availability:
                availability.is_blocked = False
                availability.save()

        booking.status = "rejected"
        booking.save()

        
        payment = booking.payments.filter(status="pending").first()
        if payment:
            payment.refund_to_user()

        return Response({"status": "Booking canceled and payment refunded"})

 
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        booking = self.get_object()
        if booking.status != "accepted":
            return Response({"error": "Only accepted bookings can be completed"}, status=400)

        booking.status = "completed"
        booking.save()

        payment = booking.payments.filter(status="pending").first()
        if payment:
            payment.release_to_worker()
            Payout.objects.create(worker=booking.worker, booking=booking, amount=payment.worker_amount, status="pending")

        return Response({"status": "Booking completed, payment released to worker"})

   
    @action(detail=True, methods=["post"])
    def report_no_show(self, request, pk=None):
        booking = self.get_object()
        if booking.status != "accepted":
            return Response({"error": "Cannot report no-show"}, status=400)

        booking.status = "no_show_reported"
        booking.save()

        payment = booking.payments.filter(status="pending").first()
        if payment:
            payment.hold_in_escrow()

        return Response({"status": "No-show reported, payment held in escrow"})

    @action(detail=True, methods=["post"])
    def submit_proof(self, request, pk=None):
        booking = self.get_object()
        files = request.FILES.getlist("files")
        for f in files:
            Proof.objects.create(booking=booking, file=f, submitted_by=request.user)
        booking.status = "investigating"
        booking.save()
        return Response({"status": "Proof submitted for investigation"})

    @action(detail=True, methods=["post"])
    def resolve_dispute(self, request, pk=None):
        booking = self.get_object()
        action_taken = request.data.get("action") 

        payment = booking.payments.filter(status="held").first()
        if not payment:
            return Response({"error": "No payment held"}, status=400)

        if action_taken == "refund_user":
            payment.refund_to_user()
            booking.status = "rejected"
        elif action_taken == "release_worker":
            payment.release_to_worker()
            booking.status = "completed"
        else:
            return Response({"error": "Invalid action"}, status=400)

        booking.save()
        return Response({"status": f"Dispute resolved: {action_taken}"})

  
    @action(detail=False, methods=["post"])
    def auto_reject_pending(self, request):
        threshold_date = timezone.now() - timedelta(days=2)
        pending_bookings = Booking.objects.filter(status="pending", created_at__lte=threshold_date)
        count = 0
        for booking in pending_bookings:
            booking.status = "rejected"
            booking.save()
            payment = booking.payments.filter(status="pending").first()
            if payment:
                payment.refund_to_user()
            count += 1
        return Response({"status": f"{count} pending bookings auto-rejected and refunded"})

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def create_payment(self, request):
        booking_id = request.data.get("booking")
        amount = Decimal(request.data.get("amount", 0))
        payment_type = request.data.get("payment_type", "balance")

        if not booking_id or amount <= 0:
            raise ValidationError({"error": "Booking and positive amount required"})

        booking = Booking.objects.get(id=booking_id)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": int(amount*100),
            "currency": "INR",
            "payment_capture": 1,
        })

        payment = Payment.objects.create(
            booking=booking,
            amount=amount,
            payment_type=payment_type,
            razorpay_order_id=razorpay_order["id"],
            status="pending"
        )

        return Response({
            "id": payment.id,
            "amount": payment.amount,
            "payment_type": payment.payment_type,
            "razorpay_order_id": razorpay_order["id"]
        })

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        payment = self.get_object()
        if payment.status != "pending":
            return Response({"error": "Payment already processed"}, status=400)

        payment.status = "completed"
        payment.save()

        booking = payment.booking
        total_paid = sum(p.amount for p in booking.payments.filter(status="completed"))
        total_due = booking.worker.daily_rate
        remaining = max(total_due - total_paid, 0)

        if remaining == 0:
            booking.status = "paid"
            booking.save()

        return Response({
            "status": "Payment confirmed",
            "payment_type": payment.payment_type,
            "total_paid": total_paid,
            "remaining": remaining
        })





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def worker_dashboard(request):
    user = request.user
    worker = getattr(user, "worker_profile", None)
    if not worker:
        return Response({"error": "Worker profile not found"}, status=404)

    bookings = Booking.objects.filter(worker=worker)

    total_advance_paid = Decimal(0)
    total_balance_paid = Decimal(0)
    total_remaining = Decimal(0)
    total_due_amount = Decimal(0)

    for b in bookings:
        completed_payments = b.payments.filter(status="completed")
        advance_paid = completed_payments.filter(payment_type="advance").aggregate(total=Sum('amount'))['total'] or 0
        balance_paid = completed_payments.filter(payment_type="balance").aggregate(total=Sum('amount'))['total'] or 0

        total_advance_paid += Decimal(advance_paid)
        total_balance_paid += Decimal(balance_paid)

        total_paid_for_booking = Decimal(advance_paid or 0) + Decimal(balance_paid or 0)
        remaining = max(Decimal(b.worker.daily_rate) - total_paid_for_booking, 0)
        total_remaining += remaining
        total_due_amount += Decimal(b.worker.daily_rate)

    total_paid = total_advance_paid + total_balance_paid

    return Response({
        "total_due_amount": total_due_amount,      
        "total_advance_paid": total_advance_paid,  
        "total_balance_paid": total_balance_paid,  
        "total_paid": total_paid,                  
        "total_remaining": total_remaining          
    })


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'list_by_worker']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        worker_id = self.request.data.get("worker")

      
        completed_booking = Booking.objects.filter(
            worker_id=worker_id,
            status='completed',
            user=self.request.user
        ).first()

        if not completed_booking:
            raise ValidationError("You can only review a worker after completing a booking.")

        serializer.save(booking=completed_booking)

    def list_by_worker(self, request, worker_id=None):
        reviews = Review.objects.filter(worker_id=worker_id)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    def perform_update(self, serializer):
        review = self.get_object()
        if review.user != self.request.user:
            raise ValidationError("You can only edit your own reviews.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise ValidationError("You can only delete your own reviews.")
        instance.delete()

  
    @action(detail=False, methods=["get"], url_path="worker/(?P<worker_id>[^/.]+)/reviews")
    def list_by_worker(self, request, worker_id=None):
        reviews = self.queryset.filter(worker_id=worker_id).order_by("-created_at")
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)





@api_view(["GET"])
def user_completed_bookings(request, worker_id):
    user = request.user
    bookings = Booking.objects.filter(
        user=user, worker_id=worker_id, status="completed"
    )
    data = [{"id": b.id, "worker": b.worker.id} for b in bookings]
    return Response(data)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read_status = True
        notification.save()
        return Response({"status": "Notification marked as read"})

    

class PayoutViewSet(viewsets.ModelViewSet):
    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        payout = self.get_object()
        # Here you can integrate Razorpay API call later
        payout.status = "paid"
        payout.save()
        return Response({"status": "Payout marked as paid"})

    @action(detail=False, methods=["get"])
    def my_payouts(self, request):
        payouts = Payout.objects.filter(worker__user=request.user)
        serializer = self.get_serializer(payouts, many=True)
        return Response(serializer.data)
    

class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    queryset = SupportTicket.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SupportTicket.objects.all().order_by('-created_at')
        return SupportTicket.objects.filter(worker=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(worker=self.request.user)

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = self.get_object()
        reply = TicketReply.objects.create(
            ticket=ticket,
            sender=request.user,
            message=request.data.get('message', '')
        )
        return Response(TicketReplySerializer(reply).data)
    
class WorkerReportViewSet(viewsets.ModelViewSet):
    queryset = WorkerReport.objects.all()
    serializer_class = WorkerReportSerializer
    permission_classes = [permissions.IsAuthenticated]  
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["worker", "report_type", "status"]
    search_fields = ["description", "admin_notes"]
    ordering_fields = ["created_at", "updated_at", "resolved_at"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)