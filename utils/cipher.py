from AesEverywhere import aes256
from django.conf import settings

import logging

_logger = logging.getLogger('django.AESCipher')

class AESCipher:

    @staticmethod
    def encrypt(raw):
        return aes256.encrypt(raw, settings.API_SECRET_KEY)

    @staticmethod
    def decrypt(enc):
        return aes256.decrypt(enc, settings.API_SECRET_KEY)