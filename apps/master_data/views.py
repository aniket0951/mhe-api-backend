from django.shortcuts import render
from rest_framework.decorators import action

from proxy.custom_endpoints import SYNC_SERVICE, VALIDATE_OTP, VALIDATE_UHID
from proxy.custom_views import ProxyView
from proxy.custom_serializables import UHID as serializable_UHID
from proxy.custom_serializers import ObjectSerializer as custom_serializer

class SpecialisationsView(ProxyView):
    # permission_classes = [IsAuthenticated]
    source = SYNC_SERVICE
    success_msg = 'Specialisations list returned successfully'

    def get_request_data(self, request):
        if 'application/json' in request.content_type:
            return json.dumps(request.data)
        return request.data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        import pdb; pdb.set_trace()
        return None

class ValidateUHIDView(ProxyView):
    # permission_classes = [IsAuthenticated]
    source = VALIDATE_UHID
    success_msg = 'OTP to your number returned successfully'

    def get_request_data(self, request):
        uhid = serializable_UHID(**request.data)
        request_data = custom_serializer().serialize(uhid, 'XML')
        return request_data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        return None


class ValidateOTPView(ProxyView):
    # permission_classes = [IsAuthenticated]
    source = VALIDATE_OTP
    success_msg = 'OTP  successfully'

    def get_request_data(self, request):
        import pdb; pdb.set_trace()
        return request.data

    def post(self, request, *args, **kwargs):
        return self.proxy(request, *args, **kwargs)

    def parse_proxy_response(self, response):
        import pdb; pdb.set_trace()
        return None