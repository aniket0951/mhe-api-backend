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