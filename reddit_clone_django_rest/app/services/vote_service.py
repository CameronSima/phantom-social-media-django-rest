from reddit_clone_django_rest.app.models import Vote
from reddit_clone_django_rest.app import constants

def create_default_vote(account, voteable_obj_params):
    Vote.objects.create(
        user = account,
        direction= constants.UP,
        **voteable_obj_params
    )