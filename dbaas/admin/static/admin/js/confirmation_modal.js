(function($) {
   
	$( '.modal.fade' ).on( 'keypress', function( e ) {
	    if( e.keyCode === 13 ) {
	        e.preventDefault();
	        $( this ).find('.btn-accept-modal').click();
	        $( this ).find('.modal-footer input').click();
	    }
	} );

	$( '.modal.fade' ).on( 'hidden', function( e ) {
        $(".btn-accept-modal.inactive").removeClass("inactive")
        .addClass("active")
        .removeAttr("disabled");
	} );

	function block() {
		var button = $(this)
		if(button.hasClass("active")) {
			button.removeClass("active")
        	.addClass("inactive");
    	}
    	else {
    		button.attr("disabled", "disabled");
    	}
	}

	var allButtons = document.getElementsByClassName('btn-accept-modal')
	for (var x = 0; x < allButtons.length; x++){
		allButtons[x].addEventListener("click", block, true);
	}

})(django.jQuery);