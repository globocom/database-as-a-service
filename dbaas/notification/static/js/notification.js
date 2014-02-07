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
            });
        },
    };

    // Document READY
    $(function() {
        var notification = new Notification();
        notification.setupRefresh();
    });

})(django.jQuery);
