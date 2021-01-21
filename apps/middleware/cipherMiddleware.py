import uuid
import ast
import json
import logging
import socket
import time

from django.utils.deprecation import MiddlewareMixin
from django.db.models.query import QuerySet
from uuid import UUID

from utils.cipher import AESCipher

# from .utils import CustomDatetimeUUIDEncoder

request_logger = logging.getLogger('django.request')
response_logger = logging.getLogger('django.response')


class CipherRequestMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization on start-up

    def __call__(self, request):
        # Logic executed on a request before the view (and other middleware) is called.
        # get_response call triggers next phase
        response = self.get_response(request)
        # Logic executed on response after the view is called.
        # Return response to finish middleware sequence
        return response

    def dict_replace_value(self,d):
        x = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = self.dict_replace_value(v)
            elif isinstance(v, list):
                v = self.list_replace_value(v)
            elif isinstance(v, UUID):
                v = v.hex
            elif isinstance(v, QuerySet):
                v = list(v.values())
                v = self.list_replace_value(v)
            x[k] = v
        return x

    def list_replace_value(self,l):
        x = []
        for e in l:
            if isinstance(e, list):
                e = self.list_replace_value(e)
            elif isinstance(e, dict):
                e = self.dict_replace_value(e)
            elif isinstance(e, UUID):
                e = e.hex
            elif isinstance(e, QuerySet):
                e = list(e.values())
                e = self.list_replace_value(e)
            x.append(e)
        return x

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Logic executed before a call to view
        # Gives access to the view itself & arguments

        request_logger.info("\n\nREQUEST request.headers: %s"%(request.headers))
        if request.headers.get('is_encryption_enabled') and request.headers.get('is_encryption_enabled')=="True":
            request_data = getattr(request, '_body', request.body)
            if isinstance(request_data, dict):
                request_data = self.dict_replace_value(request_data)
            elif isinstance(request_data, list):
                request_data = self.list_replace_value(request_data)
            # request_logger.info("\n\nREQUEST BODY ENCRYPTED: %s"%(request_data))
            if request_data:
                encrypted_request_body = json.loads(request_data)
                if encrypted_request_body.get("encrypted_data"):
                    request._body = AESCipher.decrypt(encrypted_request_body.get("encrypted_data"))
                    
        # log_data = {
        #     'remote_address': request.META['REMOTE_ADDR'],
        #     'server_hostname': socket.gethostname(),
        #     'request_method': request.method,
        #     'request_path': request.get_full_path(),
        # }

        # if hasattr(request, 'headers') and request.headers:
        #     log_data['request_headers'] = request.headers
        # if request.content_type == 'application/json' and hasattr(request, 'body') and request.body:
        #     log_data['request_body'] = str(request.body)

        # request_logger.info("\n\nREQUEST BODY PLAIN: %s"%(log_data))

        return None

    def process_exception(self, request, exception):
        # Logic executed if an exception/error occurs in the view
        pass


class CipherResponseMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization on start-up

    def __call__(self, request):
        # Logic executed on a request before the view (and other middleware) is called.
        # get_response call triggers next phase
        response = self.get_response(request)
        # Logic executed on response after the view is called.
        # Return response to finish middleware sequence
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Logic executed before a call to view
        # Gives access to the view itself & arguments
        pass

    def process_exception(self, request, exception):
        # Logic executed if an exception/error occurs in the view
        pass

    def process_template_response(self, request, response):
        # Logic executed after the view is called,
        # ONLY IF view response is TemplateResponse, see listing 2-24

        # log_data = {
        #     'remote_address': request.META['REMOTE_ADDR'],
        #     'server_hostname': socket.gethostname(),
        #     'request_method': request.method,
        #     'request_path': request.get_full_path(),
        # }
        # if request.content_type == 'application/json' and hasattr(request, 'body') and request.body:
        #     log_data['request_body'] = str(request.body)
        # if hasattr(request, 'headers') and request.headers:
        #     log_data['request_headers'] = request.headers
        # if hasattr(response, 'data') and response.data and type(response.data) == dict:
        #     log_data['response_data'] = response.data

        # request_logger.info("\n\nRESPONSE BODY PLAIN: %s"%(log_data))

        if request.headers.get('is_encryption_enabled') and request.headers.get('is_encryption_enabled')=="True":

            str_conv_response_data = json.dumps(response.data.copy(), ensure_ascii=False, cls=None)
            response.data = { 'encrypted_data': AESCipher.encrypt(str_conv_response_data) }
        
        # request_logger.info("\n\nRESPONSE BODY ENCODED: %s"%(response.data))
        return response
