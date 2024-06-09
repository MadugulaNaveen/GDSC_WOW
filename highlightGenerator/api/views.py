from django.http import JsonResponse
from django.shortcuts import render
import json


def index(request):
  return render(request,"index.html",{"show":"hidden","hide":'show'})


def getHighlights(request):
  return render(request,"index.html",{"show":"show","hide":'hidden'})