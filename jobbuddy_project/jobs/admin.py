

# from django.contrib import admin
# from django.utils.html import format_html
# from .models import *
# # ---------------- USER ----------------
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('username', 'email', 'role', 'location', 'phone', 'is_active', 'is_staff')
#     list_filter = ('role', 'is_active', 'is_staff')
#     search_fields = ('username', 'email', 'phone')
#     ordering = ('username',)
#     readonly_fields = ('id',)


# # ---------------- WORKER ----------------
# class WorkerPortfolioInline(admin.TabularInline):
#     model = WorkerPortfolio
#     extra = 1

# class WorkerCommentInline(admin.TabularInline):
#     model = WorkerComment
#     extra = 1

# class PortfolioMediaInline(admin.TabularInline):
#     model = PortfolioMedia
#     extra = 1

# @admin.register(WorkerPortfolio)
# class WorkerPortfolioAdmin(admin.ModelAdmin):
#     list_display = ('title', 'worker', 'media_count', 'media_preview')
#     inlines = [PortfolioMediaInline]

#     def media_count(self, obj):
#         return obj.media.count()
#     media_count.short_description = "Media Count"

#     def media_preview(self, obj):
#         media = obj.media.first()
#         if not media:
#             return "-"
#         if media.is_video or media.file.url.endswith(('.mp4', '.mov', '.avi')):
#             return format_html('<video src="{}" width="200" controls />', media.file.url)
#         return format_html('<img src="{}" width="200" />', media.file.url)

# @admin.register(WorkerProfile)
# class WorkerProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'availability', 'verified', 'rating', 'total_jobs')
#     list_filter = ('availability', 'verified')
#     search_fields = ('user__username', 'skills')
#     inlines = [WorkerPortfolioInline]


# # ---------------- BOOKINGS ----------------
# class PaymentInline(admin.TabularInline):
#     model = Payment
#     extra = 0
#     readonly_fields = ('amount', 'commission', 'worker_amount', 'status', 'transaction_id', 'created_at')
#     can_delete = False

# class BookingImageInline(admin.TabularInline):
#     model = BookingImage
#     extra = 1

# @admin.register(Booking)
# class BookingAdmin(admin.ModelAdmin):
#     list_display = ['id', 'user', 'worker', 'date', 'status']
#     list_filter = ['status', 'date', 'worker']
#     search_fields = ['user__username', 'worker__user__username']
#     ordering = ['-date']
#     inlines = [PaymentInline, BookingImageInline]


# # ---------------- PAYMENTS ----------------
# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('id', 'booking', 'amount', 'method', 'status', 'transaction_id', 'created_at')
#     list_filter = ('method', 'status')
#     search_fields = ('booking__user__username', 'booking__worker__user__username', 'transaction_id')
#     ordering = ('-created_at',)


# # ---------------- WALLET ----------------
# @admin.register(Wallet)
# class WalletAdmin(admin.ModelAdmin):
#     list_display = ('user', 'balance')
#     search_fields = ('user__username', 'user__email')


# # ---------------- REVIEWS ----------------
# class ReviewMediaInline(admin.TabularInline):
#     model = ReviewMedia
#     extra = 1
#     readonly_fields = ('id',)

# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     list_display = ('id', 'worker', 'user', 'booking', 'rating', 'created_at')
#     list_filter = ('rating', 'created_at', 'worker')
#     search_fields = ('worker__user__username', 'user__username', 'comment')
#     inlines = [ReviewMediaInline]


# # ---------------- NOTIFICATIONS ----------------
# @admin.register(Notification)
# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'type', 'read_status', 'created_at')
#     list_filter = ('type', 'read_status')
#     search_fields = ('user__username', 'message')
#     ordering = ('-created_at',)


# # ---------------- CATEGORY ----------------
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)


# # ---------------- EVENTS & PROMOTIONS ----------------
# @admin.register(Event)
# class EventAdmin(admin.ModelAdmin):
#     list_display = ('title', 'start_date', 'end_date', 'pricing')
#     search_fields = ('title',)
#     ordering = ('-start_date',)

# @admin.register(Promotion)
# class PromotionAdmin(admin.ModelAdmin):
#     list_display = ('title', 'start_date', 'end_date', 'price')
#     search_fields = ('title',)
#     ordering = ('-start_date',)

# @admin.register(EventPackage)
# class EventPackageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'price', 'created_at', 'updated_at')
#     search_fields = ('name',)
#     ordering = ('-created_at',)

# @admin.register(PromotionTicket)
# class PromotionTicketAdmin(admin.ModelAdmin):
#     list_display = ('promotion', 'user', 'purchased_at')
#     search_fields = ('promotion__title', 'user__username')
#     ordering = ('-purchased_at',)


