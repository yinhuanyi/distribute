# coding: utf-8
"""
@Author: Robby
@Module name: playbook.py
@Create date: 2020-12-28
@Function: 
"""

from django import forms

class PlaybookCreateForm(forms.Form):

    ips = forms.CharField(required=True, error_messages={'required': '字段不能为空'})
    task_id = forms.CharField(required=True, error_messages={'required': '字段不能为空'})
    task_name = forms.CharField(required=True, error_messages={'required': '字段不能为空'})
    playbook_content = forms.CharField(required=True, error_messages={'required': '字段不能为空'})
    playbook_name = forms.CharField(required=True, error_messages={'required': '字段不能为空'})
    task_type = forms.CharField(required=True, error_messages={'required': '字段不能为空'})

class PlaybookListForm(forms.Form):

    ips = forms.CharField(required=True, error_messages={'required': '字段不能为空'})