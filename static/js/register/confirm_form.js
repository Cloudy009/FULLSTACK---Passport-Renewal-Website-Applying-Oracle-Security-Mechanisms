  (
    function () 
    {
      'use strict';
      var form = document.getElementById('passportForm')
      // Lắng nghe sự kiện submit của form
      form.addEventListener('submit', function (event) 
      {
        event.preventDefault(); // Ngừng gửi form
        
        // Kiểm tra tính hợp lệ của form
        if (!form.checkValidity()) 
        {
          event.stopPropagation();
          form.classList.add('was-validated');
        } 
        else 
        { // Nếu form hợp lệ, hiển thị modal yêu cầu xác nhận
          var myModal = new bootstrap.Modal
          (
            document.getElementById('confirmationModal'),
            { keyboard: false,} // Không cho phép đóng modal bằng phím ESCC
          ); 
          myModal.show();
        }
      }, false)
      // Lắng nghe sự kiện nhấn "Xác nhận" trong modal
      document.getElementById('confirmSubmit').addEventListener
      (
        'click', function () 
        {
          // Sau khi người dùng xác nhận, gửi form
          form.submit();
        }
      );
    }
  )();
        