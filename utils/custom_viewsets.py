from rest_framework import viewsets

from utils import custom_mixins


class ModelViewSet(custom_mixins.CreateModelMixin,
                   custom_mixins.RetrieveModelMixin,
                   custom_mixins.UpdateModelMixin,
                   custom_mixins.DestroyModelMixin,
                   custom_mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass


class ReadOnlyModelViewSet(custom_mixins.RetrieveModelMixin,
                           custom_mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """
    pass


class ListUpdateViewSet(
        custom_mixins.UpdateModelMixin,
        custom_mixins.ListModelMixin,
        viewsets.GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass

class ListViewSet(
        custom_mixins.ListModelMixin,
        viewsets.GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass
class ListCreateViewSet(
        custom_mixins.CreateModelMixin,
        custom_mixins.ListModelMixin,
        viewsets.GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass


class CreateViewSet(
        custom_mixins.CreateModelMixin,
        viewsets.GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass


class CreateDeleteViewSet(
        custom_mixins.CreateModelMixin,
        custom_mixins.DestroyModelMixin,
        viewsets.GenericViewSet):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass
