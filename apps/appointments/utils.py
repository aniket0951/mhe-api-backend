from rest_framework.test import APIRequestFactory

def cancel_and_refund_parameters(param, factory=APIRequestFactory()):
    return factory.post(
        '', param, format='json')