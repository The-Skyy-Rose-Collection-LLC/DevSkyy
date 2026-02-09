/**
 * SkyyRose Theme Customizer JavaScript
 *
 * Handles live preview updates in the WordPress Customizer.
 *
 * @package SkyyRose_Flagship
 * @since 1.0.0
 */

(function($) {
	'use strict';

	/**
	 * Live update site title.
	 */
	wp.customize('blogname', function(value) {
		value.bind(function(to) {
			$('.site-title a').text(to);
		});
	});

	/**
	 * Live update site description.
	 */
	wp.customize('blogdescription', function(value) {
		value.bind(function(to) {
			$('.site-description').text(to);
		});
	});

	/**
	 * Live update header text color.
	 */
	wp.customize('header_textcolor', function(value) {
		value.bind(function(to) {
			if ('blank' === to) {
				$('.site-title, .site-description').css({
					'clip': 'rect(1px, 1px, 1px, 1px)',
					'position': 'absolute'
				});
			} else {
				$('.site-title, .site-description').css({
					'clip': 'auto',
					'position': 'relative',
					'color': to
				});
			}
		});
	});

})(jQuery);
