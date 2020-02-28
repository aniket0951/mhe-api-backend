import urllib

from apps.manipal_admin.models import ManipalAdmin
from apps.patients.models import Patient
from manipal_api.settings import AWS_STORAGE_BUCKET_NAME, S3_CLIENT


def generate_pre_signed_url(image_url):
    try:
        decoded_url = urllib.request.unquote(image_url)
        url = S3_CLIENT.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': AWS_STORAGE_BUCKET_NAME,
                'Key': decoded_url.split(AWS_STORAGE_BUCKET_NAME+".s3.amazonaws.com/")[-1]
            }, ExpiresIn=600
        )
        return url
    except Exception:
        return None


def patient_user_object(request):
    try:
        return Patient.objects.get(id=request.user.id)
    except Exception as error:
        # logger.error("Unable to fetch patient user : " + str(error))
        return None


def manipal_admin_object(request):
    try:
        return ManipalAdmin.objects.get(id=request.user.id)
    except Exception as error:
        # logger.error("Unable to fetch patient user : " + str(error))
        return None
