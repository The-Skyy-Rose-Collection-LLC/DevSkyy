<?php
/**
 * Cinematic Mode Toggle — Eye Button + Inline JS
 *
 * Persists cinematic mode state in sessionStorage.
 *
 * @package SkyyRose_Flagship
 * @since   6.0.0
 */
if ( ! defined( 'ABSPATH' ) ) { exit; }
?>
<button class="cinematic-toggle" type="button" aria-pressed="false" aria-label="<?php esc_attr_e( 'Toggle cinematic mode', 'skyyrose-flagship' ); ?>">
	<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
		<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
		<circle cx="12" cy="12" r="3"/>
	</svg>
</button>
<script>
(function(){
	var btn = document.querySelector('.cinematic-toggle');
	if (!btn) return;
	try {
		if (sessionStorage.getItem('skyyrose_cinematic_mode') === '1') {
			document.body.classList.add('cinematic-mode');
			btn.setAttribute('aria-pressed', 'true');
		}
	} catch(e) {}
	btn.addEventListener('click', function() {
		var active = document.body.classList.toggle('cinematic-mode');
		btn.setAttribute('aria-pressed', active ? 'true' : 'false');
		try {
			if (active) { sessionStorage.setItem('skyyrose_cinematic_mode', '1'); }
			else { sessionStorage.removeItem('skyyrose_cinematic_mode'); }
		} catch(e) {}
	});
})();
</script>
