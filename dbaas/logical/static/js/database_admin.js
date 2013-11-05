
(function($) {

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
        $(".show-password")
        .popover({"trigger": "manual", "placement": "left"})
        .click(function(e) {
            e.preventDefault();
            $(".show-password").each(function(i, el) {
                if (el == e.target) {
                    $(e.target).popover("toggle");
                } else {
                    $(this).popover("hide");
                }
            });
        });

        $(document).on("click", ".btn-reset-password", function(e) {
            var $credential = $(e.target).parents(".credential"),
                $a_show_password = $(".show-password", $credential),
                $a_reset_password = $(e.target);

            if ($a_reset_password.hasClass('disabled')) {
                return false;
            }

            var credential_pk = $credential.data("credential-pk");
            if (credential_pk) {
                $.ajax({
                    "url": "/logical/credential/" + credential_pk + "/reset_password",
                    "type": "POST",
                }).done(function(credential) {
                    $a_show_password.attr("data-content", credential.password);
                    $a_show_password.popover("show");
                });
            }
            return false;
        });
    });

})(django.jQuery);
