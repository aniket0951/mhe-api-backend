import json
import logging
from django.conf import settings
from utils.cipher import AESCipher
from django.http.request import HttpHeaders

JWT_AUTHORIZATION_KEY  = settings.JWT_AUTHORIZATION_KEY
ENCRYPTION_FLAG = settings.ENCRYPTION_FLAG
ENCRYPTION_KEYWORD = settings.ENCRYPTION_KEYWORD
ENCRYPTION_KEYWORD_LENGTH = int(settings.ENCRYPTION_KEYWORD_LENGTH)
ENCRYPTION_BODY_KEY = settings.ENCRYPTION_BODY_KEY

request_logger = logging.getLogger('django.request')

class MiddlewareUtils:

    @staticmethod
    def authenticate_encryption(request):
        jwt_token = request.META.get(JWT_AUTHORIZATION_KEY)
        if not jwt_token or len(jwt_token)<ENCRYPTION_KEYWORD_LENGTH:
            return False
        try:
            if ENCRYPTION_KEYWORD==AESCipher.decrypt(jwt_token[-ENCRYPTION_KEYWORD_LENGTH:]).decode("utf-8"):
                request.META["HTTP_AUTHORIZATION"] = ""
                if len(jwt_token)>ENCRYPTION_KEYWORD_LENGTH+4:
                    request.META["HTTP_AUTHORIZATION"] = jwt_token[:-ENCRYPTION_KEYWORD_LENGTH]
                request.META[ENCRYPTION_FLAG] = True
                return True
        except Exception as e:
            request_logger.error("Could not decrypt encryption flag: %s"%(str(e)))
        return False

        
        