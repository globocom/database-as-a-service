
(function($) {

    var Database = function() {
        this.update_components();
    };

    Database.prototype = {
        mode: function(new_instance) {
            if (new_instance) {
                // new instance
                $("select, input", "fieldset.new_instance").removeAttr("disabled");
                $("select, input", "fieldset.reuse_instance").attr("disabled", "disabled");
            } else {
                $("select, input", "fieldset.new_instance").attr("disabled", "disabled");
                $("select, input", "fieldset.reuse_instance").removeAttr("disabled");
            }
        },
        update_components: function() {
            this.mode(this.is_new_instance());
        },
        is_new_instance: function() {
            var new_instance = $(".new_instance:checked").val() == 'on';
            return new_instance;
        }
    };

    // Document READY
    $(function() {
        var database = new Database();

        $(".new_instance").on("change", function() {
            database.update_components();
        });

        $(".plan .well").on("click", function() {
            if (database.is_new_instance()) {
                $("input", ".plan").removeAttr("checked");
                $("input", $(this)).attr("checked", "checked");
            }
        });
    });

})(django.jQuery);
