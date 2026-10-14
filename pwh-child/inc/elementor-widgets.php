<?php
/**
 * Custom Elementor widgets: PWH Pricing Card and PWH Billing Toggle.
 *
 * Built from the Figma "Card / Pricing" and "Toggle / Billing" components.
 * A Billing Toggle switches every Pricing Card on the page between monthly
 * and yearly (assets/js/pwh-pricing.js). Cards with no yearly price keep
 * showing their monthly price.
 *
 * @package pwh-child
 */

defined( 'ABSPATH' ) || exit;

add_action(
	'elementor/elements/categories_registered',
	function ( $elements_manager ) {
		$elements_manager->add_category( 'pwh', array( 'title' => 'Perth Web Hosting', 'icon' => 'fa fa-server' ) );
	}
);

add_action(
	'elementor/widgets/register',
	function ( $widgets_manager ) {
		$widgets_manager->register( new PWH_Pricing_Card_Widget() );
		$widgets_manager->register( new PWH_Billing_Toggle_Widget() );
	}
);

add_action(
	'wp_enqueue_scripts',
	function () {
		wp_register_script( 'pwh-pricing', PWH_CHILD_URI . '/assets/js/pwh-pricing.js', array(), filemtime( PWH_CHILD_DIR . '/assets/js/pwh-pricing.js' ), true );
	}
);

