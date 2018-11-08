(function($) {
    /**
     * setup JQuery's AJAX methods to setup CSRF token in the request before sending it off.
     * http://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request
     */

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = $.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    $.ajaxSetup({
         beforeSend: function(xhr, settings) {
             if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                 // Only send the token to relative URLs i.e. locally.
                 xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
             }
         }
    });

    var MigrateManager = (function() {
        return {
            /**
            * Run host migrate
            */
            migrate_host: function(database_id, host_id, new_zone) {
                var self = this;
                $.ajax({
                    "url": "/admin/logical/database/" + database_id + "/migrate/",
                    "type": "POST",
                    "data": { "host_id": host_id, "new_zone": new_zone},
                }).complete(function() {
                    location.reload();
                });
            }
        };
    })();
    window.MigrateManager = MigrateManager;

})(django.jQuery);

