import sys
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from .models import Patient, Session, UserProfile, ActivityLog, CommunicationLog
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
import datetime
import pytz
import logging
from datetime import datetime, timezone, timedelta, date
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# import unicodedata
# import getpass
# import imaplib
# from imaplib import IMAP4, IMAP4_SSL
# import email


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


# info_logger = setup_logger('info_logger', 'email_info.log')
# error_logger = setup_logger('error_logger', 'email_error.log', level=logging.ERROR)
# warn_logger = setup_logger('warn_logger', 'email_warning.log', level=logging.WARNING)


# def test(request):
#     remind_treshold = datetime.datetime.now() + timedelta(days=1)
#     # remind_treshold = '2018-04-18 15:00'
#     remind = Session.objects.filter(sessionDate=remind_treshold)
#     if not remind:
#         pass
#     else:
#         patient = remind[0].patient_id
#         return patient
#     return redirect('/')


def user_login(request):
    if request.user.is_authenticated:
        log = ActivityLog(user_id=request.user, userIP=get_client_ip(request), detail=request.META['HTTP_USER_AGENT'],
                          url=get_current_path(request))
        log.save()
        return redirect('/')
    else:
        if request.POST:
            username = request.POST.get('username').lower()
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                log = ActivityLog(user_id=request.user, userIP=get_client_ip(request),
                                  detail=request.META['HTTP_USER_AGENT'], url=get_current_path(request))
                log.save()
                return redirect('/')
            else:
                state = 'user_invalid'
                return render(request, 'psychotherapist/login.html', {'state': state, 'username': username})
    return render(request, 'psychotherapist/login.html')


def user_logout(request):
    log = ActivityLog(user_id=request.user, userIP=get_client_ip(request),
                      detail=request.META['HTTP_USER_AGENT'], url=get_current_path(request))
    log.save()
    logout(request)
    return redirect('/')


@login_required(login_url='/user_login/')
def change_pass(request):
    if request.POST:
        user = authenticate(username=request.user, password=request.POST.get('oldPass'))
        if user is not None:
            user.set_password(request.POST.get('newPass'))
            user.save()
            return redirect('/')
        else:
            state = "Podane aktualne hasło jest nieprawidłowe."
            return render(request, 'psychotherapist/change_pass.html', {'state': state})
    return render(request, 'psychotherapist/change_pass.html')


@login_required(login_url='/user_login/')
def index(request):
    log = ActivityLog(user_id=request.user, userIP=get_client_ip(request), detail=request.META['HTTP_USER_AGENT'],
                      url=get_current_path(request))
    log.save()
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    return render(request, 'psychotherapist/index.html', {'firstname': firstname, 'username': username,
                                                          'patient_count': patient_count, 'date': date.today()})


