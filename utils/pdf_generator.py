from reportlab.platypus import SimpleDocTemplate,Image,HRFlowable
from reportlab.platypus import Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER



def get_discharge_summary(discharge_info, discharge_details):
    pdf_name = 'myfile.pdf'
    import pdb; pdb.set_trace()
    title="DEPARMENT OF ORTHOPAEDICS"
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
        fontSize=10,fontName='Helvetica-Bold'
    )
    y = ParagraphStyle(
        'small',
        fontSize=10,fontName='Helvetica-Bold',alignment=TA_CENTER
    )
    style = styles["Normal"]
    flowables=[]
    paragraph_0 = Paragraph("DEPARTMENT OF ORTHOPAEDICS", y)
    flowables.append(paragraph_0)
    flowables.append(Spacer(1,0.1*inch))
    paragraph_00 = Paragraph(
        "DISCHARGE SUMMARY",
        y
    )
    flowables.append(paragraph_00)
    flowables.append(Spacer(1,0.1*inch))
    data= [['Name : Naman', 'HospitalNo : 122'],
    ['Age : 23', 'IP no :12232'],
    ['Date : 11/03/2020', 'Date :11/03/2020'],
    ['consultant :hg', 'Department : forensic'],['Pay : 1223', 'Bed : 3']]
    colwidths = [4*inch]

    t=Table(data,colwidths,style=[('BOX', (0,0), (-1,-1), 1.25, colors.black),],hAlign='LEFT')
    flowables.append(t)
    flowables.append(Spacer(1,0.2*inch))

    # for i in range(10):
    #  bogustext = ("This is Paragraph number %s. " % i) *1
    #  p = Paragraph(bogustext, style)
    #  flowables.append(p)
    #  flowables.append(Spacer(1,0.2*inch))
    paragraph_1 = Paragraph("DIAGNOSIS", x)
    paragraph_2 = Paragraph(
        "Left Wrist First JOINT",
        styles['BodyText']
    )
    flowables.append(paragraph_1)
    flowables.append(paragraph_2)
    flowables.append(Spacer(1,0.2*inch))

    paragraph_3 = Paragraph("CHIEF COMPLAINTS", x)
    paragraph_4 = Paragraph(
        "Pain in Left Thumb",
        styles['BodyText']
    )
    flowables.append(paragraph_3)
    flowables.append(paragraph_4)
    flowables.append(Spacer(1,0.2*inch))


    paragraph_5 = Paragraph("HISTORY OF CURRENT ILLNESS", x)
    paragraph_6 = Paragraph(
        "sdjhasjbhadshbsjhvsdhvdshjvhasvhvsahvajhvjasvjavsjhvsj",
        styles['BodyText']
    )

    flowables.append(paragraph_5)
    flowables.append(paragraph_6)
    flowables.append(Spacer(1,0.2*inch))

    paragraph_7 = Paragraph("PAST HISTORY", x)
    paragraph_8 = Paragraph(
        "sdjhasjbhadshbsjhvsdhvdshjvhasvhvsahvajhvjasvjavsjhvsj",
        styles['BodyText']
    )

    flowables.append(paragraph_7)
    flowables.append(paragraph_8)
    flowables.append(Spacer(1,0.2*inch))

    paragraph_9 = Paragraph("PHYSICAL EXAMINATION", x)
    paragraph_10 = Paragraph(
        "sdjhasjbhadshbsjhvsdhvdshjvhasvhvsahvajhvjasvjavsjhvsjhhhhh",
        styles['BodyText']
    )

    flowables.append(paragraph_9)
    flowables.append(paragraph_10)
    flowables.append(Spacer(1,0.2*inch))





    paragraph_11 = Paragraph("SURGICAL PROCEDURE", x)
    paragraph_12 = Paragraph(
        "sdjhasjbhadshbsjhvsdhvdshjvhasvhvsahvajhvjasvjavsjhvsj",
        styles['BodyText']
    )

    flowables.append(paragraph_11)
    flowables.append(paragraph_12)
    flowables.append(Spacer(1,0.2*inch))


    paragraph_13 = Paragraph("COURSE OF TREATMENT IN HOSPITAL", x)
    paragraph_14 = Paragraph(
        "sdjhasjbhadshbsjhvsdhvdshjvhasvhvsahvajhvjasvjavsjhvsj",
        styles['BodyText']
    )

    flowables.append(paragraph_13)
    flowables.append(paragraph_14)
    flowables.append(Spacer(1,0.2*inch))

    paragraph_15 = Paragraph("CONDITION IN DISCHARGE", x)
    paragraph_16 = Paragraph(
        "sdjhasjbhadshbsjhvsdhvdshjvhasvhvsahvajhvjasvjavsjhvsj",
        styles['BodyText']
    )

    paragraph_17 = Paragraph("FURTHER ADVICE ON DISCHARGE", x)
    paragraph_18 = Paragraph(
        "sdjhasjbhadshbsjhvsdhvdshjvhasvhvsahvajhvjasvjavsjhvsj",
        styles['BodyText']
    )

    flowables.append(paragraph_17)
    flowables.append(paragraph_18)
    flowables.append(Spacer(1,0.2*inch))

    # f = './python_image.png'
    # i=Image(f,height=0.1*inch,width=0.2*inch)
    # i.hAlign='LEFT'
    # flowables.append(i)
    flowables.append(Spacer(1,0.2*inch))
    z = ParagraphStyle(
        'small',
        fontSize=9,fontName='Helvetica-Bold'
    )
    paragraph_19 = Paragraph("DR.SALUNKE", z)
    paragraph_20 = Paragraph(
        "MBBS",
        styles['BodyText']
    )
    paragraph_21 = Paragraph(
        "Department of Orthopaedics",
        styles['BodyText']
    )

    flowables.append(paragraph_19)
    flowables.append(paragraph_20)
    flowables.append(paragraph_21)
    flowables.append(Spacer(1,0.2*inch))
    paragraph_22 = Paragraph(
        "Seek medical help if :",
        z
    )
    paragraph_23 = Paragraph("<b>The intial symptoms</b>",bulletText='.')
    paragraph_24 = Paragraph("<b>dfhgdfhjgdhghdf</b> ",bulletText='.')

    flowables.append(paragraph_22)
    flowables.append(paragraph_23)
    flowables.append(paragraph_24)
    flowables.append(Spacer(1,0.1*inch))
    flowables.append(
            HRFlowable(width='100%', thickness=0.5, color=colors.black))
    paragraph_25 = Paragraph("shkkjshjshshdjshkshkshkjshkjshkjshdkjdkjh ",x)
    paragraph_26 = Paragraph("shkkjshjshshdjshkshkshkjshkjshkjshdkjdkjh ",x)
    flowables.append(paragraph_25)
    flowables.append(paragraph_26)
    flowables.append(Spacer(1,0.1*inch))

    flowables.append(
            HRFlowable(width='100%', thickness=0.5, color=colors.black))

    paragraph_27 = Paragraph("shkkjshjshshdjshkshkshkjshkjshkjshdkjdkjh ",x)
    paragraph_28 = Paragraph("shkkjshjshshdjshkshkshkjshkjshkjshdkjdkjh ",x)
    flowables.append(paragraph_27)
    flowables.append(paragraph_28)
    my_doc.build(flowables)
    import pdb; pdb.set_trace()
    return 