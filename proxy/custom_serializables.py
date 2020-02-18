class ValidateUHID:
    def __init__(self, uhid=None, otp=None):
        self.uhid = uhid
        self.otp = otp

    def serialize(self, serializer):
        serializer.start_object('ValidateRequestParam')
        serializer.add_property('UHID', self.uhid)
        serializer.add_property('POTP', self.otp)


class SyncAPIRequest:
    def __init__(self, location_code=None, sync_method=None):
        self.location_code = location_code
        self.sync_method = sync_method

    def serialize(self, serializer):
        serializer.start_object('SyncRequestParam')
        serializer.add_property('SyncLocationCode', self.location_code)
        serializer.add_property('SyncMethod', self.sync_method)


class ItemTaiffPrice:
    def __init__(self, location_code=None, sync_method='tariff', item_code=None):
        self.location_code = location_code
        self.sync_method = sync_method
        self.item_code = item_code

    def serialize(self, serializer):
        serializer.start_object('SyncRequestParam')
        serializer.add_property('SyncLocationCode', self.location_code)
        serializer.add_property('SyncMethod', self.sync_method)
        serializer.add_property('SyncItemCode', self.item_code)
