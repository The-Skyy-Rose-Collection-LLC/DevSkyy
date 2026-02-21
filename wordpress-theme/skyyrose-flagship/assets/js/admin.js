/**
 * SkyyRose Flagship — Admin Scripts
 *
 * @package SkyyRose_Flagship
 * @since 2.0.0
 */

( function( $ ) {
	'use strict';

	// Admin-specific enhancements (color pickers, meta boxes, etc.)
	$( document ).ready( function() {
		// Initialize color pickers if present
		if ( $.fn.wpColorPicker ) {
			$( '.skyyrose-color-picker' ).wpColorPicker();
		}
	} );

} )( jQuery );
