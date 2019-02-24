from reddit_clone_django_rest.app.models import Post
from django.db.models import Count, Sum, When, Case, IntegerField
from reddit_clone_django_rest.app import constants

# -----  querysets -----------------------------

def get_post_queryset():
    return Post.objects.select_related('posted_in') \
                .select_related('author', 'author__user') \
                .annotate(num_comments=Count('comments')) \
                .filter(is_visible=True) 

def get_posts_for_sub_queryset(sub_id):
    return get_post_queryset().filter(posted_in=sub_id)

def get_posts_for_user_queryset(user_id):
    return get_post_queryset().filter(posted_in__subscribers=user_id)
                   

 
