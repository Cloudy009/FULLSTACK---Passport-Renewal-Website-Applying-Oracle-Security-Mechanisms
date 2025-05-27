import datetime
import cx_Oracle
from django import forms
from django.shortcuts import render, redirect
from django.conf import settings
from dashboard.forms import LoginForm, PassportForm

# Hàm xác thực người dùng với Oracle
def authenticate_oracle_user(username, password):
    try:
        # Cố gắng kết nối đến Oracle với thông tin đăng nhập người dùng
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')  # Cấu hình địa chỉ Oracle nếu cần
        connection.close()  # Nếu kết nối thành công thì đóng kết nối
        return True
    except cx_Oracle.DatabaseError as e:
        # Nếu kết nối thất bại, tức là thông tin đăng nhập không hợp lệ
        
        return False

# View để xử lý logout
def logout_view(request):
    # Xóa thông tin đăng nhập khỏi session
    request.session.flush()
    messages.success(request, "Bạn đã đăng xuất thành công.")
    return redirect('staff_login')  # Chuyển hướng về trang login


def login_view(request):
    # Xóa hết session cũ nếu có
    request.session.flush()

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Kiểm tra xác thực thông qua Oracle
            if authenticate_oracle_user(username, password):
                # Nếu đăng nhập thành công, lưu tên người dùng vào session
                request.session['oracle_username'] = username
                request.session['oracle_password'] = password
                return redirect('staff_dashboard')  # Chuyển hướng đến trang chính sau khi đăng nhập thành công
            else:
                # Nếu đăng nhập không thành công
                form.add_error(None, 'Thông tin đăng nhập không hợp lệ.')
    else:
        form = LoginForm()

    return render(request, 'management/management_login.html', {'form': form})
from django.contrib import messages
from django.core.paginator import Paginator



def get_user_roles(cursor, username, allowed_roles):
    # Truy vấn lấy nhóm quyền của người dùng với danh sách role linh hoạt
    roles_query = """
        SELECT granted_role 
        FROM user_role_privs 
        WHERE USERNAME = :username
        AND granted_role IN ({})
    """.format(', '.join([f"'{role}'" for role in allowed_roles]))  # Sử dụng format để chèn role vào câu truy vấn

    cursor.execute(roles_query, {'username': username})
    return [row[0] for row in cursor.fetchall()]

def get_role_privileges(cursor, roles):
    # Truy vấn để lấy quyền từ SYS.ALL_ROLES_VIEW
    role_placeholders = ', '.join([f":role{i}" for i in range(len(roles))])
    get_content = f"""
        SELECT COLUMN_NAME, PRIVILEGE
        FROM SYS.ALL_ROLES_VIEW
        WHERE TABLE_NAME = 'PASSPORT' 
        AND ROLE_NAME IN ({role_placeholders})
    """

    cursor.execute(get_content, {f'role{i}': role for i, role in enumerate(roles)})
    result = cursor.fetchall()

    # Chuyển đổi kết quả thành dictionary
    return {column_name: privilege for column_name, privilege in result}

# Hàm lấy thông tin đăng nhập từ session
def get_login_info(request):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')
    if not username or not password:
        return None, None
    return username, password

# Hàm xây dựng câu lệnh SQL cho loại tìm kiếm
def build_search_query(search_query, search_type):
    if search_type == 'passport_id':
        query = """
            SELECT * FROM chivy_Admin.PASSPORT_REQUEST
            WHERE passport_id = :search_query
        """
    elif search_type == 'cccd':
        query = """
            SELECT * FROM chivy_Admin.PASSPORT_REQUEST
            WHERE LOWER(cccd) LIKE LOWER(:search_query)
        """
        search_query = '%' + search_query + '%'
    elif search_type == 'current_passport_number':
        query = """
            SELECT * FROM chivy_Admin.PASSPORT_REQUEST
            WHERE LOWER(current_passport_number) LIKE LOWER(:search_query)
        """
        search_query = '%' + search_query + '%'
    elif search_type == 'full_name':
        query = """
            SELECT * FROM chivy_Admin.PASSPORT_REQUEST
            WHERE LOWER(full_name) LIKE LOWER(:search_query)
        """
        # Thêm dấu '%' vào query để tìm kiếm tên có chứa search_query
        search_query = '%' + search_query + '%'
    return query, search_query 

# Hàm kết nối Oracle và truy vấn dữ liệu
def get_passport_data(cursor, search_query, search_type, sort_by, sort_order ):
    # Xây dựng câu lệnh truy vấn động theo loại tìm kiếm
    if search_query:
        query,search_query = build_search_query(search_query, search_type)
        query += f" ORDER BY {sort_by} {sort_order}"
        cursor.execute(query, {'search_query': search_query})
    else:
        query = "SELECT * FROM chivy_Admin.PASSPORT_REQUEST"
        query += f" ORDER BY {sort_by} {sort_order}"

        cursor.execute(query)
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

