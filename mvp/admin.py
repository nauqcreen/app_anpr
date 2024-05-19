from django.contrib import admin
from .models import Feedback, AdminReply, Profile, CheckInOut, CheckIn
from import_export import resources
from import_export.admin import ImportExportModelAdmin

admin.site.register(CheckIn)

# Resource for import/export functionality
class FeedbackResource(resources.ModelResource):
    class Meta:
        model = Feedback

# Inline admin class for AdminReply
class AdminReplyInline(admin.StackedInline):
    model = AdminReply
    extra = 0

# Admin class for Feedback with additional functionalities
@admin.register(Feedback)
class FeedbackAdmin(ImportExportModelAdmin):
    resource_class = FeedbackResource
    list_display = ('user', 'timestamp', 'feedback', 'read_status')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'feedback')
    inlines = [AdminReplyInline]
    actions = ['mark_as_read', 'send_bulk_replies']

    def read_status(self, obj):
        return obj.read
    read_status.boolean = True
    read_status.short_description = 'Read'

    def mark_as_read(self, request, queryset):
        queryset.update(read=True)
        self.message_user(request, "Selected feedbacks marked as read.")
    mark_as_read.short_description = "Mark selected feedbacks as read"

    def send_bulk_replies(self, request, queryset):
        for feedback in queryset:
            AdminReply.objects.create(feedback=feedback, reply="Thank you for your feedback!")
        self.message_user(request, "Replies sent to selected feedbacks.")
    send_bulk_replies.short_description = "Send bulk replies to selected feedbacks"

# Admin class for AdminReply
@admin.register(AdminReply)
class AdminReplyAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'timestamp', 'reply')

# Admin class for Profile
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'gender', 'address', 'hometown', 'job_position')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'job_position')

# Admin class for CheckInOut
@admin.register(CheckInOut)
class CheckInOutAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'vehicle_type', 'check_in_time', 'check_out_time')
    list_filter = ('vehicle_type', 'check_in_time', 'check_out_time')
    search_fields = ('plate_number', 'vehicle_type')
