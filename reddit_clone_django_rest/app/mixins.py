# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from rest_framework import status, serializers

from reddit_clone_django_rest.app.services.homepage_service import hot

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from reddit_clone_django_rest.app.models import Account
from markdown2 import Markdown

markdowner = Markdown()

class MarkdownToHTML(object):
    def to_markdown(self, text):
        return markdowner.convert(text)

class SaveMixin(object):
    @action(detail=True, methods=['get'])
    def unsave(self, request, pk):
        obj = self.get_object()
        account = self.get_logged_in_user_account()
        if obj is not None or account is not None:
            already_saved = obj.saved_by.filter(pk=account.id).exists()
            if already_saved:
                obj.saved_by.remove(account)
                obj.save()
            else:
                return Response({'detail', 'user has not saved post.'}, status=status.HTTP_403_FORBIDDEN)
            return Response({'detail', 'post unsaved successfully.'}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'detail', 'could not unsave post.'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get'])
    def save(self, request, pk):
        obj = self.get_object()
        account = self.get_logged_in_user_account()
        if obj is not None or account is not None:
            already_saved = obj.saved_by.filter(pk=account.id).exists()
            if not already_saved:
                obj.saved_by.add(account)
                obj.save()
            else:
                return Response({'detail', 'user already saved post.'}, status=status.HTTP_403_FORBIDDEN)
            return Response({'detail', 'post saved successfully.'}, status=status.HTTP_202_ACCEPTED)
        else:
            return Response({'detail', 'could not save post.'}, status=status.HTTP_403_FORBIDDEN)


class VoteMixin(object):
    @action(detail=True, methods=['get'])
    def downvote(self, request, pk):
        return self.vote(upvote=False)

    @action(detail=True, methods=['get'])
    def upvote(self, request, pk):
        return self.vote(upvote=True)

    def vote(self, upvote=True):
        obj = self.get_object()
        direction = obj.upvoted_by if upvote else obj.downvoted_by
        opposite_direction = obj.downvoted_by if upvote else obj.upvoted_by
        account = self.get_logged_in_user_account()
        direction.remove(account)
        opposite_direction.remove(account)
        direction.add(account)
        return Response({'detail', 'user unvoted'}, status=status.HTTP_202_ACCEPTED)

    def get_logged_in_user_account(self):
        return Account.objects.get(id=self.request.user.id)


# A serializer mixin that provides scores, such as hotness and vote tallies,
# for comments and posts.
class GetScoresMixin(object):

    def get_hotness(self, obj):
        return hot(obj.upvoted_by.count(), obj.downvoted_by.count(), obj.created)

    def get_user_upvoted(self, obj):
        user = self.context['request'].user
        if user.is_authenticated():
            return user.account in obj.upvoted_by.all()
        else:
            return False
        
    def get_user_downvoted(self, obj):
        user = self.context['request'].user
        if user.is_authenticated():
            return user.account in obj.downvoted_by.all()
        else:
            return False

    def get_num_comments(self, obj):
        return obj.comments.count()

    def get_score(self, obj):
        return obj.upvoted_by.count() - obj.downvoted_by.count()