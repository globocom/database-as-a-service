(function($) {
    $(function() {
        var endpoint_popover_active = null;
        $('.show-info').popover({'trigger': 'manual', 'html': false})
        .on('click', function(e) {
            var $this = $(this);
            if (endpoint_popover_active && endpoint_popover_active.attr('data-content') != $this.attr('data-content')) {
                endpoint_popover_active.popover('hide');
            }
            endpoint_popover_active = $this;
            endpoint_popover_active.popover('toggle');
            e.preventDefault();
        });
            });
})(django.jQuery);
