from django.db import models
from django.contrib.auth.models import User

class PassportRequest(models.Model):
    passport_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, null=True, blank=True)
    cccd = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    email = models.CharField(max_length=100)
    current_passport_number = models.CharField(max_length=20)
    verified_status = models.IntegerField(null=True, blank=True)  # Cho phép NULL
    approved_status = models.IntegerField(null=True, blank=True)  # Cho phép NULL
    user_viewed = models.IntegerField(default=0)  # Cột mới với giá trị mặc định là 0
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    detail = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'PASSPORT_REQUEST'

class RequestHistory(models.Model):
    history_id = models.AutoField(primary_key=True)  # Tạo trường AutoField cho ID tự động tăng
    passport = models.ForeignKey(PassportRequest, on_delete=models.CASCADE)  # Liên kết với bảng PASSPORT_REQUEST
    status = models.CharField(max_length=50)
    value = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Thời gian tự động được thiết lập khi tạo
    updated_at = models.DateTimeField(auto_now=True)  # Thời gian tự động được thiết lập khi cập nhật
    user_viewed = models.BooleanField(default=False)  # 0: False, 1: True
    detail = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['history_id']),  # Chỉ mục cho trường 'history_id'
            models.Index(fields=['passport_id']),  # Chỉ mục cho trường 'passport_id'
            models.Index(fields=['user_viewed']),  # Chỉ mục cho trường 'user_viewed'
        ]
        db_table = 'REQUEST_HISTORY'  # Tên bảng trong cơ sở dữ liệu

class PassportRejection(models.Model):
    reason_id = models.AutoField(primary_key=True)
    passport = models.ForeignKey(PassportRequest, on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'PASSPORT_REJECTION'

class Resident(models.Model):
    resident_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, null=True, blank=True)
    cccd = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    email = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = 'RESIDENT'

class Passport(models.Model):
    passport_id = models.AutoField(primary_key=True)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    passport_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateField(null=True, blank=True)
    reported_date = models.DateField(null=True, blank=True)
    status = models.IntegerField(default=1)
    status_detail = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'PASSPORT'
