# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.db.models import Count
from reddit_clone_django_rest.app.models import Post, Comment, Sub, Account
from reddit_clone_django_rest.app.services.homepage_service import sort_posts_by_hot, sort_posts_by_best
from reddit_clone_django_rest.app.services import comment_service, post_service, sub_service
from reddit_clone_django_rest.app.pagination import CommentPagination
from rest_framework import viewsets, generics, serializers, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import detail_route
from rest_framework.views import APIView
from reddit_clone_django_rest.app.serializers import UserSerializer, GroupSerializer, PostSerializer, CommentSerializer, SubSerializer, AccountSerializer
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from reddit_clone_django_rest.app.permissions import IsAuthorOrReadOnly, IsAdminOrReadOnly
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from abc import abstractproperty
from rest_framework.decorators import action, api_view
from reddit_clone_django_rest.app.mixins import VoteMixin, SaveMixin, MarkdownToHTML
from webpreview import web_preview

from silk.profiling.profiler import silk_profile

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

    
class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.select_related('user') \
                              .prefetch_related('subbed_to') \
                              .prefetch_related('admin_of') \
                              .prefetch_related('posts') \
                              .prefetch_related('saved_posts') \
                              .prefetch_related('saved_comments') \
                              .prefetch_related('upvoted_posts') \
                              .prefetch_related('downvoted_posts') \
                              .prefetch_related('upvoted_comments') \
                              .prefetch_related('downvoted_comments') \
                              .all().order_by('-created')
    serializer_class = AccountSerializer

    # allows searching like: http://example.com/api/users?search=russell
    search_fields = ('user__username')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response("Account delted", status.HTTP_200_OK)


class SubViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly)
    queryset = sub_service.get_sub_viewset()
    serializer_class = SubSerializer
    lookup_field = 'slug'

    @action(detail=True, methods=['patch'])
    def addadmin(self, request, slug):
        sub = self.get_object()
        user_to_add = Account.objects.get(pk=request.data['id'])

        if user_to_add is not None:
            sub.admins.add(user_to_add)
            sub.save()
            return Response({'user ' + str(user_to_add.id) + ' successfully added as an admin to ' + sub.title}, status=status.HTTP_202_ACCEPTED)
        return Response({'Bad request'}, status=status.HTTP_400_BAD_REQUEST)

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
        serializer.save(created_by=user_account, admins=[user_account])


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('-id')
    serializer_class = GroupSerializer

# @silk_profile(name="Post View Set")
class PostViewSet(viewsets.ModelViewSet, VoteMixin, SaveMixin, MarkdownToHTML):
    permission_classes = (IsAuthorOrReadOnly,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = PostSerializer
    #detail_serializer_class = PostDetailSerializer
    lookup_field = 'slug'
    slug_field = 'slug'

    def sort_queryset(self, queryset):
        sort = self.request.query_params.get('sort', None)

        if sort is None:
            sort = 'new'
        
        if sort == 'hot':
            return sort_posts_by_hot(queryset)
        
        if sort == 'best':
            return sort_posts_by_best(queryset)

        if sort == 'new':
            return queryset.order_by('-created')  


    # posts/user_personal_feed
    @action(detail=False, methods=['get'])
    def get_user_personal_feed(self):
        user = self.request.user

        if user is None:
            raise Request('Must be logged in to perform this action.', status.HTTP_403_FORBIDDEN)
        return post_service.get_posts_for_user_queryset(user.id)


    def get_posts_for_sub(self, sub_id):
        if not Sub.objects.filter(pk=sub_id).exists():
            raise Request('Must supply a valid sub id.') 
        return post_service.get_posts_for_sub_queryset(sub_id)

    # serves both main public feed and a sub list (/posts/?sub_id=123)
    def get_queryset(self):
        sub_id = self.request.query_params.get('sub_id', None)

        if self.action == 'list' and sub_id is not None:
            queryset = self.get_posts_for_sub(sub_id)
        else:
            queryset = post_service.get_post_queryset()
        return self.sort_queryset(queryset)

    @action(detail=True, methods=['patch'])
    def delete(self, request, slug):
        post = self.get_object()
        post.is_visible=False
        post.save()
        return Response('Post ' + str(post.id) + ' successfully deleted.', status.HTTP_202_ACCEPTED)

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
    serializer_class = CommentSerializer
    pagination_class = CommentPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        post_slug = self.request.query_params.get('post_slug', None)
        descendants_for = self.request.query_params.get('descendants_for', None)

        if self.action == 'list' and post_slug is not None:
            return comment_service.get_comments_for_post_queryset(post_slug)
        elif self.action == 'list' and descendants_for is not None:
            return comment_service.get_comment_descendants(descendants_for)
        else:
            return comment_service.get_queryset()


    @action(detail=False, methods=['get'])
    def comments_for_user(self, request):
        if request.user is None:
            return Response({
                'comments': []
            }, status=status.HTTP_401_UNAUTHORIZED)

        queryset = Comment.objects.filter(author_id=request.user.id)
        serializer = CommentSerializer(queryset, context={'request': request})

        return Response({ 'comments': serializer.data }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['patch'])
    def delete(self, request, pk):
        comment = self.get_object()
        comment_service.delete(comment)
        return Response('Comment ' + str(comment.id) + ' successfully deleted.', status.HTTP_202_ACCEPTED)

    def perform_create(self, serializer):

        # Have to get these values directly off the request because
        # they are not present in validated_data for some reason.
        body_text = self.request.data['body_text']
        parent = self.request.data['parent']

        # if body_text is None:
        #     return Response("body_text is required", status=status.HTTP_400_BAD_REQUEST)

        if parent is not None:
            parent = Comment.objects.get(pk=parent)

            if parent is None:
                raise serializers.ValidationError("Parent comment not found.")
            elif parent.is_deleted:
                raise serializers.ValidationError("Parent comment has been deleted.")

        account = self.get_logged_in_user_account()
        serializer.save(
            upvoted_by=[account], 
            author=account,
            body_text=body_text,
            parent=parent,
            **serializer.validated_data
            )

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


# Login handler
class CustomObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        account = Account.objects.get(id=token.user_id)
        serialized_user = AccountSerializer(account, context={'request': request})

        if serialized_user is not None and token is not None:
            return Response({
                'token': token.key,
                'account': serialized_user.data
                }, status.HTTP_200_OK)
        
        return Response({
            'token': None,
            'account': None
        }, status.HTTP_400_BAD_REQUEST)

      


        

