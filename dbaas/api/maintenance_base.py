from __future__ import absolute_import, unicode_literals
from rest_framework import permissions
from rest_framework import viewsets, filters


class MaintennanceBaseApi(viewsets.ReadOnlyModelViewSet):

    """
    Base Maintenance API
    """

    model = None
    serializer_class = None
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.OrderingFilter,)
    filter_fields = None
    ordering_fields = ('created_at', 'id')
    ordering = ('-created_at',)
    datetime_fields = ('created_at')

    def get_queryset(self):
        queryset = self.model.objects.all()
        params = self.request.GET.dict()
        valid_params = {}
        for field in params.keys():
            if field.split('__')[0] in self.filter_fields:
                valid_params[field] = params[field]
        if params:
            return queryset.filter(**valid_params)
        return queryset
