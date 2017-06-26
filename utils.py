# _*_ coding:utf-8 _*_
__author__ = 'pb'
__date__ = '2017/6/21 15:46'
from django import forms
import re


def str_to_list(str):
    s, *t, r = re.split(r'[\[,\]]', str)
    if not t:
        return None
    if s:
        t.append(s.split('[')[1])
    if r:
        t.append(r.split(']')[0])
    return t


class AddExcelForm(forms.Form):
    file = forms.FileField(label='上传文件')
