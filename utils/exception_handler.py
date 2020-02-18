from rest_framework.views import exception_handler
from rest_framework.serializers import ValidationError
from rest_framework.exceptions import APIException
from rest_framework import status
from django.contrib.humanize.templatetags.humanize import ordinal


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        customized_response = {'errors': []}

        if isinstance(exc, ValidationError):

            def generate_error_responses(data, key=''):
                if isinstance(data, str):
                    error = {'field': key, 'message': data}
                    customized_response['errors'].append(error)
                elif isinstance(data, dict):
                    for error_key, error_value in data.items():
                        latest_key = ''
                        if key != '':
                            if isinstance(error_key, int):
                                latest_key = "{} >> {}".format(key, ordinal(int(error_key)))
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
                                latest_key = "{} >> 🠖{}".format(key, ordinal(sequence_no))
                            else:
                                latest_key = ordinal(sequence_no)
                            generate_error_responses(current_data, key=latest_key)

            try:
                generate_error_responses(response.data)
            except (Exception, TypeError) as e:
                customized_response = response.data
        else:
            if hasattr(exc, 'detail') and isinstance(exc.detail, str):
                error = {'field': 'detail', 'message': str(exc.detail)}
                customized_response['errors'].append(error)
            else:
                customized_response['errors'].append(response.data)

        response.data = customized_response

    # If validation error, set status code to '422 Unprocessable Entity'
    # see: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/422
    if isinstance(exc, ValidationError):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    return response