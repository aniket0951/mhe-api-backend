import re
class ValidationUtil:

    @staticmethod
    def validate_text_only(string):
        return string.isalpha()

    @staticmethod
    def refine_text_only(string):
        new_string = ""
        if string:
            for i in string:
                if i and ValidationUtil.validate_text_only(i):
                    new_string+=i 
        return new_string
    
    @staticmethod
    def validate_alphawidespace(string):
        return re.match('[a-zA-Z ]+$',string)
