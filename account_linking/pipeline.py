from django.contrib.auth import get_user_model
from social_django.models import UserSocialAuth
from social_core.exceptions import AuthAlreadyAssociated


def get_or_create_user(strategy, details, backend, *args, **kwargs):
    """
    Kiểm tra xem người dùng đã tồn tại chưa, nếu chưa thì tạo mới.
    Nếu người dùng đã tồn tại thì ánh xạ và cập nhật thông tin nếu cần.
    """
    email = details.get('email')  # Lấy email từ thông tin xã hội
    if email:
        User = strategy.storage.user.user_model()  # Model User cấu hình trong AUTH_USER_MODEL

        try:
            # Kiểm tra người dùng dựa trên email
            user = User.objects.get(email=email)

            # Kiểm tra nếu tài khoản xã hội đã được liên kết với người dùng này
            if UserSocialAuth.objects.filter(user=user, provider=backend.name).exists():
                return {'user': user}  # Trả về người dùng đã được liên kết

            # Nếu tài khoản xã hội chưa liên kết, thực hiện ánh xạ
            if not user.username:  # Gán username từ email nếu trống
                user.username = details.get('username', email.split('@')[0])

            if not user.first_name:  # Cập nhật họ và tên nếu chưa có
                user.first_name = details.get('first_name', '')
            if not user.last_name:
                user.last_name = details.get('last_name', '')

            user.save()  # Lưu lại người dùng sau khi cập nhật
            return {'user': user}

        except User.DoesNotExist:
            # Tạo người dùng mới nếu chưa tồn tại
            username = details.get('username', email.split('@')[0])

            # Xử lý tránh trùng lặp username
            i = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}_{i}"
                i += 1

            # Tạo user mới
            user = User.objects.create(
                username=username,
                email=email,
                first_name=details.get('first_name', ''),
                last_name=details.get('last_name', ''),
            )
            return {'user': user}

    # Trường hợp không có email, trả về rỗng (có thể tùy chỉnh thêm logic ở đây)
    return {}
