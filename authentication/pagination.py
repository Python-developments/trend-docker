'''
This module defines a custom pagination class for API responses.

Imports:
    rest_framework.pagination: Provides utilities for pagination in Django REST Framework.

Classes:
    CustomPageNumberPagination(PageNumberPagination):
        A custom pagination class that extends Django REST Framework's PageNumberPagination class.

        Attributes:
            page_size (int): The default number of items to include on each page. Default is 1.
            page_size_query_param (str): The query parameter name for specifying the page size. Default is 'limit'.
            max_page_size (int): The maximum number of items allowed on a single page. Default is 2.
            page_query_param (str): The query parameter name for specifying the page number. Default is 'p'.

Usage:
    To use this custom pagination class in your Django REST Framework views, include it in the view configuration
'''

from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 10
    page_query_param = 'p'