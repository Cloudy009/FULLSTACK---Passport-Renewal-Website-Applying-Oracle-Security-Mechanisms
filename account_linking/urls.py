from django.urls import path
from account_linking import views

urlpatterns = [
    path('some_path/', views.some_view, name='some_name'),
]
