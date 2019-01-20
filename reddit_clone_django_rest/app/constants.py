# Notification types

POST_AUTHOR = 'POST_AUTHOR'
COMMENT_PARENT_AUTHOR = 'PARENT_COMMENT_AUTHOR'
MENTIONED_USER = 'MENTIONED_USER'
USER_POSTED_IN_SUB = 'USER_POSTED_IN_SUB'

NOTIFICATION_TYPES = (
    (POST_AUTHOR, 'post_author'),
    (COMMENT_PARENT_AUTHOR, 'comment_parent_author'),
    (MENTIONED_USER, 'mentioned_user'),
    (USER_POSTED_IN_SUB, 'user_posted_in_sub')
)

# Custom http actions

