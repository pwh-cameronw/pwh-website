/**
 * PWH Billing Toggle + Pricing Card behaviour.
 *
 * - Clicking Monthly/Yearly in any .pwh-billing switches every .pwh-plan on
 *   the page. Cards without a yearly price keep showing monthly.
 * - The + under a card's features reveals its technical details.
 *
 * Event delegation, so it also works for widgets added in the Elementor editor.
 */
( function () {
	'use strict';

	function setBilling( period ) {
		document.querySelectorAll( '.pwh-billing__opt' ).forEach( function ( btn ) {
			btn.setAttribute( 'aria-checked', btn.dataset.billing === period ? 'true' : 'false' );
		} );

		document.querySelectorAll( '.pwh-plan[data-has-yearly]' ).forEach( function ( plan ) {
			var yearly = period === 'yearly';
			plan.querySelectorAll( '.pwh-price--monthly, .pwh-plan__btn--monthly' ).forEach( function ( el ) {
				el.hidden = yearly;
			} );
			plan.querySelectorAll( '.pwh-price--yearly, .pwh-plan__btn--yearly' ).forEach( function ( el ) {
				el.hidden = ! yearly;
			} );
		} );
	}

	document.addEventListener( 'click', function ( e ) {
		var opt = e.target.closest( '.pwh-billing__opt' );
		if ( opt ) {
			setBilling( opt.dataset.billing );
			return;
		}

		var more = e.target.closest( '.pwh-plan__more' );
		if ( more ) {
			var open    = more.getAttribute( 'aria-expanded' ) !== 'true';
			var details = document.getElementById( more.getAttribute( 'aria-controls' ) );
			more.setAttribute( 'aria-expanded', open ? 'true' : 'false' );
			if ( details ) {
				details.hidden = ! open;
			}
		}
	} );

	// Arrow keys move between the two radio options.
	document.addEventListener( 'keydown', function ( e ) {
		var opt = e.target.closest( '.pwh-billing__opt' );
		if ( ! opt || ( e.key !== 'ArrowLeft' && e.key !== 'ArrowRight' ) ) {
			return;
		}
		var other = opt.parentElement.querySelector( '.pwh-billing__opt:not([data-billing="' + opt.dataset.billing + '"])' );
		if ( other ) {
			e.preventDefault();
			other.focus();
			setBilling( other.dataset.billing );
		}
	} );

	function init() {
		var toggle = document.querySelector( '.pwh-billing' );
		if ( toggle && toggle.dataset.default === 'yearly' ) {
			setBilling( 'yearly' );
		}
	}

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', init );
	} else {
		init();
	}
} )();
