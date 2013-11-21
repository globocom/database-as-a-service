(function($) {

$(function(){
  $(document).on('click', '.showButton', function(e){
    $(this).hide();
    $('.endpoint', $(this).parent()).show();
    e.preventDefault();
  });
});

$(function(){
  $(document).on('click', '.endpoint', function(e){
    $(this).hide();
    $('.showButton', $(this).parent()).show();
  });
});

})(django.jQuery);