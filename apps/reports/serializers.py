from utils.serializers import DynamicFieldsModelSerializer
from .models import Report, NumericReportDetails, StringReportDetails, TextReportDetails


class NumericReportDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = NumericReportDetails
        exclude = ('created_at', 'updated_at',)


class StringReportDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = StringReportDetails
        exclude = ('created_at', 'updated_at',)


class TextReportDetailsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TextReportDetails
        exclude = ('created_at', 'updated_at',)


class ReportSerializer(DynamicFieldsModelSerializer):
    string_Reports = StringReportDetailsSerializer(
        source='stringreportdetails_set', many=True, read_only=True)
    text_Reports = TextReportDetailsSerializer(
        source='textreportdetails_set', many=True, read_only=True)
    numeric_Reports = NumericReportDetailsSerializer(
        source='numericreportdetails_set', many=True, read_only=True)

    class Meta:
        model = Report
        exclude = ('created_at', 'updated_at',)