# Hàm phân trang
def paginate_data(employees, page_number):
    paginator = Paginator(employees, 10)  # 10 passport mỗi trang
    return paginator.get_page(page_number)

# Hàm chính xử lý trang chủ
def dashboard(request):
    # Lấy thông tin đăng nhập từ session
    username, password = get_login_info(request)
    if not username or not password:
        return redirect('staff_login')  # Nếu chưa đăng nhập thì yêu cầu đăng nhập

    # Lấy giá trị tìm kiếm và loại tìm kiếm từ query parameters (nếu có)
    search_query = request.GET.get('search_query', '').strip()
    search_type = request.GET.get('search_type', 'passport_id')  # Mặc định là tìm theo employee_id

    # Lấy tham số sắp xếp (cột và thứ tự)
    sort_by = request.GET.get('sort_by', 'passport_id')  # Cột mặc định là 'passport_id'
    sort_order = request.GET.get('sort_order', 'asc')  # Thứ tự mặc định là 'asc' (tăng dần)

    # Đảm bảo giá trị hợp lệ cho sort_order
    if sort_order not in ['asc', 'desc']:
        sort_order = 'asc'

    employees = []
    column_names = []
    try:
        # Tạo kết nối Oracle và truy vấn dữ liệu
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()

        # allowed_roles = ['XT', 'XD', 'LT', 'GS']  # Danh sách role cho phép
        # roles = get_user_roles(cursor, username, allowed_roles)
        # role_privileges = get_role_privileges(cursor, roles)
        
        # Lấy dữ liệu từ Oracle
        employees, column_names = get_passport_data(cursor, search_query, search_type, sort_by, sort_order )
        print(column_names)
        connection.close()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        if error.code == 20001:  # Lỗi tùy chỉnh từ trigger
            reply = error.message.splitlines()[0].strip()
            print(reply)
            messages.error(request, f"Có lỗi xảy ra: {reply.split(':')[1].strip()}")  # Lấy phần thông báo lỗi tùy chỉnh
        else:  # Lỗi khác
            messages.error(request, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.")

    # Phân trang
    page_number = request.GET.get('page')  # Lấy số trang từ URL (nếu có)
    page_obj = paginate_data(employees, page_number)

    # Loại bỏ dấu '%' để hiển thị trên giao diện
    if search_type != 'passport_id':
        search_query = search_query.strip('%')

    # Render trang chủ với dữ liệu phân trang
    return render(request, 'management/dashboard.html', {
        'page_obj': page_obj,
        'column_names': column_names,
        'search_query': search_query,  # Gửi query tìm kiếm về frontend
        'search_type': search_type,  # Gửi loại tìm kiếm về frontend
        # 'role_privileges': role_privileges,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })



def add_data(request):
    username, password = get_login_info(request)

    if not username or not password:
        return redirect('staff_login') 
    
    if request.method == 'POST':
        form = PassportForm(request.POST)
        print(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name']
            address = form.cleaned_data['address']
            gender = form.cleaned_data['gender']
            cccd = form.cleaned_data['cccd']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            current_passport_number = form.cleaned_data['current_passport_number']
            print(full_name)
            try:
                connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
                cursor = connection.cursor()

                insert_query = """
                    INSERT INTO Passport 
                    (full_name, address, gender, cccd, phone_number, email, current_passport_number)
                    VALUES (:full_name, :address, :gender, :cccd, :phone_number, :email, :current_passport_number)
                """

                cursor.execute(insert_query, {
                    'full_name': full_name,
                    'address': address,
                    'gender': gender,
                    'cccd': cccd,
                    'phone_number': phone_number,
                    'email': email,
                    'current_passport_number': current_passport_number
                })
                connection.commit()
                connection.close()

                messages.success(request, 'Passport đã được thêm thành công!')

            except cx_Oracle.DatabaseError as e:
                messages.error(request, 'Lỗi khi thêm passport: ' + str(e))

        else:
            # Hiển thị các lỗi form chi tiết
            for field in form:
                if field.errors:
                    for error in field.errors:
                        messages.error(request, f"Lỗi tại trường '{field.label}': {error}")

    else:
        form = PassportForm()

    
    # Truyền lại dữ liệu form vào context
    return render(request, 'management/add_passport.html', {'form': form})


# View xử lý xóa passport
def delete_employee(request):
    if request.method == 'POST':
        passport_id = request.POST.get('passport_id')

        username = request.session.get('oracle_username')
        password = request.session.get('oracle_password')
        
        if not username or not password:
            return redirect('staff_login')  # Nếu chưa đăng nhập thì yêu cầu đăng nhập
        try:
            # Kết nối Oracle và xóa passport
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()
            delete_query = "DELETE FROM chivy_Admin.PASSPORT_REQUEST WHERE passport_id = :passport_id"
            cursor.execute(delete_query, {'passport_id': passport_id})
            connection.commit()  # Commit để lưu thay đổi
            connection.close()

            messages.success(request, 'Xóa đơn thành công!')
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 20001:  # Lỗi tùy chỉnh từ trigger
                reply = error.message.splitlines()[0].strip()
                messages.error(request, f"Có lỗi xảy ra: {reply.split(':')[1].strip()}") 
            else:  # Lỗi khác
                messages.error(request, "No Delete Permission")

    return redirect('staff_dashboard')  # Quay lại trang chính sau khi xóa thành công

from django.views.decorators.csrf import csrf_exempt

def update_approved_status(request):
    if request.method == 'POST':
        passport_id = request.POST.get('passport_id')
        status_approved = request.POST.get('status_approved')

        username = request.session.get('oracle_username')
        password = request.session.get('oracle_password')

        if not username or not password:
            return redirect('staff_login')  # If not logged in, redirect to login page

        try:
            # Kết nối đến cơ sở dữ liệu Oracle
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()

            # Truy vấn để lấy dữ liệu passport
            query = "SELECT * FROM chivy_Admin.PASSPORT_REQUEST WHERE passport_id = :passport_id"
            cursor.execute(query, {'passport_id': passport_id})
            passport_data = cursor.fetchone()

            if passport_data:
                # Cập nhật trạng thái Xác nhận (approved)
                if status_approved == 'NULL' or status_approved is None:
                    new_approved_status = None
                else:
                    new_approved_status = int(status_approved)

                # Cập nhật vào cơ sở dữ liệu
                update_query = """
                    UPDATE chivy_Admin.PASSPORT_REQUEST
                    SET APPROVED_STATUS = :approved_status
                    WHERE passport_id = :passport_id
                """
                cursor.execute(update_query, {
                    'approved_status': new_approved_status,
                    'passport_id': passport_id
                })

                # Commit để lưu các thay đổi
                connection.commit()
                messages.success(request, f'Passport_id: {passport_id} đã cập nhật trạng thái Xác nhận thành công!')

            else:
                messages.error(request, f'Passport_id {passport_id} không tồn tại!')

            connection.close()

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 20001:  # Lỗi tùy chỉnh từ trigger
                reply = error.message.splitlines()[0].strip()
                messages.error(request, f"Có lỗi xảy ra: {reply.split(':')[1].strip()}")      
            else:
                messages.error(request, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.")

    return redirect('staff_dashboard')  # Redirect to dashboard page after processing

def update_verified_status(request):
    if request.method == 'POST':
        passport_id = request.POST.get('passport_id')
        status_verified = request.POST.get('status_verified')

        username = request.session.get('oracle_username')
        password = request.session.get('oracle_password')

        if not username or not password:
            return redirect('staff_login')  # If not logged in, redirect to login page

        try:
            # Kết nối đến cơ sở dữ liệu Oracle
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()

            # Truy vấn để lấy dữ liệu passport
            query = "SELECT * FROM chivy_Admin.PASSPORT_REQUEST WHERE passport_id = :passport_id"
            cursor.execute(query, {'passport_id': passport_id})
            passport_data = cursor.fetchone()

            if passport_data:
                # Cập nhật trạng thái Đã xác thực (verified)
                if status_verified == 'NULL' or status_verified is None:
                    new_verified_status = None
                else:
                    new_verified_status = int(status_verified)

                # Cập nhật vào cơ sở dữ liệu
                update_query = """
                    UPDATE chivy_Admin.PASSPORT_REQUEST
                    SET VERIFIED_STATUS = :verified_status
                    WHERE passport_id = :passport_id
                """
                cursor.execute(update_query, {
                    'verified_status': new_verified_status,
                    'passport_id': passport_id
                })

                # Commit để lưu các thay đổi
                connection.commit()
                messages.success(request, f'Passport_id: {passport_id} đã cập nhật trạng thái Xác thực thành công!')

            else:
                messages.error(request, f'Passport_id {passport_id} không tồn tại!')

            connection.close()

        except cx_Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 20001:  # Lỗi tùy chỉnh từ trigger
                reply = error.message.splitlines()[0].strip()
                messages.error(request, f"Có lỗi xảy ra: {reply.split(':')[1].strip()}")      
            else:
                messages.error(request, "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.")

    return redirect('staff_dashboard') 

def update_passport(request, passport_id):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')

    if not username or not password:
        return redirect('staff_login')  # Nếu chưa đăng nhập thì yêu cầu đăng nhập

    try:
        # Kết nối Oracle một lần duy nhất
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()

        # Truy vấn passport theo passport_id
        select_query = "SELECT * FROM chivy_Admin.PASSPORT_REQUEST WHERE passport_id = :passport_id"
        cursor.execute(select_query, {'passport_id': passport_id})
        passport = cursor.fetchone()

        # Nếu không tìm thấy passport, redirect về trang dashboard
        if not passport:
            messages.error(request, 'Không tìm thấy passport.')
            return redirect('staff_dashboard')

        # Nếu là POST request, xử lý cập nhật
        if request.method == 'POST':
            full_name = request.POST.get('full_name')
            address = request.POST.get('address')
            gender = request.POST.get('gender')
            cccd = request.POST.get('cccd')
            phone_number = request.POST.get('phone_number')
            email = request.POST.get('email')
            current_passport_number = request.POST.get('current_passport_number')
            verified_status = request.POST.get('verified_status')
            approved_status = request.POST.get('approved_status')
            detail = request.POST.get('detail')
            user_viewed = request.POST.get('user_viewed')
            
            # Xử lý giá trị NULL để phù hợp với kiểu dữ liệu trong cơ sở dữ liệu
            verified_status = None if verified_status == 'NULL' else int(verified_status)
            approved_status = None if approved_status == 'NULL' else int(approved_status)
            user_viewed = None if user_viewed == 'NULL' else int(user_viewed)
            print('user_viewed',user_viewed)
            # Kiểm tra nếu tất cả các trường cần thiết đã có dữ liệu
            if not all([full_name, address, cccd, phone_number, email, current_passport_number]):
                messages.error(request, 'Vui lòng điền đầy đủ thông tin yêu cầu.')
                return render(request, 'management/update_passport.html', {'passport': passport})

            # Cập nhật passport, bỏ qua passport_id và user_id
            update_query = """
            UPDATE chivy_Admin.PASSPORT_REQUEST
            SET full_name = :full_name, address = :address, gender = :gender, cccd = :cccd,
                phone_number = :phone_number, email = :email, current_passport_number = :current_passport_number,
                verified_status = :verified_status, approved_status = :approved_status, detail = :detail,
                user_viewed = :user_viewed, updated_at = CURRENT_TIMESTAMP
            WHERE passport_id = :passport_id
            """
            cursor.execute(update_query, {
                'full_name': full_name,
                'address': address,
                'gender': gender,
                'cccd': cccd,
                'phone_number': phone_number,
                'email': email,
                'current_passport_number': current_passport_number,
                'verified_status': verified_status,
                'approved_status': approved_status,
                'detail': detail,
                'user_viewed': user_viewed,
                'passport_id': passport_id
            })
            connection.commit()

            messages.success(request, 'Cập nhật thông tin passport thành công!')
            return redirect('update_passport', passport_id=passport_id)  # Quay lại trang cập nhật sau khi thành công

        # Trả về template update_passport với dữ liệu passport
        return render(request, 'management/update_passport.html', {'passport': passport})

    except cx_Oracle.DatabaseError as e:
        messages.error(request, f'Có lỗi xảy ra trong quá trình kết nối cơ sở dữ liệu: {e}')
        return redirect('staff_dashboard')  # Quay lại trang dashboard khi có lỗi
    finally:
        cursor.close()
        connection.close()  # Đảm bảo đóng kết nối sau khi sử dụng

# Hàm xây dựng câu lệnh SQL tìm kiếm cho bảng SYS.GS_PASSPORT_AUDIT
def build_audit_query(search_query, search_type):
    base_query = """
        SELECT USERNAME, TIMESTAMP, OWNER, OBJ_NAME, ACTION, CURRENT_USER
        FROM SYS.GS_PASSPORT_AUDIT
    """

    # Thêm điều kiện tìm kiếm dựa trên search_type
    if search_type == 'USERNAME':
        base_query += " WHERE LOWER(USERNAME) LIKE LOWER(:search_query)"
        search_query = f"%{search_query}%"
    elif search_type == 'ACTION':
        base_query += " WHERE LOWER(ACTION) LIKE LOWER(:search_query)"
        search_query = f"%{search_query}%"
    elif search_type == 'OBJ_NAME':
        base_query += " WHERE LOWER(OBJ_NAME) LIKE LOWER(:search_query)"
        search_query = f"%{search_query}%"

    return base_query, search_query

# Hàm lấy dữ liệu từ SYS.GS_PASSPORT_AUDIT
def get_audit_trail_data(cursor, search_query, search_type, sort_by, sort_order):
    # Xây dựng truy vấn
    query, search_query = build_audit_query(search_query, search_type)
    query += f" ORDER BY {sort_by} {sort_order}"

    cursor.execute(query, {'search_query': search_query})
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

# Phân trang
def paginate_data(data, page_number):
    paginator = Paginator(data, 10)  # 10 bản ghi mỗi trang
    return paginator.get_page(page_number)


def update_expiry_date(request, passport_id):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')

    if not username or not password:
        return redirect('staff_login')  # Yêu cầu đăng nhập nếu chưa đăng nhập

    if request.method == 'POST':
        expiry_date = request.POST.get('expiry_date')

        if expiry_date:
            try:
                expiry_date = datetime.datetime.strptime(expiry_date, '%Y-%m-%d')
            except ValueError:
                messages.error(request, "Ngày hết hạn không hợp lệ.")
                return redirect('resident_passport')  # Quay lại danh sách nếu lỗi

            try:
                # Kết nối Oracle và cập nhật ngày hết hạn
                connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
                cursor = connection.cursor()

                update_query = """
                    UPDATE CHIVY_ADMIN.PASSPORT
                    SET expiry_date = :expiry_date
                    WHERE passport_id = :passport_id
                """
                cursor.execute(update_query, {'expiry_date': expiry_date, 'passport_id': passport_id})
                connection.commit()
                connection.close()

                messages.success(request, f"Cập nhật ngày hết hạn thành công cho Passport ID {passport_id}.")
            except cx_Oracle.DatabaseError as e:
                error, = e.args
                messages.error(request, f"Lỗi khi cập nhật: {error}")
                return redirect('staff_dashboard')  # Quay lại trang chính nếu có lỗi

    return redirect('resident_passport')  # Quay lại danh sách sau khi xử lý


# View xử lý dữ liệu Audit Trail
def history(request):
    # Lấy thông tin đăng nhập từ session
    username, password = request.session.get('oracle_username'), request.session.get('oracle_password')
    if not username or not password:
        return redirect('login')

    # Lấy các tham số từ request
    search_query = request.GET.get('search_query', '').strip()
    search_type = request.GET.get('search_type', 'USERNAME')  # Mặc định tìm theo USERNAME
    sort_by = request.GET.get('sort_by', 'TIMESTAMP')  # Mặc định sắp xếp theo TIMESTAMP
    sort_order = request.GET.get('sort_order', 'desc')  # Mặc định giảm dần

    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'

    data, column_names = [], []
    try:
        # Kết nối Oracle
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()

        # Lấy dữ liệu từ bảng SYS.GS_PASSPORT_AUDIT
        data, column_names = get_audit_trail_data(cursor, search_query, search_type, sort_by, sort_order)

        connection.close()
    except cx_Oracle.DatabaseError as e:
        messages.error(request, "Có lỗi xảy ra trong quá trình truy cập dữ liệu.")
        print(e)
        return redirect('staff_dashboard')

    # Phân trang
    page_number = request.GET.get('page', 1)
    page_obj = paginate_data(data, page_number)

    # Render template
    return render(request, 'management/history.html', {
        'page_obj': page_obj,
        'column_names': column_names,
        'search_query': search_query,
        'search_type': search_type,
        'sort_by': sort_by,
        'sort_order': sort_order,
    })


###RESIDENT
# Hàm xây dựng câu lệnh SQL tìm kiếm

def build_resident_search_query(search_query, search_type):
    if search_type == 'resident_id':
        query = """
            SELECT * FROM chivy_admin.RESIDENT
            WHERE resident_id = :search_query
        """
    elif search_type == 'cccd':
        query = """
            SELECT * FROM chivy_admin.RESIDENT
            WHERE LOWER(cccd) LIKE LOWER(:search_query)
        """
        search_query = f"%{search_query}%"
    elif search_type == 'full_name':
        query = """
            SELECT * FROM chivy_admin.RESIDENT
            WHERE LOWER(full_name) LIKE LOWER(:search_query)
        """
        search_query = f"%{search_query}%"
    else:
        query = """
            SELECT * FROM chivy_admin.RESIDENT
        """
    return query, search_query

def get_resident_data(cursor, search_query, search_type):
    if search_query and search_type != 'SELECT':
        query, search_query = build_resident_search_query(search_query, search_type)
        cursor.execute(query, {'search_query': search_query})
    else:
        query = "SELECT * FROM chivy_admin.RESIDENT"
        cursor.execute(query)
    return cursor.fetchall(), [desc[0] for desc in cursor.description]

def resident(request):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')
    if not username or not password:
        return redirect('login')

    search_query = request.GET.get('search_query', '').strip()
    search_type = request.GET.get('search_field', '')  # Chỉnh lại thành search_field
    data, column_names = [], []

    try:
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()
        data, column_names = get_resident_data(cursor, search_query, search_type)
        connection.close()
    except cx_Oracle.DatabaseError as e:
        messages.error(request, f"Có lỗi xảy ra: {e}")
        return redirect('resident')

    page_number = request.GET.get('page', 1)
    page_obj = paginate_data(data, page_number)

    return render(request, 'management/resident.html', {
        'page_obj': page_obj,
        'column_names': column_names,
        'search_query': search_query,
        'search_type': search_type,
    })

def delete_resident(request):    
    if request.method == 'POST':
        resident_id = request.POST.get('resident_id')

        username = request.session.get('oracle_username')
        password = request.session.get('oracle_password')
        
        if not username or not password:
            return redirect('staff_login')  # Nếu chưa đăng nhập thì yêu cầu đăng nhập
        try:
            # Kết nối Oracle và xóa passport
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()
            delete_query = "DELETE FROM chivy_Admin.RESIDENT WHERE resident_id = :resident_id"
            cursor.execute(delete_query, {'resident_id': resident_id})
            connection.commit()  # Commit để lưu thay đổi
            connection.close()

            messages.success(request, 'Xóa cư dân thành công!')
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 20001:  # Lỗi tùy chỉnh từ trigger
                reply = error.message.splitlines()[0].strip()
                messages.error(request, f"Có lỗi xảy ra: {reply.split(':')[1].strip()}") 
            else:  # Lỗi khác
                messages.error(request, "No Delete Permission")

    return redirect('resident')  # Quay lại trang chính sau khi xóa thành công



def update_resident(request, resident_id):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')

    if not username or not password:
        return redirect('staff_login')  # Nếu chưa đăng nhập thì yêu cầu đăng nhập

    try:
        # Kết nối Oracle và lấy thông tin cư dân
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()

        # Truy vấn cư dân theo resident_id
        select_query = "SELECT * FROM chivy_Admin.RESIDENT WHERE resident_id = :resident_id"
        cursor.execute(select_query, {'resident_id': resident_id})
        resident = cursor.fetchone()

        # Nếu không tìm thấy cư dân, redirect về trang dashboard
        if not resident:
            messages.error(request, 'Không tìm thấy cư dân.')
            return redirect('staff_dashboard')

        connection.close()

        # Nếu là POST request, xử lý cập nhật
        if request.method == 'POST':
            full_name = request.POST.get("full_name")
            address = request.POST.get("address")
            gender = request.POST.get("gender")
            cccd = request.POST.get("cccd")
            phone_number = request.POST.get("phone_number")
            email = request.POST.get("email")
            status = request.POST.get("status")
            
            # Nếu không chọn status, đặt giá trị NULL
            if status == '':
                status = None

            # Kết nối lại Oracle và cập nhật thông tin cư dân
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()

            update_query = """
                UPDATE chivy_admin.RESIDENT
                SET full_name = :full_name,
                    address = :address,
                    gender = :gender,
                    cccd = :cccd,
                    phone_number = :phone_number,
                    email = :email,
                    status = :status,
                    updated_at = CURRENT_TIMESTAMP
                WHERE resident_id = :resident_id
            """
            cursor.execute(update_query, {
                'full_name': full_name,
                'address': address,
                'gender': gender,
                'cccd': cccd,
                'phone_number': phone_number,
                'email': email,
                'status': status,
                'resident_id': resident_id
            })
            connection.commit()
            connection.close()

            messages.success(request, 'Cập nhật thông tin cư dân thành công!')
            return redirect('update_resident', resident_id=resident_id)

        if resident:
            resident_data = {
                'resident_id': resident[0],
                'full_name': resident[1],
                'address': resident[2],
                'gender': resident[3],
                'cccd': resident[4],
                'phone_number': resident[5],
                'email': resident[6],
                'created_at': resident[7],  # Lấy ngày tạo từ cơ sở dữ liệu
                'status': resident[9],  # Lấy status từ cơ sở dữ liệu
            }

        return render(request, 'management/update_resident.html', {'resident': resident_data})

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        messages.error(request, f"Có lỗi xảy ra: {error}")
        return redirect('update_resident', resident_id=resident_id)



def build_passport_search_query(search_query, search_type):
    if search_type == 'passport_id':
        query = """
            SELECT * FROM CHIVY_ADMIN.PASSPORT
            WHERE passport_id = :search_query
        """
    elif search_type == 'current_passport_code':
        query = """
            SELECT * FROM CHIVY_ADMIN.PASSPORT
            WHERE LOWER(current_passport_code) LIKE LOWER(:search_query)
        """
        search_query = f"%{search_query}%"
    elif search_type == 'resident_id':
        query = """
            SELECT * FROM CHIVY_ADMIN.PASSPORT
            WHERE resident_id = :search_query
        """
    else:
        query = """
            SELECT * FROM CHIVY_ADMIN.PASSPORT
        """
    return query, search_query


def resident_passport(request):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')
    if not username or not password:
        return redirect('staff_login')

    search_query = request.GET.get('search_query', '').strip()
    search_type = request.GET.get('search_field', '')  # Chỉnh lại thành search_field
    data, column_names = [], []

    try:
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()
        data, column_names = get_resident_passport_data(cursor, search_query, search_type)
        connection.close()
    except cx_Oracle.DatabaseError as e:
        messages.error(request, f"Có lỗi xảy ra: {e}")
        return redirect('resident_passport')

    page_number = request.GET.get('page', 1)
    page_obj = paginate_data(data, page_number)

    return render(request, 'management/resident_passport.html', {
        'page_obj': page_obj,
        'column_names': column_names,
        'search_query': search_query,
        'search_type': search_type,
    })


def get_resident_passport_data(cursor, search_query, search_type):
    if search_query and search_type != 'SELECT':
        query, search_query = build_passport_search_query(search_query, search_type)
        cursor.execute(query, {'search_query': search_query})
    else:
        query = "SELECT * FROM CHIVY_ADMIN.PASSPORT"
        cursor.execute(query)
    return cursor.fetchall(), [desc[0] for desc in cursor.description]


def delete_resident_passport(request):    
    if request.method == 'POST':
        passport_id = request.POST.get('passport_id')

        username = request.session.get('oracle_username')
        password = request.session.get('oracle_password')
        
        if not username or not password:
            return redirect('staff_login')  # Nếu chưa đăng nhập thì yêu cầu đăng nhập

        try:
            # Kết nối Oracle và xóa passport
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()
            delete_query = "DELETE FROM CHIVY_ADMIN.PASSPORT WHERE passport_id = :passport_id"
            cursor.execute(delete_query, {'passport_id': passport_id})
            connection.commit()  # Commit để lưu thay đổi
            connection.close()

            messages.success(request, 'Xóa passport thành công!')
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 20001:  # Lỗi tùy chỉnh từ trigger
                reply = error.message.splitlines()[0].strip()
                messages.error(request, f"Có lỗi xảy ra: {reply.split(':')[1].strip()}") 
            else:  # Lỗi khác
                messages.error(request, "No Delete Permission")

    return redirect('resident_passport')  # Quay lại trang chính sau khi xóa thành công


def update_resident_passport(request, passport_id):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')

    if not username or not password:
        return redirect('staff_login')  # Nếu chưa đăng nhập thì yêu cầu đăng nhập

    try:
        # Kết nối Oracle và lấy thông tin passport
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()

        # Truy vấn passport theo passport_id
        select_query = "SELECT * FROM CHIVY_ADMIN.PASSPORT WHERE passport_id = :passport_id"
        cursor.execute(select_query, {'passport_id': passport_id})
        passport = cursor.fetchone()

        # Nếu không tìm thấy passport, redirect về trang dashboard
        if not passport:
            messages.error(request, 'Không tìm thấy passport.')
            return redirect('staff_dashboard')

        connection.close()

        # Nếu là POST request, xử lý cập nhật
        if request.method == 'POST':
            passport_type = request.POST.get("passport_type")
            current_passport_code = request.POST.get("current_passport_code")
            expiry_date = request.POST.get("expiry_date")
            status = request.POST.get("status")
            status_detail = request.POST.get("status_detail")
            
            # Chuyển đổi expiry_date thành đối tượng datetime
            if expiry_date:
                try:
                    expiry_date = datetime.datetime.strptime(expiry_date, '%Y-%m-%d')  # Định dạng yyyy-mm-dd
                except ValueError:
                    messages.error(request, "Ngày hết hạn không hợp lệ. Định dạng phải là YYYY-MM-DD.")
                    return redirect('update_resident_passport', passport_id=passport_id)
            # Kết nối lại Oracle và cập nhật thông tin passport
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()

            update_query = """
                UPDATE CHIVY_ADMIN.PASSPORT
                SET passport_type = :passport_type,
                    current_passport_code = :current_passport_code,
                    expiry_date = :expiry_date,
                    status = :status,
                    status_detail = :status_detail,
                    updated_at = CURRENT_TIMESTAMP
                WHERE passport_id = :passport_id
            """
            cursor.execute(update_query, {
                'passport_type': passport_type,
                'current_passport_code': current_passport_code,
                'expiry_date': expiry_date,
                'status': status,
                'status_detail': status_detail,
                'passport_id': passport_id
            })
            connection.commit()
            connection.close()

            messages.success(request, 'Cập nhật passport thành công!')
            return redirect('update_resident_passport', passport_id=passport_id)

        if passport:
            passport_data = {
                'passport_id': passport[0],
                'passport_type': passport[2],
                'current_passport_code': passport[3],
                'expiry_date': passport[6],
                'status': passport[8],
                'status_detail': passport[9],
            }

        return render(request, 'management/update_resident_passport.html', {'passport': passport_data})

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        messages.error(request, f"Có lỗi xảy ra: {error}")
        return redirect('update_resident_passport', passport_id=passport_id)




###REQUEST HISTORY

def build_request_history_search_query(search_query, search_type):
    if search_type == 'history_id':
        query = """
            SELECT * FROM CHIVY_ADMIN.REQUEST_HISTORY
            WHERE history_id = :search_query
        """
    elif search_type == 'passport_id':
        query = """
            SELECT * FROM CHIVY_ADMIN.REQUEST_HISTORY
            WHERE passport_id = :search_query
        """
    elif search_type == 'status':
        query = """
            SELECT * FROM CHIVY_ADMIN.REQUEST_HISTORY
            WHERE LOWER(status) LIKE LOWER(:search_query)
        """
        search_query = f"%{search_query}%"
    elif search_type == 'value':
        query = """
            SELECT * FROM CHIVY_ADMIN.REQUEST_HISTORY
            WHERE LOWER(value) LIKE LOWER(:search_query)
        """
        search_query = f"%{search_query}%"
    else:
        query = """
            SELECT * FROM CHIVY_ADMIN.REQUEST_HISTORY
        """
    return query, search_query

def create_request_history(request):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')

    if not username or not password:
        return redirect('staff_login')

    if request.method == 'POST':
        passport_id = request.POST.get('passport_id')
        status = request.POST.get('status')
        value = request.POST.get('value')
        detail = request.POST.get('detail')

        try:
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()

            insert_query = """
                INSERT INTO CHIVY_ADMIN.REQUEST_HISTORY (passport_id, status, value, detail)
                VALUES (:passport_id, :status, :value, :detail)
            """
            cursor.execute(insert_query, {'passport_id': passport_id, 'status': status, 'value': value, 'detail': detail})
            connection.commit()
            connection.close()

            messages.success(request, 'Tạo yêu cầu thành công!')
        except cx_Oracle.DatabaseError as e:
            messages.error(request, f"Có lỗi xảy ra: {e}")
            return redirect('create_request_history')

    return render(request, 'management/create_request_history.html')



def request_history(request):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')
    if not username or not password:
        return redirect('staff_login')

    search_query = request.GET.get('search_query', '').strip()
    search_type = request.GET.get('search_field', '')  # Chỉnh lại thành search_field
    data, column_names = [], []

    try:
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()
        data, column_names = get_request_history_data(cursor, search_query, search_type)
        connection.close()
    except cx_Oracle.DatabaseError as e:
        messages.error(request, f"Có lỗi xảy ra: {e}")
        return redirect('request_history')

    page_number = request.GET.get('page', 1)
    page_obj = paginate_data(data, page_number)

    return render(request, 'management/request_history.html', {
        'page_obj': page_obj,
        'column_names': column_names,
        'search_query': search_query,
        'search_type': search_type,
    })

def get_request_history_data(cursor, search_query, search_type):
    if search_query and search_type != 'SELECT':
        query, search_query = build_request_history_search_query(search_query, search_type)
        cursor.execute(query, {'search_query': search_query})
    else:
        query = "SELECT * FROM CHIVY_ADMIN.REQUEST_HISTORY"
        cursor.execute(query)
    return cursor.fetchall(), [desc[0] for desc in cursor.description]


def update_request_history(request, history_id):
    username = request.session.get('oracle_username')
    password = request.session.get('oracle_password')

    if not username or not password:
        return redirect('staff_login')

    try:
        connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
        cursor = connection.cursor()

        # Truy vấn yêu cầu theo history_id
        select_query = "SELECT * FROM CHIVY_ADMIN.REQUEST_HISTORY WHERE history_id = :history_id"
        cursor.execute(select_query, {'history_id': history_id})
        request_history = cursor.fetchone()

        # Nếu không tìm thấy yêu cầu, redirect về trang dashboard
        if not request_history:
            messages.error(request, 'Không tìm thấy yêu cầu.')
            return redirect('staff_dashboard')

        connection.close()

        if request.method == 'POST':
            status = request.POST.get("status")
            value = request.POST.get("value")
            detail = request.POST.get("detail")
            user_viewed = request.POST.get("user_viewed")
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()

            update_query = """
                UPDATE CHIVY_ADMIN.REQUEST_HISTORY
                SET status = :status,
                    value = :value,
                    detail = :detail,
                    user_viewed = :user_viewed,
                    updated_at = CURRENT_TIMESTAMP
                WHERE history_id = :history_id
            """
            cursor.execute(update_query, {
                'status': status,
                'value': value,
                'detail': detail,
                'history_id': history_id,
                'user_viewed': user_viewed if user_viewed != "NULL" else None
            })
            connection.commit()
            connection.close()

            messages.success(request, 'Cập nhật yêu cầu thành công!')
            return redirect('update_request_history', history_id=history_id)

        if request_history:
            history_data = {
                'history_id': request_history[0],
                'passport_id': request_history[1],
                'status': request_history[2],
                'value': request_history[3],
                'user_viewed': request_history[6],
                'detail': request_history[7],
            }

        return render(request, 'management/update_request_history.html', {'history': history_data})

    except cx_Oracle.DatabaseError as e:
        error, = e.args
        messages.error(request, f"Có lỗi xảy ra: {error}")
        return redirect('update_request_history', history_id=history_id)


def delete_request_history(request):
    if request.method == 'POST':
        history_id = request.POST.get('history_id')

        username = request.session.get('oracle_username')
        password = request.session.get('oracle_password')

        if not username or not password:
            return redirect('staff_login')

        try:
            connection = cx_Oracle.connect(username, password, 'localhost:1521/ORCLPDB')
            cursor = connection.cursor()
            delete_query = "DELETE FROM CHIVY_ADMIN.REQUEST_HISTORY WHERE history_id = :history_id"
            cursor.execute(delete_query, {'history_id': history_id})
            connection.commit()  # Commit để lưu thay đổi
            connection.close()

            messages.success(request, 'Xóa yêu cầu thành công!')
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 20001:  # Lỗi tùy chỉnh từ trigger
                reply = error.message.splitlines()[0].strip()
                messages.error(request, f"Có lỗi xảy ra: {reply.split(':')[1].strip()}") 
            else:  # Lỗi khác
                messages.error(request, "No Delete Permission")

    return redirect('request_history')
