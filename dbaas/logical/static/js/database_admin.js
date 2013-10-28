
(function($) {

    var Database = function() {
        this.update_components();
    };

    Database.prototype = {
        is_new_databaseinfra: function() {
            var new_databaseinfra = $(".new_databaseinfra:checked").val() == 'on';
            return new_databaseinfra;
        },
        mode: function(new_databaseinfra) {
            if (new_databaseinfra) {
                // new databaseinfra
                $("select, input", "fieldset.new_databaseinfra").removeAttr("disabled");
                $("select, input", "fieldset.reuse_databaseinfra").attr("disabled", "disabled");
            } else {
                $("select, input", "fieldset.new_databaseinfra").attr("disabled", "disabled");
                $("select, input", "fieldset.reuse_databaseinfra").removeAttr("disabled");
            }
        },
        update_components: function() {
            this.mode(this.is_new_databaseinfra());
            this.filter_plans();
        },
        get_engine: function() {
            return $("#id_engine").val();
        },
        filter_plans: function() {
            var engine_id = this.get_engine();
            var data_attribute_name = 'engine-' + engine_id;
            $(".plan").each(function(index, el) {
                var $el = $(el);
                if ($el.data(data_attribute_name) == "1") {
                    $el.show();
                } else {
                    $el.hide();
                }
            });
        }
    };

    // Document READY
    $(function() {
        var database = new Database();

        $(".new_databaseinfra, #id_engine").on("change", function() {
            database.update_components();
        });

        $(".plan .well").on("click", function() {
            if (database.is_new_databaseinfra()) {
                $("input", ".plan").removeAttr("checked");
                $("input", $(this)).attr("checked", "checked");
            }
        });
    });

})(django.jQuery);
