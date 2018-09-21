from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Patient(models.Model):
    firstName = models.CharField(max_length=30)
    lastName = models.CharField(max_length=50)
    # dob = models.DateField(default=None, blank=True)
    byear = models.IntegerField(blank=False)
    registerDate = models.DateTimeField(auto_now_add=True, null=True)
    bio = models.TextField(max_length=50000, blank=True)
    gender = models.CharField(max_length=1, blank=True)
    owner = models.ForeignKey(User, related_name='patients', on_delete=models.CASCADE)
    lastMod = models.DateTimeField(default=None, blank=True, null=True)

    objects = models.Manager()

    class Meta:
        get_latest_by = 'registerDate'
        ordering = ('-registerDate',)
        verbose_name_plural = 'patients'

    def __unicode__(self):
        return self.firstName

    def get_absolute_url(self):
        return "/patient_details/%s" % self.pk


class Session(models.Model):
    patient_id = models.ForeignKey(Patient, related_name='sessions', on_delete=models.CASCADE)
    sessionNo = models.IntegerField(blank=False)
    sessionDate = models.DateTimeField(default=None, null=True)
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField(max_length=50000, blank=True)
    notes = models.TextField(max_length=1000, blank=True)
    paymentDate = models.DateField(default=None, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True, default=None)
    timestamp = models.DateTimeField(auto_now_add=True)
    lastMod = models.DateTimeField(default=None, blank=True, null=True)

    objects = models.Manager()

    class Meta:
        get_latest_by = 'sessionDate'
        ordering = ('sessionNo',)
        verbose_name_plural = 'sessions'

    def __unicode__(self):
        return self.pk

    def get_absolute_url(self):
        return "/patient_details/%s" % self.patient_id


class UserProfile(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    consent = models.BooleanField(default=True)
    consentTime = models.DateTimeField(auto_now_add=True)


class ActivityLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    userIP = models.CharField(max_length=15, default=None)
    detail = models.TextField(default=None)
    url = models.TextField(default=None)


class CommunicationLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    commType = models.CharField(max_length=20, blank=True, null=True)
    rcpt = models.CharField(max_length=100, blank=True, null=True)
    exception = models.TextField(default=None, blank=True, null=True)
    content = models.TextField(default=None, blank=True, null=True)

