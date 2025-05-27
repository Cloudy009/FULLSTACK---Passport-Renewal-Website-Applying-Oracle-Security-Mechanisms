from django.shortcuts import redirect, render

from django.http import HttpResponse

from django.contrib import messages

from passport.forms import PassportRequestForm
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, DatabaseError
import logging

from passport.models import PassportRequest, RequestHistory

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        user = request.user

        # Lấy các PassportRequest của người dùng
        passport_requests = PassportRequest.objects.filter(user=user)

        # Biến để kiểm tra xem có thông báo nào chưa xem không
        has_news = False
        news = []

        for passport_request in passport_requests:
            # Lấy các bản ghi lịch sử cho verified_status và approved_status
            history_records = RequestHistory.objects.filter(
                passport_id=passport_request
            ).filter(status__in=['verified_status', 'approved_status']).order_by('-created_at')

            # Kiểm tra xem có bất kỳ bản ghi nào có user_viewed = 0
            for record in history_records:
                if record.user_viewed == 0:
                    has_news = True
                    news.append({
                        'history_id': record.history_id,
                        'passport_id': passport_request.passport_id,
                        'status': record.status,
                        'value': record.value,
                        'created_at': record.created_at.isoformat(), 
                        'has_news': True
                    })
                    break  # Nếu đã tìm thấy 1 bản ghi chưa xem, dừng kiểm tra

        # Debug: Xuất ra dữ liệu của news
        print("News:", news)  # Xuất ra console

        # Lưu thông tin has_news và news vào session
        request.session['has_news'] = has_news
        request.session['news'] = news

        context = {
            'news': news,
            'has_news': has_news
        }
    else:
        print("User is not authenticated.")
        context = {}
        print(context)

    return render(request, 'page/home.html', context)


def register(request):

    return render(request, 'page/register.html')

# Thiết lập logger
logger = logging.getLogger(__name__)

@login_required
def register_passport(request):
    if request.method == 'POST':
        form = PassportRequestForm(request.POST)
        
        if form.is_valid():
            try:
                # Gọi hàm kiểm tra trùng current_passport_number và verified_status là NULL
                passport_request = form.save(commit=False)
                if check_existing_passport_request(passport_request.current_passport_number, request.user.id):
                    # Nếu có dữ liệu trùng, thông báo lỗi
                    messages.error(request, f'Đã có hồ sơ với mã hộ chiếu {passport_request.current_passport_number} chưa được xác minh.')
                    return render(request, 'page/register.html', {'form': form})

                # Gán user hiện tại vào trường 'user' trước khi lưu
                passport_request.user = request.user  # Gán user vào trường 'user'
                passport_request.save()  # Lưu đối tượng với user đã được gán

                # Lấy ID của đối tượng vừa được tạo
                passport_id = passport_request.passport_id

                # Thêm thông báo thành công cùng với mã số ID
                messages.success(request, f'Đăng ký gia hạn hộ chiếu thành công! Mã số hồ sơ: {passport_id}')
                return redirect('register')

            except IntegrityError as e:
                # Ghi lỗi ra log và không hiển thị trên UI
                logger.error(f'IntegrityError: {str(e)}')
                return render(request, 'page/register.html', {'form': form})

            except DatabaseError as e:
                # Ghi lỗi cơ sở dữ liệu ra log và không hiển thị trên UI
                logger.error(f'DatabaseError: {str(e)}')
                return render(request, 'page/register.html', {'form': form})

            except Exception as e:
                # Ghi tất cả các lỗi khác ra log và không hiển thị trên UI
                logger.error(f'Exception: {str(e)}')
                return render(request, 'page/register.html', {'form': form})
        else:
            # Nếu form không hợp lệ, hiển thị thông báo lỗi
            messages.error(request, 'Đã có lỗi xảy ra, vui lòng kiểm tra lại thông tin.')
            return render(request, 'page/register.html', {'form': form})

    else:
        form = PassportRequestForm()
        return render(request, 'page/register.html', {'form': form})

# Hàm kiểm tra xem có dữ liệu trùng current_passport_number và verified_status = NULL không
def check_existing_passport_request(current_passport_number, user_id):
    # Kiểm tra trong PassportRequest nếu đã có dòng dữ liệu nào với current_passport_number trùng và verified_status là NULL
    existing_requests = PassportRequest.objects.filter(current_passport_number=current_passport_number, user_id=user_id, verified_status__isnull=True)
    return existing_requests.exists()  # Trả về True/False nếu có dòng dữ liệu trùng





def about(request):
    return render(request, 'page/about.html')

def donate(request):
    return render(request, 'page/donate.html')

def news(request):
    return render(request, 'page/news.html')

def mission(request):
    return render(request, 'page/mission.html')

