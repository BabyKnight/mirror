from django.urls import re_path, path
from .views import *

urlpatterns = [
    # to be updated to direct to the home page as default
    path('', dummy_view),
    re_path(r'^api/ping/?$', ping),
    #User & User Profile
    re_path(r'^api/user/create/?$', dummy_view),
    re_path(r'^api/user/update/?$', dummy_view),
    #Image
    re_path(r'^api/image/add/?$', dummy_view),
    re_path(r'^api/image/update/?$', dummy_view),
    re_path(r'^api/image/delete/?$', dummy_view),
    re_path(r'^api/image/detail/?$', dummy_view),
    #Sample
    re_path(r'^api/sample/add/?$', dummy_view),
    re_path(r'^api/sample/delete/?$', dummy_view),
    re_path(r'^api/sample/update/?$', dummy_view),
    re_path(r'^api/sample/detail/?$', dummy_view),
    #Status /* Pre-defined status and code */
    #Task
    re_path(r'^api/task/run/?$', dummy_view),
    re_path(r'^api/task/cancel/?$', dummy_view),
    re_path(r'^api/task/detail/?$', dummy_view),
    #Test case
    re_path(r'^api/case/add/?$', dummy_view),
    re_path(r'^api/case/delete/?$', dummy_view),
    re_path(r'^api/case/update/?$', dummy_view),
    re_path(r'^api/case/detail/?$', dummy_view),
]
