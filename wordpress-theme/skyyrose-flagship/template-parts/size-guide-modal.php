<?php
/**
 * Size Guide Modal — dark luxury size guide accessible site-wide.
 * Triggered by [data-open-size-guide] or .js-size-guide-trigger elements.
 *
 * @package SkyyRose_Flagship
 * @since   5.3.0
 */

defined( 'ABSPATH' ) || exit;

$sg_tables = array(
	'tops'    => array(
		'label'   => __( 'Tops', 'skyyrose-flagship' ),
		'headers' => array( 'Size', 'Chest', 'Waist', 'Length', 'Sleeve' ),
		'rows'    => array(
			array( 'XS', '34', '28', '27', '32' ),
			array( 'S', '36', '30', '28', '33' ),
			array( 'M', '38', '32', '29', '34' ),
			array( 'L', '40', '34', '30', '35' ),
			array( 'XL', '42', '36', '31', '35.5' ),
			array( '2XL', '44', '38', '32', '36' ),
		),
	),
	'bottoms' => array(
		'label'   => __( 'Bottoms', 'skyyrose-flagship' ),
		'headers' => array( 'Size', 'Waist', 'Hip', 'Inseam', 'Length' ),
		'rows'    => array(
			array( 'XS', '28', '34', '30', '38' ),
			array( 'S', '30', '36', '31', '39' ),
			array( 'M', '32', '38', '32', '40' ),
			array( 'L', '34', '40', '32', '41' ),
			array( 'XL', '36', '42', '33', '42' ),
			array( '2XL', '38', '44', '33', '43' ),
		),
	),
	'kids'    => array(
		'label'   => __( 'Kids', 'skyyrose-flagship' ),
		'headers' => array( 'Size', 'Age', 'Chest', 'Waist', 'Height' ),
		'rows'    => array(
			array( '2T', '2', '21', '20', '33-36' ),
			array( '3T', '3', '22', '20.5', '36-39' ),
			array( '4T', '4', '23', '21', '39-42' ),
			array( '5', '5-6', '24', '21.5', '42-45' ),
			array( '6', '6-7', '25', '22', '45-48' ),
		),
	),
);
?>
<div id="size-guide-modal" class="sg-overlay" role="dialog" aria-labelledby="sg-heading" aria-modal="true" aria-hidden="true" inert>
<div class="sg-panel">
	<button type="button" class="sg-close" aria-label="<?php esc_attr_e( 'Close size guide', 'skyyrose-flagship' ); ?>">
		<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
	</button>
	<h2 id="sg-heading" class="sg-heading"><?php esc_html_e( 'Size Guide', 'skyyrose-flagship' ); ?></h2>
	<p class="sg-subheading"><?php esc_html_e( 'All measurements in inches', 'skyyrose-flagship' ); ?></p>

	<div class="sg-tabs" role="tablist" aria-label="<?php esc_attr_e( 'Size categories', 'skyyrose-flagship' ); ?>">
		<?php $first = true; foreach ( $sg_tables as $key => $t ) : ?>
			<button type="button" role="tab" id="sg-tab-<?php echo esc_attr( $key ); ?>" class="sg-tab<?php echo $first ? ' sg-tab--active' : ''; ?>" aria-selected="<?php echo $first ? 'true' : 'false'; ?>" aria-controls="sg-panel-<?php echo esc_attr( $key ); ?>" data-sg-tab="<?php echo esc_attr( $key ); ?>"><?php echo esc_html( $t['label'] ); ?></button>
		<?php $first = false; endforeach; ?>
	</div>

	<?php $first = true; foreach ( $sg_tables as $key => $t ) : ?>
		<div id="sg-panel-<?php echo esc_attr( $key ); ?>" class="sg-tabpanel" role="tabpanel" aria-labelledby="sg-tab-<?php echo esc_attr( $key ); ?>"<?php echo $first ? '' : ' hidden'; ?>>
			<div class="sg-table-wrap"><table class="sg-table">
				<thead><tr><?php foreach ( $t['headers'] as $h ) : ?><th><?php echo esc_html( $h ); ?></th><?php endforeach; ?></tr></thead>
				<tbody>
					<?php foreach ( $t['rows'] as $row ) : ?>
						<tr><?php foreach ( $row as $c ) : ?><td><?php echo esc_html( $c ); ?></td><?php endforeach; ?></tr>
					<?php endforeach; ?>
				</tbody>
			</table></div>
		</div>
	<?php $first = false; endforeach; ?>

	<div class="sg-measure">
		<h3 class="sg-measure__heading"><?php esc_html_e( 'How to Measure', 'skyyrose-flagship' ); ?></h3>
		<div class="sg-measure__content">
			<svg class="sg-measure__icon" width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><ellipse cx="24" cy="10" rx="6" ry="7"/><path d="M14 22c0-2 4-4 10-4s10 2 10 4v2c0 1-2 3-10 3s-10-2-10-3z"/><path d="M18 27v18M30 27v18"/><path d="M18 34h12"/></svg>
			<ul class="sg-measure__list">
				<li><?php esc_html_e( 'Chest: Measure around the fullest part, keeping the tape level.', 'skyyrose-flagship' ); ?></li>
				<li><?php esc_html_e( 'Waist: Measure around your natural waistline, just above the navel.', 'skyyrose-flagship' ); ?></li>
				<li><?php esc_html_e( 'Hip: Measure around the widest part of your hips.', 'skyyrose-flagship' ); ?></li>
				<li><?php esc_html_e( 'Inseam: Measure from the crotch seam to the ankle bone.', 'skyyrose-flagship' ); ?></li>
			</ul>
		</div>
	</div>
</div>
</div>

<script>
(function(){
	var o=document.getElementById('size-guide-modal');if(!o)return;
	var p=o.querySelector('.sg-panel'),c=o.querySelector('.sg-close'),
		ts=o.querySelectorAll('[data-sg-tab]'),ps=o.querySelectorAll('.sg-tabpanel'),lf=null;
	function open(){lf=document.activeElement;o.setAttribute('aria-hidden','false');o.removeAttribute('inert');c.focus();}
	function close(){o.setAttribute('aria-hidden','true');o.setAttribute('inert','');if(lf&&lf.focus)lf.focus();}
	function sw(k){for(var i=0;i<ts.length;i++){var a=ts[i].getAttribute('data-sg-tab')===k;ts[i].classList.toggle('sg-tab--active',a);ts[i].setAttribute('aria-selected',a?'true':'false');}for(var j=0;j<ps.length;j++){if(ps[j].id==='sg-panel-'+k)ps[j].removeAttribute('hidden');else ps[j].setAttribute('hidden','');}}
	o.addEventListener('keydown',function(e){if(e.key==='Escape'){close();return;}if(e.key!=='Tab')return;var els=p.querySelectorAll('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])');if(!els.length)return;var f=els[0],l=els[els.length-1];if(e.shiftKey&&document.activeElement===f){e.preventDefault();l.focus();}else if(!e.shiftKey&&document.activeElement===l){e.preventDefault();f.focus();}});
	o.addEventListener('click',function(e){if(e.target===o)close();});
	c.addEventListener('click',close);
	for(var i=0;i<ts.length;i++)ts[i].addEventListener('click',function(){sw(this.getAttribute('data-sg-tab'));});
	document.addEventListener('click',function(e){var t=e.target.closest('[data-open-size-guide],.js-size-guide-trigger');if(t){e.preventDefault();open();}});
})();
</script>
