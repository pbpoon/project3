# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/21 15:46'
from django import forms

class AddExcelForm(forms.Form):
    file = forms.FileField(label='上传文件')