class DashboardUtils:

    @staticmethod
    def compare_versions(older_version,newer_version):
        version1 = [int(pt) for pt in older_version.split(".")]
        version2 = [int(pt) for pt in newer_version.split(".")]

        for i in range(max(len(version1), len(version2))):
            v1 = version1[i] if i < len(version1) else 0
            v2 = version2[i] if i < len(version2) else 0
            if v1 == v2:    continue
            return 1 if v1 > v2 else -1
        return 0
        
# print(DashboardUtils.compare_versions("1.1.2","1.3"))
# print(DashboardUtils.compare_versions("1.7","1.10"))
# print(DashboardUtils.compare_versions("1.3.8","1.3.9"))