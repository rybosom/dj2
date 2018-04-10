from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Patient(models.Model):
    firstName = models.CharField(max_length=30)
    lastName = models.CharField(max_length=50)
    dob = models.DateField(default=None, blank=True)
    registerDate = models.DateTimeField(auto_now_add=True, null=True)
    bio = models.TextField(max_length=50000, blank=True)
    gender = models.CharField(max_length=1, blank=True)
    owner = models.ForeignKey(User, related_name='patients', on_delete=models.CASCADE)

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

    objects = models.Manager()

    class Meta:
        get_latest_by = 'sessionDate'
        ordering = ('sessionNo',)
        verbose_name_plural = 'sessions'

    def __unicode__(self):
        return self.pk

    def get_absolute_url(self):
        return "/patient_details/%s" % self.patient_id

