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

	/*
	 * Phones: the plan cards in a .pwh-plans container become a swipe slider
	 * (CSS in pwh.css). Add dots under it like the Home products slider.
	 */
	function initSlider( plans ) {
		if ( plans.dataset.pwhSlider ) {
			return;
		}
		var track = plans.querySelector( ':scope > .e-con-inner' ) || plans;
		var cards = Array.prototype.filter.call( track.children, function ( c ) {
			return c.classList.contains( 'elementor-widget-pwh-pricing-card' );
		} );
		if ( cards.length < 2 ) {
			return;
		}
		plans.dataset.pwhSlider = '1';

		var dots = document.createElement( 'div' );
		dots.className = 'pwh-plan-dots';
		dots.setAttribute( 'role', 'tablist' );
		dots.setAttribute( 'aria-label', 'Plans' );
		cards.forEach( function ( card, i ) {
			var b = document.createElement( 'button' );
			var t = card.querySelector( '.pwh-plan__title, h3' );
			b.type = 'button';
			b.setAttribute( 'role', 'tab' );
			b.setAttribute( 'aria-label', 'Show ' + ( t ? t.textContent.trim() : 'plan ' + ( i + 1 ) ) );
			b.appendChild( document.createElement( 'span' ) );
			b.addEventListener( 'click', function () {
				track.scrollTo( { left: card.offsetLeft - cards[ 0 ].offsetLeft, behavior: 'smooth' } );
			} );
			dots.appendChild( b );
		} );
		if ( track === plans ) {
			plans.after( dots );
		} else {
			plans.appendChild( dots );
		}

		var btns = dots.querySelectorAll( 'button' );
		function update() {
			var x = track.scrollLeft, best = 0, bestD = Infinity;
			cards.forEach( function ( c, i ) {
				var d = Math.abs( c.offsetLeft - cards[ 0 ].offsetLeft - x );
				if ( d < bestD ) {
					bestD = d;
					best = i;
				}
			} );
			if ( x > 0 && x + track.clientWidth >= track.scrollWidth - 4 ) {
				best = cards.length - 1;
			}
			btns.forEach( function ( b, i ) {
				b.setAttribute( 'aria-selected', i === best ? 'true' : 'false' );
			} );
		}
		track.addEventListener( 'scroll', function () {
			window.requestAnimationFrame( update );
		}, { passive: true } );
		window.addEventListener( 'resize', update );
		update();
	}

	function init() {
		var toggle = document.querySelector( '.pwh-billing' );
		if ( toggle && toggle.dataset.default === 'yearly' ) {
			setBilling( 'yearly' );
		}
		document.querySelectorAll( '.pwh-plans' ).forEach( initSlider );
	}

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', init );
	} else {
		init();
	}
} )();
