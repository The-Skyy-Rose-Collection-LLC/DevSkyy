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
					'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
					'label' => 'Premium Materials',
					'desc'  => '280–400gsm cotton. Italian wool blends. Full-grain leather. No shortcuts.',
				),
				array(
					'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
					'label' => 'Oakland Made Mentality',
					'desc'  => 'Born from the struggle of East Oakland. Designed for the world. Built to last generations.',
				),
				array(
					'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
					'label' => 'Gender Neutral',
					'desc'  => 'Pioneer in Bay Area gender-neutral fashion. Designed for anyone, regardless of gender or age.',
				),
				array(
					'icon'  => '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
					'label' => 'Limited Editions',
					'desc'  => 'Small batch production. Individually numbered. When it\'s gone, it\'s gone.',
				),
			);

			$card_delay = 1;
			foreach ( $craft_cards as $card ) :
				?>
				<div class="craft-card rv rv-d<?php echo esc_attr( $card_delay ); ?>">
					<div class="craft-icon" aria-hidden="true"><?php
					// SVG icons — developer-controlled, not user input.
					echo $card['icon']; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
				?></div>
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
