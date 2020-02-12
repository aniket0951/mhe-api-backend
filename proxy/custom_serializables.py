class UHID:
    def __init__(self, uhid=None):
        self.uhid = uhid

    def serialize(self, serializer):
        serializer.start_object('ValidateRequestParam')
        serializer.add_property('UHID', self.uhid)