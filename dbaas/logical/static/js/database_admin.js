
(function($) {

    var Database = function() {
        this.update_components();
    };

    Database.prototype = {
        mode: function(new_instance) {
            if (new_instance) {
                // new instance
                $("fieldset.new_instance select").removeAttr("disabled");
                $("fieldset.reuse_instance select").attr("disabled", "disabled");
            } else {
                $("fieldset.new_instance select").attr("disabled", "disabled");
                $("fieldset.reuse_instance select").removeAttr("disabled");
            }
        },
        update_components: function() {
            new_instance = $(".new_instance:checked").val() == 'on';
            this.mode(new_instance);
        }
    };

    // Document READY
    $(function() {
        var database = new Database();

        $(".new_instance").on("change", function() {
            database.update_components();
        });
    });

})(django.jQuery);
