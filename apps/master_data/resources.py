from import_export import resources

from .models import BillingGroup, BillingSubGroup, Specialisation


class BillingGroupResource(resources.ModelResource):
    class Meta:
        model = BillingGroup


class BillingSubGroupResource(resources.ModelResource):
    class Meta:
        model = BillingSubGroup


class BillingGroupResource(resources.ModelResource):
    class Meta:
        model = BillingGroup


class SpecialisationResource(resources.ModelResource):
    class Meta:
        model = Specialisation
