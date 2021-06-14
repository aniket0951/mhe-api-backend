import logging
from apps.additional_features.models import Drive
from rest_framework.serializers import ValidationError
import random
import re

logger = logging.getLogger("AdditionalFeatures")

class AdditionalFeatures:

    @staticmethod
    def generate_unique_drive_code(description):
        if not description or len(description)<3:
            raise ValidationError("Drive name is too short!")
        while(True):
            try:
                code = AdditionalFeatures.generate_code(description)
                Drive.objects.get(code=code)
            except Exception as e:
                logger.debug("Exception generate_unique_drive_code: %s"%(str(e)))
                return code

    @staticmethod
    def generate_code(description):
        description = AdditionalFeatures.remove_whitespaces(description)
        description = description.upper()
        start_index = random.randint(0,len(description)-2)
        return "%s%s"%(str(description[start_index:start_index+2]),str(random.randint(1000,9999)))

    @staticmethod
    def remove_whitespaces(string):
        pattern = re.compile(r'\s+')
        return re.sub(pattern, '', string)