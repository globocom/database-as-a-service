(function($) {


    /**
     * setup JQuery's AJAX methods to setup CSRF token in the request before sending it off.
     * http://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request
     */

    
    // Document READY
    $(function() {

        $("#cs_plan_attributes-group").hide();
        $("#nfsaas_plan_attributes-group").hide();
        if ($("#id_provider").val() == 1){
            $("#cs_plan_attributes-group").show();
            $("#nfsaas_plan_attributes-group").show();
        }else{
            $("#cs_plan_attributes-group").hide();
            $("#nfsaas_plan_attributes-group").hide();
        }
    
        $("#id_provider").change(function() {
            if (this.value == 1){
                $("#cs_plan_attributes-group").show();
                $("#nfsaas_plan_attributes-group").show();
            }else{
                $("#cs_plan_attributes-group").hide();
                $("#nfsaas_plan_attributes-group").hide();
            }
        });
    });

})(django.jQuery);