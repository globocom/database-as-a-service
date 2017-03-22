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

    var ExtraDnsManager = (function() {
        var DATABASE_ID = null;
        var get_database_id = function() {
            if (!DATABASE_ID) {
                DATABASE_ID = $("#table-extradns").data("database-id");
            }
            return DATABASE_ID;
        };

        var ExtraDns = function($row) {
            this.$row = $row;
            this.pk = $row.attr('data-extradns-pk');
        };


        /**
        * Remove a extradns from server and the page.
        */
        ExtraDns.prototype.delete = function(callback) {
            var extradns = this;
            if (confirm("Are you sure?")) {
                $.ajax({
                    "url": "/extra_dns/extradns/" + this.pk,
                    "type": "DELETE",
                }).done(function(data) {
                    extradns.$row.remove();
                    if (callback) {
                        callback(extradns);
                    }
                }).fail(function() {
                    show_error_message($row, 'You do not have permission to perform this!');
                });
            }
        };

        /**
        * Put the listeners on extradns
        */
        var initialize_listeners = function(extradns) {
            // put all listeners
            var $row = extradns.$row;

            // Delete extradns
            $row.on("click.delete-extradns", ".btn-extradns-remove", function(e) {
                extradns.delete();
                return false;
            });
        };

        ///////// ADD BUTTON is the only function isolated
        $(document).on("click.add-extradns", "#add-extradns", function(e) {
            $("tbody", "#table-extradns").append(
                "<tr class='extradns'><td colspan='3'>" +
                "<input type='text' placeholder='type dns' maxlength='100' name='dns' value='' />" +
                "<a href='#' class='save-new-extradns btn btn-primary'>Save</a>" +
                "</td></tr>");
        });

        $(document).on("click.save-new-extradns", ".save-new-extradns", function(e) {
            var $insert_row = $(e.target).parent().parent(),
                dns = $("input", $insert_row).val();

            ExtraDnsManager.create(dns, $insert_row, function(extradns) {
                $insert_row.remove();

            });
            return false;
        });

        var show_error_message = function($row, message) {
            var errormsg = '<div class="alert alert-error"><button type="button" class="close" data-dismiss="alert">&times;</button><strong>Erro</strong> ' + message + '</div>';
            $('td .alert', $row).remove();
            $('td', $row).prepend(errormsg);
        };


        return {
            /**
            * Get the extradns object with pk specified. If no extradns exists
            * in page, returns null.
            */
            get: function(extradns_pk) {
                var $row = $("#table-extradns tr[data-extradns-pk=" + extradns_pk + "]");
                if ($row.length === 0) {
                    return null;
                }
                return new ExtraDns($row);
            },
            /**
            * Includes a extradns json representation on page (always include at the bottom).
            */
            include: function(extradns_json) {
                var selector = "#table-extradns tr[data-extradns-pk=" + extradns_json.extradns.pk + "]";

                var html_row = $("#extradns-template").mustache(extradns_json);
                $("tbody", "#table-extradns").append(html_row);

                // request new DOM element already attached
                var extradns = this.get(extradns_json.extradns.pk);
                initialize_listeners(extradns);
                return extradns;
            },
            /**
            * Create a new extradns on server and put on page
            */
            create: function(dns, $row, callback) {
                var self = this;
                $.ajax({
                    "url": "/extra_dns/extradns/",
                    "type": "POST",
                    "data": { "dns": dns, "database_id": get_database_id() },
                }).done(function(data) {
                    if (data.error) {
                        show_error_message($row, data.error);
                    }

                    var extradns = self.include(data);
                    if (callback) {
                        callback(extradns);
                    }
                }).fail(function() {
                    show_error_message($row, 'You do not have permission to perform this!');
                });
            }
        };
    })();

    window.ExtraDnsManager = ExtraDnsManager;

})(django.jQuery);
