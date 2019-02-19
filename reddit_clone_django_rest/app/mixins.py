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
# class GetScoresMixin(object):

#     def get_best_ranking(self, obj):
#         return confidence(obj.upvoted_by.count(), obj.downvoted_by.count())

#     def get_hot(self, obj):
#         return hot(obj.upvoted_by.count(), obj.downvoted_by.count(), obj.created)

#     def get_user_upvoted(self, obj):
#         user = self.context['request'].user
#         if user.is_authenticated():
#             return  obj.upvoted_by.filter(pk=user.id).exists()
#         return False

#     def get_user_saved(self, obj):
#         user = self.context['request'].user
#         if user.is_authenticated():
#             return obj.saved_by.filter(pk=user.id).exists()
#         else:
#             return False
        
#     def get_user_downvoted(self, obj):
#         user = self.context['request'].user
#         if user.is_authenticated():
#             #return user.account in obj.downvoted_by.all()
#             return obj.downvoted_by.filter(pk=user.id).exists()
#         else:
#             return False

#     def get_num_comments(self, obj):
#         return obj.comments.count()

#     def get_score(self, obj):
#         return obj.upvoted_by.count() - obj.downvoted_by.count()

class MarkdownToHTML(object):
    def get_body_html(self, obj):
        return markdowner.convert(obj.body_text)
