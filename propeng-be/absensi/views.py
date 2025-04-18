from django.http import JsonResponse
from django.shortcuts import render
from .models import *
from kelas.models import *
from user.models import Student
from rest_framework.decorators import api_view, permission_classes
import re
from rest_framework.permissions import IsAuthenticated, BasePermission
# Create your views here.

