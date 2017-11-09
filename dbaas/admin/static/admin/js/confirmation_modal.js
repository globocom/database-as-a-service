(function($) {
   
	$( '.modal.fade' ).on( 'keypress', function( e ) {
	    if( e.keyCode === 13 ) {
	        e.preventDefault();
	        $( this ).find('.btn-accept-modal').click();
	    }
	} );

})(django.jQuery);