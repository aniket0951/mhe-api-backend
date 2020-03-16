import logging
import mimetypes
import os

import magic
from django.core.exceptions import ValidationError
from manipal_api.settings import MAX_FILE_UPLOAD_SIZE


def validate_file_size(value):
    filesize = value.size
    if filesize > MAX_FILE_UPLOAD_SIZE * 1024 * 1024:
        raise ValidationError(
            "The maximum file size that can be uploaded is {}MB".format(MAX_FILE_UPLOAD_SIZE))
    else:
        return value

def validate_file_authenticity(value):
    mime_type = magic.from_buffer(
        value.file.getvalue(), mime=True)

    possible_file_extensions = mimetypes.guess_all_extensions(mime_type)

    if os.path.splitext(value.name)[1].lower() not in possible_file_extensions:
        raise ValidationError('Corrupted file is uploaded!')

    return value