add_action(
	'elementor/init',
	function () {
		if ( ! class_exists( '\Elementor\Widget_Base' ) ) {
			return;
		}

		/**
		 * Pricing card.
		 */
		class PWH_Pricing_Card_Widget extends \Elementor\Widget_Base {

			public function get_name() {
				return 'pwh-pricing-card';
			}

			public function get_title() {
				return 'PWH Pricing Card';
			}

			public function get_icon() {
				return 'eicon-price-table';
			}

			public function get_categories() {
				return array( 'pwh' );
			}

			public function get_keywords() {
				return array( 'pricing', 'plan', 'price', 'hosting' );
			}

			public function get_script_depends() {
				return array( 'pwh-pricing' );
			}

			protected function register_controls() {
				$c = '\Elementor\Controls_Manager';

				$this->start_controls_section( 'plan', array( 'label' => 'Plan' ) );
				$this->add_control( 'featured', array( 'label' => 'Featured (navy border, amber button)', 'type' => $c::SWITCHER, 'default' => '' ) );
				$this->add_control( 'tag', array( 'label' => 'Tag', 'type' => $c::TEXT, 'default' => '', 'placeholder' => 'MOST POPULAR' ) );
				$this->add_control( 'title', array( 'label' => 'Plan name', 'type' => $c::TEXT, 'default' => 'Starter' ) );
				$this->add_control( 'description', array( 'label' => 'Description', 'type' => $c::TEXTAREA, 'rows' => 2, 'default' => 'For your first website.' ) );
				$this->end_controls_section();

				$this->start_controls_section( 'pricing', array( 'label' => 'Price' ) );
				$this->add_control( 'currency', array( 'label' => 'Currency symbol', 'type' => $c::TEXT, 'default' => '$' ) );
				$this->add_control( 'monthly_heading', array( 'label' => 'Monthly', 'type' => $c::HEADING ) );
				$this->add_control( 'monthly_price', array( 'label' => 'Price', 'type' => $c::TEXT, 'default' => '7.95' ) );
				$this->add_control( 'monthly_period', array( 'label' => 'Period', 'type' => $c::TEXT, 'default' => '/ month' ) );
				$this->add_control( 'monthly_note', array( 'label' => 'Note', 'type' => $c::TEXT, 'default' => 'Billed monthly. Cancel any time.' ) );
				$this->add_control( 'monthly_url', array( 'label' => 'Order link', 'type' => $c::URL, 'default' => array( 'url' => '' ) ) );
				$this->add_control( 'yearly_heading', array( 'label' => 'Yearly', 'type' => $c::HEADING, 'separator' => 'before' ) );
				$this->add_control( 'yearly_price', array( 'label' => 'Price', 'type' => $c::TEXT, 'default' => '', 'description' => 'Leave empty to keep showing the monthly price when Yearly is selected.' ) );
				$this->add_control( 'yearly_period', array( 'label' => 'Period', 'type' => $c::TEXT, 'default' => '/ year' ) );
				$this->add_control( 'yearly_note', array( 'label' => 'Note', 'type' => $c::TEXT, 'default' => '' ) );
				$this->add_control( 'yearly_url', array( 'label' => 'Order link', 'type' => $c::URL, 'default' => array( 'url' => '' ) ) );
				$this->add_control( 'button_text', array( 'label' => 'Button text', 'type' => $c::TEXT, 'default' => 'Order Now', 'separator' => 'before' ) );
				$this->end_controls_section();

				$this->start_controls_section( 'features_section', array( 'label' => 'Features' ) );
				$rep = new \Elementor\Repeater();
				$rep->add_control( 'text', array( 'label' => 'Feature', 'type' => $c::TEXT, 'default' => 'Feature', 'label_block' => true ) );
				$this->add_control(
					'features',
					array(
						'label'       => 'Features',
						'type'        => $c::REPEATER,
						'fields'      => $rep->get_controls(),
						'title_field' => '{{{ text }}}',
						'default'     => array( array( 'text' => 'Free SSL certificate' ) ),
					)
				);
				$this->add_control( 'details', array( 'label' => 'Technical details (shown with +)', 'type' => $c::TEXTAREA, 'rows' => 3, 'default' => '', 'description' => 'One item per line. Leave empty to hide the + toggle.', 'separator' => 'before' ) );
				$this->end_controls_section();
			}

			private function link_attrs( $link ) {
				$url = ! empty( $link['url'] ) ? $link['url'] : '#';
				$out = ' href="' . esc_url( $url ) . '"';
				if ( ! empty( $link['is_external'] ) ) {
					$out .= ' target="_blank"';
				}
				if ( ! empty( $link['nofollow'] ) || ! empty( $link['is_external'] ) ) {
					$rel  = array_filter( array( ! empty( $link['nofollow'] ) ? 'nofollow' : '', ! empty( $link['is_external'] ) ? 'noopener' : '' ) );
					$out .= ' rel="' . esc_attr( implode( ' ', $rel ) ) . '"';
				}
				return $out;
			}

			private function price_block( $s, $which ) {
				?>
				<div class="pwh-price pwh-price--<?php echo esc_attr( $which ); ?>"<?php echo 'yearly' === $which ? ' hidden' : ''; ?>>
					<div class="pwh-price__row">
						<span class="pwh-price__amount"><span class="pwh-price__currency"><?php echo esc_html( $s['currency'] ); ?></span><?php echo esc_html( $s[ $which . '_price' ] ); ?></span>
						<span class="pwh-price__period"><?php echo esc_html( $s[ $which . '_period' ] ); ?></span>
					</div>
					<?php if ( '' !== trim( (string) $s[ $which . '_note' ] ) ) : ?>
						<p class="pwh-price__note"><?php echo esc_html( $s[ $which . '_note' ] ); ?></p>
					<?php endif; ?>
				</div>
				<?php
			}

			protected function render() {
				$s          = $this->get_settings_for_display();
				$featured   = 'yes' === $s['featured'];
				$has_yearly = '' !== trim( (string) $s['yearly_price'] );
				$details    = array_filter( array_map( 'trim', preg_split( '/\R/', (string) $s['details'] ) ) );
				$details_id = 'pwh-details-' . $this->get_id();
				$btn_class  = $featured ? 'pwh-plan__btn pwh-plan__btn--amber' : 'pwh-plan__btn pwh-plan__btn--navy';
				?>
				<div class="pwh-plan<?php echo $featured ? ' pwh-plan--featured' : ''; ?>"<?php echo $has_yearly ? ' data-has-yearly' : ''; ?>>
					<?php if ( '' !== trim( (string) $s['tag'] ) ) : ?>
						<span class="pwh-plan__tag"><?php echo esc_html( $s['tag'] ); ?></span>
					<?php endif; ?>
					<h3 class="pwh-plan__title"><?php echo esc_html( $s['title'] ); ?></h3>
					<p class="pwh-plan__desc"><?php echo esc_html( $s['description'] ); ?></p>

					<?php
					$this->price_block( $s, 'monthly' );
					if ( $has_yearly ) {
						$this->price_block( $s, 'yearly' );
					}
					?>

					<a class="<?php echo esc_attr( $btn_class ); ?> pwh-plan__btn--monthly"<?php echo $this->link_attrs( $s['monthly_url'] ); // phpcs:ignore WordPress.Security.EscapeOutput ?>><?php echo esc_html( $s['button_text'] ); ?></a>
					<?php if ( $has_yearly ) : ?>
						<a class="<?php echo esc_attr( $btn_class ); ?> pwh-plan__btn--yearly" hidden<?php echo $this->link_attrs( ! empty( $s['yearly_url']['url'] ) ? $s['yearly_url'] : $s['monthly_url'] ); // phpcs:ignore WordPress.Security.EscapeOutput ?>><?php echo esc_html( $s['button_text'] ); ?></a>
					<?php endif; ?>

					<hr class="pwh-plan__rule">

					<ul class="pwh-plan__features">
						<?php foreach ( (array) $s['features'] as $f ) : ?>
							<li><?php echo esc_html( $f['text'] ); ?></li>
						<?php endforeach; ?>
					</ul>

					<?php if ( $details ) : ?>
						<button type="button" class="pwh-plan__more" aria-expanded="false" aria-controls="<?php echo esc_attr( $details_id ); ?>">
							<span class="screen-reader-text">Technical details</span>
						</button>
						<ul class="pwh-plan__details" id="<?php echo esc_attr( $details_id ); ?>" hidden>
							<?php foreach ( $details as $d ) : ?>
								<li><?php echo esc_html( $d ); ?></li>
							<?php endforeach; ?>
						</ul>
					<?php endif; ?>
				</div>
				<?php
			}
		}

		/**
		 * Monthly / Yearly switch.
		 */
		class PWH_Billing_Toggle_Widget extends \Elementor\Widget_Base {

			public function get_name() {
				return 'pwh-billing-toggle';
			}

			public function get_title() {
				return 'PWH Billing Toggle';
			}

			public function get_icon() {
				return 'eicon-toggle';
			}

			public function get_categories() {
				return array( 'pwh' );
			}

			public function get_script_depends() {
				return array( 'pwh-pricing' );
			}

			protected function register_controls() {
				$c = '\Elementor\Controls_Manager';
				$this->start_controls_section( 'labels', array( 'label' => 'Labels' ) );
				$this->add_control( 'monthly_label', array( 'label' => 'Monthly', 'type' => $c::TEXT, 'default' => 'Monthly' ) );
				$this->add_control( 'yearly_label', array( 'label' => 'Yearly', 'type' => $c::TEXT, 'default' => 'Yearly' ) );
				$this->add_control( 'yearly_badge', array( 'label' => 'Yearly badge', 'type' => $c::TEXT, 'default' => 'Best value' ) );
				$this->add_control(
					'default',
					array(
						'label'   => 'Selected by default',
						'type'    => $c::SELECT,
						'default' => 'monthly',
						'options' => array( 'monthly' => 'Monthly', 'yearly' => 'Yearly' ),
					)
				);
				$this->end_controls_section();
			}

			protected function render() {
				$s   = $this->get_settings_for_display();
				$def = 'yearly' === $s['default'] ? 'yearly' : 'monthly';
				?>
				<div class="pwh-billing" role="radiogroup" aria-label="Billing period" data-default="<?php echo esc_attr( $def ); ?>">
					<button type="button" role="radio" class="pwh-billing__opt" data-billing="monthly" aria-checked="<?php echo 'monthly' === $def ? 'true' : 'false'; ?>"><?php echo esc_html( $s['monthly_label'] ); ?></button>
					<button type="button" role="radio" class="pwh-billing__opt" data-billing="yearly" aria-checked="<?php echo 'yearly' === $def ? 'true' : 'false'; ?>">
						<?php echo esc_html( $s['yearly_label'] ); ?>
						<?php if ( '' !== trim( (string) $s['yearly_badge'] ) ) : ?>
							<span class="pwh-billing__badge"><?php echo esc_html( $s['yearly_badge'] ); ?></span>
						<?php endif; ?>
					</button>
				</div>
				<?php
			}
		}
	}
);
