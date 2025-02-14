from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello, Misel Ica Dien Arshad!")
