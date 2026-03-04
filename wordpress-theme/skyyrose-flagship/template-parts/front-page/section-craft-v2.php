<?php
/**
 * Template Part: Craft Section (Homepage V2)
 *
 * @package SkyyRose_Flagship
 * @since   4.1.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<!-- ═══ CRAFT ═══ -->
<section class="craft" id="craft" aria-label="<?php esc_attr_e( 'Our Craft', 'skyyrose-flagship' ); ?>">
	<div class="craft-inner">
		<div class="craft-header rv">
			<h2><?php echo esc_html( 'The Craft' ); ?></h2>
			<p><?php echo esc_html( 'Every stitch, every fabric, every detail — intentional.' ); ?></p>
		</div>
		<div class="craft-grid">
			<?php
			$craft_cards = array(
				array(
					'icon'  => '&#9830;',
					'label' => 'Premium Materials',
					'desc'  => '280–400gsm cotton. Italian wool blends. Full-grain leather. No shortcuts.',
				),
				array(
					'icon'  => '&#9733;',
					'label' => 'Oakland Made Mentality',
					'desc'  => 'Born from the struggle of East Oakland. Designed for the world. Built to last generations.',
				),
				array(
					'icon'  => '&#9775;',
					'label' => 'Gender Neutral',
					'desc'  => 'Pioneer in Bay Area gender-neutral fashion. Designed for anyone, regardless of gender or age.',
				),
				array(
					'icon'  => '&#9830;',
					'label' => 'Limited Editions',
					'desc'  => 'Small batch production. Individually numbered. When it\'s gone, it\'s gone.',
				),
			);

			$card_delay = 1;
			foreach ( $craft_cards as $card ) :
				?>
				<div class="craft-card rv rv-d<?php echo esc_attr( $card_delay ); ?>">
					<div class="craft-icon" aria-hidden="true"><?php echo wp_kses_post( $card['icon'] ); ?></div>
					<div class="craft-label"><?php echo esc_html( $card['label'] ); ?></div>
					<p class="craft-desc"><?php echo esc_html( $card['desc'] ); ?></p>
				</div>
				<?php
				$card_delay++;
			endforeach;
			?>
		</div>
	</div>
</section>
