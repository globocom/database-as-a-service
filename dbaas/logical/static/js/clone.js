(function($) {
            $(document).ready(function(){
                    var $environment = $('#id_environment');
                    var $old_plan = $('#id_old_plan').val();
                    var $planInput = $('#id_plan');
                    var $engine = $('#id_engine').val()

                    $environment.change(function() {
                            environment_id = $('#id_environment option:selected').val()

                            if(environment_id){
                                $.getJSON('/api/plan/?format=json', {'engine_id': $engine, 'environment_id': environment_id, 'active':'True'},function(plans) {
                                        plans = plans['plan']
                                        $("#id_plan option").remove();

                                        for(i in plans) {
                                                    $planInput.append('<option value="'+plans[i].id+'">'+plans[i].name+'</option>');
                                         }
                                });
                            }
                    }).trigger('change');
            });
})(django.jQuery);
