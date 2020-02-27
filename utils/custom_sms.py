from manipal_api.settings import AWS_SNS_CLIENT, SMS_SENDER


def send_sms(mobile_number=None, message=None):
    response = AWS_SNS_CLIENT.publish(PhoneNumber=mobile_number,
                                      Message=message,
                                      MessageAttributes={
                                          'AWS.SNS.SMS.SenderID': {
                                              'DataType': 'String',
                                              'StringValue': SMS_SENDER
                                          }
                                      }
                                      )
    return response['ResponseMetadata']['HTTPStatusCode'] == 200
