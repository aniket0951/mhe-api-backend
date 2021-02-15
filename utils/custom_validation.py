class ValidationUtil:

    @staticmethod
    def validate_text_only(string):
        return string.isalpha()

    @staticmethod
    def refine_text_only(string):
        new_string = ""
        for i in string:
            if ValidationUtil.validate_text_only(i):
                new_string+=i 
        return new_string