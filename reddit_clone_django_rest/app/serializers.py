from django.contrib.auth.models import User, Group
from reddit_clone_django_rest.app.models import Post, Comment, Account, Sub
from rest_framework import serializers
from reddit_clone_django_rest.app.services.homepage_service import hot
from reddit_clone_django_rest.app.mixins import GetScoresMixin, MarkdownToHTML

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
        

class CommentSerializer(serializers.ModelSerializer, GetScoresMixin, MarkdownToHTML):
    author = AccountLimitedInfoSerializer(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    user_upvoted = serializers.SerializerMethodField()
    user_downvoted = serializers.SerializerMethodField()
    user_saved = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
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
            
    class Meta:
        model = Comment
        fields = ('id', 'url', 'user_upvoted', 'user_downvoted', 'user_saved', 'has_descendants', 'author', 'body_text', 'body_html', 'parent', 'post', 'created', 'score', 'body_html')

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
    # comments = serializers.HyperlinkedRelatedField(
    #     many=True,
    #     read_only=True,
    #     view_name="comment-detail"
    # )
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
    upvoted_posts = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    downvoted_posts = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    upvoted_comments = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    downvoted_comments = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )
    class Meta:
        model = Account
        fields = ('username', 'created', 'id', 'url', 'user', 'subbed_to',  'admin_of', 'posts', 'saved_posts', 'saved_comments', 'upvoted_comments', 'downvoted_comments', 'upvoted_posts', 'downvoted_posts')


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

class PostSerializer(serializers.HyperlinkedModelSerializer, GetScoresMixin):
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

    # These are not needed in production because in the frontpage view and logged-in user view,
    # the values and sorting are calculated in the view and are not necessary here -- just for
    # tests to pass.
    hot = serializers.SerializerMethodField()
    best_ranking = serializers.SerializerMethodField()

    class Meta:
        model = Post
        read_only_fields = ('body_html', 'url', 'slug', 'posted_in', 'created', 'num_comments', 'score')  
        fields = ('id', 'author', 'hot', 'best_ranking', 'title', 'slug', 'body_text', 'body_html', 'link_url', 'link_preview_img', 'image_url', 'posted_in', 'num_comments', 'created', 'score', 'url')
        lookup_fild = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }

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

