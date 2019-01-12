from django.contrib.auth.models import User, Group
from reddit_clone_django_rest.app.models import Post, Comment, Account, Sub
from rest_framework import serializers
from reddit_clone_django_rest.app.services.homepage_service import hot
from reddit_clone_django_rest.app.mixins import GetScoresMixin

class SubInPostDetailSerializer(serializers.HyperlinkedModelSerializer):
    num_subscribers = serializers.SerializerMethodField()

    class Meta:
        model = Sub
        fields = ('id', 'url', 'created', 'title', 'slug', 'num_subscribers', 'admins', 'created_by')

    def get_num_subscribers(self, obj):
        return obj.subscribers.count()


class AccountLimitedInfoSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(source='user.username')
    class Meta:
        model = Account
        fields = ('url', 'username')

class SubLimitedInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sub
        fields = ('url', 'title', 'id')

class CommentSerializer(serializers.ModelSerializer, GetScoresMixin):
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    user_upvoted = serializers.SerializerMethodField()
    user_downvoted = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'url', 'author', 'body_text', 'body_html', 'parent', 'post', 'upvoted_by', 'downvoted_by', 'created', 'score', 'user_upvoted', 'user_downvoted')

class AccountSerializer(serializers.HyperlinkedModelSerializer):
    subbed_to = SubLimitedInfoSerializer(
        many=True,
        read_only=True,
        
    )
    username = serializers.CharField(source='user.username')
    
    comments = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="comment-detail"
    )
    posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="post-detail"
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
    upvoted_posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="post-detail"
    )
    downvoted_posts = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="post-detail"
    )
    upvoted_comments = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="comment-detail"
    )
    downvoted_comments = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="comment-detail"
    )
    class Meta:
        model = Account
        fields = ('username', 'created', 'id', 'url', 'user', 'subbed_to', 'admin_of', 'comments', 'posts', 'saved_posts', 'saved_comments', 'upvoted_comments', 'downvoted_comments', 'upvoted_posts', 'downvoted_posts')

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'password', 'email', 'groups', 'date_joined')

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

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

class PostSerializer(serializers.HyperlinkedModelSerializer, GetScoresMixin):
    author = AccountLimitedInfoSerializer(read_only=True)
    posted_in = SubLimitedInfoSerializer(read_only=True)
    num_comments = serializers.SerializerMethodField()
    user_upvoted = serializers.SerializerMethodField()
    user_downvoted = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    link_preview_img = serializers.SerializerMethodField()

    class Meta:
        model = Post
        read_only_fields = ('body_html', 'url', 'slug', 'upvoted_by', 'downvoted_by', 'created', 'num_comments', 'score')  
        fields = ('id', 'author', 'title', 'body_text', 'body_html', 'link_url', 'link_preview_img', 'image_url', 'posted_in', 'num_comments', 'created', 'score', 'url', 'user_upvoted', 'user_downvoted')

    def get_link_preview_img(self, obj):
        if obj.link_preview_img:
            return obj.link_preview_img.url

class PostDetailSerializer(serializers.ModelSerializer, GetScoresMixin):
    author = AccountLimitedInfoSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    posted_in = SubInPostDetailSerializer()
    num_comments = serializers.SerializerMethodField()
    user_upvoted = serializers.SerializerMethodField()
    user_downvoted = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        read_only_fields = ('comments', 'body_html', 'url', 'slug', 'upvoted_by', 'downvoted_by', 'created', 'num_comments', 'score')  
        fields = ('id', 'author', 'title', 'created', 'body_text', 'comments', 'url', 'link_url', 'image_url', 'posted_in', 'score', 'user_upvoted', 'user_downvoted', 'num_comments')

class SubSerializer(serializers.HyperlinkedModelSerializer):
    posts = PostSerializer(many=True, read_only=True)
    num_subscribers = serializers.SerializerMethodField()

    class Meta:
        model = Sub
        fields = ('id', 'url', 'created', 'title', 'slug', 'num_subscribers', 'admins', 'created_by', 'posts')

    def get_num_subscribers(self, obj):
        return obj.subscribers.count()
