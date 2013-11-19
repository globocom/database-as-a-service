(function($) {

$(function(){
  $(document).on('click', '.showButton', function(e){
    $(this).hide();
    $('.endpoint', $(this).parent()).show();
    e.preventDefault();
  });
});

})(django.jQuery);