$(document).ready(function () {

    $('.register-close').click(function () {
        $('.register-modal').addClass('fadeOut');
        $('.register-modal').removeClass('fadeIn');
        $('.register-modal').hide();
    })

    $('.login-close').click(function () {
        $('.login-modal').addClass('fadeOut');
        $('.login-modal').removeClass('fadeIn');
        $('.login-modal').hide();
    })

    $('.btn-login').click(function () {
        $('.login-modal').addClass('fadeIn');
        $('.login-modal').removeClass('fadeOut');
        $('.login-modal').show();
        $('.register-modal').hide();
    })

    $('.btn-signup').click(function () {
        $('.register-modal').addClass('fadeIn');
        $('.register-modal').removeClass('fadeOut');
        $('.register-modal').show();
        $('.login-modal').hide();
    })

    $('.sorting-btn').click(function () {
        if ($(this).hasClass("sorting-active")) {
            $(this).removeClass("sorting-active");
        } else {
            $('.sorting-btn').removeClass("sorting-active");
            $(this).addClass("sorting-active");
        }
    })

   
    
})

function goBack() {
    window.history.back();
}

function buttonClicked(){
    return true;
}