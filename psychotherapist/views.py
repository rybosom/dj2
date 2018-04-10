from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient, Session
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
import datetime


def user_login(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:
        if request.POST:
            username = request.POST.get('username').lower()
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                state = 'user_invalid'
                return render(request, 'psychotherapist/login.html', {'state': state, 'username': username})
    return render(request, 'psychotherapist/login.html')


def user_logout(request):
    logout(request)
    return redirect('/')


@login_required(login_url='/user_login/')
def index(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    return render(request, 'psychotherapist/index.html', {'firstname': firstname, 'username': username,
                                                          'patient_count': patient_count})


@login_required(login_url='/user_login/')
def add_patient(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    uid = request.user.id
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    state = ''
    if request.POST:
        givenName = request.POST.get('firstName')
        lastName = request.POST.get('lastName')
        bday = request.POST.get('bday')
        gender = request.POST.get('gender')
        bio = request.POST.get('patient_info')
        user = User.objects.get(id=uid)
        new_patient = Patient(firstName=givenName, lastName=lastName, dob=bday, registerDate=datetime.datetime.now(),
                              gender=gender, bio=bio, owner=user)
        new_patient.save()
        pfName = new_patient.firstName
        plName = new_patient.lastName
        pfullname = pfName + ' ' + plName
        state = 'Dodano pacjenta: %s' % pfullname
        patient_count = int(Patient.objects.filter(owner=request.user).count())
        return render(request, 'psychotherapist/patient.html', {'firstname': firstname, 'username': username,
                                                                'patient_count': patient_count, 'state': state})
    return render(request, 'psychotherapist/patient.html', {'firstname': firstname, 'username': username,
                                                            'patient_count': patient_count, 'state': state})


@login_required(login_url='/user_login/')
def list_patients(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    uid = request.user.id
    objects = Patient.objects.all().filter(owner=uid)
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    state = ''
    if request.POST:
        for key in request.POST:
            if 'rm_' in key:
                patient_id = key.replace('rm_', '')
                Patient.objects.filter(pk=patient_id).delete()
                state = "Usunięto pacjenta nr %s." % patient_id
        patient_count = int(Patient.objects.filter(owner=request.user).count())
    return render(request, 'psychotherapist/patient_list.html', {'firstname': firstname, 'username': username,
                                                                 'objects': objects, 'patient_count': patient_count,
                                                                 'state': state})


def daterange(start_date, end_date, weekday):
    for n in range(int((end_date - start_date).days)):
        next_date = start_date + timedelta(n)
        if next_date.weekday() == weekday:
            yield start_date + timedelta(n)


@login_required(login_url='/user_login/')
def patient_details(request, patient_id):
    state = ''
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    patient = get_object_or_404(Patient, pk=patient_id)
    ex_ses = int(Session.objects.filter(patient_id=patient_id).count())
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    session_list = Session.objects.filter(patient_id=patient)
    # check if current user is owner of the patient
    if request.user == patient.owner:
        # patient data modification
        if 'mod_patient' in request.POST:
            patient.firstName = request.POST.get('firstName')
            patient.lastName = request.POST.get('lastName')
            patient.gender = request.POST.get('gender')
            patient.bio = request.POST.get('patient_info')
            patient.save()
            sessions = request.POST.getlist('sessionList')
            for s in sessions:
                # save session data only if session date was added
                if request.POST.get('session_date_'+s) == '':
                    pass
                else:
                    session = get_object_or_404(Session, sessionNo=int(s), patient_id=patient)
                    session.sessionDate = request.POST.get('session_date_'+s)
                    session.subject = request.POST.get('session_subject_'+s)
                    session.content = request.POST.get('session_content_'+s)
                    session.notes = request.POST.get('session_notes_'+s)
                    session.save()
            state = "Dane pacjenta i wszystkich sesji zostały zapisane."
            return render(request, 'psychotherapist/patient_details.html', {'username': username, 'patient': patient,
                                                                            'patient_count': patient_count,
                                                                            'session_list': session_list,
                                                                            'state': state})
        # adding new sessions to patient
        if 'add_session' in request.POST:
            new_sessions = int(request.POST.get('session_count'))
            session_pattern = int(request.POST.get('session_pattern'))
            # if no session pattern selected then date for 1st session is not saved
            if session_pattern == 0:
                # if no existing session - numbering starts from 1.
                if ex_ses == 0:
                    for i in range(1, new_sessions + 1):
                        s = Session(patient_id=patient, sessionNo=i)
                        s.save()
                    state = "Dodano sesje."
                    return render(request, 'psychotherapist/patient_details.html',
                                  {'username': username, 'patient': patient,
                                   'session_list': session_list,
                                   'patient_count': patient_count,
                                   'state': state})
                else:
                    # session numbering starting at last session number n+1
                    for i in range(1, new_sessions + 1):
                        add_sessions = ex_ses + i
                        s = Session(patient_id=patient, sessionNo=add_sessions)
                        s.save()
                    state = "Dodano sesje."
                    return render(request, 'psychotherapist/patient_details.html',
                                  {'username': username, 'patient': patient,
                                   'session_list': session_list,
                                   'patient_count': patient_count,
                                   'state': state})
            # for weekly sessions dates are calculated based on weekday of 1st session date (e.g. all mondays between
            # start_date and end_date)
            if session_pattern == 7:
                str_init_session = request.POST.get('init_session')
                init_session = datetime.datetime.strptime(str_init_session, '%Y-%m-%d %H:%M')
                end_session = init_session + timedelta(days=(new_sessions*session_pattern))
                session_dates = list()
                # dummy record added to list so that i matches list item d
                session_dates.append('')
                for d in daterange(init_session, end_session, init_session.weekday()):
                    session_dates.append(d)
                if ex_ses == 0:
                    for i in range(1, new_sessions + 1):
                        s = Session(patient_id=patient, sessionNo=i, sessionDate=session_dates[i])
                        s.save()
                    state = "Dodano sesje."
                    return render(request, 'psychotherapist/patient_details.html',
                                  {'username': username, 'patient': patient,
                                   'session_list': session_list,
                                   'patient_count': patient_count,
                                   'state': state})
                else:
                    for i in range(1, new_sessions + 1):
                        add_sessions = ex_ses + i
                        s = Session(patient_id=patient, sessionNo=add_sessions, sessionDate=session_dates[i])
                        s.save()
                    state = "Dodano sesje."
                    return render(request, 'psychotherapist/patient_details.html',
                                  {'username': username, 'patient': patient,
                                   'session_list': session_list,
                                   'patient_count': patient_count,
                                   'state': state})
            # biweekly sessions dates calculation
            else:
                str_init_session = request.POST.get('init_session')
                init_session = datetime.datetime.strptime(str_init_session, '%Y-%m-%d %H:%M')
                end_session = init_session + timedelta(days=(new_sessions*session_pattern))
                session_dates = list()
                # dummy list record
                session_dates.append('')
                for d in daterange(init_session, end_session, init_session.weekday()):
                    session_dates.append(d)
                if ex_ses == 0:
                    for i in range(1, new_sessions + 1):
                        if i == 1:
                            s = Session(patient_id=patient, sessionNo=i, sessionDate=session_dates[i])
                            s.save()
                        else:
                            # for i <> 1 datelist record is chosen d=i+(i-1)
                            s = Session(patient_id=patient, sessionNo=i, sessionDate=session_dates[i+(i-1)])
                            s.save()
                    state = "Dodano sesje."
                    return render(request, 'psychotherapist/patient_details.html',
                                  {'username': username, 'patient': patient,
                                   'session_list': session_list,
                                   'patient_count': patient_count,
                                   'state': state})
                else:
                    for i in range(1, new_sessions + 1):
                        add_sessions = ex_ses + i
                        s = Session(patient_id=patient, sessionNo=add_sessions, sessionDate=session_dates[i+(i-1)])
                        s.save()
                    state = "Dodano sesje."
                    return render(request, 'psychotherapist/patient_details.html',
                                  {'username': username, 'patient': patient,
                                   'session_list': session_list,
                                   'patient_count': patient_count,
                                   'state': state})
        # remove session and recalculate session numbering for all entries for current patient
        if 'remove' in request.POST:
            session_id = request.POST.get('remove')
            s = Session.objects.filter(sessionNo=session_id, patient_id=patient)
            s.delete()
            rows = Session.objects.filter(patient_id=patient)
            for row in rows:
                s_num = row.sessionNo
                if s_num > int(session_id):
                    s_tomod = Session.objects.get(patient_id=patient, sessionNo=s_num)
                    s_tomod.sessionNo = s_num-1
                    s_tomod.save()
            state = "Skasowano sesję nr %s." % session_id
            return render(request, 'psychotherapist/patient_details.html', {'username': username, 'patient': patient,
                                                                            'session_list': session_list,
                                                                            'patient_count': patient_count,
                                                                            'state': state})
        # save currently edited session data - session date is not required for performing save operation
        if 'save' in request.POST:
            s = request.POST.get('save')
            session = get_object_or_404(Session, sessionNo=int(s), patient_id=patient)
            if request.POST.get('session_date_'+s) == '':
                session.subject = request.POST.get('session_subject_' + s)
                session.content = request.POST.get('session_content_' + s)
                session.notes = request.POST.get('session_notes_' + s)
                session.save()
            else:
                session.sessionDate = request.POST.get('session_date_'+s)
                session.subject = request.POST.get('session_subject_'+s)
                session.content = request.POST.get('session_content_'+s)
                session.notes = request.POST.get('session_notes_'+s)
                session.save()
            state = "Zapisano dane sesji nr %s." % s
            return render(request, 'psychotherapist/patient_details.html', {'username': username, 'patient': patient,
                                                                            'session_list': session_list,
                                                                            'patient_count': patient_count,
                                                                            'state': state})
        return render(request, 'psychotherapist/patient_details.html', {'username': username, 'patient': patient,
                                                                        'session_list': session_list,
                                                                        'patient_count': patient_count,
                                                                        'state': state})
    else:
        # no access display
        return render(request, 'psychotherapist/deny.html', {'username': username, 'firstname': firstname})


@login_required(login_url='/user_login/')
def payment_list(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    patients = Patient.objects.filter(owner=request.user)
    # display sessions with sessionDate filled
    objects = Session.objects.filter(patient_id__in=patients, sessionDate__isnull=False)
    if 'rm' in request.POST:
        pk = request.POST.get('rm')
        Session.objects.filter(pk=pk).delete()
    return render(request, 'psychotherapist/payment_list.html', {'objects': objects, 'username': username,
                                                                 'patient_count': patient_count})


@login_required(login_url='/user_login/')
def patient_payments(request, patient_id):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    patient = get_object_or_404(Patient, pk=patient_id)
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    session_list = Session.objects.filter(patient_id=patient)
    if request.POST:
        new_payments = request.POST.getlist('paymentList')
        for p in new_payments:
            if request.POST.get('paymentDate'+p) == '':
                pass
            else:
                payment = get_object_or_404(Session, pk=int(p))
                payment.paymentDate = request.POST.get('paymentDate'+p)
                payment.amount = request.POST.get('amount'+p)
                payment.method = request.POST.get('method'+p)
                payment.save()
    return render(request, 'psychotherapist/patient_payments.html', {'patient_count': patient_count,
                                                                     'session_list': session_list,
                                                                     'patient': patient,
                                                                     'username': username})


@login_required(login_url='/admin/')
@user_passes_test(lambda u: u.is_superuser, login_url='/user_login/')
def admin(request):
    patient_count = Patient.objects.all().count()
    session_count = Session.objects.all().count()
    return render(request, 'psychotherapist/admin.html', {'patient_count': patient_count,
                                                          'session_count': session_count})

