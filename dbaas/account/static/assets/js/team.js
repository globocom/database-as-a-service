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

    $(function() {
        $("#result_list tbody tr").each(function(){
            $this = $(this);
            var team_id = $this.find(".action-select").val() || "";
            var show_resources = $this.find("#resources");
            $.ajax({
                url: "/account/team_resources/" + team_id,
                type: "GET",
                dataType: "json",
                async: true,
            }).done(function(response) {
                var html = "";
                html += '<ul>' + 
                '<li>VMs in use: ' + response.vms + '</li>' +
                '<li>Total CPUs: ' + response.cpu + '</li>' +
                '<li>Total memory: ' + response.memory + ' GB</li>' +
                '<li>Total disk: ' + response.disk + ' GB</li>';
                $(show_resources).html(html);
            });
        });
    });
})(django.jQuery);
