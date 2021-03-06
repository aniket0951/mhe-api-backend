from rest_framework import pagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPagination(pagination.PageNumberPagination):
    page_size_query_param = 'page_count'
    max_page_size = 100

    def custom_previous_page_number(self):
        if not self.page.has_previous():
            return None
        return self.page.previous_page_number()

    def custom_next_page_number(self):
        if not self.page.has_next():
            return None
        return self.page.next_page_number()

    def get_paginated_response(self, data):
        return OrderedDict([
            ('total_count', self.page.paginator.count),
            ('next_page', self.get_next_link()),
            ('next_page_number', self.custom_next_page_number()),
            ('previous_page', self.get_previous_link()),
            ('previous_page_number', self.custom_previous_page_number())
        ])
