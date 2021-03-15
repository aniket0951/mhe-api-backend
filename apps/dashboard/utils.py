from django.conf import settings
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
