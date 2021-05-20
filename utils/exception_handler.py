import logging

from django.contrib.humanize.templatetags.humanize import ordinal
from ratelimit.exceptions import Ratelimited
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger('django')


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    customized_response = {'errors': []}
    if response is not None:
        
        if isinstance(exc, Ratelimited):
            error = {
                'field': 'Ratelimit',
                'error_code': 'Ratelimit',
                'message': "You cannot perform this action too much! Please wait for some time and try again!"
            }
            customized_response['errors'].append(error)
        elif isinstance(exc, ValidationError):
            def generate_error_responses(data, key=''):
                if isinstance(data, str):
                    error = {
                        'field': key, 
                        'message': data,
                        'error_code': str(key)
                    }
                    customized_response['errors'].append(error)
                elif isinstance(data, dict):
                    for error_key, error_value in data.items():
                        latest_key = ''
                        if key != '':
                            if isinstance(error_key, int):
                                latest_key = "{} >> {}".format(
                                    key, ordinal(int(error_key)))
                            else:
                                latest_key = "{} >> {}".format(key, error_key)
                        else:
                            latest_key = error_key
                        generate_error_responses(error_value, key=latest_key)
                elif isinstance(data, list):
                    if len(data) == 1:
                        generate_error_responses(data[0], key=key)
                    else:
                        for sequence_no, current_data in enumerate(data, start=1):
                            latest_key = ''
                            if key:
                                latest_key = "{} >> 🠖{}".format(
                                    key, ordinal(sequence_no))
                            else:
                                latest_key = ordinal(sequence_no)
                            generate_error_responses(current_data, key=latest_key)
            try:
                generate_error_responses(response.data)
            except (Exception, TypeError):
                customized_response = response.data
        else:
            if hasattr(exc, 'detail') and isinstance(exc.detail, str):
                error = {
                    'field': 'detail', 
                    'error_code':exc.default_code,
                    'message': str(exc.detail)
                }
                customized_response['errors'].append(error)
            else:
                customized_response['errors'].append(response.data)

        response.data = customized_response
    else:
        error = {
            'field': 'debug', 
            'error_code': 'debug',
            'message': "Internal server error, please try again after sometime",
            "exception": str(exc)
        }
        customized_response['errors'].append(error)
        logger.error("INTERNAL SERVER EXCEPTION : %s"%(str(exc)))
        response = Response(customized_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return response
