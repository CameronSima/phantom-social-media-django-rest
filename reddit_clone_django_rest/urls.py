"""reddit_clone_django_rest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers
from django.contrib import admin
from reddit_clone_django_rest.app import views
from rest_framework.authtoken import views as authViews
from reddit_clone_django_rest.app.admin import admin_site

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'posts', views.PostViewSet, base_name='post')
router.register(r'comments', views.CommentViewSet, base_name='comment')
router.register(r'subs', views.SubViewSet)
router.register(r'accounts', views.AccountViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-token-auth/', views.CustomObtainAuthToken.as_view()),
    url(r'home', views.PostViewSet.as_view({'get': 'list'})),
    url(r'^search/(?P<search_term>[-\w]+)', views.SearchViewSet.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', admin_site.urls),
    url(r'^silk/', include('silk.urls', namespace='silk')),
  #url(r"^posts/(?P<slug>[-\w]+)/$", views.PostViewSet.as_view({'get': 'list'}, lookup_field = 'slug'))
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
