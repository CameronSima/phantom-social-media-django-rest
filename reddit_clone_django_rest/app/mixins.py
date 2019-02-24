# -*- coding: utf-8 -*-
import json
from django.contrib.auth.models import User, Group
from rest_framework import status, serializers

from reddit_clone_django_rest.app.services.homepage_service import hot
from reddit_clone_django_rest.app.services.comment_service import confidence

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from reddit_clone_django_rest.app.models import Account
from markdown2 import Markdown

markdowner = Markdown()

# --------------- vieset mixins -----------------------------------------


class SortableMixin(object):
    default_sort = 'new'

    def get_queryset(self):
        queryset = super(SortableMixin, self).get_queryset()
        return self.sort_queryset(queryset)

    def sort_queryset(self, queryset):
        sort = self.request.query_params.get('sort', None)

        if sort is None:
            sort = self.default_sort

        if sort == 'top':
            return queryset.order_by('-score')

        if sort == 'hot':
            return queryset.order_by('-hot')

        if sort == 'best' or sort == 'confidence':
            return queryset.order_by('-confidence')

        if sort == 'controversial':
            return queryset.order_by('-controversy')

        if sort == 'new':
            return queryset.order_by('-created')


class SaveMixin(object):
    @action(detail=True, methods=['get'])
    def unsave(self, request, slug):
        obj = self.get_object()
        account = self.get_logged_in_user_account()
        if obj is not None or account is not None:
            already_saved = obj.saved_by.filter(pk=account.id).exists()
            if already_saved:
                obj.saved_by.remove(account)
                obj.save()
            else:
                return Response({'detail', 'user has not saved post.'}, status=status.HTTP_403_FORBIDDEN)
            return Response({obj.__class__.__name__: obj.id}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'detail', 'could not unsave post.'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get'])
    def save(self, request, slug):
        obj = self.get_object()
        account = self.get_logged_in_user_account()
        if obj is not None or account is not None:
            already_saved = obj.saved_by.filter(pk=account.id).exists()
            if not already_saved:
                obj.saved_by.add(account)
                obj.save()
            else:
                return Response({'detail', 'user already saved post.'}, status=status.HTTP_403_FORBIDDEN)
            return Response({obj.__class__.__name__: obj.id}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'detail', 'could not save post.'}, status=status.HTTP_403_FORBIDDEN)

# ------------------- serializer mixins -------------------------------------------

# A serializer mixin that provides scores, such as hotness and vote tallies,
# for comments and posts.


class MarkdownToHTML(object):
    def get_body_html(self, obj):
        return markdowner.convert(obj.body_text)
