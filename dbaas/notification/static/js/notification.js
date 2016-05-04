(function($) {

    var Notification = function() {

    };

    Notification.prototype = {
        setupRefresh: function() {
            var REFRESH_TIMEOUT=10000;
            // setInterval("location.reload()", 10000);
            $('.countdown.callback').countdown({
              date: + (new Date) + REFRESH_TIMEOUT,
              render: function(data) {
                $(this.el).text(this.leadingZeros(data.sec, 2) + " sec to refresh");
              },
              onEnd: function() {
                $(this.el).addClass('ended');
                location.reload();
              }
            }).on("click", function() {
              $(this).removeClass('ended').data('countdown').update(+(new Date) + REFRESH_TIMEOUT).start();
            });
        },
    };

    // Document READY
    $(function() {
        var notification = new Notification();
        notification.setupRefresh();
        $("#disable_auto_refresh")[0].checked=true;

        $("#disable_auto_refresh").click(function() {
          if(!this.checked){
            console.log('Stopping countdown!');
            $('.countdown.callback').css("background-color", "#BAB9B9");
            $('.countdown.callback').data('countdown').stop();
          }else{
            console.log("Starting countdown");
            $('.countdown.callback').css("background-color", "#27ae60");
            $('.countdown.callback').data('countdown').start();
          };
        });
    });

})(django.jQuery);