# # ---------------- ANALYTICS ----------------
# @admin.register(Analytics)
# class AnalyticsAdmin(admin.ModelAdmin):
#     list_display = ('worker', 'total_jobs', 'ratings', 'earnings', 'portfolio_views')
#     search_fields = ('worker__user__username',)


# # ---------------- PAYOUTS ----------------
# @admin.register(Payout)
# class PayoutAdmin(admin.ModelAdmin):
#     list_display = ('id', 'worker', 'booking', 'amount', 'status', 'transaction_id', 'created_at', 'updated_at')
#     list_filter = ('status', 'created_at')
#     search_fields = ('worker__user__username', 'booking__user__username', 'transaction_id')
#     ordering = ('-created_at',)
#     readonly_fields = ('created_at', 'updated_at', 'transaction_id')


# # ---------------- SITE SETTINGS ----------------
# @admin.register(SiteSettings)
# class SiteSettingsAdmin(admin.ModelAdmin):
#     list_display = ('commission_rate', 'advance_percentage','currency')

# @admin.register(WorkerVerificationRequest)
# class WorkerVerificationAdmin(admin.ModelAdmin):
#     list_display = ("worker", "status", "verification_fee", "created_at")
#     list_filter = ("status",)
#     search_fields = ("worker__email", "worker__username", "full_name")
#     readonly_fields = ("created_at", "updated_at", "payment_transaction_id")
#     fieldsets = (
#         ("Worker Info", {"fields": ("worker", "full_name", "date_of_birth")}),
#         ("Identity Verification", {"fields": ("id_document", "selfie")}),
#         ("Professional Verification", {"fields": ("certificates", "portfolio", "additional_info")}),
#         ("Payment Info", {"fields": ("verification_fee", "payment_transaction_id")}),
#         ("Admin Actions", {"fields": ("status", "admin_notes")}),
#         ("Timestamps", {"fields": ("created_at", "updated_at")}),
#     )
from django.contrib import admin
from django.utils.html import format_html
from .models import *

# ---------------- USER ----------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'location', 'phone', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    ordering = ('username',)
    readonly_fields = ('id',)

# ---------------- WORKER ----------------
class WorkerPortfolioInline(admin.TabularInline):
    model = WorkerPortfolio
    extra = 1

class WorkerCommentInline(admin.TabularInline):
    model = WorkerComment
    extra = 1

class PortfolioMediaInline(admin.TabularInline):
    model = PortfolioMedia
    extra = 1

@admin.register(WorkerPortfolio)
class WorkerPortfolioAdmin(admin.ModelAdmin):
    list_display = ('title', 'worker', 'media_count', 'media_preview')
    inlines = [PortfolioMediaInline]

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media Count"

    def media_preview(self, obj):
        media = obj.media.first()
        if not media:
            return "-"
        if media.is_video or media.file.url.endswith(('.mp4', '.mov', '.avi')):
            return format_html('<video src="{}" width="200" controls />', media.file.url)
        return format_html('<img src="{}" width="200" />', media.file.url)

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'availability', 'verified', 'rating', 'total_jobs')
    list_filter = ('availability', 'verified')
    search_fields = ('user__username', 'skills')
    inlines = [WorkerPortfolioInline]

# ---------------- BOOKINGS ----------------
class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('amount', 'commission', 'worker_amount', 'status', 'transaction_id', 'created_at')
    can_delete = False

class BookingImageInline(admin.TabularInline):
    model = BookingImage
    extra = 1

class ProofInline(admin.TabularInline):
    model = Proof
    extra = 1
    readonly_fields = ('submitted_by', 'submitted_at', 'file')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'worker', 'date', 'status']
    list_filter = ['status', 'date', 'worker']
    search_fields = ['user__username', 'worker__user__username']
    ordering = ['-date']
    inlines = [PaymentInline, BookingImageInline, ProofInline]

# ---------------- PAYMENTS ----------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'method', 'status', 'transaction_id', 'created_at')
    list_filter = ('method', 'status')
    search_fields = ('booking__user__username', 'booking__worker__user__username', 'transaction_id')
    ordering = ('-created_at',)

# ---------------- WALLET ----------------
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username', 'user__email')

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("wallet_user", "transaction_type", "amount", "description", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("wallet__user__username", "wallet__user__email", "description")
    ordering = ("-created_at",)
    readonly_fields = ("wallet", "amount", "transaction_type", "description", "created_at")

    def wallet_user(self, obj):
        return obj.wallet.user.username
    wallet_user.short_description = "User"

# ---------------- REVIEWS ----------------
class ReviewMediaInline(admin.TabularInline):
    model = ReviewMedia
    extra = 1
    readonly_fields = ('id',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'worker', 'user', 'booking', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'worker')
    search_fields = ('worker__user__username', 'user__username', 'comment')
    inlines = [ReviewMediaInline]

# ---------------- NOTIFICATIONS ----------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'read_status', 'created_at')
    list_filter = ('type', 'read_status')
    search_fields = ('user__username', 'message')
    ordering = ('-created_at',)

# ---------------- CATEGORY ----------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# ---------------- EVENTS & PROMOTIONS ----------------
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'pricing')
    search_fields = ('title',)
    ordering = ('-start_date',)

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'price')
    search_fields = ('title',)
    ordering = ('-start_date',)

