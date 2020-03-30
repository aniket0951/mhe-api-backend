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
    # string_reports = StringReportDetailsSerializer(
    #     source='stringreportdetails_set', many=True, read_only=True)
    # text_reports = TextReportDetailsSerializer(
    #     source='textreportdetails_set', many=True, read_only=True)
    # numeric_reports = NumericReportDetailsSerializer(
    #     source='numeric_report', many=True, read_only=True)

    class Meta:
        model = Report
        exclude = ('created_at', 'updated_at',)

    def to_representation(self, instance):
        response_object = super().to_representation(instance)
        if not self.context['request'].query_params.get('numeric_report__identifier', None):
            response_object['string_reports'] = StringReportDetailsSerializer(
                instance.stringreportdetails_set.all(),
                many=True, read_only=True).data
            response_object['text_reports'] = TextReportDetailsSerializer(
                instance.textreportdetails_set.all(),
                many=True, read_only=True).data
        response_object['numeric_reports'] = NumericReportDetailsSerializer(
            instance.numeric_report.all(),
            many=True, read_only=True).data

        return response_object
