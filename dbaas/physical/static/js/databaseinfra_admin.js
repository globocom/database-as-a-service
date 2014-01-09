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
            this.update_components();
        },
        update_components: function() {
            this.update_endpoint();
            this.update_plans();
        },
        update_endpoint: function() {
            var engine_id = $("#id_engine").val() || "none";
            var engine_name = $('#id_engine :selected').text() || "none";

            if (engine_name.match(/mongo/g)) {
                this.hide_endpoint();
            } else {
                if (engine_id == "none") {
                    this.hide_endpoint();
                } else {
                    this.show_endpoint();
                };
            };
        },
        clean_plan_options: function() {
            $('#id_plan option:gt(0)').remove();
        },
        update_plans: function() {            
            var first_plan_id = $("#id_plan").val() || "0";

            //remove options from plan, except the first one
            this.clean_plan_options();

            var engine_id = $("#id_engine").val() || "none";
            if (engine_id != "none") {
                
                $.ajax({
                    "dataType": "json",
                    "url": "/api/plan/",
                    "type": "GET",
                    "data": { "engine_id": engine_id, },
                }).done(function(data) {
                    if (data.error) {
                        alert(data.error);
                    } else {
                        var plan = $("#id_plan");
                        $.each(data, function(index, item) {
                            plan.append($("<option></option>").attr("value", item.id).text(item.name));
                            /* 
                            discover if it is the selected value. This is necessary in cases where the form is submited
                            but is returned with a validation error.
                            */
                            if (parseInt(item.id) == parseInt(first_plan_id)) {
                                plan.val(first_plan_id);
                            };
                        });
                    };
                }).fail(function() {
                    alert("invalid server response");
                });
            };
            
        },
        hide_endpoint: function() {
            var engine_id = $("#id_engine").val() || "none";
            var engine_name = $('#id_engine :selected').text() || "none";
            // only hide if it is not mongo or if no engine is selected
            if ((engine_name.match(/mongo/g) || engine_id == "none" )) {
                var endpoint = $(".control-group.field-endpoint");
                if (endpoint.is(":visible")) {
                    endpoint.hide();
                };
            };
        },
        show_endpoint: function() {
            var endpoint = $(".control-group.field-endpoint");
            if (! endpoint.is(":visible")) {
                endpoint.show();
            };
        },
    };
    
    // Document READY
    $(function() {
        
        var databaseinfra = new DatabaseInfra();
        
        //hide endpoint?
        databaseinfra.hide_endpoint();
        
        //update plans
        databaseinfra.update_plans();
        
        // 
        $("#id_engine").on("change", function() {
            // alert("engine change");
            databaseinfra.engine_changed();
        });

    });

})(django.jQuery);
