from django.contrib import admin
from psychotherapist.models import Patient, Session


class PatientAdmin(admin.ModelAdmin):
    exclude = ('owner',)
    list_display = ('pk', 'firstName', 'lastName', 'dob', 'bio', 'owner')

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
                    'paymentDate', 'amount', 'method')

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