def contact(request):
    return render(request, 'page/contact.html')

def thongbao(request):
    # Kiểm tra xem người dùng đã đăng nhập chưa
    if not request.user.is_authenticated:
        return redirect('login')  # Chuyển hướng đến trang đăng nhập nếu chưa đăng nhập

    # Lấy danh sách các thông báo từ session 'news'
    news = request.session.get('news', [])

    if not news:
        # Nếu không có thông báo, trả về trang trống hoặc thông báo không có dữ liệu
        return render(request, 'page/thongbao.html', {'display_data': []})

    # Xác định các status_name và value_name để tránh việc kiểm tra nhiều lần trong vòng lặp
    status_mapping = {
        'verified_status': 'Xác thực',
        'approved_status': 'Xét duyệt'
    }
    value_mapping = {
        '1': 'Đã xác nhận',
        '0': 'Thất bại'
    }

    # Chuẩn bị dữ liệu hiển thị
    display_data = []
    history_ids = []  # Lưu danh sách history_id để cập nhật sau

    for item in news:
        # Lấy status_name từ mapping hoặc mặc định 'Chưa xác định'
        status_name = status_mapping.get(item.get('status'), 'Chưa xác định')

        # Lấy value_name từ mapping hoặc mặc định 'Đang tiến hành'
        value_name = value_mapping.get(item.get('value'), 'Đang tiến hành')

        # Chuẩn bị dữ liệu cho từng thông báo
        display_data.append({
            'passport_id': item.get('passport_id'),
            'status': status_name,
            'value': value_name,
            'created_at': item.get('created_at')
        })

        # Thêm history_id vào danh sách để cập nhật
        history_ids.append(item.get('history_id'))

    # Cập nhật cột 'user_viewed' trong RequestHistory cho tất cả các history_id theo từng batch
    if history_ids:
        # Chia danh sách history_ids thành các batch để cập nhật
        batch_size = 100  # Số lượng bản ghi mỗi lần cập nhật
        for i in range(0, len(history_ids), batch_size):
            batch_ids = history_ids[i:i + batch_size]
            # Cập nhật 'user_viewed' thành True cho tất cả các history_id trong batch
            RequestHistory.objects.filter(history_id__in=batch_ids).update(user_viewed=True)

    request.session['old_news'] = news

    # Xóa session liên quan
    request.session.pop('has_news', None)
    request.session.pop('news', None)

    # Trả về dữ liệu cho giao diện
    return render(request, 'page/thongbao.html', {
        'display_data': display_data
    })

from django.shortcuts import render
from .models import PassportRequest

def tra_cuu(request):
    # Lấy tham số tìm kiếm từ request
    search_value = request.GET.get('search_value', '').strip()
    search_type = request.GET.get('search_type', 'SELECT')  # Lựa chọn mặc định là 'ALL'

    # Lấy danh sách passport_id từ session (nếu có)
    news_passport_ids = [news_item['passport_id'] for news_item in request.session.get('old_news', [])]

    passport_requests = PassportRequest.objects.all()

    if search_type == 'SELECT':
        passport_requests = []
    else:

    # Tùy thuộc vào lựa chọn trong dropdown, lọc theo trường tương ứng
        if search_type == 'Passport ID' and search_value:
            try:
                passport_requests = passport_requests.filter(passport_id=int(search_value))
            except ValueError:
                passport_requests = passport_requests  # Không thay đổi nếu không hợp lệ

        elif search_type == 'CCCD' and search_value:
            passport_requests = passport_requests.filter(cccd=search_value)

        elif search_type == 'Current Passport Number' and search_value:
            passport_requests = passport_requests.filter(current_passport_number=search_value)

    # Hàm để lấy label cho trạng thái
    def get_status_label(status):
        if status == 0:
            return "THẤT BẠI"
        elif status == 1:
            return "THÀNH CÔNG"
        else:
            return "đang tiến hành"

    # Xử lý các yêu cầu tìm kiếm và trả về dữ liệu
    processed_requests = []
    for request_obj in passport_requests:
        request_data = {
            'passport_id': request_obj.passport_id,
            'full_name': request_obj.full_name,
            'address': request_obj.address,
            'verified_status': get_status_label(request_obj.verified_status),
            'approved_status': get_status_label(request_obj.approved_status),
            # Kiểm tra passport_id có trong session không, nếu có thì đánh dấu là "new"
            'new': 'new' if request_obj.passport_id in news_passport_ids else ''
        }
        processed_requests.append(request_data)

    return render(request, 'page/tra_cuu.html', {
        'passport_requests': processed_requests,
        'search_value': search_value,
        'search_type': search_type  # Truyền giá trị search_type vào context
    })

