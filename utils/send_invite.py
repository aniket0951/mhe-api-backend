import logging
from datetime import datetime,timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as Encoders
from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger('django')

STANDARD_DATE_FORMAT        = "%Y-%m-%d"
STANDARD_TIME_FORMAT        = "%H:%M:%S"
STANDARD_DATETIME_FORMAT    = "%Y-%m-%d %H:%M:%S"
OUTPUT_TIME_FORMAT          = "%I:%M %p"
OUTPUT_DATE_FORMAT          = "%d-%m-%Y"
APPOINTMENT_MODE = {
        "HV":"Hospital Visit",
        "VC":"Video Consultation",
        "PR":"Prime Consultation",
}

def prepare_query_resp_of_appointment(appointment_obj):

    query_resp = {}

    date_str = appointment_obj.appointment_date.strftime(STANDARD_DATE_FORMAT)
    
    start_time_obj = appointment_obj.appointment_slot
    start_time_str = start_time_obj.strftime(STANDARD_TIME_FORMAT)
    
    dtstart = datetime.strptime(date_str + " "+ start_time_str, STANDARD_DATETIME_FORMAT)
    end_time_obj = dtstart + timedelta(minutes=int(10))

    email = appointment_obj.patient.email
    
    if appointment_obj.family_member:
        email = appointment_obj.family_member.email
    if appointment_obj.patient and appointment_obj.patient.active_view == 'Corporate':
        email = appointment_obj.patient.corporate_email
    
    query_resp['date']              = date_str
    query_resp['name']              = appointment_obj.doctor.name
    query_resp['hospital']          = appointment_obj.hospital.description
    query_resp['unique_id']         = appointment_obj.root_appointment_id or appointment_obj.id
    query_resp["recipient"]         = email
    query_resp['guest_email']       = settings.EMAIL_FROM_USER
    query_resp['appointment_mode']  = APPOINTMENT_MODE[appointment_obj.appointment_mode]
    query_resp['start_time']        = start_time_str
    query_resp['end_time']          = end_time_obj.strftime(STANDARD_TIME_FORMAT)
    query_resp['start_time_obj']    = start_time_obj
    query_resp['end_time_obj']      = end_time_obj

    return query_resp

def send_appointment_invitation(appointment_obj):

    query_resp = prepare_query_resp_of_appointment(appointment_obj)
    query_resp['subject']       = "Appointment booking confirmation with {dr_name} from {start_date} to {end_date} on {appointment_date}".format(
                                                    dr_name             = query_resp['name'],
                                                    start_date          = query_resp['start_time_obj'].strftime(OUTPUT_TIME_FORMAT), 
                                                    end_date            = query_resp['end_time_obj'].strftime(OUTPUT_TIME_FORMAT),
                                                    appointment_date    = appointment_obj.appointment_date.strftime(OUTPUT_DATE_FORMAT),
                                                )
    
    query_resp['description']   = "Your {appointment_mode} appointment with {name} at Manipal Hospitals has been confirmed,\nPlease download the app for more information about appointments.\nClick here to download http://onelink.to/tzyzna". \
                                format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'])
    query_resp['eml_body'] = "Your {appointment_mode} appointment with {name} at {hospital} has been confirmed,\nPlease download the app for more information about appointments.\nClick here to download http://onelink.to/tzyzna". \
                                format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'], hospital=query_resp['hospital'])
    
    if query_resp['appointment_mode'] == "VC":
        query_resp['description']   = "Your {appointment_mode} appointment with {name} at Manipal Hospitals has been confirmed,\nPlease download the app to join your video consultation appointment.\nClick here to download http://onelink.to/tzyzna". \
                                    format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'])
        query_resp['eml_body'] = "Your {appointment_mode} appointment with {name} at {hospital} has been confirmed,\nPlease download the app to join your video consultation appointment.\nClick here to download http://onelink.to/tzyzna". \
                                    format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'], hospital=query_resp['hospital'])
    query_resp['summary']       = "Your {appointment_mode} appointment is confirmed in Manipal Hospitals".format(appointment_mode=query_resp['appointment_mode'])
    query_resp['event_method']  = "REQUEST"
    query_resp['event_status']  = "CONFIRMED"

    return send_invitation_mail(query_resp)

