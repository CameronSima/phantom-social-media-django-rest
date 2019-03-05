# -*- coding: utf-8 -*-
import json
from django.contrib.auth.models import User, Group
from rest_framework import status, serializers
from django.core.cache import cache

from reddit_clone_django_rest.app.services.homepage_service import hot
from reddit_clone_django_rest.app.services.comment_service import confidence
from reddit_clone_django_rest.tasks import vote
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from reddit_clone_django_rest.app.models import Account, Vote
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


class VotableMixin(object):

    @action(detail=True, methods=['post'])
    def vote(self, request, slug):
        body = json.loads(request.body)
        direction = body['direction']
        obj = self.get_object()
        model_type = obj.__class__.__name__.lower() + '_id'
        kwargs = {model_type: obj.id}

        if direction is None or obj is None:
            raise Response('Invalid vote')
    
        vote.delay(direction, self.request.user.id, kwargs)
        return Response('OK', status.HTTP_202_ACCEPTED)

class SaveMixin(object):
    model_type = None

    def update_cache(self, saved):
        cache_key = '{}-{}-user-{}-save'.format(
            self.model_type, self.get_object().id, self.request.user.id
        )
        cache.set(cache_key, saved)

    def get_logged_in_user_account(self):
        return Account.objects.get(pk=self.request.user.id)

    @action(detail=True, methods=['get'])
    def save(self, request, slug):
        obj = self.get_object()
        account = self.get_logged_in_user_account()

        if obj is not None or account is not None:
            self.model_type = obj.__class__.__name__.lower()
            already_saved = obj.saved_by.filter(pk=account.id).exists()

            if not already_saved:
                obj.saved_by.add(account)
                saved = True
            else:
                obj.saved_by.remove(account)
                saved = False

            obj.save()
            self.update_cache(saved)

            return Response(self.model_type + ' ' + str(obj.id) + ' saved: ' + str(saved), status=status.HTTP_202_ACCEPTED)
        else:
            return Response('could not save object.', status=status.HTTP_400_BAD_REQUEST)

# ------------------- serializer mixins -------------------------------------------


class MarkdownToHTML(object):
    def get_body_html(self, obj):
        return markdowner.convert(obj.body_text)
