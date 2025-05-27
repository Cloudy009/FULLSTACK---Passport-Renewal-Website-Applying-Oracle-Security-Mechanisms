from django.test import TestCase

# Create your tests here.
from passport.models import PassportRequest
from django.contrib.auth.models import User  # Nếu bạn sử dụng model User mặc định của Django

# Tìm user bằng ID hoặc username
user = User.objects.get(id=1)  # Giả sử user có ID = 1

# Tạo đối tượng PassportRequest mới
passport_request = PassportRequest(
    full_name="Nguyễn Thi Mai",
    address="123 Phường ABC, Quận 1, TP.HCM 123456789",
    gender="Female",
    cccd="123456789",
    phone_number="0123456789",
    email="mai@example.com",
    current_passport_number="A1265465467",
    user=user  # Liên kết với user có ID = 1
)

# Lưu đối tượng vào cơ sở dữ liệu
passport_request.save()
# from passport.models import PassportRequest  # Import mô hình PassportRequest

# PassportRequest.objects.all().delete()  # Xóa tất cả đối tượng trong bảng



