(function($) {


    /**
     * setup JQuery's AJAX methods to setup CSRF token in the request before sending it off.
     * http://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request
     */


    // Document READY
    $(function() {

       status = $("div.control-group.field-status").find('p').text();
       revoke_button = $("#revoke_maintenance");

        if(status!='Waiting' && revoke_button){
            revoke_button.hide();
        }else{
            revoke_button.show()
        };
    });

})(django.jQuery);
