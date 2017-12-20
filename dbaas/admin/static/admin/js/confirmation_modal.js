(function($) {
   
	$( '.modal.fade' ).on( 'keypress', function( e ) {
	    if( e.keyCode === 13 ) {
	        e.preventDefault();
	        $( this ).find('.btn-accept-modal').click();
	        $( this ).find('.modal-footer input').click();
	    }
	} );

})(django.jQuery);