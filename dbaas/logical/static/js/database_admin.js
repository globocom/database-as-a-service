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

    var Database = function() {
        this.update_components();
    };

    Database.prototype = {
        update_modal_message: function() {
            var environment_id = $("#id_environment").val() || "";
            if (environment_id) {
              $.ajax({
                  type: "GET",
                  dataType: "json",
                  url: "/logical/" + environment_id + "/credential_parameter_by_name/add_database_modal_msg"
              }).done(function (response) {
                  var msg = response.msg || "";
                  $("label[for=id_database_name] .modal_message .modal_extra_message").text(msg).css({'color': 'red'});
              });
            }
        },
        update_components: function() {
            this.filter_plans();
        },
        update_engines: function(engines) {
            this.filter_engines(engines);
        },
        filter_plans: function(engine_id) {
            var environment_id = $("#id_environment").val() || "none";
            engine_id = engine_id || $("#id_engine").val() || "none";
            var data_environment_attribute = "data-environment-" + environment_id;
            var data_engine_attribute = "data-engine-" + engine_id;
            $(".plan").each(function(index, el) {
                var $el = $(el);
                if ($el.attr(data_environment_attribute) && $el.attr(data_engine_attribute)) {
                    $(el).parent().show('fast');
                } else {
                    ($el).parent().hide('fast');
                }
            });
        },
        filter_engines: function(all_engines) {
            var environment_id = $("#id_environment").val() || "none";
            var current_engine = $("#id_engine").val() || "none";
            if(environment_id !== "none"){
                var engine_selector = $("#id_engine");
                var $engineOptions = $("#id_engine option");
                var self = this;
                $.ajax({
                    type: "GET",
                    dataType: "json",
                    url: "/physical/engines_by_env/" + environment_id + "/"
                }).done(function (response) {
                    $("#engnoopts").remove();
                    if(response.engines.length !== 0){
                        response.engines.push("");
                        var options2ShowSelector = response.engines.map(function(id) {
                          return "[value='" + id + "']";
                        }).join(",");
                        
                        $engineOptions.hide();
                        $engineOptions.filter(options2ShowSelector).show();
                        var selectedId = parseInt($engineOptions.filter(':selected').val(), 10);
                        if (response.engines.indexOf(selectedId) === -1) {
                          $engineOptions.filter("[value='']").eq(0).attr('selected', 'selected');
                          self.filter_plans('none');
                        }
                    }
                    else{
                        $engineOptions.hide();
                        engine_selector.append('<option id="engnoopts" selected="selected">' +
                                                    'This environment has no active plans</option>');
                    }
                });
                $(document.getElementsByClassName("field-engine")[0]).fadeIn("slow");
            }
            else{
                $(document.getElementsByClassName("field-engine")[0]).fadeOut("slow");
            }
        },
        filter_pools: function() {
            var envId = $("#id_environment").val() || null;
            var teamId = $("#id_team").val() || null;
            if(envId && teamId){
                $.ajax({
                    type: "GET",
                    dataType: "json",
                    async: false,
                    url: "/api/environment/?get_provisioner_by_label=Kubernetes&&id=" + envId
                }).done(function (response) {
                    if (response.environment.length > 0) {
                        var pool_selector = document.getElementById("id_pool");
                        var self = this;
                        $.ajax({
                            type: "GET",
                            dataType: "json",
                            url: "/api/pool/?teams__id=" + teamId + "&environment__id=" + envId
                        }).done(function (response) {
                            response.pool.push({"id": ""});
                            var options2ShowSelector = response.pool.map(function(pool) {
                                return "[value='" + pool.id + "']";
                            }).join(",");
                            var $poolOptions = $("#id_pool option");
                            $poolOptions.hide();
                            $poolOptions.filter(options2ShowSelector).show();
                            var selectedId = parseInt($poolOptions.filter(':selected').val(), 10);
                            if (response.pool.indexOf(selectedId) === -1) {
                                $poolOptions.filter("[value='']").eq(0).attr('selected', 'selected');
                            }
                        });
                        $(document.getElementsByClassName("field-pool")[0]).fadeIn("slow");
                    } else {
                        $(document.getElementsByClassName("field-pool")[0]).fadeOut("slow");
                    }
                });
                
                
            }
            else{
                $(document.getElementsByClassName("field-pool")[0]).fadeOut("slow");
            }
        }
    };

    // Document READY
    $(function() {
        var database = new Database();
        field_engine = document.getElementsByClassName("field-engine");
        if(field_engine.length !== 0){
            field_engine = field_engine[0];
            field_engine.style.display = "none";
        }

        //Saving all engines before changing it
        engine_selector = document.getElementById("id_engine");
        if(engine_selector !== null){
            var engines = {};
            for(var i=0; i< engine_selector.options.length; i++){
                option = engine_selector.options[i];
                if(option.value !== null)
                    engines[option.value] = option.text;
            }
        }

        $("#id_environment").on("change", function() {
            database.update_engines(engines);
            database.filter_pools();
            database.update_components();
            database.update_modal_message();
        });
        $("#id_environment").change();

        $("#id_engine").on("change", function() {
            database.update_components();
        });
        $("#id_team").on("change", function() {
            database.filter_pools();
        });
        $("#id_engine").change();

        $(".plan").on("click", function() {
            $("input", ".plan").removeAttr("checked");
            $("input", $(this)).attr("checked", "checked");
        });

        $("#adv_button").on("click", function(ev) {
            var $btn = $(this).button('loading')
            $btn.button('reset')
        });

        $( document ).ready(function() {
            if ($("#id_offering").val() == ""){
                $("#id_offering").hide();
                $("#resizeDatabase").hide();
                $('input[id="id_offering"], label[for="id_offering"]').hide();

            }
        });

        var endpoint_popover_active = null;
        $('.show-endpoint').popover({'trigger': 'manual', 'html': false})
        .on('click', function(e) {
            var $this = $(this);
            if (endpoint_popover_active && endpoint_popover_active.attr('data-content') != $this.attr('data-content')) {
                endpoint_popover_active.popover('hide');
            }
            endpoint_popover_active = $this;
            endpoint_popover_active.popover('toggle');
            e.preventDefault();
        });

        var endpoint_popover_active = null;
        $('.show-upgrade, .show-resize').popover({'trigger': 'manual', 'html': true})
        .on('click', function(e) {
            var $this = $(this);
            if (endpoint_popover_active && endpoint_popover_active.attr('data-content') != $this.attr('data-content')) {
                endpoint_popover_active.popover('hide');
            }
            endpoint_popover_active = $this;
            endpoint_popover_active.popover('toggle');
            e.preventDefault();
        });
    });

})(django.jQuery);
