import boto3
from datetime import datetime,timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders as Encoders
from django.conf import settings

def send_invitation(appointment_id, recipient):
    query_resp = {}
    query_resp['start_time'] = "10:00:00"
    query_resp['end_time'] = "12:00:00"
    query_resp['appointment_date']="2021-09-02"
    query_resp['prefix_name']="Dr."
    query_resp['name']="Anand"
    
    ses_client = boto3.client('ses')
    msg = MIMEMultipart('mixed')
    attendees = ["{}".format(recipient)]
    msg['To'] = attendees[0]
    service_email = settings.EMAIL_FROM_USER
    organizer = "ORGANIZER;CN=organiser:mailto:{service_email}".format(service_email=service_email)
    fro = "{service_email}".format(service_email=service_email)
    
    dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    start_time = query_resp['start_time']
    end_time = query_resp['end_time']

    appointment_start_date = query_resp['appointment_date'] + " "+start_time
    appointment_end_date = query_resp['appointment_date'] + " "+end_time
    
    dr_name = query_resp['prefix_name'] + " " + query_resp['name']

    dtstart = datetime.strptime(appointment_start_date, "%Y-%m-%d %H:%M:%S")
    dtstart = dtstart - timedelta(hours=5, minutes=30)
    dtstart = dtstart.strftime("%Y%m%dT%H%M%SZ")
    dtend = datetime.strptime(appointment_end_date, "%Y-%m-%d %H:%M:%S")
    dtend = dtend - timedelta(hours=5, minutes=30)
    dtend = dtend.strftime("%Y%m%dT%H%M%SZ")

    # ddtstart and dtend used to show the time of appointment
    websiteurl = settings.WEBSITE

    CRLF = "\r\n"
    attendee = ""

    guest = ''

    guest = query_resp['docter_email']
    name = dr_name
    description = "DESCRIPTION: Your appointment with {name} is now confirmed"+CRLF.format(name=name) # doctor name
    attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE"+CRLF + " ;CN={guest};X-NUM-GUESTS=0:"+CRLF+" mailto:{guest}" + CRLF.format(guest=query_resp['docter_email'])

    for att in attendees:
        attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE" + CRLF+" ;CN="+att+";X-NUM-GUESTS=0:"+CRLF+" mailto:"+att+CRLF

    ical = "BEGIN:VCALENDAR"+CRLF+"PRODID:pyICSParser" + CRLF+"VERSION:2.0"+CRLF+"CALSCALE:GREGORIAN"+CRLF
    ical += "METHOD:REQUEST"+CRLF+"BEGIN:VEVENT"+CRLF+"DTSTART:"+dtstart + CRLF+"DTEND:"+dtend+CRLF+"DTSTAMP:"+dtstamp+CRLF+organizer+CRLF
    ical += "UID:{appointment_id}"+"@"+"{site_url}"+CRLF.format(appointment_id=appointment_id, site_url=websiteurl)  # appointment_id@c2cdomain.com
    ical += attendee+"CREATED:"+dtstamp+CRLF+description+"LAST-MODIFIED:" + dtstamp+CRLF+"LOCATION:"+CRLF+"SEQUENCE:0"+CRLF+"STATUS:CONFIRMED"+CRLF
    ical += "SUMMARY:Your Connect2Clinic appointment is confirmed " + CRLF+"TRANSP:OPAQUE"+CRLF+"END:VEVENT"+CRLF+"END:VCALENDAR"+CRLF

    if guest:
        ical = ical.format(name=name, appointment_id=appointment_id, site_url=websiteurl, guest=guest)
    else:
        ical = ical.format(name=name, appointment_id=appointment_id, site_url=websiteurl)

    eml_body = "Invitation Link for doctor appointment booking"
    msg = MIMEMultipart('mixed')
    msg['Reply-To'] = fro
    msg['Date'] = dtstamp
    msg['Subject'] = "Appointment Booking Invitation with {dr_name} from {appointment_start_date} to {appointment_end_date}".format(dr_name=dr_name, appointment_start_date=appointment_start_date, appointment_end_date=appointment_end_date)  # Subject formating
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

    response = ses_client.send_raw_email(
        Source=msg['From'],
        Destinations=attendees,  # patient email id
        RawMessage={
            'Data': msg.as_string()
        }
    )