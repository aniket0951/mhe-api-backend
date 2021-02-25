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

    @staticmethod
    def validate_email(string):
        return re.match("[^@]+@[^@]+\.[^@]+",string)

    @staticmethod
    def refine_string(text):
        text = re.sub(r'^https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
        text = ValidationUtil.cleanhtml(text)
        return text

    @staticmethod
    def cleanhtml(raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext
