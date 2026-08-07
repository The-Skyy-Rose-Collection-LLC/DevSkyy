<?php
defined( 'ABSPATH' ) || exit;
$context = is_front_page() ? 'homepage' : 'default';
if ( is_page( 'pre-order' ) || is_page( 'preorder' ) ) { $context = 'preorder'; }
if ( is_page( 'black-rose' ) ) { $context = 'black-rose'; }
if ( is_page( 'love-hurts' ) ) { $context = 'love-hurts'; }
if ( is_page( 'signature' ) ) { $context = 'signature'; }
if ( is_page( 'kids-capsule' ) ) { $context = 'kids-capsule'; }
$mascot = skyyrose2_sot_asset_uri( 'images/mascot/skyy-canonical-v2.png' );
?>
<canvas id="skyy-3d-canvas" class="skyy-3d-canvas" width="220" height="340" aria-hidden="true" style="display:none"></canvas>
<div id="skyyrose-mascot" class="skyyrose-mascot skyyrose-mascot--hidden" aria-label="Skyy, your SkyyRose style guide" data-context="<?php echo esc_attr( $context ); ?>" data-walk-side="right" role="complementary">
	<div id="skyy-bubble" class="skyy-bubble" role="status" aria-live="polite" hidden>
		<p id="skyy-bubble-text" class="skyy-bubble__text"></p>
		<div id="skyy-chips" class="skyy-chips" role="group" aria-label="Quick replies"></div>
		<button id="skyy-ask-trigger" class="skyy-ask-trigger" type="button" hidden>Ask a question</button>
	</div>
	<button id="skyyrose-mascot-trigger" class="skyyrose-mascot__character" type="button" aria-label="Chat with Skyy" aria-expanded="false">
		<img class="skyyrose-mascot__image" src="<?php echo esc_url( $mascot ); ?>" alt="SkyyRose mascot" width="220" height="220" loading="lazy" decoding="async">
	</button>
	<button id="skyyrose-mascot-minimize" class="skyyrose-mascot__minimize" type="button" aria-label="Minimize Skyy">×</button>
</div>
<button id="skyyrose-mascot-recall" class="skyyrose-mascot__recall" type="button" style="display:none" aria-hidden="true" aria-label="Bring Skyy back"><img src="<?php echo esc_url( $mascot ); ?>" alt="" width="32" height="32"><span>Skyy</span></button>
<dialog id="skyy-ask-dialog" class="skyy-ask-dialog" aria-labelledby="skyy-ask-dialog-title"><form id="skyy-ask-form" class="skyy-ask-form" method="dialog"><h2 id="skyy-ask-dialog-title">Ask Skyy</h2><label for="skyy-ask-input">Sizing, shipping, a collection…</label><input id="skyy-ask-input" type="text" autocomplete="off"><div><button type="button" id="skyy-ask-cancel">Cancel</button><button type="submit">Ask</button></div></form></dialog>
