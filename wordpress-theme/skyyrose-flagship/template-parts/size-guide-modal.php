<?php
/**
 * Template Part: Size & Fit Guide Modal
 *
 * Accessible overlay with per-category size charts, visual measurement
 * reference, unit toggle (in/cm), and collection-specific fit notes.
 *
 * Included via get_template_part() on collection and pre-order pages.
 *
 * @package SkyyRose_Flagship
 * @since   3.10.0
 */

defined( 'ABSPATH' ) || exit;
?>

<div class="size-guide-modal" id="size-guide-modal"
     role="dialog" aria-modal="true"
     aria-label="<?php esc_attr_e( 'Size & Fit Guide', 'skyyrose-flagship' ); ?>"
     aria-hidden="true" inert tabindex="-1">

	<div class="size-guide-modal__backdrop"></div>

	<div class="size-guide-modal__content">

		<button type="button" class="size-guide-modal__close"
		        aria-label="<?php esc_attr_e( 'Close size guide', 'skyyrose-flagship' ); ?>">&times;</button>

		<h2 class="size-guide-modal__title">
			<?php esc_html_e( 'Size & Fit Guide', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="size-guide-modal__subtitle">
			<?php esc_html_e( 'Find your perfect SkyyRose fit', 'skyyrose-flagship' ); ?>
		</p>

		<!-- ====== Category Tabs ====== -->
		<div class="size-guide-tabs" role="tablist" aria-label="<?php esc_attr_e( 'Size chart categories', 'skyyrose-flagship' ); ?>">
			<button class="size-guide-tab active" role="tab"
			        aria-selected="true" aria-controls="sg-panel-tops" id="sg-tab-tops">
				<?php esc_html_e( 'Tops', 'skyyrose-flagship' ); ?>
			</button>
			<button class="size-guide-tab" role="tab"
			        aria-selected="false" aria-controls="sg-panel-bottoms" id="sg-tab-bottoms" tabindex="-1">
				<?php esc_html_e( 'Bottoms', 'skyyrose-flagship' ); ?>
			</button>
			<button class="size-guide-tab" role="tab"
			        aria-selected="false" aria-controls="sg-panel-outerwear" id="sg-tab-outerwear" tabindex="-1">
				<?php esc_html_e( 'Outerwear', 'skyyrose-flagship' ); ?>
			</button>
		</div>

		<!-- ====== Unit Toggle ====== -->
		<div class="size-guide-unit-toggle" role="radiogroup"
		     aria-label="<?php esc_attr_e( 'Measurement unit', 'skyyrose-flagship' ); ?>">
			<button class="size-guide-unit active" role="radio" aria-checked="true" data-unit="in">IN</button>
			<button class="size-guide-unit" role="radio" aria-checked="false" data-unit="cm">CM</button>
		</div>

		<!-- ====== Tops Panel ====== -->
		<div class="size-guide-panel active" id="sg-panel-tops"
		     role="tabpanel" aria-labelledby="sg-tab-tops">
			<div class="size-guide-chart">
				<table>
					<thead>
						<tr>
							<th><?php esc_html_e( 'Size', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Chest', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Length', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Sleeve', 'skyyrose-flagship' ); ?></th>
						</tr>
					</thead>
					<tbody>
						<tr><td>XS</td><td data-in="34–36" data-cm="86–91">34–36″</td><td data-in="26" data-cm="66">26″</td><td data-in="31" data-cm="79">31″</td></tr>
						<tr><td>S</td><td data-in="36–38" data-cm="91–97">36–38″</td><td data-in="27" data-cm="69">27″</td><td data-in="32" data-cm="81">32″</td></tr>
						<tr><td>M</td><td data-in="38–40" data-cm="97–102">38–40″</td><td data-in="28" data-cm="71">28″</td><td data-in="33" data-cm="84">33″</td></tr>
						<tr><td>L</td><td data-in="40–42" data-cm="102–107">40–42″</td><td data-in="29" data-cm="74">29″</td><td data-in="34" data-cm="86">34″</td></tr>
						<tr><td>XL</td><td data-in="42–44" data-cm="107–112">42–44″</td><td data-in="30" data-cm="76">30″</td><td data-in="35" data-cm="89">35″</td></tr>
						<tr><td>XXL</td><td data-in="44–46" data-cm="112–117">44–46″</td><td data-in="31" data-cm="79">31″</td><td data-in="36" data-cm="91">36″</td></tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- ====== Bottoms Panel ====== -->
		<div class="size-guide-panel" id="sg-panel-bottoms"
		     role="tabpanel" aria-labelledby="sg-tab-bottoms" hidden>
			<div class="size-guide-chart">
				<table>
					<thead>
						<tr>
							<th><?php esc_html_e( 'Size', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Waist', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Hip', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Inseam', 'skyyrose-flagship' ); ?></th>
						</tr>
					</thead>
					<tbody>
						<tr><td>XS</td><td data-in="26–28" data-cm="66–71">26–28″</td><td data-in="34–36" data-cm="86–91">34–36″</td><td data-in="7" data-cm="18">7″</td></tr>
						<tr><td>S</td><td data-in="28–30" data-cm="71–76">28–30″</td><td data-in="36–38" data-cm="91–97">36–38″</td><td data-in="7.5" data-cm="19">7.5″</td></tr>
						<tr><td>M</td><td data-in="30–32" data-cm="76–81">30–32″</td><td data-in="38–40" data-cm="97–102">38–40″</td><td data-in="8" data-cm="20">8″</td></tr>
						<tr><td>L</td><td data-in="32–34" data-cm="81–86">32–34″</td><td data-in="40–42" data-cm="102–107">40–42″</td><td data-in="8.5" data-cm="22">8.5″</td></tr>
						<tr><td>XL</td><td data-in="34–36" data-cm="86–91">34–36″</td><td data-in="42–44" data-cm="107–112">42–44″</td><td data-in="9" data-cm="23">9″</td></tr>
						<tr><td>XXL</td><td data-in="36–38" data-cm="91–97">36–38″</td><td data-in="44–46" data-cm="112–117">44–46″</td><td data-in="9.5" data-cm="24">9.5″</td></tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- ====== Outerwear Panel ====== -->
		<div class="size-guide-panel" id="sg-panel-outerwear"
		     role="tabpanel" aria-labelledby="sg-tab-outerwear" hidden>
			<div class="size-guide-chart">
				<table>
					<thead>
						<tr>
							<th><?php esc_html_e( 'Size', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Chest', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Length', 'skyyrose-flagship' ); ?></th>
							<th><?php esc_html_e( 'Shoulder', 'skyyrose-flagship' ); ?></th>
						</tr>
					</thead>
					<tbody>
						<tr><td>XS</td><td data-in="36–38" data-cm="91–97">36–38″</td><td data-in="27" data-cm="69">27″</td><td data-in="17" data-cm="43">17″</td></tr>
						<tr><td>S</td><td data-in="38–40" data-cm="97–102">38–40″</td><td data-in="28" data-cm="71">28″</td><td data-in="17.5" data-cm="44">17.5″</td></tr>
						<tr><td>M</td><td data-in="40–42" data-cm="102–107">40–42″</td><td data-in="29" data-cm="74">29″</td><td data-in="18" data-cm="46">18″</td></tr>
						<tr><td>L</td><td data-in="42–44" data-cm="107–112">42–44″</td><td data-in="30" data-cm="76">30″</td><td data-in="18.5" data-cm="47">18.5″</td></tr>
						<tr><td>XL</td><td data-in="44–46" data-cm="112–117">44–46″</td><td data-in="31" data-cm="79">31″</td><td data-in="19" data-cm="48">19″</td></tr>
						<tr><td>XXL</td><td data-in="46–48" data-cm="117–122">46–48″</td><td data-in="32" data-cm="81">32″</td><td data-in="19.5" data-cm="50">19.5″</td></tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- ====== How to Measure ====== -->
		<div class="size-guide-measure">
			<h3><?php esc_html_e( 'How to Measure', 'skyyrose-flagship' ); ?></h3>
			<div class="size-guide-measure__grid">
				<div class="size-guide-measure__item">
					<span class="size-guide-measure__icon" aria-hidden="true">&#9675;</span>
					<strong><?php esc_html_e( 'Chest', 'skyyrose-flagship' ); ?></strong>
					<p><?php esc_html_e( 'Measure around the fullest part of your chest, keeping the tape level.', 'skyyrose-flagship' ); ?></p>
				</div>
				<div class="size-guide-measure__item">
					<span class="size-guide-measure__icon" aria-hidden="true">&#9675;</span>
					<strong><?php esc_html_e( 'Waist', 'skyyrose-flagship' ); ?></strong>
					<p><?php esc_html_e( 'Measure around your natural waistline, the narrowest part of your torso.', 'skyyrose-flagship' ); ?></p>
				</div>
				<div class="size-guide-measure__item">
					<span class="size-guide-measure__icon" aria-hidden="true">&#9675;</span>
					<strong><?php esc_html_e( 'Hip', 'skyyrose-flagship' ); ?></strong>
					<p><?php esc_html_e( 'Measure around the widest part of your hips, about 8 inches below your waist.', 'skyyrose-flagship' ); ?></p>
				</div>
			</div>
		</div>

		<!-- ====== Collection Fit Notes ====== -->
		<div class="size-guide-fit-notes">
			<h3><?php esc_html_e( 'Collection Fit Guide', 'skyyrose-flagship' ); ?></h3>

			<div class="size-guide-fit-note" data-collection="signature">
				<span class="size-guide-fit-note__badge" style="--note-accent: var(--color-primary, #B76E79)">
					<?php esc_html_e( 'Signature', 'skyyrose-flagship' ); ?>
				</span>
				<p><?php esc_html_e( 'True to size. Classic streetwear fit — relaxed through the body with a modern taper. Order your usual size.', 'skyyrose-flagship' ); ?></p>
			</div>

			<div class="size-guide-fit-note" data-collection="black-rose">
				<span class="size-guide-fit-note__badge" style="--note-accent: #C0C0C0">
					<?php esc_html_e( 'Black Rose', 'skyyrose-flagship' ); ?>
				</span>
				<p><?php esc_html_e( 'Slightly oversized. Gothic-inspired relaxed silhouette. Size down one for a fitted look, or stay true for the intended drape.', 'skyyrose-flagship' ); ?></p>
			</div>

			<div class="size-guide-fit-note" data-collection="love-hurts">
				<span class="size-guide-fit-note__badge" style="--note-accent: #DC143C">
					<?php esc_html_e( 'Love Hurts', 'skyyrose-flagship' ); ?>
				</span>
				<p><?php esc_html_e( 'Slim fashion fit. Designed to hug the body with intention. Size up one for a more relaxed feel.', 'skyyrose-flagship' ); ?></p>
			</div>
		</div>

	</div><!-- .size-guide-modal__content -->
</div><!-- .size-guide-modal -->
