var TABLE_ROW_TEMPLATE = '<tr class="credential" data-credential-pk="{{credential.pk}}" >' +
                '<td>{{credential.user}}</td>' +
                '<td>' +
                '   <a href="#" class="btn show-password" title="{{credential.user}}" data-content="{{credential.password}}" >show password</a>'+
                '   <a class="btn btn-warning btn-reset-password" href="#"><i class="icon-refresh"></i></a>'+
                '</td>'+
                '<td>'+
                '   <a class="btn btn-danger" href="#"><i class="icon-trash icon-white"></i></a>'+
                '</td>'+
            '</tr>';

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
        update_components: function() {
            this.filter_plans();
        },
        filter_plans: function() {
            $(".plan").each(function(index, el) {
                // var
                //     $el = $(el),
                //     data_attribute_name = 'engine-' + engine_id;

                // if ($el.data(data_attribute_name)) {
                //     $el.show();
                // } else {
                //     $el.hide();
                // }
            });
        }
    };


    // Document READY
    $(function() {
        var database = new Database();

        $(".new_databaseinfra, #id_engine").on("change", function() {
            database.update_components();
        });

        $(".plan").on("click", function() {
            $("input", ".plan").removeAttr("checked");
            $("input", $(this)).attr("checked", "checked");
        });

        $(".btn-plan").on("click", function(ev) {
            $("#plan-type").val(this.dataset.planId);
        });

        // show password
        $("#table-credentials").on("click", ".show-password", function(e) {
            e.preventDefault();
            $(".show-password", "#table-credentials").each(function(i, el) {
                if (el == e.target) {
                    $(e.target).popover("toggle");
                } else {
                    $(this).popover("hide");
                }
            });
        });

        $('.show-password').popover({"trigger": "manual", "placement": "left"});

        // reset password
        $(document).on("click", ".btn-reset-password", function(e) {
            var $credential = $(e.target).parents(".credential"),
                $a_show_password = $(".show-password", $credential),
                $a_reset_password = $(e.target);

            var credential_pk = $credential.data("credential-pk");
            if (credential_pk) {
                $.ajax({
                    "url": "/logical/credential/" + credential_pk,
                    "type": "PUT",
                }).done(function(credential) {
                    $a_show_password.attr("data-content", credential.password);
                    $a_show_password.popover("show");
                });
            }
            return false;
        });

        // add credential
        $("#add-credential").on("click.add-credential", function(e) {
            $("tbody", "#table-credentials").append(
                "<tr class='credential'><td colspan='3'>" +
                "<input type='text' placeholder='type username' name='user' value='' />" +
                "<a href='#' class='save-new-credential btn btn-primary'>Save</a>" +
                "</td></tr>");
        });

        $(document).on("click.save-new-credential", ".save-new-credential", function(e) {
            var $table_row = $(e.target).parent().parent(),
                username = $("input", $table_row).val(),
                database_id = $("#table-credentials").data("database-id");
            e.preventDefault();
            $table_row.remove();
            $.ajax({
                "url": "/logical/credential/",
                "type": "POST",
                "data": { "username": username, "database_id": database_id },
            }).done(function(data) {
                if (!data || data.errors || !data.credential) {
                    return;
                }
                var credential = data.credential;

                var table_row = TABLE_ROW_TEMPLATE
                    .replace(/{{credential.pk}}/g, credential.pk)
                    .replace(/{{credential.user}}/g, credential.user)
                    .replace(/{{credential.password}}/g, credential.password);
                var $table_row = $(table_row);
                $("tbody", "#table-credentials").append($table_row);
                $(".show-password", $table_row).popover({"trigger": "manual", "placement": "left"}).popover("show");
            }).fail(function() {
                alert("Error creating user");
            });

            return false;
        });

        // Remove credential
        $(document).on("click", ".btn-credential-remove", function(e) {
            var $credential = $(e.target).parents(".credential");

            var credential_pk = $credential.data("credential-pk");
            if (credential_pk) {
                $.ajax({
                    "url": "/logical/credential/" + credential_pk,
                    "type": "DELETE",
                }).done(function(credential) {
                    $credential.remove();
                });
            }
            return false;
        });
    });

})(django.jQuery);
