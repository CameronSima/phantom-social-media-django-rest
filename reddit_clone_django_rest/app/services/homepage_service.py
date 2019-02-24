from datetime import datetime, timedelta
from math import log
from reddit_clone_django_rest.app.services.comment_service import confidence as best
from reddit_clone_django_rest.app import models

epoch = datetime(1970, 1, 1)


def epoch_seconds(date):
    td = date - epoch
    return td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)


def score(ups, downs):
    return ups - downs


def hot(ups, downs, date):
    date = date.replace(tzinfo=None)
    s = score(ups, downs)
    order = log(max(abs(s), 1), 10)
    sign = 1 if s > 0 else -1 if s < 0 else 0
    seconds = epoch_seconds(date) - 1134028003
    return round(sign * order + seconds / 45000, 7)


def controversy(ups, downs):
    if downs <= 0 or ups <= 0:
        return 0

    magnitude = ups + downs
    balance = float(downs) / ups if ups > downs else float(ups) / downs
    return magnitude ** balance

