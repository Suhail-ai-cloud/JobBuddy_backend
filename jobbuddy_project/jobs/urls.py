from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()

# ---------------- USERS ----------------
router.register(r'users', UserViewSet, basename='users')

# ---------------- WORKERS ----------------
router.register(r'worker-profiles', WorkerProfileViewSet, basename='worker-profiles')
router.register(r'worker-portfolios', WorkerPortfolioViewSet, basename='worker-portfolios')
router.register(r'worker-comments', WorkerCommentViewSet, basename='worker-comments')

# ---------------- BOOKINGS ----------------
router.register(r'bookings', BookingViewSet, basename='bookings')

# ---------------- PAYMENTS ----------------
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'payouts', PayoutViewSet, basename='payouts')

# ---------------- REVIEWS ----------------
router.register(r'reviews', ReviewViewSet, basename='reviews')

# ---------------- NOTIFICATIONS ----------------
router.register(r'notifications', NotificationViewSet, basename='notifications')

# ---------------- CATEGORIES ----------------
router.register(r'categories', CategoryViewSet, basename='categories')

# ---------------- Extra Endpoints ----------------
worker_reviews = ReviewViewSet.as_view({'get': 'list_by_worker'})
router.register('tickets', SupportTicketViewSet, basename='tickets')
router.register(r'worker-reports', WorkerReportViewSet, basename='worker-report')

urlpatterns = [
    path("users/me/", current_user, name="current-user"),
    path("search/workers/", WorkerSearchView.as_view(), name="worker-search"),
    path("", include(router.urls)),  
    path("worker/<int:worker_id>/completed-bookings/", user_completed_bookings),
    path("workers/<int:worker_id>/reviews/", worker_reviews, name="worker-reviews"),
    path('worker/dashboard/', worker_dashboard, name='worker-dashboard'),
    path("users/me/update/", update_current_user, name="update_current_user"),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path("worker/verification/payment/create/", create_verification_payment, name="create_verification_payment"),
    path("worker/verification/payment/confirm/", confirm_verification_payment, name="confirm_verification_payment"),
    path("worker/verification/", WorkerVerificationRequestView.as_view(), name="worker-verification"),
    path("admin/verification-requests/", AdminVerificationListView.as_view(), name="admin-verification-list"),
    path('google-role-selection/', GoogleRoleSelectionView.as_view(), name='google-role-selection'),
    path("auth/google-login/", GoogleLoginView.as_view(), name="google-login"),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('become-worker/', BecomeWorkerView.as_view(), name='become-worker'),

]