@admin.register(EventPackage)
class EventPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(PromotionTicket)
class PromotionTicketAdmin(admin.ModelAdmin):
    list_display = ('promotion', 'user', 'purchased_at')
    search_fields = ('promotion__title', 'user__username')
    ordering = ('-purchased_at',)

# ---------------- ANALYTICS ----------------
@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('worker', 'total_jobs', 'ratings', 'earnings', 'portfolio_views', 'created_at', 'updated_at')
    search_fields = ('worker__user__username',)
    readonly_fields = ('worker', 'total_jobs', 'ratings', 'earnings', 'portfolio_views', 'created_at', 'updated_at')

# ---------------- PAYOUTS ----------------
@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'worker', 'booking', 'amount', 'status', 'transaction_id', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('worker__user__username', 'booking__user__username', 'transaction_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'transaction_id', 'amount', 'worker', 'booking')

# ---------------- SITE SETTINGS ----------------
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('commission_rate', 'advance_percentage','currency')

# ---------------- WORKER VERIFICATION ----------------
@admin.register(WorkerVerificationRequest)
class WorkerVerificationAdmin(admin.ModelAdmin):
    list_display = ("worker", "status", "verification_fee", "verified_until", "created_at")
    list_filter = ("status",)
    search_fields = ("worker__email", "worker__username", "full_name")
    readonly_fields = ("created_at", "updated_at", "payment_transaction_id",
                       "id_document", "selfie", "certificates", "portfolio")
    fieldsets = (
        ("Worker Info", {"fields": ("worker", "full_name", "date_of_birth")}),
        ("Identity Verification", {"fields": ("id_document", "selfie")}),
        ("Professional Verification", {"fields": ("certificates", "portfolio", "additional_info")}),
        ("Payment Info", {"fields": ("verification_fee", "payment_transaction_id")}),
        ("Admin Actions", {"fields": ("status", "admin_notes", "verified_until")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

# ---------------- SUPPORT TICKETS ----------------
# ---------------- SUPPORT TICKETS ----------------
class TicketReplyInline(admin.TabularInline):
    model = TicketReply
    extra = 1
    readonly_fields = ("timestamp",)

    # Automatically set the sender to the current admin user
    def save_new(self, form, commit=True):
        obj = form.save(commit=False)
        if not obj.sender_id:
            obj.sender = self.admin_site.request.user  # admin user
        if commit:
            obj.save()
        return obj

    def get_formset(self, request, obj=None, **kwargs):
        # store request in self so we can access it in save_new
        self.admin_site.request = request
        return super().get_formset(request, obj, **kwargs)


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("subject", "worker", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("subject", "worker__username", "description")
    ordering = ("-created_at",)
    inlines = [TicketReplyInline]
    readonly_fields = ("created_at", "updated_at")

@admin.register(WorkerReport)
class WorkerReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "worker",
        "booking",
        "reported_by",
        "report_type",
        "status",
        "evidence_preview",
        "created_at",
        "resolved_at",
    )
    list_filter = ("status", "report_type", "created_at")
    search_fields = ("worker__user__username", "reported_by__username", "description", "admin_notes")
    readonly_fields = ("created_at", "updated_at", "resolved_at", "evidence_preview")
    ordering = ("-created_at",)

    actions = ["mark_selected_resolved"]

    fieldsets = (
        (None, {
            "fields": (
                "worker",
                "booking",
                "reported_by",
                "report_type",
                "description",
                "evidence",
                "evidence_preview",
            )
        }),
        ("Admin Actions", {
            "fields": ("status", "admin_notes", "resolved_at"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def mark_selected_resolved(self, request, queryset):
        updated = queryset.update(status="resolved", resolved_at=timezone.now())
        self.message_user(request, f"{updated} report(s) marked as resolved.")
    mark_selected_resolved.short_description = "Mark selected reports as resolved"

    def evidence_preview(self, obj):
        if obj.evidence:
            # Show image thumbnail if image, else show link for other file types
            if obj.evidence.url.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                return format_html(
                    '<img src="{}" style="max-height: 100px; border-radius: 8px;" />', 
                    obj.evidence.url
                )
            else:
                return format_html('<a href="{}" target="_blank">View File</a>', obj.evidence.url)
        return "-"
    evidence_preview.short_description = "Evidence"