def send_appointment_cancellation_invitation(appointment_obj):

    query_resp = prepare_query_resp_of_appointment(appointment_obj)
    query_resp['subject']       = "Your appointment with {dr_name} on {appointment_date} has been cancelled".format(
                                                    dr_name             = query_resp['name'],
                                                    appointment_date    = appointment_obj.appointment_date.strftime(OUTPUT_DATE_FORMAT),
                                                )

    query_resp['description']   = "Your appointment with {name} has been cancelled".format(name=query_resp['name'])
    query_resp['summary']       = "Your {appointment_mode} appointment with {dr_name} has been cancelled".format(appointment_mode=query_resp['appointment_mode'],dr_name=query_resp['name'])
    query_resp['eml_body']      = "Appointment cancellation with {name} for {appointment_mode}".format(name=query_resp['name'],appointment_mode=query_resp['appointment_mode'])
    query_resp['event_method']  = "CANCEL"
    query_resp['event_status']  = "CANCELLED"

    return send_invitation_mail(query_resp)

def send_appointment_rescheduling_invitation(appointment_obj):

    query_resp = prepare_query_resp_of_appointment(appointment_obj)
    query_resp['subject']       = "Your appointment with {dr_name} has been rescheduled on {appointment_date} from {start_date} to {end_date}".format(
                                                    dr_name             = query_resp['name'],
                                                    appointment_date    = appointment_obj.appointment_date.strftime(OUTPUT_DATE_FORMAT),
                                                    start_date          = query_resp['start_time_obj'].strftime(OUTPUT_TIME_FORMAT), 
                                                    end_date            = query_resp['end_time_obj'].strftime(OUTPUT_TIME_FORMAT)
                                                )
    query_resp['description']   = "Your {appointment_mode} appointment with {name} at Manipal Hospitals has been confirmed,\nPlease download the app for more information about appointments.\nClick here to download http://onelink.to/tzyzna". \
                                format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'])
    query_resp['eml_body'] = "Your {appointment_mode} appointment with {name} at {hospital} has been confirmed,\nPlease download the app for more information about appointments.\nClick here to download http://onelink.to/tzyzna". \
                                format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'], hospital=query_resp['hospital'])
    
    if query_resp['appointment_mode'] == "VC":
        query_resp['description']   = "Your {appointment_mode} appointment with {name} at Manipal Hospitals has been confirmed,\nPlease download the app to join your video consultation appointment.\nClick here to download http://onelink.to/tzyzna". \
                                    format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'])
        query_resp['eml_body'] = "Your {appointment_mode} appointment with {name} at {hospital} has been confirmed,\nPlease download the app to join your video consultation appointment.\nClick here to download http://onelink.to/tzyzna". \
                                    format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'], hospital=query_resp['hospital'])
    
    query_resp['summary']       = "Your {appointment_mode} appointment with {dr_name} has been rescheduled".format(appointment_mode=query_resp['appointment_mode'],dr_name=query_resp['name'])
    query_resp['eml_body']      = "Confirmation for rescheduling the {appointment_mode} appointment with {name}".format(appointment_mode=query_resp['appointment_mode'],name=query_resp['name'])
    query_resp['event_method']  = "REQUEST"
    query_resp['event_status']  = "CONFIRMED"
    query_resp['event_sequence']  = "1"
    
    return send_invitation_mail(query_resp)

