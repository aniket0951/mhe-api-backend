from django.contrib import admin

# Register your models here.
from .models import BillingGroup, BillingSubGroup, Department, Hospital

admin.site.register(Hospital)
admin.site.register(Department)
admin.site.register(BillingGroup)
admin.site.register(BillingSubGroup)
