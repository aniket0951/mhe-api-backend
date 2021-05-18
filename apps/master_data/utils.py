from datetime import datetime
from .constants import MasterDataConstants

class MasterDataUtils:

    @staticmethod
    def process_department_details(each_department,department_sorted_keys):

        department_details = dict()

        for index, key in enumerate(sorted(each_department.keys())):
            if not each_department[key]:
                each_department[key] = None

            if key in ['DateFrom', 'DateTo'] and each_department[key]:
                each_department[key] = datetime.strptime(
                    each_department[key], '%d/%m/%Y').strftime(MasterDataConstants.DATE_FORMAT)

            department_details[department_sorted_keys[index]] = each_department[key]
        
        return department_details