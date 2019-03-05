from reddit_clone_django_rest.app.models import Post, Vote, Account
from django.db.models import Count, Sum, When, Case, IntegerField, BooleanField, Value, Q, Subquery, OuterRef
from django.core.cache import cache
from reddit_clone_django_rest.app import constants

# -----  querysets -----------------------------


def get_post_queryset(user):
    try:
        account = Account.objects.get(pk=user.id)

        q = Q(post=OuterRef('pk'), user=account)
        vote_subquery = Vote.objects.filter(q).values('direction')
        user_vote_annotation = {
            'user_vote': Subquery(vote_subquery[:1])
        }

        user_save_annotation = {
            'user_saved': Case(
                When(
                    id__in=account.saved_posts.values('id'), then=True),
                default=Value(False),
                output_field=BooleanField()
            )
        }

    except Account.DoesNotExist:
        user_vote_annotation = {
            'user_vote': Value(constants.NONE, output_field=IntegerField())
        }
        user_save_annotation = {
            'user_saved': Value(False, BooleanField())
        }

    return Post.objects.select_related('posted_in') \
        .select_related('author', 'author__user') \
        .annotate(num_comments=Count('comments')) \
        .annotate(**user_vote_annotation) \
        .annotate(**user_save_annotation) \
        .filter(is_visible=True)


def get_posts_for_sub_queryset(user, sub_id):
    return get_post_queryset(user).filter(posted_in=sub_id)


def get_posts_for_user_queryset(user, user_id):
    return get_post_queryset(user).filter(posted_in__subscribers=user_id)
