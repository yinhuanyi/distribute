# coding: utf-8
"""
@Author: Robby
@Module name: urls.py
@Create date: 2020-12-17
@Function: 
"""

from django.urls import path
from .views import AdhocView, PlaybookView, FileView


urlpatterns = [

    path('adhoc/', AdhocView.as_view(), name='task'),
    path('playbook/', PlaybookView.as_view(), name='playbook'),

    path('file/', FileView.as_view(), name='file'),
]