from django.contrib import admin
from psychotherapist.models import Patient, Session, UserProfile, ActivityLog, CommunicationLog


class PatientAdmin(admin.ModelAdmin):
    exclude = ('owner',)
    list_display = ('pk', 'firstName', 'lastName', 'byear', 'owner', 'registerDate', 'lastMod')

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(PatientAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser and request.user.id != obj.owner.id:
            return False
        return True

    def queryset(self, request):
        if request.user.is_superuser:
            return Patient.objects.all()
        return Patient.objects.filter(owner=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        obj.save()


admin.site.register(Patient, PatientAdmin)


class SessionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'patient_id', 'sessionNo', 'sessionDate', 'subject',
                    'paymentDate', 'amount', 'method', 'timestamp', 'lastMod')

    def has_change_permission(self, request, obj=None):
        has_class_permission = super(SessionAdmin, self).has_change_permission(request, obj)
        if not has_class_permission:
            return False
        if obj is not None and not request.user.is_superuser:
            return False
        return True

    def queryset(self, request):
        if request.user.is_superuser:
            return Session.objects.all()

    def save_model(self, request, obj, form, change):
        obj.save()


admin.site.register(Session, SessionAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user_id', 'consent', 'consentTime')


admin.site.register(UserProfile, UserProfileAdmin)


class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('pk', 'timestamp', 'user_id', 'userIP', 'detail', 'url')


admin.site.register(ActivityLog, ActivityLogAdmin)


class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ('pk', 'timestamp', 'commType', 'rcpt', 'exception', 'content')


admin.site.register(CommunicationLog, CommunicationLogAdmin)

