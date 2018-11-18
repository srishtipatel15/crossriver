from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('gettotalloan/', views.get_amount_applied_for, name='gettotalloan'),
    path('getgrade/', views.get_grade, name='getgrade'),
    path('getvolume/', views.get_volume, name='getvolume'),
]

