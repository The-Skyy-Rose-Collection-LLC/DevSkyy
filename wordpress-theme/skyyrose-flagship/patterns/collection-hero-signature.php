<?php
/**
 * Title: Signature Collection Hero
 * Slug: skyyrose/collection-hero-signature
 * Categories: skyyrose-collections
 * Description: Full-width hero section for the Signature collection with gold accent.
 * Keywords: hero, signature, collection, luxury
 * Block Types: core/group
 *
 * @package SkyyRose
 * Post Types: page
 */

$collection = function_exists( 'skyyrose_get_collection' ) ? skyyrose_get_collection( 'signature' ) : null;
$label      = $collection ? $collection['label'] : esc_html__( 'Signature', 'skyyrose' );
$tagline    = $collection ? $collection['tagline'] : esc_html__( 'Elevated, confident, refined', 'skyyrose' );
$desc       = $collection ? $collection['description'] : '';
?>
<!-- wp:group {"align":"full","style":{"color":{"background":"#0A0A0A"},"spacing":{"padding":{"top":"var:preset|spacing|2xl","bottom":"var:preset|spacing|2xl","left":"var:preset|spacing|lg","right":"var:preset|spacing|lg"}}},"layout":{"type":"constrained","contentSize":"1200px"}} -->
<div class="wp-block-group alignfull has-background" style="background-color:#0A0A0A;padding-top:var(--wp--preset--spacing--2xl);padding-right:var(--wp--preset--spacing--lg);padding-bottom:var(--wp--preset--spacing--2xl);padding-left:var(--wp--preset--spacing--lg)">

<!-- wp:heading {"level":1,"style":{"typography":{"fontStyle":"normal","fontWeight":"700","letterSpacing":"-0.025em"}},"textColor":"gold","fontFamily":"archivo"} -->
<h1 class="wp-block-heading has-gold-color has-text-color has-archivo-font-family" style="font-style:normal;font-weight:700;letter-spacing:-0.025em"><?php echo esc_html( $label ); ?></h1>
<!-- /wp:heading -->

<!-- wp:paragraph {"style":{"typography":{"fontSize":"1.25rem","lineHeight":"1.6"}},"textColor":"text-secondary","fontFamily":"hanken-grotesk"} -->
<p class="has-text-secondary-color has-text-color has-hanken-grotesk-font-family" style="font-size:1.25rem;line-height:1.6"><?php echo esc_html( $tagline ); ?></p>
<!-- /wp:paragraph -->

<?php if ( $desc ) : ?>
<!-- wp:paragraph {"textColor":"text-muted"} -->
<p class="has-text-muted-color has-text-color"><?php echo esc_html( $desc ); ?></p>
<!-- /wp:paragraph -->
<?php endif; ?>

<!-- wp:buttons -->
<div class="wp-block-buttons">
<!-- wp:button {"backgroundColor":"gold","textColor":"black","style":{"border":{"radius":"4px"},"typography":{"textTransform":"uppercase","letterSpacing":"0.1em","fontStyle":"normal","fontWeight":"600"}},"fontFamily":"inter"} -->
<div class="wp-block-button"><a class="wp-block-button__link has-black-color has-gold-background-color has-text-color has-background has-inter-font-family wp-element-button" style="border-radius:4px;font-style:normal;font-weight:600;letter-spacing:0.1em;text-transform:uppercase"><?php esc_html_e( 'Shop Signature', 'skyyrose' ); ?></a></div>
<!-- /wp:button -->
</div>
<!-- /wp:buttons -->

</div>
<!-- /wp:group -->
