import xml.etree.ElementTree as ET
from datetime import datetime
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (HRFlowable, Image, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from apps.doctors.models import Doctor
from apps.master_data.models import Department, Hospital
from apps.discharge_summaries.serializers import DischargeSummarysSerializer
from rest_framework.test import APIClient
client = APIClient()

def determine_heading(tag,root):
    heading = ""
    if tag == "CM1":
        heading = "PHYSICAL EXAMINATION"
    elif tag == "CM2":
        heading = "Other Laboratory Reports"
    elif tag == "CM3":
        heading = "RADIOLOGY INVESTIGATIONS"
    elif tag == "CM4":
        heading = "When to obtain Urgent Care"
    else:
        heading = root.find('OBX.3').find('OBX.3.2').text
    return heading
    

def get_discharge_summary(discharge_info, discharge_details):
    name = discharge_info["PatientName"]
    uhid = discharge_info["UHID"]
    visit_id = discharge_info["VisitID"]
    pdf_name = visit_id + '.pdf'
    root = ET.fromstring(discharge_info['rawMessage'])
    doctor_code = root.find('PV1').find('PV1.7').find('PV1.7.1').text.upper()
    doctor = Doctor.objects.filter(code=doctor_code).first()
    doctor_name = root.find('PV1').find('PV1.7').find('PV1.7.2').text.upper()
    department_code = root.find('PV1').find('PV1.10').find('PV1.10.1').text
    department = Department.objects.filter(code=department_code).first()
    admission_date_message = root.find(
        'PV1').find('PV1.44').find('PV1.44.1').text
    admission_date = None
    if admission_date_message:
        admission_date = datetime.strptime(
            admission_date_message, '%Y%m%d%H%M%S')
    root.find('PID').find('PID.7')[0].text
    sex = root.find('PID').find('PID.8')[0].text

    title = "DEPARMENT OF "
    if department:
        title = title + department.name.upper()
    my_doc = SimpleDocTemplate(
        pdf_name,
        pagesize=letter,
        showBoundary=1,
        bottomMargin=.4 * inch,
        topMargin=.4 * inch,
        rightMargin=.3 * inch,
        leftMargin=.1 * inch,
        allowSplitting=1,
        title=title)

    styles = getSampleStyleSheet()
    x = ParagraphStyle(
        'small',
        fontSize=10, fontName='Helvetica-Bold'
    )
    y = ParagraphStyle(
        'small',
        fontSize=10, fontName='Helvetica-Bold', alignment=TA_CENTER
    )
    styles["Normal"]
    flowables = []
    paragraph_0 = Paragraph(title, y)
    flowables.append(paragraph_0)
    flowables.append(Spacer(1, 0.1*inch))
    paragraph_00 = Paragraph(
        "DISCHARGE SUMMARY",
        y
    )
    flowables.append(paragraph_00)
    flowables.append(Spacer(1, 0.1*inch))
    data = [
        ['Name : ' + name, 'Hospital NO : ' + uhid],
        ['Age/Sex : ' + sex, 'IP NO : ' + visit_id],
        [
            'Admission Date : ' + admission_date.strftime("%m/%d/%Y") if admission_date else "",
            'Medical Discharge Date : ' + admission_date.strftime("%m/%d/%Y") if admission_date else ""
        ],
        ['Consultant : ' + doctor_name, 'Department : ' + department_code],
        ['PayorName : ' + name, 'Ward/Bed : ']
    ]
    colwidths = [4*inch]

    t = Table(data, colwidths, style=[
              ('BOX', (0, 0), (-1, -1), 1.25, colors.black), ], hAlign='LEFT')
    flowables.append(t)
    flowables.append(Spacer(1, 0.2*inch))

    count = 0
    paragraph = []
    for discharge_detail in discharge_details:
        root = ET.fromstring(discharge_detail['msgObx'])
        tag = root.find('OBX.3').find('OBX.3.1').text

        heading = determine_heading(tag,root)

        paragraph.append(Paragraph(heading, x))
        flowables.append(paragraph[count])
        content = ""
        content_root = root.findall('OBX.5')
        content_line = []
        content_count = 0
        for each_branch in content_root:
            content = ""
            for branch in each_branch:
                content = branch.text
                content_line.append(Paragraph(content, styles['BodyText']))
                flowables.append(content_line[content_count])
                content_count += 1
        flowables.append(Spacer(1, 0.2*inch))
        count = count + 1

    flowables.append(Spacer(1, 0.2*inch))
    z = ParagraphStyle(
        'small',
        fontSize=9, fontName='Helvetica-Bold'
    )
    paragraph_19 = Paragraph(doctor_name, z)
    degree = "MBBS"
    if doctor and doctor.qualification:
        degree = doctor.qualification
    paragraph_20 = Paragraph(
        degree,
        styles['BodyText']
    )
    paragraph_21 = Paragraph(
        title,
        styles['BodyText']
    )

    flowables.append(paragraph_19)
    flowables.append(paragraph_20)
    flowables.append(paragraph_21)
    flowables.append(Spacer(1, 0.2*inch))
    paragraph_22 = Paragraph(
        "Seek medical help if :",
        z
    )
    paragraph_23 = Paragraph("<b>The intial symptoms</b>", bulletText='.')
    paragraph_24 = Paragraph(
        "<b>Any new symptoms (like breathlessness , bleeding etc) is causing concern </b> ", bulletText='.')

    flowables.append(paragraph_22)
    flowables.append(paragraph_23)
    flowables.append(paragraph_24)
    flowables.append(Spacer(1, 0.1*inch))
    flowables.append(
        HRFlowable(width='100%', thickness=0.5, color=colors.black))
    paragraph_25 = Paragraph(
        "For booking an appointment, call on 1800 102 5555. For any other enquiries, call on 080 2502 3344", x)
    paragraph_26 = Paragraph(
        "For any Medical Emergency in Bangalore Dial 080 2222 1111. MARS 24 X 7 Manipal Ambulance Response Service", x)
    flowables.append(paragraph_25)
    flowables.append(paragraph_26)
    flowables.append(Spacer(1, 0.1*inch))

    flowables.append(
        HRFlowable(width='100%', thickness=0.5, color=colors.black))

    paragraph_27 = Paragraph("We offer HomeCare services to provide care at your home. \
        For further details please contact the HomeCare Hotline No: +91 95911 40000", x)

    flowables.append(paragraph_27)
    my_doc.build(flowables)
    data = dict()
    data["uhid"] = uhid
    data["name"] = name
    data["doctor_name"] = doctor_name
    data["file_name"] = pdf_name
    data["visit_id"] = visit_id
    data["doctor_code"] = doctor_code
    data["time"] = admission_date_message
    f = open(pdf_name,'rb')
    data["discharge_document"] = f
    client.post('/api/discharge_summaries/all_disharge_summary',
                                    data, format='multipart')

    return pdf_name
