<?php
/**
 * One-click site setup: imports the Elementor templates built from Figma,
 * creates the primary menu and wires JetMenu mega content to it.
 *
 * Run from Appearance → PWH Setup, or `wp pwh setup` with WP-CLI.
 *
 * Re-running never touches the header, footer, primary menu or JetMenu mega
 * content once they exist; those are maintained in Elementor/WordPress by hand.
 * The Home page and kit globals are only re-applied when asked for explicitly
 * (checkboxes on the setup page, or --home / --kit with WP-CLI).
 *
 * @package pwh-child
 */

defined( 'ABSPATH' ) || exit;

class PWH_Setup {

	const OPTION = 'pwh_setup_state';

	/**
	 * Theme Builder templates and pages. key => [ file, Elementor type, title ].
	 */
	const TEMPLATES = array(
		'header'        => array( 'header.json', 'header', 'PWH – Header' ),
		'footer'        => array( 'footer.json', 'footer', 'PWH – Footer' ),
		'mega-products' => array( 'mega-products.json', 'section', 'PWH – Mega Menu / Products' ),
		'mega-support'  => array( 'mega-support.json', 'section', 'PWH – Mega Menu / Support' ),
		'mega-about'    => array( 'mega-about.json', 'section', 'PWH – Mega Menu / About' ),
	);

	/**
	 * Primary menu. Items with a "mega" key get JetMenu mega content.
	 * Children are kept for JetMenu's mobile menu and for non-mega fallbacks.
	 */
	const MENU = array(
		array(
			'title'    => 'Products',
			'url'      => '/products/',
			'mega'     => 'mega-products',
			'width'    => 1180,
			'position' => 'default',
			'children' => array(
				array( 'Search Domains', '/domains/search/' ),
				array( 'Transfer Domains', '/domains/transfer/' ),
				array( 'cPanel Hosting', '/web-hosting/cpanel/' ),
				array( 'Semi-managed WordPress', '/web-hosting/wordpress/' ),
				array( 'Email', '/email/' ),
				array( 'Microsoft 365', '/email/microsoft-365/' ),
				array( 'Reseller', '/reseller-hosting/' ),
				array( 'VPS', '/vps-hosting/' ),
			),
		),
		array(
			'title'    => 'About',
			'url'      => '/about/',
			'mega'     => 'mega-about',
			'width'    => 280,
			'position' => 'relative-item',
			'children' => array(
				array( 'About Us', '/about/' ),
				array( 'Privacy Policy', '/privacy-policy/' ),
				array( 'Terms of Service', '/terms-of-service/' ),
				array( 'Acceptable Use Policy', '/acceptable-use-policy/' ),
			),
		),
		array(
			'title'    => 'Support',
			'url'      => '/support/',
			'mega'     => 'mega-support',
			'width'    => 1180,
			'position' => 'default',
			'children' => array(
				array( 'Contact Us', '/contact/' ),
				array( 'Remote Support', '/support/remote-support/' ),
				array( 'Mac Remote Support', '/support/mac-remote-support/' ),
				array( 'Knowledge Base', '/knowledge-base/' ),
				array( 'Network Status', '/network-status/' ),
				array( 'Hosting Transfer Request', '/support/hosting-transfer-request/' ),
				array( 'Service Level Agreement', '/service-level-agreement/' ),
				array( 'Microsoft Transfer', '/support/microsoft-transfer-request/' ),
				array( 'MyToolbox', '/client-login/' ),
				array( 'Submit a Ticket', '/submit-a-ticket/' ),
			),
		),
	);

	/**
	 * Inner pages. key => [ template file, title, preferred path, fallback path ].
	 * Created at the preferred path when its parent page exists (else the
	 * fallback), never over a page someone else made there, and protected after
	 * the first import like the Home page.
	 */
	const PAGES = array(
		'cpanel'  => array( 'cpanel.json', 'cPanel Hosting', 'web-hosting/cpanel', 'cpanel-hosting' ),
		'domains' => array( 'domains.json', 'Domains', 'domains', 'domains' ),
		'about'   => array( 'about.json', 'About Us', 'about', 'about' ),
		'wordpress' => array( 'wordpress.json', 'Semi-managed WordPress', 'web-hosting/wordpress', 'wordpress-hosting' ),
	);

	/** @var array */
	public $state;

