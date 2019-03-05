from math import sqrt
from reddit_clone_django_rest.app.models import Comment, Post, Vote, Account
from reddit_clone_django_rest.app import constants
from django.db.models import F, Count, Sum, When, Case, IntegerField, BooleanField, Value, Q, Subquery, OuterRef


def _confidence(ups, downs):
    n = ups + downs

    if n == 0:
        return 0

    z = 1.281551565545
    p = float(ups) / n

    left = p + 1/(2*n)*z*z
    right = z*sqrt(p*(1-p)/n + z*z/(4*n*n))
    under = 1+1/n*z*z

    return (left - right) / under


def confidence(ups, downs):
    if ups + downs == 0:
        return 0
    else:
        return _confidence(ups, downs)


def has_child_comment(comment, comments_for_post):
    for c in comments_for_post:
        if c.parent_id == comment.id:
            return True
    return False


def delete(comment):
    post = Post.objects.prefetch_related('comments').get(pk=comment.post.id)
    if not has_child_comment(comment, post.comments.all()):
        comment.is_visible = False
    comment.is_deleted = True
    comment.save()


def get_queryset(user):
    try:
        account = Account.objects.get(pk=user.id)

        q = Q(comment=OuterRef('pk'), user=account)
        vote_subquery = Vote.objects.filter(q).values('direction')
        user_vote_annotation = {
            'user_vote': Subquery(vote_subquery[:1])
        }

        user_save_annotation = {
            'user_saved': Case(
                When(
                    id__in=account.saved_comments.values('id'), then=True),
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

    return Comment.objects.select_related('author', 'author__user') \
                              .select_related('parent') \
                              .prefetch_related('votes') \
                              .annotate(**user_save_annotation) \
                              .annotate(**user_vote_annotation) \
                              .annotate(post_id=F('post__id')) \
                              .filter(is_visible=True) \
                              .filter(level__lte=2)

def get_comments_for_post_queryset(user, post_slug):
    return get_queryset(user).filter(post__slug=post_slug)

def get_comment_descendants(user, comment_id):
    parent = Comment.objects.get(pk=comment_id)
    return parent.get_descendants(include_self=False) 
