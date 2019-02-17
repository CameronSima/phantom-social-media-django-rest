from reddit_clone_django_rest.app.models import Sub
from django.db.models import Count

def get_sub_viewset():
    return Sub.objects.select_related('created_by') \
            .annotate(num_subscribers=Count('subscribers')) \
            .order_by('-created')
