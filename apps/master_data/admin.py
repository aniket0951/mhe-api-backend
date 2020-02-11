from django.contrib import admin

# Register your models here.
from .models import Hospital, Specialisation, BillingGroup, BillingSubGroup

admin.site.register(Hospital)
admin.site.register(Specialisation)
admin.site.register(BillingGroup)
admin.site.register(BillingSubGroup)
