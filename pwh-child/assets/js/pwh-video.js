/**
 * UAEL Video widgets (YouTube, Vimeo …): play on the first press.
 *
 * UAEL swaps its thumbnail/play button for the player iframe on click, but it
 * only adds autoplay=1 when the widget's own Autoplay option is on (which would
 * start the video on page load instead). Without it the player loads paused
 * and needs a second press. Add autoplay=1 to the address UAEL will use, so
 * the click that loads the player also starts it.
 */
( function () {
	function withAutoplay( src ) {
		if ( ! src || /[?&]autoplay=1\b/.test( src ) ) {
			return src;
		}
		var hashAt = src.indexOf( '#' );
		var base = hashAt < 0 ? src : src.slice( 0, hashAt );
		var hash = hashAt < 0 ? '' : src.slice( hashAt );
		if ( hash === '#t=' ) {
			hash = ''; // empty start time
		}
		var sep = base.indexOf( '?' ) < 0 ? '?' : ( /[?&]$/.test( base ) ? '' : '&' );
		return base + sep + 'autoplay=1' + hash;
	}

	function prepare( root ) {
		( root || document ).querySelectorAll( '.uael-video__play[data-src]' ).forEach( function ( el ) {
			var src = withAutoplay( el.getAttribute( 'data-src' ) );
			el.setAttribute( 'data-src', src );
			if ( window.jQuery ) {
				window.jQuery( el ).data( 'src', src ); // UAEL reads it with .data()
			}
		} );
	}

	if ( document.readyState === 'loading' ) {
		document.addEventListener( 'DOMContentLoaded', function () { prepare(); } );
	} else {
		prepare();
	}

	// Elementor editor preview re-renders widgets as they're edited.
	window.addEventListener( 'elementor/frontend/init', function () {
		if ( window.elementorFrontend && window.elementorFrontend.hooks ) {
			window.elementorFrontend.hooks.addAction( 'frontend/element_ready/uael-video.default', function ( $scope ) {
				prepare( $scope[ 0 ] );
			} );
		}
	} );
} )();
