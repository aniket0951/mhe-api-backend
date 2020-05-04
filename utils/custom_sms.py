from django.conf import settings


def send_sms(mobile_number=None, message=None):
    response = settings.AWS_SNS_CLIENT.publish(PhoneNumber=mobile_number,
                                               Message=message,
                                               MessageAttributes={
                                                   'AWS.SNS.SMS.SenderID': {
                                                       'DataType': 'String',
                                                       'StringValue': settings.SMS_SENDER
                                                   }
                                               }
                                               )
    return response['ResponseMetadata']['HTTPStatusCode'] == 200
