from django.urls import path
from . import views

urlpatterns = [
  path('',views.index,name='index'),
  path('getHighlights',views.getHighlights,name='getHighlights'),
  path('index',views.index,name="index"),
]