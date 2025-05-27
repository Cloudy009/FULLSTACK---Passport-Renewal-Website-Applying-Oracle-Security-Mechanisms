# accounts/forms.py
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class PassportForm(forms.Form):
    full_name = forms.CharField(
        max_length=100, 
        label="Họ và tên", 
        required=True,
        error_messages={'required': 'Họ và tên là bắt buộc.'}  # Thông báo lỗi tùy chỉnh
    )
    address = forms.CharField(
        max_length=255, 
        label="Địa chỉ thường trú", 
        required=True,
        error_messages={'required': 'Địa chỉ là bắt buộc.'}  # Thông báo lỗi tùy chỉnh
    )
    gender = forms.ChoiceField(
        choices=[('M', 'Nam'), ('F', 'Nữ')], 
        label="Phái", 
        required=True,
        error_messages={'required': 'Vui lòng chọn phái.'}  # Thông báo lỗi tùy chỉnh
    )
    cccd = forms.CharField(
        max_length=20, 
        label="Số CMND", 
        required=True,
        error_messages={'required': 'Số CMND là bắt buộc.'}  # Thông báo lỗi tùy chỉnh
    )
    phone_number = forms.CharField(
        max_length=15, 
        label="Số điện thoại", 
        required=True,
        error_messages={'required': 'Số điện thoại là bắt buộc.'}  # Thông báo lỗi tùy chỉnh
    )
    email = forms.EmailField(
        max_length=100, 
        label="Email", 
        required=True,
        error_messages={'required': 'Email là bắt buộc.', 'invalid': 'Email không hợp lệ.'}  # Thông báo lỗi tùy chỉnh
    )
    current_passport_number = forms.CharField(
        max_length=20, 
        label="Mã số hộ chiếu hiện tại", 
        required=True,
        error_messages={'required': 'Mã số hộ chiếu là bắt buộc.'}  # Thông báo lỗi tùy chỉnh
    )
