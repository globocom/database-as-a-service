
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
    });

})(django.jQuery);