	/** @var string[] */
	private $log = array();

	/** @var array<string,int> Imported attachment IDs by asset path. */
	private $attachments = array();

	public static function init() {
		add_action( 'admin_menu', array( __CLASS__, 'admin_menu' ) );
		add_action( 'admin_post_pwh_setup', array( __CLASS__, 'handle_post' ) );
		add_action( 'admin_notices', array( __CLASS__, 'activation_notice' ) );

		if ( defined( 'WP_CLI' ) && WP_CLI ) {
			WP_CLI::add_command(
				'pwh setup',
				function ( $args, $assoc ) {
					$setup = new self();
					$setup->run(
						array(
							'home'  => ! empty( $assoc['home'] ),
							'pages' => array_keys( array_intersect_key( $assoc, self::PAGES ) ),
							'kit'  => ! empty( $assoc['kit'] ),
						)
					);
					foreach ( $setup->log as $line ) {
						WP_CLI::log( $line );
					}
					WP_CLI::success( 'PWH setup complete.' );
				}
			);
		}
	}

	public static function admin_menu() {
		add_theme_page( 'PWH Setup', 'PWH Setup', 'manage_options', 'pwh-setup', array( __CLASS__, 'render_page' ) );
	}

	public static function activation_notice() {
		$screen = get_current_screen();
		if ( get_option( self::OPTION ) || ! current_user_can( 'manage_options' ) || ( $screen && 'appearance_page_pwh-setup' === $screen->id ) ) {
			return;
		}
		printf(
			'<div class="notice notice-info"><p>%s <a href="%s">%s</a></p></div>',
			esc_html__( 'Perth Web Hosting theme: import the header, footer, home page and mega menus.', 'pwh-child' ),
			esc_url( admin_url( 'themes.php?page=pwh-setup' ) ),
			esc_html__( 'Run PWH Setup →', 'pwh-child' )
		);
	}

	public static function render_page() {
		$checks = array(
			'Elementor'     => did_action( 'elementor/loaded' ),
			'Elementor Pro' => defined( 'ELEMENTOR_PRO_VERSION' ),
			'JetMenu'       => function_exists( 'jet_menu' ) || class_exists( 'Jet_Menu' ),
		);
		$log = get_transient( 'pwh_setup_log' );
		delete_transient( 'pwh_setup_log' );
		?>
		<div class="wrap">
			<h1>Perth Web Hosting – Setup</h1>
			<p>Imports the Figma build into Elementor: Theme Builder header &amp; footer, the Home page (set as the front page), the three mega menu panels, the <em>PWH Primary</em> menu wired to JetMenu, and the site kit colours &amp; fonts. Re-running updates the same posts.</p>

			<h2>Requirements</h2>
			<ul>
				<?php foreach ( $checks as $label => $ok ) : ?>
					<li><?php echo $ok ? '✅' : '❌'; ?> <?php echo esc_html( $label ); ?></li>
				<?php endforeach; ?>
			</ul>

			<?php
			$setup  = new self();
			$exists = $setup->existing();
			?>
			<h2>Protected</h2>
			<p>These are never imported over once they exist. Edit them in Elementor / Appearance → Menus.</p>
			<ul>
				<li><?php echo $exists['header'] ? '🔒 Header – exists, kept as is' : '➕ Header – will be imported'; ?></li>
				<li><?php echo $exists['footer'] ? '🔒 Footer – exists, kept as is' : '➕ Footer – will be imported'; ?></li>
				<li><?php echo $exists['menu'] ? '🔒 PWH Primary menu &amp; JetMenu mega content – exists, kept as is' : '➕ PWH Primary menu &amp; JetMenu mega content – will be created'; ?></li>
			</ul>

			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<?php wp_nonce_field( 'pwh_setup' ); ?>
				<input type="hidden" name="action" value="pwh_setup">
				<h2>Optional</h2>
				<p>
					<label><input type="checkbox" name="pwh_home" value="1" <?php checked( ! $exists['home'] ); ?>>
					<?php echo $exists['home'] ? '<strong>Re-import the Home page</strong> – overwrites any edits made to it in Elementor' : 'Import the Home page'; ?></label>
				</p>
				<?php foreach ( self::PAGES as $key => $def ) : ?>
					<p>
						<label><input type="checkbox" name="pwh_pages[<?php echo esc_attr( $key ); ?>]" value="1" <?php checked( ! $exists['pages'][ $key ] ); ?>>
						<?php echo $exists['pages'][ $key ] ? '<strong>Re-import the ' . esc_html( $def[1] ) . ' page</strong> – overwrites any edits made to it in Elementor' : 'Import the ' . esc_html( $def[1] ) . ' page'; ?></label>
					</p>
				<?php endforeach; ?>
				<p>
					<label><input type="checkbox" name="pwh_kit" value="1" <?php checked( empty( $setup->state['kit_done'] ) ); ?>>
					<?php echo empty( $setup->state['kit_done'] ) ? 'Apply PWH colours &amp; fonts to the Elementor kit' : '<strong>Re-apply PWH colours &amp; fonts</strong> – overwrites changes made in Site Settings'; ?></label>
				</p>
				<?php submit_button( get_option( self::OPTION ) ? 'Re-run setup' : 'Run setup', 'primary', 'submit', true, $checks['Elementor'] ? array() : array( 'disabled' => 'disabled' ) ); ?>
			</form>

			<?php if ( $log ) : ?>
				<h2>Log</h2>
				<pre style="background:#fff;padding:12px;border:1px solid #ccd0d4;max-height:400px;overflow:auto"><?php echo esc_html( implode( "\n", $log ) ); ?></pre>
			<?php endif; ?>
		</div>
		<?php
	}

