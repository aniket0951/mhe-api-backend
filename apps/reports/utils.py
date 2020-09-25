import base64
import xml.etree.ElementTree as ET
from datetime import datetime

from apps.doctors.models import Doctor
from apps.master_data.models import Hospital
from rest_framework.test import APIRequestFactory

from .exceptions import ReportExistsException
from .models import Report, VisitReport
from .serializers import VisitReportsSerializer


def report_handler(report_info, factory=APIRequestFactory()):

    required_keys = ['UHID', 'ReportCode', 'ReportName', 'ReportDateTime']

    if report_info and type(report_info) == dict and \
            set(required_keys).issubset(set(report_info.keys())):
        report_visit = VisitReport.objects.filter(
            visit_id=report_info['VisitID']).first()
        if Report.objects.filter(visit_id=report_info['VisitID'], place_order=report_info['place_order']).exists():
            report_instances = Report.objects.filter(
                visit_id=report_info['VisitID'], place_order=report_info['place_order'], code=report_info['ReportCode'])
            for report_instance in report_instances:
                report_instance.text_report.all().delete()
                report_instance.numeric_report.all().delete()
                report_instance.string_report.all().delete()
                report_instance.free_text_report.all().delete()
                if report_visit:
                    report_visit.report_info.remove(report_instance)
                report_instance.delete()

        report_request_data = {}
        report_request_data['uhid'] = report_info['UHID']
        report_request_data['place_order'] = report_info['place_order']
        report_request_data['code'] = report_info['ReportCode']
        report_request_data['patient_class'] = report_info['PatientClass']
        report_request_data['visit_id'] = report_info['VisitID']
        report_request_data['message_id'] = report_info['MsgID']
        report_request_data['name'] = report_info['ReportName']
        if report_info['ReportCode'] and report_info['ReportCode'].startswith("DRAD"):
            report_request_data['report_type'] = "Radiology"
        report_request_data['visit_date_time'] = datetime.strptime(
            report_info["VisitDateTime"], '%Y%m%d%H%M%S')
        report_request_data['time'] = datetime.strptime(
            report_info['ReportDateTime'], '%Y%m%d%H%M%S')
        hospital_info = Hospital.objects.filter(
            code=report_info['LocationCode']).first()
        if hospital_info:
            report_request_data['hospital'] = hospital_info.id
            doctor_info = Doctor.objects.filter(code=report_info['DoctorCode'].split(',')[
                                                0], hospital=hospital_info).first()
            if doctor_info:
                report_request_data['doctor'] = doctor_info.id
            else:
                report_request_data['doctor_name'] = report_info['DoctorName']

        if not report_visit:
            data = dict()
            data["visit_id"] = report_info['VisitID']
            data["uhid"] = report_info['UHID']
            data["patient_class"] = report_info['PatientClass']
            data['created_at'] = datetime.strptime(
                report_info["VisitDateTime"], '%Y%m%d%H%M%S')
            serializer = VisitReportsSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            visit_obj = serializer.save()
            visit_obj.created_at = data['created_at']
            visit_obj.save()
        return factory.post(
            '', report_request_data, format='json')


def string_report_hanlder(report_detail, report_id, factory=APIRequestFactory()):

    string_report_request_data = {}
    string_report_required_keys = [
        'ObxIdentifierID', 'ObxIdentifierText', 'ObxValue']

    if report_detail and type(report_detail) == dict and \
            set(string_report_required_keys).issubset(set(report_detail.keys())):
        string_report_request_data = {}
        string_report_request_data['code'] = report_detail['ObxIdentifierID']
        string_report_request_data['name'] = report_detail['ObxIdentifierText']
        string_report_request_data['observation_value'] = report_detail['ObxValue']
        string_report_request_data['report'] = report_id
        return factory.post(
            '', string_report_request_data, format='json')


def free_text_report_hanlder(report_detail, report_id, factory=APIRequestFactory()):

    string_report_request_data = {}
    string_report_required_keys = [
        'ObxIdentifierID', 'ObxIdentifierText', 'ObxValue']

    if report_detail and type(report_detail) == dict and \
            set(string_report_required_keys).issubset(set(report_detail.keys())):
        string_report_request_data = {}
        string_report_request_data['code'] = report_detail['ObxIdentifierID']
        string_report_request_data['name'] = report_detail['ObxIdentifierText']
        string_report_request_data['observation_value'] = report_detail['ObxValue']
        string_report_request_data['report'] = report_id
        return factory.post(
            '', string_report_request_data, format='json')


def text_report_hanlder(report_detail, report_id, factory=APIRequestFactory()):
    text_report_request_data = {}
    text_report_required_keys = [
        'ObxIdentifierID', 'ObxIdentifierText', 'msgObx', ]

    if report_detail and type(report_detail) == dict and \
            set(text_report_required_keys).issubset(set(report_detail.keys())):
        text_report_request_data = {}
        text_report_request_data['code'] = report_detail['ObxIdentifierText']
        text_report_request_data['name'] = report_detail['ObxIdentifierID']
        text_report_request_data['report'] = report_id

        root = ET.fromstring(report_detail['msgObx'])
        observation_results_info = root.find(
            'OBX.5').find('OBX.5.1')
        observation_results = ''

        for each_child_node in observation_results_info:
            observation_results += each_child_node.text.strip()

        if not observation_results:
            observation_results += observation_results_info.text

        text_report_request_data['observation_value'] = observation_results

        return factory.post(
            '', text_report_request_data, format='json')


def numeric_report_hanlder(report_detail, report_id, factory=APIRequestFactory()):

    numeric_report_request_data = {}
    numeric_report_required_keys = [
        'ObxIdentifierID', 'ObxIdentifierText', 'ObxValue', 'ObxRange', 'ObxUnit']

    if report_detail and type(report_detail) == dict and \
            set(numeric_report_required_keys).issubset(set(report_detail.keys())):
        numeric_report_request_data = {}
        numeric_report_request_data['identifier'] = report_detail['ObxIdentifierID']
        numeric_report_request_data['name'] = report_detail['ObxIdentifierText']
        numeric_report_request_data['observation_value'] = report_detail['ObxValue']
        numeric_report_request_data['observation_range'] = report_detail['ObxRange']
        if report_detail['ObxUnit']:
            numeric_report_request_data['observation_unit'] = base64.b64decode(
                report_detail['ObxUnit']).decode('utf-8')
        numeric_report_request_data['report'] = report_id
        return factory.post(
            '', numeric_report_request_data, format='json')
