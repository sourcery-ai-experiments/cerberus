# Standard Library
from collections import OrderedDict

# Third Party
from rest_framework import pagination
from rest_framework.response import Response


class NullPagination(pagination.BasePagination):
    """This does no pagination but it does decorate the response to look
    paginated."""

    def paginate_queryset(self, queryset, request, view=None):
        return queryset

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", len(data)),
                    ("next", None),
                    ("previous", None),
                    ("results", data),
                ]
            )
        )