	public static function handle_post() {
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( 'Not allowed.' );
		}
		check_admin_referer( 'pwh_setup' );

		$setup = new self();
		$setup->run(
			array(
				'home'  => ! empty( $_POST['pwh_home'] ),
				'pages' => array_map( 'sanitize_key', array_keys( (array) ( $_POST['pwh_pages'] ?? array() ) ) ),
				'kit'  => ! empty( $_POST['pwh_kit'] ),
			)
		);

		set_transient( 'pwh_setup_log', $setup->log, 5 * MINUTE_IN_SECONDS );
		wp_safe_redirect( admin_url( 'themes.php?page=pwh-setup' ) );
		exit;
	}

	public function __construct() {
		$this->state = wp_parse_args(
			(array) get_option( self::OPTION, array() ),
			array( 'templates' => array(), 'jet' => array(), 'jet_items' => array(), 'home' => 0, 'pages' => array(), 'menu' => 0, 'attachments' => array() )
		);
		$this->attachments = (array) $this->state['attachments'];
	}

	/**
	 * What already exists on the site. Header/footer count if ANY Theme Builder
	 * header/footer exists, so a hand-built one is never shadowed by an import.
	 */
	public function existing() {
		$has_type = function ( $type ) {
			$q = new WP_Query(
				array(
					'post_type'      => 'elementor_library',
					'post_status'    => array( 'publish', 'draft', 'private', 'future', 'pending' ),
					'posts_per_page' => 1,
					'fields'         => 'ids',
					'no_found_rows'  => true,
					'meta_key'       => '_elementor_template_type', // phpcs:ignore WordPress.DB.SlowDBQuery
					'meta_value'     => $type, // phpcs:ignore WordPress.DB.SlowDBQuery
				)
			);
			return (bool) $q->posts;
		};

		$menu_id = (int) $this->state['menu'];
		$menu    = ( $menu_id && wp_get_nav_menu_object( $menu_id ) ) || wp_get_nav_menu_object( 'PWH Primary' );

		return array(
			'header' => $has_type( 'header' ),
			'footer' => $has_type( 'footer' ),
			'menu'   => (bool) $menu,
			'home'   => $this->state['home'] && get_post( $this->state['home'] ),
			'pages'  => array_map(
				function ( $key ) {
					return ! empty( $this->state['pages'][ $key ] ) && get_post( $this->state['pages'][ $key ] );
				},
				array_combine( array_keys( self::PAGES ), array_keys( self::PAGES ) )
			),
		);
	}

	/**
	 * @param array $opts { home: bool, pages: string[] PAGES keys to (re-)import, kit: bool }.
	 */
	public function run( array $opts = array() ) {
		if ( ! did_action( 'elementor/loaded' ) ) {
			$this->log[] = 'Elementor is not active – nothing imported.';
			return;
		}

		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';

		$exists = $this->existing();

		if ( ! empty( $opts['kit'] ) || empty( $this->state['kit_done'] ) ) {
			$this->setup_kit();
			$this->state['kit_done'] = 1;
		} else {
			$this->log[] = 'Kit colours & fonts: kept as is';
		}

		// Menu + JetMenu mega content: created once, then left alone.
		if ( $exists['menu'] ) {
			$menu                = wp_get_nav_menu_object( (int) $this->state['menu'] ) ?: wp_get_nav_menu_object( 'PWH Primary' );
			$this->state['menu'] = (int) $menu->term_id;
			$this->log[]         = "Menu \"{$menu->name}\" (#{$menu->term_id}) and its mega content: protected, not changed";
		} else {
			$this->state['menu'] = $this->setup_menu();
		}

		$this->state['templates'] = (array) $this->state['templates'];
		$new_theme_parts          = false;

		foreach ( self::TEMPLATES as $key => $def ) {
			list( $file, $type, $title ) = $def;

			if ( in_array( $type, array( 'header', 'footer' ), true ) && $exists[ $type ] ) {
				$this->log[] = ucfirst( $type ) . ': protected, not changed';
				continue;
			}
			// Saved mega templates are reference copies; create once, never overwrite.
			if ( ! empty( $this->state['templates'][ $key ] ) && get_post( $this->state['templates'][ $key ] ) ) {
				$this->log[] = "Template \"$title\": exists, not changed";
				continue;
			}

			$data = $this->load( $file );
			if ( ! $data ) {
				continue;
			}
			$id = $this->upsert_library_template( $key, $title, $type, $data );
			if ( in_array( $type, array( 'header', 'footer' ), true ) ) {
				update_post_meta( $id, '_elementor_conditions', array( 'include/general' ) );
				$new_theme_parts = true;
			}
		}

		if ( ! empty( $opts['home'] ) || ! $exists['home'] ) {
			$this->setup_home();
		} else {
			$this->log[] = 'Home page: kept as is (tick "Re-import the Home page" to overwrite)';
		}

		$wanted = isset( $opts['pages'] ) ? (array) $opts['pages'] : array();
		foreach ( self::PAGES as $key => $def ) {
			if ( in_array( $key, $wanted, true ) || ! $exists['pages'][ $key ] ) {
				$this->setup_page( $key );
			} else {
				$this->log[] = "{$def[1]} page: kept as is (tick \"Re-import the {$def[1]} page\" to overwrite)";
			}
		}

		if ( ! $exists['menu'] ) {
			$this->setup_jetmenu( $this->state['menu'] );
		}
		$this->finish( $new_theme_parts );

		$this->state['attachments'] = $this->attachments;
		update_option( self::OPTION, $this->state, false );
	}

	/* ---------------------------------------------------------------------
	 * Templates
	 * ------------------------------------------------------------------ */

	private function load( $file ) {
		$path = PWH_CHILD_DIR . '/elementor-templates/' . $file;
		if ( ! is_readable( $path ) ) {
			$this->log[] = "Missing template file: $file";
			return null;
		}
		$json = json_decode( file_get_contents( $path ), true ); // phpcs:ignore WordPress.WP.AlternativeFunctions
		if ( empty( $json['content'] ) ) {
			$this->log[] = "Invalid template file: $file";
			return null;
		}
		return $json;
	}

	/**
	 * Resolve {{PWH_*}} placeholders throughout an element tree.
	 */
	private function resolve( $node ) {
		if ( is_array( $node ) ) {
			// Image controls: { url: "{{PWH_ASSET:...}}", id: "" }.
			if ( isset( $node['url'] ) && is_string( $node['url'] ) && 0 === strpos( $node['url'], '{{PWH_ASSET:' ) ) {
				$path        = substr( $node['url'], 12, -2 );
				$node['url'] = PWH_CHILD_URI . '/assets/' . $path;
				$att         = $this->import_attachment( $path );
				if ( $att ) {
					$node['id']  = $att;
					$node['url'] = wp_get_attachment_url( $att );
				}
				return $node;
			}
			// Image controls pointing at a file already in the Media Library (the logos).
			if ( isset( $node['url'], $node['id'] ) && '' === $node['id'] && is_string( $node['url'] ) && preg_match( '#/wp-content/uploads/#', $node['url'] ) ) {
				$att = $this->find_media( $node['url'] );
				if ( $att ) {
					$node['id']  = $att;
					$node['url'] = wp_get_attachment_url( $att );
				} else {
					$this->log[] = 'Not in the Media Library, using the URL as is: ' . $node['url'];
				}
				return $node;
			}
			foreach ( $node as $k => $v ) {
				$node[ $k ] = $this->resolve( $v );
			}
			return $node;
		}

		if ( is_string( $node ) && false !== strpos( $node, '{{PWH_' ) ) {
			$node = preg_replace_callback(
				'/\{\{PWH_URL:([^}]*)\}\}/',
				function ( $m ) {
					return home_url( $m[1] );
				},
				$node
			);
			$node = preg_replace_callback(
				'/\{\{PWH_MENU:([^}]*)\}\}/',
				function () {
					return (string) $this->state['menu'];
				},
				$node
			);
			$node = preg_replace_callback(
				'/\{\{PWH_ASSET:([^}]*)\}\}/',
				function ( $m ) {
					return PWH_CHILD_URI . '/assets/' . $m[1];
				},
				$node
			);
		}
		return $node;
	}

	/**
	 * Find an attachment by URL, falling back to its file name so a template
	 * built against the dev site still resolves on the live domain.
	 */
	private function find_media( $url ) {
		$id = attachment_url_to_postid( $url );
		if ( $id ) {
			return $id;
		}

		global $wpdb;
		$file = wp_basename( wp_parse_url( $url, PHP_URL_PATH ) );
		$id   = $wpdb->get_var( // phpcs:ignore WordPress.DB.DirectDatabaseQuery
			$wpdb->prepare(
				"SELECT post_id FROM {$wpdb->postmeta} WHERE meta_key = '_wp_attached_file' AND ( meta_value = %s OR meta_value LIKE %s ) ORDER BY post_id DESC LIMIT 1",
				$file,
				'%/' . $wpdb->esc_like( $file )
			)
		);
		return (int) $id;
	}

	/**
	 * Raster images go into the Media Library so Elementor can serve responsive
	 * sizes. SVGs stay as theme files (WordPress blocks SVG uploads by default).
	 */
	private function import_attachment( $path ) {
		if ( ! preg_match( '/\.(png|jpe?g|webp|gif)$/i', $path ) ) {
			return 0;
		}
		if ( ! empty( $this->attachments[ $path ] ) && get_post( $this->attachments[ $path ] ) ) {
			return (int) $this->attachments[ $path ];
		}

		$file = PWH_CHILD_DIR . '/assets/' . $path;
		if ( ! is_readable( $file ) ) {
			$this->log[] = "Asset not found (export it from Figma – see README): assets/$path";
			return 0;
		}

		$tmp = wp_tempnam( basename( $file ) );
		copy( $file, $tmp );
		$id = media_handle_sideload(
			array(
				'name'     => 'pwh-' . basename( $file ),
				'tmp_name' => $tmp,
			),
			0
		);
		if ( is_wp_error( $id ) ) {
			@unlink( $tmp ); // phpcs:ignore WordPress.PHP.NoSilencedErrors
			$this->log[] = "Could not import $path: " . $id->get_error_message();
			return 0;
		}
		$this->attachments[ $path ] = $id;
		$this->log[]                = "Imported image $path (#$id)";
		return $id;
	}

	private function save_elementor_data( $post_id, array $content, $type, array $page_settings = array() ) {
		$content = $this->resolve( $content );

		update_post_meta( $post_id, '_elementor_edit_mode', 'builder' );
		if ( $type ) {
			update_post_meta( $post_id, '_elementor_template_type', $type );
		}
		update_post_meta( $post_id, '_elementor_version', defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : '3.0.0' );
		if ( defined( 'ELEMENTOR_PRO_VERSION' ) ) {
			update_post_meta( $post_id, '_elementor_pro_version', ELEMENTOR_PRO_VERSION );
		}
		update_post_meta( $post_id, '_elementor_data', wp_slash( wp_json_encode( $content ) ) );
		if ( $page_settings ) {
			update_post_meta( $post_id, '_elementor_page_settings', $page_settings );
		}
		delete_post_meta( $post_id, '_elementor_css' );
	}

	private function upsert_library_template( $key, $title, $type, array $data ) {
		$id = isset( $this->state['templates'][ $key ] ) ? (int) $this->state['templates'][ $key ] : 0;
		if ( ! $id || ! get_post( $id ) ) {
			$id = wp_insert_post(
				array(
					'post_type'   => 'elementor_library',
					'post_status' => 'publish',
					'post_title'  => $title,
				)
			);
		}
		wp_set_object_terms( $id, $type, 'elementor_library_type' );
		$this->save_elementor_data( $id, $data['content'], $type );

		$this->state['templates'][ $key ] = $id;
		$this->log[]                      = "Template \"$title\" (#$id)";
		return $id;
	}

	private function setup_home() {
		$data = $this->load( 'home.json' );
		if ( ! $data ) {
			return;
		}

		$id = (int) $this->state['home'];
		if ( ! $id || ! get_post( $id ) ) {
			$id = wp_insert_post(
				array(
					'post_type'   => 'page',
					'post_status' => 'publish',
					'post_title'  => 'Home',
					'post_name'   => 'home',
				)
			);
		}

		update_post_meta( $id, '_wp_page_template', 'elementor_header_footer' );
		$this->save_elementor_data( $id, $data['content'], 'wp-page', array( 'hide_title' => 'yes' ) );

		update_option( 'show_on_front', 'page' );
		update_option( 'page_on_front', $id );

		$this->state['home'] = $id;
		$this->log[]         = "Home page (#$id) set as the front page";
	}

	/**
	 * Import one of self::PAGES. See the PAGES doc for where it's created.
	 */
	private function setup_page( $key ) {
		list( $file, $title, $path, $fallback ) = self::PAGES[ $key ];

		$data = $this->load( $file );
		if ( ! $data ) {
			return;
		}

		$this->state['pages'] = (array) $this->state['pages'];
		$id                   = isset( $this->state['pages'][ $key ] ) ? (int) $this->state['pages'][ $key ] : 0;

		if ( ! $id || ! get_post( $id ) ) {
			$parent_path = false !== strpos( $path, '/' ) ? dirname( $path ) : '';
			$parent      = $parent_path ? get_page_by_path( $parent_path ) : null;
			if ( $parent_path && ! $parent ) {
				$path = $fallback;
			}
			$slug = basename( $path );
			if ( get_page_by_path( $path ) ) {
				$this->log[] = "A page already exists at /$path/ – left alone; the $title page uses /$slug-new/ instead";
				$slug       .= '-new';
			}
			$id = wp_insert_post(
				array(
					'post_type'   => 'page',
					'post_status' => 'publish',
					'post_title'  => $title,
					'post_name'   => $slug,
					'post_parent' => $parent ? $parent->ID : 0,
				)
			);
		}

		update_post_meta( $id, '_wp_page_template', 'elementor_header_footer' );
		$this->save_elementor_data( $id, $data['content'], 'wp-page', array( 'hide_title' => 'yes' ) );

		$this->state['pages'][ $key ] = $id;
		$this->log[]                  = "$title page (#$id): " . get_permalink( $id );
	}

	/* ---------------------------------------------------------------------
	 * Kit: colours, fonts, layout
	 * ------------------------------------------------------------------ */

	private function setup_kit() {
		// Stop Elementor injecting its default global colours/fonts into widgets,
		// which would override the theme classes.
		update_option( 'elementor_disable_color_schemes', 'yes' );
		update_option( 'elementor_disable_typography_schemes', 'yes' );

		$kit_id = (int) get_option( 'elementor_active_kit' );
		if ( ! $kit_id ) {
			$this->log[] = 'No active Elementor kit found – skipped global colours/fonts.';
			return;
		}

		$settings = get_post_meta( $kit_id, '_elementor_page_settings', true );
		$settings = is_array( $settings ) ? $settings : array();

		$settings['system_colors'] = array(
			array( '_id' => 'primary', 'title' => 'Navy Ink', 'color' => '#0B1629' ),
			array( '_id' => 'secondary', 'title' => 'Navy', 'color' => '#1A325B' ),
			array( '_id' => 'text', 'title' => 'Grey Dark', 'color' => '#575557' ),
			array( '_id' => 'accent', 'title' => 'Amber', 'color' => '#C89439' ),
		);
		$settings['custom_colors'] = array(
			array( '_id' => 'pwhcream', 'title' => 'Cream', 'color' => '#FFFEF4' ),
			array( '_id' => 'pwhnavydeep', 'title' => 'Navy Deep', 'color' => '#1A315C' ),
			array( '_id' => 'pwhnavysoft', 'title' => 'Navy Soft', 'color' => '#6B91BE' ),
			array( '_id' => 'pwhnavypale', 'title' => 'Navy Pale', 'color' => '#C2D3E8' ),
			array( '_id' => 'pwhnavymist', 'title' => 'Navy Mist', 'color' => '#EAF0F8' ),
			array( '_id' => 'pwhgrey', 'title' => 'Grey', 'color' => '#828082' ),
			array( '_id' => 'pwhgreylight', 'title' => 'Grey Light', 'color' => '#D4D3D5' ),
		);

		$display = function ( $id, $title, $size, $line, $spacing = null, $weight = '900' ) {
			$t = array(
				'_id'                       => $id,
				'title'                     => $title,
				'typography_typography'     => 'custom',
				'typography_font_family'    => 'GT Standard',
				'typography_font_weight'    => $weight,
				'typography_font_size'      => array( 'unit' => 'px', 'size' => $size ),
				'typography_line_height'    => array( 'unit' => 'px', 'size' => $line ),
			);
			if ( null !== $spacing ) {
				$t['typography_letter_spacing'] = array( 'unit' => 'px', 'size' => $spacing );
			}
			return $t;
		};

		$settings['system_typography'] = array(
			$display( 'primary', 'PWH/H2', 40, 46, -0.9 ),
			$display( 'secondary', 'PWH/H3', 28, 34 ),
			array(
				'_id'                    => 'text',
				'title'                  => 'PWH/Body',
				'typography_typography'  => 'custom',
				'typography_font_family' => 'Inter',
				'typography_font_weight' => '400',
				'typography_font_size'   => array( 'unit' => 'px', 'size' => 18 ),
				'typography_line_height' => array( 'unit' => 'px', 'size' => 26 ),
			),
			array(
				'_id'                    => 'accent',
				'title'                  => 'Button',
				'typography_typography'  => 'custom',
				'typography_font_family' => 'Inter',
				'typography_font_weight' => '700',
				'typography_font_size'   => array( 'unit' => 'px', 'size' => 15 ),
			),
		);
		$settings['custom_typography'] = array(
			$display( 'pwhh1', 'PWH/H1', 56, 62, -1.3 ),
			$display( 'pwhcard', 'Card Title', 22, 26 ),
			$display( 'pwheyebrow', 'PWH/Eyebrow', 12, 16, 1.8, '700' ),
		);

		$settings['body_background_background'] = 'classic';
		$settings['body_background_color']      = '#FFFEF4';
		$settings['container_width']            = array( 'unit' => 'px', 'size' => 1180 );
		$settings['container_padding']          = array( 'unit' => 'px', 'top' => '0', 'right' => '0', 'bottom' => '0', 'left' => '0', 'isLinked' => true );
		$settings['space_between_widgets']      = array( 'unit' => 'px', 'size' => 0, 'column' => '0', 'row' => '0', 'isLinked' => true );
		$settings['viewport_tablet']            = 1024;
		$settings['viewport_mobile']            = 767;

		update_post_meta( $kit_id, '_elementor_page_settings', $settings );
		$this->log[] = "Elementor kit (#$kit_id): PWH colours, fonts and 1180px container set";
	}

	/* ---------------------------------------------------------------------
	 * Menu + JetMenu
	 * ------------------------------------------------------------------ */

	private function setup_menu() {
		$menu_id = (int) $this->state['menu'];
		if ( ! $menu_id || ! wp_get_nav_menu_object( $menu_id ) ) {
			$existing = wp_get_nav_menu_object( 'PWH Primary' );
			$menu_id  = $existing ? $existing->term_id : wp_create_nav_menu( 'PWH Primary' );
		}
		if ( is_wp_error( $menu_id ) ) {
			$this->log[] = 'Could not create menu: ' . $menu_id->get_error_message();
			return 0;
		}

		// Only reached when the menu was just created (existing menus are protected).
		foreach ( (array) wp_get_nav_menu_items( $menu_id, array( 'post_status' => 'any' ) ) as $item ) {
			wp_delete_post( $item->ID, true );
		}

		$this->state['jet_items'] = array();
		foreach ( self::MENU as $pos => $top ) {
			$parent = wp_update_nav_menu_item(
				$menu_id,
				0,
				array(
					'menu-item-title'    => $top['title'],
					'menu-item-url'      => home_url( $top['url'] ),
					'menu-item-type'     => 'custom',
					'menu-item-status'   => 'publish',
					'menu-item-position' => $pos + 1,
				)
			);
			$this->state['jet_items'][ $top['mega'] ] = array(
				'item'     => $parent,
				'width'    => $top['width'],
				'position' => $top['position'],
			);

			foreach ( $top['children'] as $child ) {
				list( $title, $url ) = $child;
				wp_update_nav_menu_item(
					$menu_id,
					0,
					array(
						'menu-item-title'     => $title,
						'menu-item-url'       => 0 === strpos( $url, 'http' ) ? $url : home_url( $url ),
						'menu-item-type'      => 'custom',
						'menu-item-status'    => 'publish',
						'menu-item-parent-id' => $parent,
					)
				);
			}
		}

		$locations                = (array) get_theme_mod( 'nav_menu_locations', array() );
		$locations['pwh-primary'] = $menu_id;
		set_theme_mod( 'nav_menu_locations', $locations );

		$this->log[] = "Menu \"PWH Primary\" (#$menu_id)";
		return (int) $menu_id;
	}

	/**
	 * JetMenu stores each item's mega content in a "jet-menu" post edited with
	 * Elementor, linked from the nav item by the "jet-menu-item" meta, and the
	 * per-item options in "jet_menu_settings".
	 */
	private function setup_jetmenu( $menu_id ) {
		if ( ! post_type_exists( 'jet-menu' ) ) {
			$this->log[] = 'JetMenu not active – mega content not attached. The panels are saved under Templates → Saved Templates; insert them via JetMenu later (see README).';
			return;
		}

		$this->state['jet'] = (array) $this->state['jet'];

		foreach ( (array) $this->state['jet_items'] as $key => $info ) {
			$data = $this->load( self::TEMPLATES[ $key ][0] );
			if ( ! $data || empty( $info['item'] ) ) {
				continue;
			}

			$post_id = isset( $this->state['jet'][ $key ] ) ? (int) $this->state['jet'][ $key ] : 0;
			if ( ! $post_id || ! get_post( $post_id ) ) {
				$post_id = wp_insert_post(
					array(
						'post_type'   => 'jet-menu',
						'post_status' => 'publish',
						'post_title'  => 'mega-item-' . $info['item'],
					)
				);
			}
			// Document type is left to JetMenu, which registers its own for this post type.
			$this->save_elementor_data( $post_id, $data['content'], null );
			update_post_meta( $post_id, '_wp_page_template', 'elementor_canvas' );

			update_post_meta( $info['item'], 'jet-menu-item', $post_id );

			$settings = get_post_meta( $info['item'], 'jet_menu_settings', true );
			$settings = is_array( $settings ) ? $settings : array();
			$settings = array_merge(
				$settings,
				array(
					'enabled'                   => 'true',
					'custom_mega_menu_position' => $info['position'],
					'custom_mega_menu_width'    => (string) $info['width'],
				)
			);
			update_post_meta( $info['item'], 'jet_menu_settings', $settings );

			$this->state['jet'][ $key ] = $post_id;
			$this->log[]                = "JetMenu mega content for menu item #{$info['item']} → #$post_id";
		}
	}

	private function finish( $new_theme_parts ) {
		if ( ! $new_theme_parts ) {
			// Nothing new for the Theme Builder; leave its display conditions alone.
		} elseif ( class_exists( '\ElementorPro\Modules\ThemeBuilder\Module' ) ) {
			$module     = \ElementorPro\Modules\ThemeBuilder\Module::instance();
			$conditions = method_exists( $module, 'get_conditions_manager' ) ? $module->get_conditions_manager() : null;
			if ( $conditions && method_exists( $conditions, 'get_cache' ) ) {
				$conditions->get_cache()->regenerate();
				$this->log[] = 'Theme Builder conditions: header & footer set to Entire Site';
			}
		} else {
			$this->log[] = 'Elementor Pro not active – header/footer imported but not applied (needs Theme Builder).';
		}

		if ( isset( \Elementor\Plugin::$instance->files_manager ) ) {
			\Elementor\Plugin::$instance->files_manager->clear_cache();
		}
		$this->log[] = 'Elementor CSS cache cleared';
	}
}

PWH_Setup::init();
