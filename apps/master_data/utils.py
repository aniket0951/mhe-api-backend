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

    @staticmethod
    def process_lab_and_radiology_items(each_lab_radiology_item,lab_radiology_items_sorted_keys):
        hospital_lab_radiology_item_details = dict()
        for index, key in enumerate(sorted(each_lab_radiology_item.keys())):
            if not each_lab_radiology_item[key]:
                each_lab_radiology_item[key] = None
            if key in ['DateFrom', 'DateTo'] and each_lab_radiology_item[key]:
                each_lab_radiology_item[key] = datetime.strptime(each_lab_radiology_item[key], '%d/%m/%Y').strftime(MasterDataConstants.DATE_FORMAT)
            if key == 'ItemDesc' and each_lab_radiology_item[key]:
                each_lab_radiology_item[key] = each_lab_radiology_item[key].title()
            hospital_lab_radiology_item_details[lab_radiology_items_sorted_keys[index]] = each_lab_radiology_item[key]
        return each_lab_radiology_item, hospital_lab_radiology_item_details
