import base64
import xml.etree.ElementTree as ET
from datetime import datetime

from rest_framework.test import APIRequestFactory

from apps.doctors.models import Doctor
from apps.master_data.models import Hospital

from .exceptions import ReportExistsException
from .models import Report


def report_handler(report_info, factory=APIRequestFactory()):

    required_keys = ['UHID', 'ReportCode', 'ReportName', 'ReportDateTime']

    if report_info and type(report_info) == dict and \
            set(required_keys).issubset(set(report_info.keys())):

        if Report.objects.filter(message_id=report_info['MsgID']).exists():
            raise ReportExistsException

        report_request_data = {}
        report_request_data['uhid'] = report_info['UHID']
        report_request_data['code'] = report_info['ReportCode']
        report_request_data['patient_class'] = report_info['PatientClass']
        report_request_data['visit_id'] = report_info['VisitID']
        report_request_data['message_id'] = report_info['MsgID']
        report_request_data['name'] = report_info['ReportName']
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
