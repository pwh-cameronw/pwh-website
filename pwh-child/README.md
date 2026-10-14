# Perth Web Hosting – WordPress child theme

Child theme of **Hello Elementor**, built from the Figma file
[Perth Web Hosting](https://www.figma.com/design/i4OddJr6teWRSoThGo59O3/Perth-Web-Hosting) for **Elementor Pro** with **JetMenu** mega menus.

What it gives you:

| Piece | Where it ends up |
| --- | --- |
| Header (logo, JetMenu mega menu, Client Login pill, sticky) | Templates → Theme Builder → Header, shown on the entire site |
| Footer (brand, contact, 3 link columns, copyright bar) | Templates → Theme Builder → Footer, shown on the entire site |
| Home page (hero, clients strip, product cards, "Not sure" band, testimonials, "Feeling lost" CTA) | Pages → Home, set as the front page |
| Mega menu panels: Products, Support, About | JetMenu mega content on the *PWH Primary* menu, plus copies in Templates → Saved Templates |
| Colours and type styles from the Figma variables | Elementor Site Settings → Global Colours / Global Fonts |
| Component styles (buttons, cards, testimonial, mega panels, footer) | `assets/css/pwh.css`, applied through CSS classes |

## Requirements

- WordPress 6.3+, PHP 7.4+
- [Hello Elementor](https://wordpress.org/themes/hello-elementor/) (parent theme, installed but not activated)
- Elementor + **Elementor Pro** (Theme Builder, sticky header)
- **JetMenu** (Crocoblock) 2.x

## Install

1. **Get the images and icons from Figma.** Figma's asset host was blocked from the environment this theme was built in, so the files aren't committed yet. On your machine:
   ```bash
   cd pwh-child
   FIGMA_TOKEN=figd_your_token python3 tools/fetch-figma-assets.py
   ```
   Create the token under Figma → Settings → Security → Personal access tokens (read-only file content). It writes everything listed in `assets/images/README.md` and `assets/icons/README.md`.

   The three logos are **not** part of this. They come from the Media Library: `pwh-logo-noborder-navy.svg` (header), `pwh-logo-noborder.svg` (footer) and `nhc-credit-1.svg` ("Website by"). The setup finds them by file name, so upload them with those names on any site you install to. To change them, edit `LOGO_*` in `tools/build-templates.py`.
2. **Fonts (optional):** add the licensed GT Standard files. See `assets/fonts/README.md`. Without them, headings use Archivo Expanded.
3. Zip the `pwh-child` folder and upload it in **Appearance → Themes → Add New → Upload**, or copy it to `wp-content/themes/`. Activate **Perth Web Hosting**.
4. Go to **Appearance → PWH Setup** and click **Run setup** (or run `wp pwh setup`). It:
   - turns on Elementor's *Disable Default Colours/Fonts*, so the theme classes aren't overridden
   - sets the kit's global colours and fonts, a 1180px container and 0 container padding
   - creates the **PWH Primary** menu (Products / About / Support, each with child links for mobile)
   - imports the header and footer and applies them to the entire site
   - imports the Home page and sets it as the front page
   - creates the JetMenu mega content for Products, About and Support and turns mega menu on for those items
   - adds the PNG photos to the Media Library

   You can run it again at any time without losing your work:
   - **Header, footer, PWH Primary menu and JetMenu mega content are protected.** Once they exist (including a header or footer you built yourself), setup never imports over them, never changes their display conditions and never rebuilds the menu. Edit them in Elementor and Appearance → Menus. To get the original import back, delete that template or menu first.
   - **Home page and kit colours & fonts** are only re-applied when you tick them on the setup page (or pass `--home` / `--kit` to `wp pwh setup`). Re-importing the Home page overwrites edits made to it in Elementor.

## JetMenu: check, or connect by hand

The importer writes JetMenu's menu-item data directly (`jet_menu_settings` and `jet-menu-item`). If your JetMenu version stores it differently and the panels don't show on hover, connect them by hand. It takes about two minutes:

1. **Appearance → Menus → PWH Primary**. Hover **Products** → **JetMenu** button → enable **Mega Submenu** → **Edit Mega Menu Item Content**.
2. In the Elementor editor, click the folder icon → **My Templates** → insert **PWH – Mega Menu / Products** → Update.
3. Item settings: width **1180px**, position **Default**. Do the same for **Support** (1180px) and **About** (template *PWH – Mega Menu / About*, width **280px**, position **Relative item**).
4. Edit the **PWH – Header** template and make sure the JetMenu *Mega Menu* widget has **PWH Primary** selected.

The panel's look (cream background, pale-navy border, 16px radius, shadow, 44px padding) is on the template's own container (`.pwh-mega`), so it doesn't depend on JetMenu's style settings. `pwh.css` makes JetMenu's wrapper transparent and adds the 14px gap under the bar, as in Figma.

## Things to fill in

These weren't in the design, so they are placeholders:

- **Links:** every page link is a relative path (`/domains/`, `/web-hosting/cpanel/`, `/contact/` and so on). Create pages with those slugs or edit the links. Client Login, MyToolbox and Submit a Ticket point to `/client-login/` and `/submit-a-ticket/`. Change them to your WHMCS or portal URLs.
- **Social links:** Facebook and LinkedIn in the footer are `#facebook` and `#linkedin`.
- **Client logos:** the six dashed slots on the home page show names. Replace each heading with an Image widget. `.pwh-logo-slot img` limits logos to 40px high.
- **Testimonial avatars** use the same placeholder image.
- The empty right-hand box in the "Not sure what you need?" band is empty in the Figma file as well. It's hidden on tablet and mobile.

## Editing in Elementor

Layout (direction, gaps, padding, widths, backgrounds) is set in each container's Elementor settings. Typography and colour come from CSS classes in **Advanced → CSS Classes**, so the design stays consistent:

| Class | Use on | Figma style |
| --- | --- | --- |
| `pwh-h1`, `pwh-h2`, `pwh-h3` | Heading | PWH/H1 56/62, H2 40/46, H3 28/34 |
| `pwh-card-title`, `pwh-eyebrow` | Heading | Card Title 22, PWH/Eyebrow 12 caps |
| `pwh-body`, `pwh-lead` | Text Editor | PWH/Body Inter 18/26, Inter Light 18 |
| `pwh-text-cream`, `pwh-text-ink`, `pwh-text-mist` | Heading / Text | colour |
| `pwh-btn pwh-btn--amber` / `--navy` / `--outline` / `--outline-cream` / `--pill` (+ `--sm`) | Button | Button component styles |
| `pwh-media-card` | Container (link) | Card / Media |
| `pwh-testimonial` | Container | Testimonial Card |
| `pwh-mega`, `pwh-mega-group`, `pwh-mega-item`, `pwh-mega-link`, `pwh-mega-desc`, `pwh-mega-box` | Mega content | Mega Menu panels |

A `<ul class="pwh-dots">` inside a Text Editor gives the amber-dot list from the hero.

## Rebuilding the templates

The JSON in `elementor-templates/` is generated. Edit `tools/build-templates.py`, then:

```bash
python3 tools/build-templates.py
```

Then re-run **PWH Setup** with *Re-import the Home page* ticked. Header and footer changes in the generator only reach a site that doesn't have a header or footer yet. The files are also in Elementor's export format, so you can import them through **Templates → Saved Templates → Import**. That route doesn't fill in the `{{PWH_…}}` placeholders, though (image URLs, links and the menu ID), so use the setup page where you can.

## Not in this build yet

The Figma *Foundations* page also has components for pages that haven't been designed yet: Pricing card (with monthly/yearly toggle and technical details), Managed pricing card, Add-on card and row, FAQ row, Persona card, Feature tile, and the clock, phone and location icons. Only the Home page has a full page design, so those components aren't built yet. Add them to `pwh.css` and the generator when the product pages are designed.

## cPanel Plans page

Built from the Figma *Page / cPanel Plans* frame. Import it from **Appearance → PWH Setup → Import the cPanel Plans page**, or run `wp pwh setup --cpanel`. It's created at `/web-hosting/cpanel/` (the mega menu link) if a *web-hosting* page exists, otherwise at `/cpanel-hosting/`. It never takes over a page someone else made at that address. After the first import it's protected like the Home page, and is only re-imported when you tick it.

**Upload these to the Media Library first** (setup finds them by file name):

| File | Used for |
| --- | --- |
| `cpanel-hero.jpg` | Header photo (shown under an 80% navy overlay) |
| `cpanel.png`, `jetbackups.png`, `cloudlinux.png`, `imunify360.png`, `spamexperts.png`, `softaculous.png` | "What's available on all our cPanel plans" logos |

**Two new Elementor widgets** (panel category *Perth Web Hosting*) that you can reuse on other plan pages:

- **PWH Pricing Card:** set the plan name, tag, description, monthly and yearly price, notes and order links, the features (a repeater) and the technical details (one per line, shown under the **+**). Turn on **Featured** for the navy border and amber button.
- **PWH Billing Toggle:** the Monthly / Yearly switch. It switches every Pricing Card on the page. A card with no yearly price keeps showing its monthly price.

**To fill in:** the design only gives a yearly price and technical details for **Business**. Starter and Advanced need their yearly price, note and details entered on the card. Every *Order Now* button currently goes to `/client-login/`, so set each card's monthly and yearly order links to your WHMCS cart URLs.

## Domains page

Built from the Figma *Page / Domains* frame. Import it from **Appearance → PWH Setup → Import the Domains page**, or run `wp pwh setup --domains`. It goes to `/domains/` (the mega menu link), unless a page already exists there; then it goes to `/domains-new/` and the existing page is left alone.

**Images (Media Library, matched by file name):**
- the hero phone reuses your Home *Domains* card image (`f3df1232345aad30c3209977ac09361515473c56.png`), already uploaded
- upload **`domains-transfer.jpg`**, the photo behind "Bringing a domain across?" (shown under an 80% navy overlay)

**New widget, PWH Domain Search:** the grey search bar in the hero. Set **Domain checker URL** to your WHMCS `cart.php`. It submits `?a=add&domain=register&query=<name>`. Until it's set, the form does nothing.

**Check before publishing:**
- **FAQ answers are drafts.** Figma only has the questions. Each answer uses only what your pages already say (transfer, WHOIS, reminders, bundling, choosing an extension). They're in the Toggle widget, which also outputs FAQ schema.
- **Not taken from Figma** (the Figma API limit was hit): the testimonials reuse the Home page's three reviews; the "Not sure which extension…" block is centred on cream with an amber **Contact Us** button to `/contact/`; and an open FAQ answer is styled as 16px grey text. Adjust any of these in Elementor if the design differs.
- "Ask Us About Transferring" links to `/support/hosting-transfer-request/`.

