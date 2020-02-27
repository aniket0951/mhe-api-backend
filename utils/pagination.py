from rest_framework import pagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPagination(pagination.PageNumberPagination):
    page_size_query_param = 'page_count'
    max_page_size = 100

    def get_paginated_response(self, data):
        return OrderedDict([
            ('total_count', self.page.paginator.count),
            ('next_page', self.get_next_link()),
            ('previous_page', self.get_previous_link())
        ])