@login_required(login_url='/user_login/')
def deny(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    return render(request, 'psychotherapist/deny.html', {'firstname': firstname, 'username': username})


@login_required(login_url='/user_login/')
def add_patient(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    uid = request.user.id
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    state = ''
    if 'save_add' in request.POST:
        givenName = request.POST.get('firstName')
        lastName = request.POST.get('lastName')
        # bday = request.POST.get('bday')
        byear = request.POST.get('byear')
        gender = request.POST.get('gender')
        bio = request.POST.get('patient_info')
        user = User.objects.get(id=uid)
        new_patient = Patient(firstName=givenName, lastName=lastName, byear=byear, registerDate=datetime.now(),
                              gender=gender, bio=bio, owner=user)
        new_patient.save()
        pfName = new_patient.firstName
        plName = new_patient.lastName
        pfullname = pfName + ' ' + plName
        state = 'Dodano pacjenta: %s' % pfullname
        patient_count = int(Patient.objects.filter(owner=request.user).count())
        return render(request, 'psychotherapist/patient.html', {'firstname': firstname, 'username': username,
                                                                'patient_count': patient_count, 'state': state})
    if 'save_edit' in request.POST:
        givenName = request.POST.get('firstName')
        lastName = request.POST.get('lastName')
        # bday = request.POST.get('bday')
        byear = request.POST.get('byear')
        gender = request.POST.get('gender')
        bio = request.POST.get('patient_info')
        user = User.objects.get(id=uid)
        new_patient = Patient(firstName=givenName, lastName=lastName, byear=byear, registerDate=datetime.now(),
                              gender=gender, bio=bio, owner=user)
        new_patient.save()
        return redirect('/patient_details/' + str(new_patient.pk))
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
            patient.lastMod = datetime.now()
            patient.save()
            sessions = request.POST.getlist('sessionList')
            for s in sessions:
                session = get_object_or_404(Session, sessionNo=int(s), patient_id=patient)
                session.subject = request.POST.get('session_subject_' + s)
                session.content = request.POST.get('session_content_' + s)
                session.notes = request.POST.get('session_notes_' + s)
                session.lastMod = datetime.now()
                if request.POST.get('session_date_' + s) == '':
                    session.paymentDate = None
                    session.sessionDate = None
                else:
                    session.paymentDate = request.POST.get('session_date_' + s)[:10]
                    session.sessionDate = request.POST.get('session_date_' + s)
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
                        s = Session(patient_id=patient, sessionNo=i, lastMod=datetime.now())
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
                        s = Session(patient_id=patient, sessionNo=add_sessions, lastMod=datetime.now())
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
                init_session = datetime.strptime(str_init_session, '%Y-%m-%d %H:%M')
                end_session = init_session + timedelta(days=(new_sessions * session_pattern))
                session_dates = list()
                # dummy record added to list so that i matches list item d
                session_dates.append('')
                for d in daterange(init_session, end_session, init_session.weekday()):
                    session_dates.append(d)
                if ex_ses == 0:
                    for i in range(1, new_sessions + 1):
                        s = Session(patient_id=patient, sessionNo=i, sessionDate=session_dates[i],
                                    paymentDate=session_dates[i], lastMod=datetime.now())
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
                        s = Session(patient_id=patient, sessionNo=add_sessions, sessionDate=session_dates[i],
                                    paymentDate=session_dates[i], lastMod=datetime.now())
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
                init_session = datetime.strptime(str_init_session, '%Y-%m-%d %H:%M')
                end_session = init_session + timedelta(days=(new_sessions * session_pattern))
                session_dates = list()
                # dummy list record
                session_dates.append('')
                for d in daterange(init_session, end_session, init_session.weekday()):
                    session_dates.append(d)
                if ex_ses == 0:
                    for i in range(1, new_sessions + 1):
                        if i == 1:
                            s = Session(patient_id=patient, sessionNo=i, sessionDate=session_dates[i],
                                        paymentDate=session_dates[i], lastMod=datetime.now())
                            s.save()
                        else:
                            # for i <> 1 datelist record is chosen d=i+(i-1)
                            s = Session(patient_id=patient, sessionNo=i, sessionDate=session_dates[i + (i - 1)],
                                        paymentDate=session_dates[i + (i - 1)], lastMod=datetime.now())
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
                        s = Session(patient_id=patient, sessionNo=add_sessions, sessionDate=session_dates[i + (i - 1)],
                                    paymentDate=session_dates[i + (i - 1)], lastMod=datetime.now())
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
                    s_tomod.sessionNo = s_num - 1
                    s_tomod.lastMod = datetime.now()
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
            if request.POST.get('session_date_' + s) == '':
                session.subject = request.POST.get('session_subject_' + s)
                session.content = request.POST.get('session_content_' + s)
                session.notes = request.POST.get('session_notes_' + s)
                session.lastMod = datetime.now()
                session.save()
            else:
                session.sessionDate = request.POST.get('session_date_' + s)
                session.subject = request.POST.get('session_subject_' + s)
                session.content = request.POST.get('session_content_' + s)
                session.notes = request.POST.get('session_notes_' + s)
                session.paymentDate = request.POST.get('session_date_' + s)[:10]
                session.lastMod = datetime.now()
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
        return redirect('/deny')


@login_required(login_url='/user_login/')
def payment_list(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    patient_count = int(Patient.objects.filter(owner=request.user).count())
    patients = Patient.objects.filter(owner=request.user)
    # display sessions with sessionDate filled
    objects = Session.objects.filter(patient_id__in=patients, sessionDate__isnull=False)
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
    if request.user == patient.owner:
        if request.POST:
            new_payments = request.POST.getlist('paymentList')
            for p in new_payments:
                if request.POST.get('paymentDate' + p) == '':
                    pass
                else:
                    payment = get_object_or_404(Session, pk=int(p))
                    payment.paymentDate = request.POST.get('paymentDate' + p)
                    payment.lastMod = datetime.now()
                    if request.POST.get('amount' + p) == '':
                        payment.amount = None
                        payment.method = None
                    else:
                        payment.amount = request.POST.get('amount' + p)
                        payment.method = request.POST.get('method' + p)
                    payment.save()
        return render(request, 'psychotherapist/patient_payments.html', {'patient_count': patient_count,
                                                                         'session_list': session_list,
                                                                         'patient': patient,
                                                                         'username': username})
    else:
        # no access display
        return redirect('/deny')


@login_required(login_url='/admin/')
@user_passes_test(lambda u: u.is_superuser, login_url='/user_login/')
def psycho_admin(request):
    firstname = request.user.first_name
    lastname = request.user.last_name
    username = firstname + ' ' + lastname
    patient_count = Patient.objects.all().count()
    session_count = Session.objects.all().count()
    inactive_user = User.objects.filter(is_active=False)
    if "activate" in request.POST:
        u = get_object_or_404(User, username=request.POST.get("activate"))
        u.is_active = True
        u.save()
        send_email(u.email, u.username)
        return redirect('/psycho_admin/')
    return render(request, 'psychotherapist/admin.html', {'patient_count': patient_count,
                                                          'session_count': session_count,
                                                          'inactive_user': inactive_user,
                                                          'username': username})


def send_email(recipient, username):
    smtp_server = 's1.laohost.net'
    smtp_port = '587'
    mail_subject = 'Psychotherapist.pl - aktywacja konta'
    email_body = 'Twoje konto zostało aktywowane. Nazwa użytkownika: ' + username

    msg = MIMEMultipart()
    msg['From'] = 'noreply@psychotherapist.pl'
    msg['To'] = recipient
    msg['Subject'] = mail_subject
    body = MIMEText(email_body, 'plain')
    msg.attach(body)

    # noinspection PyBroadException
    try:
        smtpObj = smtplib.SMTP(smtp_server, smtp_port)
        smtpObj.login('kontakt@psychotherapist.pl', 'o$Htf0A1eo^Zsy#7')
        smtpObj.sendmail('noreply@psychotherapist.pl', recipient, msg.as_string())
        c = CommunicationLog(commType='email', rcpt=recipient, content=msg.as_string())
        c.save()
    except Exception:
        c = CommunicationLog(commType='email', rcpt=recipient, exception=sys.exc_info()[1], content=msg.as_string())
        c.save()
        # error_logger.error('ERROR: ', sys.exc_info()[1])


def register(request):
    firstname = request.POST.get('id_firstname')
    lastname = request.POST.get('id_lastname')
    email = request.POST.get('id_email')
    password = request.POST.get('id_password')
    password_rep = request.POST.get('id_rep_password')
    state = '0'
    if request.POST:
        if password == password_rep:
            letters = {'ł': 'l', 'ą': 'a', 'ń': 'n', 'ć': 'c', 'ó': 'o', 'ę': 'e', 'ś': 's', 'ź': 'z', 'ż': 'z'}
            trans = str.maketrans(letters)
            val = "{0}{1}".format(firstname[:1], lastname).lower()
            uid = val.translate(trans)
            x = User.objects.filter(username__contains=uid).count()
            if x == 0 and User.objects.filter(username=uid).count() == 0:
                u = User(username=uid, first_name=firstname, last_name=lastname, email=email,
                         is_active=False, is_superuser=False)
                u.set_password(password)
                u.save()
                up = UserProfile(user_id=u, consent=True)
                up.save()
                state = '2'
                return render(request, 'psychotherapist/register.html', {'state': state, 'user': u})
            else:
                n_uid = "{0}{1}".format(uid, x)
                u = User(username=n_uid, first_name=firstname, last_name=lastname, email=email,
                         is_active=False, is_superuser=False)
                u.set_password(password)
                u.save()
                up = UserProfile(user_id=u, consent=True)
                up.save()
                state = '2'
                return render(request, 'psychotherapist/register.html', {'state': state, 'user': u})
        else:
            state = '1'
    return render(request, 'psychotherapist/register.html', {'state': state})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_current_path(request):
    return {
        'current_path': request.get_full_path()
    }

# def mail_imap(request):
#     mail = imaplib.IMAP4_SSL('mail.s1.laohost.net')
#     (retcode, capabilities) = mail.login('test@psychotherapist.pl', 'Haslo123!')
#     mail.list()
#     mail.select('inbox')
#     n = 0
#     (retcode, messages) = mail.search(None, '(UNSEEN)')
#     if retcode == 'OK':
#         for num in messages[0].split():
#             print('Processing ')
#             n = n + 1
#             typ, data = mail.fetch(num, '(RFC822)')
#             for response_part in data:
#                 if isinstance(response_part, tuple):
#                     original = email.message_from_bytes(response_part[1])
#                     print(original['From'])
#                     print(original['Subject'])
#                     typ, data = mail.store(num, '+FLAGS', '\\Seen')
#
#     print(n)
#     return redirect('/')
