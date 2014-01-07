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

    var DatabaseInfra = function() {
        // this.engine_changed();
    };

    DatabaseInfra.prototype = {
        engine_changed: function() {
            var el = $("#id_engine");
            var engine_id = el.val() || "none";
            var engine_name = $('#id_engine :selected').text() || "none";
            var endpoint = $(".control-group.field-endpoint");
            if (engine_name.match(/mongo/g)) {
                endpoint.hide();
            } else {
                if (engine_id == "none") {
                    endpoint.hide();
                } else {
                    endpoint.show();
                };
            };
        },
    };
    
    // Document READY
    $(function() {
        
        var databaseinfra = new DatabaseInfra();
        
        //hide endpoint
        var endpoint = $(".control-group.field-endpoint");
        if (endpoint.is(":visible")) {
            endpoint.hide();
        };
        
        // 
        $("#id_engine").on("change", function() {
            // alert("engine change");
            databaseinfra.engine_changed();
        });

    });

})(django.jQuery);
