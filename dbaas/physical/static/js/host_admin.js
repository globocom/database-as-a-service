(function($) {


    /**
     * setup JQuery's AJAX methods to setup CSRF token in the request before sending it off.
     * http://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request
     */

    
    // Document READY
    $(function() {

    
        console.log($("#cs_host_attributes-group"));
        /*$("#cs_host_attributes-group").hide();*/

        if ($("#id_cs_host_attributes-0-vm_id").val() == null){
            $("#cs_host_attributes-group").hide();
        }else{
            $("#cs_host_attributes-group").show();
        }
    

    });

})(django.jQuery);