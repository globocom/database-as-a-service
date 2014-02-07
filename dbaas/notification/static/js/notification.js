(function($) {

    var Notification = function() {

    };

    Notification.prototype = {
        setupRefresh: function() {
            setInterval("location.reload()", 10000);
        },
    };

    // Document READY
    $(function() {
        var notification = new Notification();
        notification.setupRefresh();
    });

})(django.jQuery);
