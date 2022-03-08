"""
Utilities for url shortner generation
"""
from django.conf import settings
import random
import string
from .models import UrlShorter

URL_SIZE = getattr(settings, 'MAX_URL_CHARS', 7)

AVAIABLE_CHARS = string.ascii_letters + string.digits


def short_it(full_url):
    s = string.ascii_uppercase + string.ascii_lowercase + string.digits

    url_id = ''.join(random.choices(s, k=URL_SIZE))

    if not UrlShorter.objects.filter(short_url=url_id).exists():
        # create a new entry for new one
        UrlShorter.objects.create(long_url=full_url, short_url=url_id)
        return url_id
    else:
        # if exists create a new url
        short_it(full_url)
