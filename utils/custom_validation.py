class ValidationUtil:

    @staticmethod
    def validate_text_only(string):
        return string.isalpha()