<?php
/**
 * Marketplace page router.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

get_header();

while ( have_posts() ) :
	the_post();
	$slug = sanitize_title( get_post_field( 'post_name', get_the_ID() ) );
	?>
	<main id="primary" class="sr2-page sr2-page--<?php echo esc_attr( $slug ); ?>">
		<?php if ( 'collections' === $slug ) : ?>
			<?php get_template_part( 'template-parts/collections-index' ); ?>

		<?php elseif ( 'pre-order' === $slug || 'preorder' === $slug ) : ?>
			<?php $preorder_collection = skyyrose2_preorder_collection( get_the_ID() ); ?>
			<section class="sr2-preorder-hero<?php echo $preorder_collection ? ' sr2-preorder-hero--' . esc_attr( $preorder_collection ) : ' sr2-preorder-hero--unassigned'; ?>" aria-labelledby="sr2-page-title"<?php echo $preorder_collection ? ' data-collection="' . esc_attr( $preorder_collection ) . '"' : ''; ?>>
				<div class="sr2-preorder-hero__media" data-preorder-film>
					<img class="sr2-preorder-hero__poster" src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/preorder-portrait-poster.jpg' ) ); ?>" alt="" width="720" height="1280" fetchpriority="high">
					<video class="sr2-preorder-hero__video" poster="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/preorder-portrait-poster.jpg' ) ); ?>" width="720" height="1280" muted loop playsinline autoplay controls preload="metadata" aria-label="<?php esc_attr_e( 'Silent SkyyRose pre-order editorial film', 'skyyrose-flagship-2' ); ?>">
						<source src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'video/preorder-portrait-noaudio.mp4' ) ); ?>" type="video/mp4">
					</video>
				</div>
				<div class="sr2-preorder-hero__copy"><p class="sr2-eyebrow"><?php esc_html_e( 'Pre-Order', 'skyyrose-flagship-2' ); ?></p><h1 id="sr2-page-title"><?php esc_html_e( 'The next chapter begins here.', 'skyyrose-flagship-2' ); ?></h1><p><?php esc_html_e( 'Explore pieces currently offered for pre-order. Product pages provide the details available for each piece.', 'skyyrose-flagship-2' ); ?></p><a class="sr2-button sr2-button--fill" href="#reserve"><?php esc_html_e( 'Explore pieces', 'skyyrose-flagship-2' ); ?></a></div>
			</section>
			<?php
			$black_rose_scene_products = array(
				array( 'slug' => 'br-001', 'label' => __( 'Black Is Beautiful', 'skyyrose-flagship-2' ), 'note' => __( 'The Oakland statement jersey.', 'skyyrose-flagship-2' ), 'x' => '17%', 'y' => '62%' ),
				array( 'slug' => 'br-003', 'label' => __( 'Number 30', 'skyyrose-flagship-2' ), 'note' => __( 'A numbered piece from the house.', 'skyyrose-flagship-2' ), 'x' => '42%', 'y' => '58%' ),
				array( 'slug' => 'br-004', 'label' => __( 'Number 32', 'skyyrose-flagship-2' ), 'note' => __( 'Bay Area sports memory, recut.', 'skyyrose-flagship-2' ), 'x' => '53%', 'y' => '59%' ),
				array( 'slug' => 'br-008', 'label' => __( 'The Oakland Jacket', 'skyyrose-flagship-2' ), 'note' => __( 'Black Rose armor for the night.', 'skyyrose-flagship-2' ), 'x' => '78%', 'y' => '58%' ),
				array( 'slug' => 'br-009', 'label' => __( 'The Bay Tee', 'skyyrose-flagship-2' ), 'note' => __( 'The rose travels across the Bay.', 'skyyrose-flagship-2' ), 'x' => '55%', 'y' => '83%' ),
			);
			?>
			<section class="sr2-black-rose-scene" aria-labelledby="sr2-black-rose-scene-title" data-interactive-scene>
				<header class="sr2-section-head sr2-section-head--split"><div><p><?php esc_html_e( 'Black Rose / Pre-Order Salon', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-black-rose-scene-title"><?php esc_html_e( 'Choose your seat in the room.', 'skyyrose-flagship-2' ); ?></h2></div><p><?php esc_html_e( 'Move through the salon. Select a piece. Enter its world.', 'skyyrose-flagship-2' ); ?></p></header>
				<div class="sr2-black-rose-scene__frame">
					<img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/preorder/black-rose-salon.webp' ) ); ?>" alt="Black Rose jerseys and jackets arranged in a dark salon overlooking the Bay Bridge" width="1536" height="1024" loading="lazy" decoding="async">
					<div class="sr2-black-rose-scene__hotspots">
						<?php foreach ( $black_rose_scene_products as $index => $scene_product ) : $product_post = get_page_by_path( $scene_product['slug'], OBJECT, 'product' ); $product_url = $product_post ? get_permalink( $product_post ) : skyyrose2_collection_url( 'black-rose' ); ?>
							<a class="sr2-scene-hotspot<?php echo 0 === $index ? ' is-active' : ''; ?>" data-scene-hotspot href="<?php echo esc_url( $product_url ); ?>" style="--hotspot-x:<?php echo esc_attr( $scene_product['x'] ); ?>;--hotspot-y:<?php echo esc_attr( $scene_product['y'] ); ?>" aria-label="<?php echo esc_attr( $scene_product['label'] ); ?>"><span><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span></a>
						<?php endforeach; ?>
					</div>
				</div>
				<div class="sr2-black-rose-scene__rail" role="list">
					<?php foreach ( $black_rose_scene_products as $index => $scene_product ) : $scene_post = get_page_by_path( $scene_product['slug'], OBJECT, 'product' ); $scene_url = $scene_post ? get_permalink( $scene_post ) : skyyrose2_collection_url( 'black-rose' ); ?><a role="listitem" class="sr2-scene-card<?php echo 0 === $index ? ' is-active' : ''; ?>" data-scene-card href="<?php echo esc_url( $scene_url ); ?>"><span><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span><strong><?php echo esc_html( $scene_product['label'] ); ?></strong><em><?php echo esc_html( $scene_product['note'] ); ?></em></a><?php endforeach; ?>
				</div>
			</section>
			<section class="sr2-preorder-steps" aria-labelledby="sr2-preorder-steps-title">
				<header><p class="sr2-eyebrow"><?php esc_html_e( 'How It Works', 'skyyrose-flagship-2' ); ?></p><h2 id="sr2-preorder-steps-title"><?php esc_html_e( 'Three moves. Your place held.', 'skyyrose-flagship-2' ); ?></h2></header>
				<div><article><span>01</span><h3><?php esc_html_e( 'Choose your world', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'Enter collection story and find piece carrying your code.', 'skyyrose-flagship-2' ); ?></p></article><article><span>02</span><h3><?php esc_html_e( 'Select your piece', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'Confirm size, edition details, and expected fulfillment window.', 'skyyrose-flagship-2' ); ?></p></article><article><span>03</span><h3><?php esc_html_e( 'Hold your place', 'skyyrose-flagship-2' ); ?></h3><p><?php esc_html_e( 'Checkout securely. Order updates follow from reservation through delivery.', 'skyyrose-flagship-2' ); ?></p></article></div>
			</section>
			<?php skyyrose2_render_collection_rail(); ?>
			<section id="reserve" class="sr2-section sr2-section--products"><header class="sr2-section-head"><p><?php esc_html_e( 'Available to Reserve', 'skyyrose-flagship-2' ); ?></p><h2><?php esc_html_e( 'Future pieces. Present choice.', 'skyyrose-flagship-2' ); ?></h2><p class="sr2-section-head__note"><?php esc_html_e( 'Reserve now. We make each piece with intention and publish fulfillment timing before checkout.', 'skyyrose-flagship-2' ); ?></p></header><?php skyyrose2_product_cards( 12, 'pre-order' ); ?></section>

		<?php elseif ( 'about' === $slug ) : ?>
			<?php get_template_part( 'template-parts/about-scroll-world' ); ?>

		<?php elseif ( 'contact' === $slug ) : ?>
			<?php
			$contact_email = sanitize_email( get_option( 'admin_email' ) );
			$contact_link  = 'mailto:' . $contact_email;
			?>
			<section class="sr2-contact-hero" aria-labelledby="sr2-page-title">
				<div class="sr2-contact-hero__media"><img src="<?php echo esc_url( skyyrose2_sot_asset_uri( 'images/immersive/scene-signature-oakland-atelier-gpt2.webp' ) ); ?>" alt="" width="1920" height="1080" fetchpriority="high"></div>
				<div class="sr2-contact-hero__copy"><p class="sr2-eyebrow"><?php esc_html_e( 'Client Services', 'skyyrose-flagship-2' ); ?></p><h1 id="sr2-page-title"><?php esc_html_e( 'Talk to the house.', 'skyyrose-flagship-2' ); ?></h1><p><?php esc_html_e( 'Orders, sizing, press, collaborations, or anything between.', 'skyyrose-flagship-2' ); ?></p></div>
			</section>
			<section class="sr2-contact-grid">
				<div><p class="sr2-eyebrow"><?php esc_html_e( 'Direct', 'skyyrose-flagship-2' ); ?></p><a class="sr2-contact-grid__email" href="<?php echo esc_url( $contact_link ); ?>"><?php echo esc_html( $contact_email ); ?></a><p><?php esc_html_e( 'Replies typically arrive within two business days.', 'skyyrose-flagship-2' ); ?></p></div>
				<div class="sr2-contact-form-wrap"><?php if ( isset( $_GET['contact_sent'] ) ) : ?><p class="sr2-form-notice sr2-form-notice--success" role="status"><?php esc_html_e( 'Message received. The house will reply soon.', 'skyyrose-flagship-2' ); ?></p><?php elseif ( isset( $_GET['contact_error'] ) ) : ?><p class="sr2-form-notice sr2-form-notice--error" role="alert"><?php esc_html_e( 'Complete every field and try again.', 'skyyrose-flagship-2' ); ?></p><?php endif; ?><form class="sr2-contact-form" method="post"><p class="sr2-eyebrow"><?php esc_html_e( 'Send a note', 'skyyrose-flagship-2' ); ?></p><?php wp_nonce_field( 'skyyrose2_contact', 'skyyrose2_contact_nonce' ); ?><input type="hidden" name="skyyrose2_contact_submit" value="1"><label><?php esc_html_e( 'Name', 'skyyrose-flagship-2' ); ?><input name="contact_name" type="text" autocomplete="name" required></label><label><?php esc_html_e( 'Email', 'skyyrose-flagship-2' ); ?><input name="contact_email" type="email" autocomplete="email" required></label><label><?php esc_html_e( 'What can we help with?', 'skyyrose-flagship-2' ); ?><select name="contact_subject"><option>Order support</option><option>Styling appointment</option><option>Press or collaboration</option><option>Wholesale</option></select></label><label><?php esc_html_e( 'Message', 'skyyrose-flagship-2' ); ?><textarea name="contact_message" rows="6" required></textarea></label><button class="sr2-button sr2-button--fill" type="submit"><?php esc_html_e( 'Send to the house', 'skyyrose-flagship-2' ); ?></button></form></div>
			</section>
			<nav class="sr2-service-links" aria-label="<?php esc_attr_e( 'Customer service resources', 'skyyrose-flagship-2' ); ?>"><a href="<?php echo esc_url( home_url( '/shipping-returns/' ) ); ?>"><span><?php esc_html_e( 'Shipping + Returns', 'skyyrose-flagship-2' ); ?></span><b>↗</b></a><a href="<?php echo esc_url( home_url( '/size-guide/' ) ); ?>"><span><?php esc_html_e( 'Size Guide', 'skyyrose-flagship-2' ); ?></span><b>↗</b></a><a href="<?php echo esc_url( home_url( '/faq/' ) ); ?>"><span><?php esc_html_e( 'FAQ', 'skyyrose-flagship-2' ); ?></span><b>↗</b></a></nav>

		<?php else : ?>
			<header class="sr2-generic-head"><p class="sr2-eyebrow"><?php echo esc_html( get_the_title() ); ?></p><h1><?php the_title(); ?></h1></header><div class="sr2-page-copy sr2-page-copy--generic"><?php the_content(); ?></div>
		<?php endif; ?>
	</main>
	<?php
endwhile;

get_footer();
