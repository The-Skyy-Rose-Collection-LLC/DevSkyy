<?php
/**
 * Size Guide — canonical /size-guide/ page (virtual route).
 *
 * Served by skyyrose_virtual_template() (inc/redirects.php) — there is no WP
 * page object behind this route. Tables come from
 * skyyrose_get_size_guide_tables(), the same source the site-wide modal
 * renders, so the deep-link page and the PDP modal can never drift.
 *
 * @package SkyyRose
 * @since   1.8.0
 */

defined( 'ABSPATH' ) || exit;

$sg_tables = skyyrose_get_size_guide_tables();

get_header();
?>

<main id="primary" class="site-main sg-page" role="main" tabindex="-1">

	<?php
	// Hero + first size table are above the fold — no reveal classes: the hidden
	// resting state stalls LCP behind the deferred JS queue (the PDP 24.9s bug
	// class). Later tables keep reveals. Wave 5.
	?>
	<section class="sg-page__hero">
		<p class="sg-page__eyebrow"><?php esc_html_e( 'Fit Guide', 'skyyrose' ); ?></p>
		<h1 class="sg-page__title"><?php esc_html_e( 'Size Guide', 'skyyrose' ); ?></h1>
		<p class="sg-page__subtitle"><?php esc_html_e( 'Measure once, shop every drop with confidence. All measurements in inches.', 'skyyrose' ); ?></p>
	</section>

	<?php $sg_idx = 0; ?>
	<?php foreach ( $sg_tables as $sg_key => $sg_table ) : ?>
		<section class="sg-page__section<?php echo 0 === $sg_idx ? '' : ' rv-clip-up'; ?>" aria-labelledby="sg-page-<?php echo esc_attr( $sg_key ); ?>">
			<h2 id="sg-page-<?php echo esc_attr( $sg_key ); ?>" class="sg-page__heading"><?php echo esc_html( $sg_table['label'] ); ?></h2>
			<div class="sg-page__table-wrap">
				<table class="sg-page__table">
					<thead>
						<tr>
							<?php foreach ( $sg_table['headers'] as $sg_header ) : ?>
								<th scope="col"><?php echo esc_html( $sg_header ); ?></th>
							<?php endforeach; ?>
						</tr>
					</thead>
					<tbody>
						<?php foreach ( $sg_table['rows'] as $sg_row ) : ?>
							<tr>
								<?php foreach ( $sg_row as $sg_i => $sg_cell ) : ?>
									<?php if ( 0 === $sg_i ) : ?>
										<th scope="row"><?php echo esc_html( $sg_cell ); ?></th>
									<?php else : ?>
										<td><?php echo esc_html( $sg_cell ); ?></td>
									<?php endif; ?>
								<?php endforeach; ?>
							</tr>
						<?php endforeach; ?>
					</tbody>
				</table>
			</div>
		</section>
		<?php ++$sg_idx; ?>
	<?php endforeach; ?>

	<section class="sg-page__help rv-blur">
		<p><?php esc_html_e( 'Between sizes? Size up — every piece is cut for a relaxed, gender-neutral fit.', 'skyyrose' ); ?></p>
		<a class="sg-page__contact" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>"><?php esc_html_e( 'Still unsure? Reach out', 'skyyrose' ); ?></a>
	</section>

</main>

<?php
get_footer();
