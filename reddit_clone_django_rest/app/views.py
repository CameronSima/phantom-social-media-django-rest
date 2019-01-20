# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from reddit_clone_django_rest.app.models import Post, Comment, Sub, Account
from reddit_clone_django_rest.app.services.homepage_service import sort_posts_by_hot
from reddit_clone_django_rest.app.services.comment_service import confidence
from rest_framework import viewsets, generics, serializers, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import detail_route
from rest_framework.views import APIView
from reddit_clone_django_rest.app.serializers import UserSerializer, GroupSerializer, PostDetailSerializer, PostSerializer, CommentSerializer, SubSerializer, AccountSerializer
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from reddit_clone_django_rest.app.permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from rest_framework.authtoken.models import Token
from abc import abstractproperty
from rest_framework.decorators import action
from reddit_clone_django_rest.app.mixins import VoteMixin, SaveMixin, MarkdownToHTML
from webpreview import web_preview

from reddit_clone_django_rest.app.services.create_test_data import TestDataCreator

class GetAndPostViewSet(viewsets.ModelViewSet):
    """
    A Viewset that can switch serializers based 
    on whether the request is a POST or GET.
    """
    pass

    @abstractproperty
    def post_serializer_class():
        pass

class DetailAndListViewSet(viewsets.ModelViewSet):
    """
     A ModelViewSet that implements a detail serializer and a 
    list serializer.
    """

    def get_serializer_class(self):
        if self.action == 'retrieve':
            if hasattr(self, 'detail_serializer_class'):
                return self.detail_serializer_class
        return super(DetailAndListViewSet, self).get_serializer_class()

class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all().order_by('-created')
    serializer_class = AccountSerializer

    #testing
    #lookup_field = 'slug'
    

    # allows searching like: http://example.com/api/users?search=russell
    search_fields = ('user__username')

class SubViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly)
    queryset = Sub.objects.all().order_by('-created')
    serializer_class = SubSerializer
    lookup_field = 'slug'
    

    @action(detail=True, methods=['patch'])
    def unsubscribe(self, request, slug):
        sub = self.get_object()
        subbed = sub.subscribers.filter(pk=request.user.id).exists()

        if subbed:
            user_account = Account.objects.get(pk=request.user.id)
            sub.subscribers.remove(user_account)
            sub.save()
            return Response({'detail', 'user unsubscribed successfully.'}, status=status.HTTP_202_ACCEPTED)
        else :
            return Response({'detail', 'user is not currently subscribed.'}, status=status.HTTP_403_FORBIDDEN)


    @action(detail=True, methods=['patch'])
    def subscribe(self, request, slug):
        sub = self.get_object()
        already_subbed = sub.subscribers.filter(pk=request.user.id).exists()

        if not already_subbed:
            user_account = Account.objects.get(pk=request.user.id)
            sub.subscribers.add(user_account)
            sub.save()
            return Response({'detail', 'user subscribed successfully.'}, status=status.HTTP_202_ACCEPTED)
        else :
            return Response({'detail', 'user is already subscribed.'}, status=status.HTTP_403_FORBIDDEN)


    #TODO move functionality like this to serializers (see UserSerializer.create)
    def perform_create(self, serializer):

        # Assign the logged-in user as the sub creator, and add as admin.
        user_account = Account.objects.get(pk=self.request.user.id)
        serializer.save(created_by = user_account, admins = [user_account])


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('-id')
    serializer_class = GroupSerializer

class PostViewSet(DetailAndListViewSet, VoteMixin, SaveMixin, MarkdownToHTML):
    queryset = Post.objects.all().order_by('-created')
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    authentication_classes = (TokenAuthentication,)
    serializer_class = PostSerializer
    detail_serializer_class = PostDetailSerializer
    lookup_field = 'slug'
    slug_field = 'slug'
   
    def perform_create(self, serializer):
        
        # Add user's account as the author of the Post.
        # IsAuthenticatedOrReadOnly permission class will 
        # stop unauthenticated requests from reaching this code
        # and causing an error.
        posted_in = Sub.objects.get(id=self.request.data['posted_in'])
        account = self.get_logged_in_user_account()

        # Commented because html is generated in the serializer.
        #body_html = self.to_markdown(self.request.data['body_text'])

        link_image = None
        if 'link_url' in self.request.data:
            title, description, link_image = web_preview(self.request.data['link_url'])

        serializer.save(upvoted_by=[account], author=account, posted_in=posted_in, link_preview_img=link_image)

class CommentViewSet(viewsets.ModelViewSet, VoteMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    authentication_classes = (TokenAuthentication,)

    def perform_create(self, serializer):
        account = self.get_logged_in_user_account()
        serializer.save(upvoted_by=[account], author=account)


class SearchViewSet(APIView):
    """
    View for searchbar functionality.
    """

    search_term_kwarg = "search_term"

    def get(self, request, format=None):
        search_term = self.kwargs.get(self.search_term_kwarg)
        users = User.objects.filter(username=search_term)
        posts = Post.objects.filter(title=search_term)

        response = {
            'users': {
                'count': len(users),
                'results': users
            },
            'posts': {
                'count': len(posts),
                'results': posts
            }
        }
        return Response(response)


class LoggedInUserSubbedPostsViewSet(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = PostSerializer

    def get_queryset(self):
        user_subs = Sub.objects.filter(subscribers__in=[self.request.user.id])
        return Post.objects.filter(posted_in__in=user_subs)


class FrontPage(generics.ListAPIView):
    serializer_class = PostSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        posts = Post.objects.filter(is_private=False)
        return sort_posts_by_hot(posts)


# Login handler
class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        account = Account.objects.get(id=token.user_id)
        return Response({
            'token': token.key,
            'account': AccountSerializer(account, context={'request': request}).data
            })


      


        

