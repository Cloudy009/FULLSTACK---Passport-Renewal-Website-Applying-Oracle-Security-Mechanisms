from django.urls import path
from passport import views

urlpatterns = [
    path('', views.home, name='index'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
    path('mission', views.mission, name='mission'),
    path('news', views.news, name='news'),
    path('register', views.register, name='register'),
    path('add_register', views.register_passport, name='register_passport'),
    
    path('cost', views.donate, name='donate'),
    path('thongbao', views.thongbao, name='thong_bao'),
    path('tracuu', views.tra_cuu, name='tra_cuu'),
]