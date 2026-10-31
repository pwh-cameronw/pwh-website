/**
 * Gravity Forms helpers.
 *
 * A checkbox field with the CSS class pwh-focus-next (field > Appearance >
 * Custom CSS Class): ticking it puts the cursor in the next visible field
 * after it, once conditional logic has shown that field.
 */
( function () {
	'use strict';

	var CONTROLS = 'input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]), select, textarea';

	function nextControl( field ) {
		for ( var el = field.nextElementSibling; el; el = el.nextElementSibling ) {
			if ( ! el.classList.contains( 'gfield' ) || el.offsetParent === null ) {
				continue;
			}
			var control = el.querySelector( CONTROLS );
			if ( control && control.offsetParent !== null ) {
				return control;
			}
		}
		return null;
	}

	document.addEventListener( 'change', function ( e ) {
		var box = e.target;
		if ( box.type !== 'checkbox' || ! box.checked ) {
			return;
		}
		var field = box.closest( '.gfield.pwh-focus-next' );
		if ( ! field ) {
			return;
		}
		// Conditional logic shows the fields on the same change event (or fades
		// them in if animation is on), so keep looking for up to a second.
		var tries = 0;
		( function look() {
			var control = nextControl( field );
			if ( control ) {
				control.focus();
			} else if ( ++tries < 60 ) {
				window.requestAnimationFrame( look );
			}
		} )();
	} );
} )();
