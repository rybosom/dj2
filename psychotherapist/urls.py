from django.conf.urls import url
from . import views
from django.contrib.auth.decorators import login_required, user_passes_test


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^user_login', views.user_login),
    url(r'^user_logout', views.user_logout),
    url(r'^add_patient', views.add_patient),
    url(r'^list_patients', views.list_patients),
    url(r'^patient_details/(?P<patient_id>[0-9]+)/$', views.patient_details, name='patient_details'),
    url(r'^patient_payments/(?P<patient_id>[0-9]+)/$', views.patient_payments, name='patient_payments'),
    url(r'^payment_list', views.payment_list),
    url(r'^admin', views.admin),
]
