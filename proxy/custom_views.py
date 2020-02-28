import json

import requests
import six
from django.http import HttpResponse
from requests.exceptions import ConnectionError, SSLError, Timeout
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.response import Response
from rest_framework.utils.mediatypes import media_type_matches
from rest_framework.views import APIView
from six import BytesIO as StringIO

from manipal_api.settings import REST_PROXY as manipal_api_proxy_settings
from proxy.custom_serializables import \
    SyncAPIRequest as serializable_SyncAPIRequest
from proxy.custom_serializers import ObjectSerializer as custom_serializer


class BaseProxyView(APIView):
    proxy_settings = manipal_api_proxy_settings
    proxy_host = None
    source = None
    return_raw = False
    verify_ssl = None
    success_msg = None


class ProxyView(BaseProxyView):
    """
    Proxy view
    """

    def get_proxy_host(self):
        return self.proxy_host or self.proxy_settings['HOST']

    def get_source_path(self):
        if self.source:
            return self.source % self.kwargs
        return None

    def get_request_url(self, request):
        host = self.get_proxy_host()
        path = self.get_source_path()
        if path:
            return '/'.join([host, path])
        return host

    def get_request_params(self, request):
        if request.query_params:
            qp = request.query_params.copy()
            for param in self.proxy_settings.DISALLOWED_PARAMS:
                if param in qp:
                    del qp[param]
            return six.iterlists(qp)
        return {}

    def get_sync_request_data(self, request):
        request.data['sync_method'] = self.sync_method
        serializable_data = serializable_SyncAPIRequest(**request.data)
        request_data = custom_serializer().serialize(serializable_data, 'XML')
        return request_data

    def get_request_data(self, request):
        if 'application/json' in request.content_type:
            return json.dumps(request.data)
        return request.data

    def get_request_files(self, request):
        files = {}
        if request.FILES:
            for field, content in request.FILES.items():
                files[field] = content
        return files

    def get_default_headers(self, request):
        return {
            'Accept': request.META.get('HTTP_ACCEPT', self.proxy_settings['DEFAULT_HTTP_ACCEPT']),
            'Accept-Language': request.META.get('HTTP_ACCEPT_LANGUAGE', self.proxy_settings['DEFAULT_HTTP_ACCEPT_LANGUAGE']),
            'Content-Type': self.proxy_settings['DEFAULT_CONTENT_TYPE'],
        }

    def get_headers(self, request):
        headers = self.get_default_headers(request)
        """
        # Translate Accept HTTP field
        accept_maps = self.proxy_settings.ACCEPT_MAPS
        for old, new in accept_maps.items():
            headers['Accept'] = headers['Accept'].replace(old, new)

        username = self.proxy_settings.AUTH.get('user')
        password = self.proxy_settings.AUTH.get('password')
        if username and password:
            auth_token = '%s:%s' % (username, password)
            auth_token = base64.b64encode(auth_token.encode('utf-8')).decode()
            headers['Authorization'] = 'Basic %s' % auth_token
        else:
            auth_token = self.proxy_settings.AUTH.get('token')
            if auth_token:
                headers['Authorization'] = auth_token
        """
        return headers

    def get_verify_ssl(self, request):
        return self.verify_ssl or self.proxy_settings['VERIFY_SSL']

    def get_cookies(self, requests):
        return None

    def parse_proxy_response(self, response):
        """
        Modified version of rest_framework.request.Request._parse(self)
        """
        parsers = self.get_parsers()
        stream = StringIO(response._content)
        content_type = response.headers.get('content-type', None)

        if stream is None or content_type is None:
            return {}

        parser = None
        for item in parsers:
            if media_type_matches(item.media_type, content_type):
                parser = item
        if not parser:
            raise UnsupportedMediaType(content_type)

        parsed = parser.parse(stream, content_type)

        # Parser classes may return the raw data, or a
        # DataAndFiles object. Return only data.
        try:
            return parsed.data
        except AttributeError:
            return parsed
        
    def custom_success_response(self, success=False, message=None, data=None, error= None):
        custom_response = dict()
        custom_response['success'] = success
        custom_response['message'] = message
        custom_response['data'] = data
        custom_response['error'] = error
        return custom_response

    def create_response(self, response):
        if self.return_raw or self.proxy_settings['RETURN_RAW']:
            return HttpResponse(response.text, status=response.status_code,
                                content_type=response.headers.get('content-type'))

        status = response.status_code
        if status >= 400:
            body = {
                'code': status,
                'success' : False,
                'error': response.reason,
            }
        else:
            body = self.parse_proxy_response(response)
        return Response(body, status)

    def create_error_response(self, body, status):
        return Response(body, status)

    def proxy(self, request, *args, **kwargs):
        url = self.get_request_url(request)
        params = self.get_request_params(request)
        data = self.get_request_data(request)
        files = self.get_request_files(request)
        headers = self.get_headers(request)
        verify_ssl = self.get_verify_ssl(request)
        cookies = self.get_cookies(request)

        try:
            response = requests.request(request.method, url,
                                        # params=params,
                                        data=data,
                                        # files=files,
                                        headers=headers,
                                        timeout=self.proxy_settings['TIMEOUT'],
                                        verify=verify_ssl,
                                        # cookies=cookies
                                        )
        except (ConnectionError, SSLError) as e:
            status = requests.status_codes.codes.bad_gateway
            return self.create_error_response({
                'success' : False,
                'code': status,
                'message': 'We are unable to reach our servers, please try after sometime.'
            }, status)

        except (Timeout):
            status = requests.status_codes.codes.gateway_timeout
            return self.create_error_response({
                'success' : False,
                'code': status,
                'message': 'Gateway timed out, please contact our helpdesk.',
            }, status)

        return self.create_response(response)

    def get(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)