def send_invitation_mail(query_resp):

    if not settings.SEND_CALENDAR_INVITATION:
        return True
    
    msg = MIMEMultipart('mixed')
    attendees = ["{}".format(query_resp["recipient"])]
    msg['To'] = attendees[0]
    service_email = settings.EMAIL_FROM_USER
    organizer = "ORGANIZER;CN=organiser:mailto:{service_email}".format(service_email=service_email)
    fro = "{service_email}".format(service_email=service_email)
    
    dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    
    dtstart = datetime.strptime(query_resp['date'] + " "+ query_resp['start_time'], STANDARD_DATETIME_FORMAT)
    dtstart = dtstart - timedelta(hours=5, minutes=30)
    dtstart = dtstart.strftime("%Y%m%dT%H%M%SZ")

    dtend = datetime.strptime(query_resp['date'] + " "+ query_resp['end_time'], STANDARD_DATETIME_FORMAT)
    dtend = dtend - timedelta(hours=5, minutes=30)
    dtend = dtend.strftime("%Y%m%dT%H%M%SZ")

    websiteurl = settings.WEBSITE

    CRLF = "\r\n"
    attendee = ""

    guest = query_resp.get('guest_email')

    description = "DESCRIPTION: "+query_resp['description'] + CRLF

    if guest:
        attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE"+CRLF + " ;CN={guest};X-NUM-GUESTS=0:"+CRLF+" mailto:{guest}" + CRLF

    for att in attendees:
        attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE" + CRLF+" ;CN="+att+";X-NUM-GUESTS=0:"+CRLF+" mailto:"+att+CRLF
    
    
    ical = "BEGIN:VCALENDAR"+CRLF+"PRODID:pyICSParser" + CRLF+"VERSION:2.0"+CRLF+"CALSCALE:GREGORIAN"+CRLF
    if query_resp.get('event_method'):
        ical += "METHOD:"+query_resp['event_method']+CRLF
    ical += "BEGIN:VEVENT"+CRLF+"DTSTART:"+dtstart + CRLF+"DTEND:"+dtend+CRLF+"DTSTAMP:"+dtstamp+CRLF+organizer+CRLF
    ical += "UID:{unique_id}"+"@"+"{site_url}"+CRLF
    ical += attendee+"CREATED:"+dtstamp+CRLF+description+"LAST-MODIFIED:" + dtstamp+CRLF+"LOCATION:"+CRLF+"SEQUENCE:0"+CRLF
    if query_resp.get('event_sequence'):
        ical += "SEQUENCE:"+query_resp['event_sequence']+CRLF
    
    ical += "STATUS:"+query_resp['event_status']+CRLF
    ical += "SUMMARY:"+query_resp['summary'] + CRLF+"TRANSP:OPAQUE"+CRLF+"END:VEVENT"+CRLF+"END:VCALENDAR"+CRLF

    if guest:
        ical = ical.format(unique_id=query_resp['unique_id'], site_url=websiteurl, guest=guest)
    else:
        ical = ical.format(unique_id=query_resp['unique_id'], site_url=websiteurl)

    eml_body = query_resp['eml_body']
    msg = MIMEMultipart('mixed')
    msg['Reply-To'] = fro
    msg['Date'] = dtstamp
    msg['Subject'] = query_resp['subject']
    msg['From'] = fro
    msg['To'] = ",".join(attendees)

    part_email = MIMEText(eml_body, "html")
    part_cal = MIMEText(ical, 'calendar;method=REQUEST')

    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)

    ical_atch = MIMEBase('application/ics', ' ;name="%s"' % ("invite.ics"))
    ical_atch.set_payload(ical)
    Encoders.encode_base64(ical_atch)
    ical_atch.add_header('Content-Disposition', 'attachment; filename="%s"' % ("invite.ics"))

    eml_atch = MIMEBase('text/plain', '')
    eml_atch.add_header('Content-Transfer-Encoding', "")

    msgAlternative.attach(part_email)
    msgAlternative.attach(part_cal)

    email = EmailMultiAlternatives(
        msg['Subject'], None, msg['From'], attendees
    )
    email.attach(msg)
    email_sent = email.send()

    return email_sent