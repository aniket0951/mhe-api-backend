import json
import logging

from django.db.models.query import QuerySet
from django.conf import settings
from uuid import UUID
from .utils import MiddlewareUtils
from utils.cipher import AESCipher
from collections import OrderedDict


request_logger = logging.getLogger('django.request')
response_logger = logging.getLogger('django.response')

ENCRYPTION_FLAG = settings.ENCRYPTION_FLAG
ENCRYPTION_BODY_KEY = settings.ENCRYPTION_BODY_KEY

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


    def process_view(self, request, view_func, view_args, view_kwargs):
        # Logic executed before a call to view
        # Gives access to the view itself & arguments

        request_logger.info("\n\nREQUEST BODY: %s"%(getattr(request, '_body', request.body)))
        request_logger.info("\n\nREQUEST HEADERS: %s"%(request.headers))
        if MiddlewareUtils.authenticate_encryption(request):
            request_data = getattr(request, '_body', request.body)
            if request_data:
                try:
                    encrypted_request_body = json.loads(request_data)
                    if encrypted_request_body.get(ENCRYPTION_BODY_KEY):
                        request._body = AESCipher.decrypt(encrypted_request_body.get(ENCRYPTION_BODY_KEY))
                except Exception as e:
                    request_logger.error("\n\nREQUEST BODY Parsing Failed: %s"%(e))

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

    
    def dict_replace_value(self,d):
        x = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = self.dict_replace_value(v)
            elif isinstance(v, list):
                v = self.list_replace_value(v)
            elif isinstance(v, UUID):
                v = v.hex
            elif isinstance(v, OrderedDict):
                v = dict(v)
            elif isinstance(v, bytes):
                v = v.decode('utf-8')
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
            elif isinstance(e, OrderedDict):
                e = dict(e)
            elif isinstance(e, bytes):
                e = e.decode('utf-8')
            elif isinstance(e, QuerySet):
                e = list(e.values())
                e = self.list_replace_value(e)
            x.append(e)
        return x

    def process_template_response(self, request, response):
        # Logic executed after the view is called,
        # ONLY IF view response is TemplateResponse, see listing 2-24

        request_logger.info("\n\nRESPONSE BODY: %s"%(response.data.copy()))
        if request.META.get(ENCRYPTION_FLAG) and request.META.get(ENCRYPTION_FLAG)==True and response.data:
            try:
                response_data = response.data.copy()
                if isinstance(response_data, dict):
                    response_data = self.dict_replace_value(response_data)
                elif isinstance(response_data, list):
                    response_data = self.list_replace_value(response_data)    
                str_conv_response_data = json.dumps(response_data, ensure_ascii=False, cls=None)
                response.data = { ENCRYPTION_BODY_KEY: AESCipher.encrypt(str_conv_response_data) }
            except Exception as e:
                response_logger.error("\n\nRESPONSE BODY Parsing Failed: %s"%(e))
        
        return response
