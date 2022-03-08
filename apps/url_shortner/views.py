from django.shortcuts import redirect
from django.contrib.sites.requests import RequestSite
from django.contrib.sites.models import Site
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UrlShorter
from .utils import short_it


@csrf_exempt
def shortView(request):
    long_url = request.POST.get("url")
    hash = short_it(long_url)
    current_site = str(request.get_host())
    data = {
        "success": True,
        "id": hash,
        "short_url": "http://{}/{}".format(current_site, hash),
        "long_url": long_url
    }
    return JsonResponse(data)


def redirect_url_view(request, shortened_part):
    try:
        url = UrlShorter.objects.get(short_url=shortened_part)
        print(url)
        print(str(url))
        url.times_followed += 1
        url.save()
        return redirect(url.long_url)
    except:
        raise JsonResponse({"success": False})
