# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='staff_dashboard'),  # Trang chính sau khi đăng nhập
    path('staff_login/', views.login_view, name='staff_login'),
    path('add/', views.add_data, name='add_data'),
    path('delete_employee/', views.delete_employee, name='delete_employee'),  # Thêm đường dẫn xóa
    path('update_approved_status/', views.update_approved_status, name='update_approved_status'),
    path('update_verified_status/', views.update_verified_status, name='update_verified_status'),

    path('update_passport/<int:passport_id>/', views.update_passport, name='update_passport'),
    path('history/', views.history, name='history'),
    path('cudan/', views.resident, name='resident'),
    path('logout/', views.logout_view, name='staff_logout'),
    path('delete_resident/', views.delete_resident, name='delete_resident'),
    path('update_resident/<int:resident_id>/', views.update_resident, name='update_resident'),
    path('resident_passport/', views.resident_passport, name='resident_passport'),
    path('update-expiry-date/<int:passport_id>/', views.update_expiry_date, name='update_expiry_date'),
    path('delete_resident_passport/', views.delete_resident_passport, name='delete_resident_passport'),
    path('update_resident_passport/<int:passport_id>/', views.update_resident_passport, name='update_resident_passport'),
    path('request_history/', views.request_history, name='request_history'),
    path('delete_request_history/', views.delete_request_history, name='delete_request_history'),
    path('update_request_history/<int:history_id>/', views.update_request_history, name='update_request_history'),
]
