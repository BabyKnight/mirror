from django.urls import re_path, path
from .views import *

urlpatterns = [
    # to be updated to direct to the home page as default
    path('', dummy_view),
    
    path('index/', index),
    path('index/dashboard/', dashboard),
    path('index/sample/', sample),
    path('index/image/', image),
    path('index/task/', task),
    path('index/testcase/', testcase),
    path('index/platform/', platform),
    path('chart/<str:chart_type>/', chart),

    #API
    re_path(r'^api/ping/?$', ping),
    # api for User & User Profile
    re_path(r'^api/user/create/?$', dummy_view),
    re_path(r'^api/user/update/?$', dummy_view),
    # api for Image
    re_path(r'^api/image/add/?$', dummy_view),
    re_path(r'^api/image/update/?$', dummy_view),
    re_path(r'^api/image/delete/?$', dummy_view),
    re_path(r'^api/image/detail/?$', dummy_view),
    # api for Sample
    re_path(r'^api/sample/add/?$', dummy_view),
    re_path(r'^api/sample/delete/?$', dummy_view),
    re_path(r'^api/sample/update/?$', dummy_view),
    re_path(r'^api/sample/detail/?$', dummy_view),
    re_path(r'^api/sample/show_all/?$', dummy_view),
    #Status /* Pre-defined status and code */
    # api for Task
    re_path(r'^api/task/run/?$', dummy_view),
    re_path(r'^api/task/cancel/?$', dummy_view),
    re_path(r'^api/task/detail/?$', dummy_view),
    # api for log
    re_path(r'^api/log_upload/?$', log_upload),
    # api for Test case
    re_path(r'^api/case/add/?$', dummy_view),
    re_path(r'^api/case/delete/?$', dummy_view),
    re_path(r'^api/case/update/?$', dummy_view),
    re_path(r'^api/case/detail/?$', dummy_view),
    re_path(r'^api/case/show_all/?$', dummy_view),
]
