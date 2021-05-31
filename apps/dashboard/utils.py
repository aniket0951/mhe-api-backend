from apps.dashboard.constants import DashboardConstants
from apps.dashboard.serializers import FlyerImagesSerializer
from apps.dashboard.models import FlyerImages, FlyerScheduler
from django.conf import settings
from datetime import datetime
from rest_framework.serializers import ValidationError

class DashboardUtils:

    @staticmethod
    def compare_versions(older_version,newer_version):
        if not older_version or not newer_version:
            return 1
        version1 = [int(pt) for pt in str(older_version).split(".")]
        version2 = [int(pt) for pt in str(newer_version).split(".")]

        for i in range(max(len(version1), len(version2))):
            v1 = version1[i] if i < len(version1) else 0
            v2 = version2[i] if i < len(version2) else 0
            if v1 == v2:    continue
            return 1 if v1 > v2 else -1
        return 0

    @staticmethod
    def validate_app_version(version_number,dashboard_details):
        if version_number:
            dashboard_details["force_update_enable"] = settings.FORCE_UPDATE_ENABLE
            dashboard_details["force_update_required"] = DashboardUtils.check_if_version_update_required(version_number)
        return dashboard_details


    @staticmethod
    def check_if_version_update_enabled():
        if settings.FORCE_UPDATE_ENABLE in ["True","true"]:
            return True
        return False

    @staticmethod
    def check_if_version_update_required(version_number):
        force_update_required = False
        current_version = settings.IOS_VERSION
        if version_number:
            if DashboardUtils.compare_versions(version_number,current_version)!=-1:
                force_update_required = False
            else:
                force_update_required = True
        return force_update_required
    
    @staticmethod
    def get_all_todays_flyers():
        flyer_images = []
        current_datetime = datetime.today()
        flyer_scheduler_ids = FlyerScheduler.objects.filter(
                                    is_active=True,
                                    start_date_time__lte=current_datetime,
                                    end_date_time__gte=current_datetime
                                ).order_by('-start_date_time')
        for flyer_scheduler_id in flyer_scheduler_ids:
            flyer_images.extend(
                FlyerImagesSerializer(
                    FlyerImages.objects.filter(
                            flyer_scheduler_id=flyer_scheduler_id.id
                    ).order_by('sequence'),
                    many = True
                ).data
            )
        return flyer_images
    
    @staticmethod
    def start_end_datetime_comparision(start_date,end_date):
        start_date_time = datetime.strptime(start_date,'%Y-%m-%dT%H:%M:%S')
        end_date_time = datetime.strptime(end_date,'%Y-%m-%dT%H:%M:%S')
        if start_date_time > end_date_time:
            raise ValidationError("Start date time should not be greater than End date time")

    @staticmethod
    def validate_max_no_of_flyers(flyer_scheduler_id):
        flyer_images = FlyerImages.objects.filter(flyer_scheduler_id=flyer_scheduler_id)
        if len(flyer_images) >= int(settings.MAX_FLYER_IMAGES):
            raise ValidationError(DashboardConstants.REACHED_FLYER_LIMIT%(str(settings.MAX_FLYER_IMAGES)))

    @staticmethod
    def validate_flyers_sequence(flyer_scheduler_id,sequence,id=None):
        seq_flyer_images = FlyerImages.objects.filter(flyer_scheduler_id=flyer_scheduler_id,sequence=sequence)
        if id:
            seq_flyer_images = seq_flyer_images.exclude(id=id)
        if len(seq_flyer_images)>0:
            raise ValidationError("You cannot upload multiple flyers with the same sequence.")