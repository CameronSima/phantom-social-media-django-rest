from django.contrib.auth.models import User, Group
from reddit_clone_django_rest.app.models import Post, Comment, Account, Sub, Vote
from rest_framework import serializers
from reddit_clone_django_rest.app.services.homepage_service import hot
from reddit_clone_django_rest.app.mixins import MarkdownToHTML
from reddit_clone_django_rest.app import constants

class SubInPostDetailSerializer(serializers.HyperlinkedModelSerializer):
    num_subscribers = serializers.SerializerMethodField()

    class Meta:
        model = Sub
        fields = ('id', 'url', 'created', 'title', 'slug', 'num_subscribers', 'admins', 'created_by')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': { 'lookup_field': 'slug' }
        }
        
    def get_num_subscribers(self, obj):
        return obj.subscribers.count()


class AccountLimitedInfoSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(source='user.username')
    class Meta:
        model = Account
        fields = ('url', 'username', 'id')
    

class SubLimitedInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sub
        fields = ('url', 'title', 'id', 'slug')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }
        

class CommentSerializer(serializers.ModelSerializer, MarkdownToHTML):
    author = AccountLimitedInfoSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    # user_upvoted = serializers.SerializerMethodField()
    # user_downvoted = serializers.SerializerMethodField()
    user_saved = serializers.SerializerMethodField()
    #score = serializers.SerializerMethodField()
    score = serializers.IntegerField()
    body_html = serializers.SerializerMethodField()
    body_text = serializers.SerializerMethodField()
    has_descendants = serializers.SerializerMethodField()

    # If a comment is a leaf node, we can tell client side
    # if it has unloaded descendants
    def get_has_descendants(self, comment):
        return not comment.is_leaf_node()

    def get_body_text(self, comment):
        if comment.is_deleted:
            return '- deleted -'
        return comment.body_text

    def get_user_saved(self, comment):
        user = self.context['request'].user
        if user.is_authenticated():
            account = Account.objects.get(pk=user.id)
            return account.saved_comments.filter(pk=comment.id).exists()

            
    class Meta:
        model = Comment
        fields = ('id', 'url', 'user_saved', 'has_descendants', 'author', 'body_text', 'body_html', 'parent', 'post', 'created', 'score', 'body_html')

class AccountSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    subbed_to = SubLimitedInfoSerializer(
        many=True,
        read_only=True
    )
    admin_of = SubLimitedInfoSerializer(
        many=True,
        read_only=True
    ) 
    posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="post-detail",
        lookup_field='slug'
    )
    saved_posts = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    saved_comments = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="comment-detail"
    )
    class Meta:
        model = Account
        fields = ('username', 'created', 'id', 'url', 'user', 'subbed_to',  'admin_of', 'posts', 'saved_posts', 'saved_comments')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'password', 'email', 'date_joined')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class PostSerializer(serializers.HyperlinkedModelSerializer):
    author = AccountLimitedInfoSerializer(read_only=True)
    posted_in = SubLimitedInfoSerializer(read_only=True)
    
    # Annotated method field is much faster than SerializerMethodField()
    num_comments = serializers.IntegerField()
    score = serializers.SerializerMethodField()
    link_preview_img = serializers.SerializerMethodField()
    posted_in = SubLimitedInfoSerializer()
    # user_saved = serializers.SerializerMethodField()
    # user_upvoted = serializers.SerializerMethodField()
    # user_downvoted = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Post
        read_only_fields = ('body_html', 'url', 'slug', 'posted_in', 'created', 'num_comments', 'score')  
        fields = ('id', 'author', 'user_vote', 'title', 'slug', 'body_text', 'body_html', 'link_url', 'link_preview_img', 'image_url', 'posted_in', 'num_comments', 'created', 'score', 'url')
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }

    def get_user_vote(self, post):
        if self.context['request'].user.is_authenticated():
            vote = post.votes.filter(pk=self.context['request'].user.id)
            if vote.exists():
                return vote.direction
        return constants.NONE

    def get_score(self, post):
        return sum(vote.direction for vote in post.votes.all())

    def get_link_preview_img(self, obj):
        if obj.link_preview_img:
            return obj.link_preview_img.url

class SubSerializer(serializers.HyperlinkedModelSerializer):
    created_by = AccountLimitedInfoSerializer(read_only=True)
    admins = AccountLimitedInfoSerializer(many=True, read_only=True)
    num_subscribers = serializers.IntegerField()

    class Meta:
        model = Sub
        fields = ('id', 'url', 'created', 'title', 'slug', 'num_subscribers', 'admins', 'created_by')
        lookup_field = 'slug'
        extra_kwargs = {
            'created_by': {'read_only': True, 'required': False},
            'url': {'lookup_field': 'slug'}
        }

    def get_num_subscribers(self, obj):
        return obj.subscribers.count()


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('created', 'user', 'post', 'comment', 'direction')
        read_only_fields = ('user', '')

    def create(self, validated_data):

        post_id = validated_data.get('post', None)
        comment_id = validated_data.get('comment', None)
        direction = validated_data.get('direction', None)

        if not post_id and not comment_id:
            raise Response('Must supply a Post id or Comment id to vote on')

        if post_id and comment_id:
            raise Response('Cannot vote on both a comment and a post.')

        if post_id:
            params = {'post': post_id}
        else:
            params = {'comment': comment_id}

        # check if user already voted
        existing_vote = Vote.objects.filter(user=self.context['request'].user.id, **params)
            
        if existing_vote.exists():
            existing_vote = existing_vote[0]
            if direction == existing_vote.direction:
                existing_vote.direction = constants.NONE
            else:
                existing_vote.direction = direction
            existing_vote.save()
            return existing_vote

        else:
            account = Account.objects.get(pk=self.context['request'].user.id)
            new_vote = Vote.objects.create(
                user=account,
                direction=direction,
                **params
            )
            return new_vote
                




    