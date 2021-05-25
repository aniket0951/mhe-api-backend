from apps.dashboard.serializers import FlyerImagesSerializer
from apps.dashboard.models import FlyerImages, FlyerScheduler
from django.conf import settings
from datetime import datetime

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
                                    start_date_time__lte=current_datetime,
                                    end_date_time__gte=current_datetime
                                ).order_by('-start_date_time')
        for flyer_scheduler_id in flyer_scheduler_ids:
            flyer_images.extend(
                FlyerImagesSerializer(
                    FlyerImages.objects.filter(
                            flyer_scheduler_id=flyer_scheduler_id.id
                    ).order_by('Sequence'),
                    many = True
                ).data
            )
        return flyer_images