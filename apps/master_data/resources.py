from import_export import resources

from .models import BillingGroup, BillingSubGroup


class BillingGroupResource(resources.ModelResource):
    class Meta:
        model = BillingGroup


class BillingSubGroupResource(resources.ModelResource):
    class Meta:
        model = BillingSubGroup
