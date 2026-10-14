#!/usr/bin/env python3
"""
Builds the Elementor template JSON files in ../elementor-templates from the
Figma "Perth Web Hosting" design.

Run:  python3 tools/build-templates.py

Output files use Elementor's export format ({"version","title","type","content"}),
so they can be imported with Elementor → Templates → Import as well as by the
theme's Appearance → PWH Setup importer.

Placeholders resolved by the importer (inc/setup.php):
  {{PWH_ASSET:path}}  file under assets/ (PNG/JPG are added to the Media Library)
  {{PWH_URL:/path/}}  home_url( '/path/' )
  {{PWH_MENU:slug}}   term ID of the menu created by the importer
"""

import hashlib
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "elementor-templates")

_ids = {}


def _id(seed):
    """Stable 7-char Elementor element id."""
    n = _ids.get(seed, 0)
    _ids[seed] = n + 1
    return hashlib.md5(f"{seed}:{n}".encode()).hexdigest()[:7]


def asset(path):
    """Theme file under assets/, or a full URL of an image already in the Media Library."""
    src = path if path.startswith("http") else "{{PWH_ASSET:%s}}" % path
    return {"url": src, "id": "", "size": "", "alt": "", "source": "library"}


# Logos uploaded to the Media Library. The importer matches them by file name,
# so they still resolve when the site moves from dev to the live domain.
MEDIA = "https://dev.perthhosting.net/wp-content/uploads/2026/10/"
LOGO_HEADER = MEDIA + "pwh-logo-noborder-navy.svg"
LOGO_FOOTER = MEDIA + "pwh-logo-noborder.svg"
LOGO_CREDIT = MEDIA + "nhc-credit-1.svg"


def url(path, external=False):
    return {"url": path if external else "{{PWH_URL:%s}}" % path,
            "is_external": "on" if external else "", "nofollow": "", "custom_attributes": ""}


def px(size):
    return {"unit": "px", "size": size, "sizes": []}


def pct(size):
    return {"unit": "%", "size": size, "sizes": []}


def box(t, r=None, b=None, l=None):
    r = t if r is None else r
    b = t if b is None else b
    l = r if l is None else l
    return {"unit": "px", "top": str(t), "right": str(r), "bottom": str(b), "left": str(l),
            "isLinked": len({t, r, b, l}) == 1}


def gap(size):
    return {"unit": "px", "size": size, "column": str(size), "row": str(size), "isLinked": True}


# --- elements -------------------------------------------------------------

def con(name, children, *, cls="", direction="column", full=None, boxed=None, width=None,
        gap_px=None, pad=None, pad_t=None, pad_m=None, justify=None, align=None,
        dir_t=None, dir_m=None, gap_t=None, gap_m=None, width_t=None, width_m=None,
        min_h=None, min_h_t=None, min_h_m=None, tag=None, link=None, extra=None):
    # Only top-level sections are "boxed" (they pass boxed=1180). Everything nested
    # is "full width": Elementor ignores the Width control on boxed containers,
    # which made the product cards each 100% wide.
    if full is None:
        full = boxed is None
    s = {
        "content_width": "full" if full else "boxed",
        "flex_direction": direction,
        "padding": pad if pad is not None else box(0),
        "_title": name,
    }
    if boxed:
        s["boxed_width"] = px(boxed)
    if width is not None:
        s["width"] = width
    if width_t is not None:
        s["width_tablet"] = width_t
    if width_m is not None:
        s["width_mobile"] = width_m
    if gap_px is not None:
        s["flex_gap"] = gap(gap_px)
    if gap_t is not None:
        s["flex_gap_tablet"] = gap(gap_t)
    if gap_m is not None:
        s["flex_gap_mobile"] = gap(gap_m)
    if pad_t is not None:
        s["padding_tablet"] = pad_t
    if pad_m is not None:
        s["padding_mobile"] = pad_m
    if justify:
        s["flex_justify_content"] = justify
    if align:
        s["flex_align_items"] = align
    if dir_t:
        s["flex_direction_tablet"] = dir_t
    if dir_m:
        s["flex_direction_mobile"] = dir_m
    if min_h is not None:
        s["min_height"] = px(min_h)
    if min_h_t is not None:
        s["min_height_tablet"] = px(min_h_t)
    if min_h_m is not None:
        s["min_height_mobile"] = px(min_h_m)
    if tag:
        s["html_tag"] = tag
    if link:
        s["link"] = link
    if cls:
        s["css_classes"] = cls
    if extra:
        s.update(extra)
    return {"id": _id(name), "elType": "container", "settings": s, "elements": children, "isInner": False}


def widget(kind, settings, cls=""):
    if cls:
        settings["_css_classes"] = cls
    return {"id": _id(kind), "elType": "widget", "widgetType": kind, "settings": settings, "elements": []}


def heading(text, cls, tag="h2", link=None, align=None):
    s = {"title": text, "header_size": tag}
    if link:
        s["link"] = link
    if align:
        s["align"] = align
    return widget("heading", s, cls)


def text(html, cls):
    return widget("text-editor", {"editor": html}, cls)


def button(label, link, cls, align=None):
    s = {"text": label, "link": link, "size": "md"}
    if align:
        s["align"] = align
    return widget("button", s, "pwh-btn " + cls)


def image(path, cls, link=None, alt="", align="left", width=None):
    img = asset(path)
    img["alt"] = alt
    s = {"image": img, "image_size": "full", "align": align}
    if link:
        s["link_to"] = "custom"
        s["link"] = link
    if width:
        s["width"] = width
    return widget("image", s, cls)


def template(title, kind, content, page_settings=None):
    return {"version": "0.4", "title": title, "type": kind, "content": content,
            "page_settings": page_settings or []}


# --- Header ---------------------------------------------------------------

def header():
    nav = widget("jet-mega-menu", {
        # Resolved by the importer to the "PWH Primary" menu.
        "menu": "{{PWH_MENU:pwh-primary}}",
    }, "pwh-mainnav")

    bar = con("Header", [
        image(LOGO_HEADER, "pwh-logo", link=url("/"), alt="Perth Web Hosting",
              width=px(142)),
        nav,
        button("Client Login", url("/client-login/"),
               "pwh-btn--pill pwh-btn--sm"),
    ], cls="pwh-header", direction="row", boxed=1180, justify="space-between", align="center",
        min_h=84, pad=box(0), pad_t=box(0, 24), tag="header",
        extra={
            "background_background": "classic",
            "background_color": "#FFFEF4",
            # Elementor Pro sticky header
            "sticky": "top",
            "sticky_on": ["desktop", "tablet", "mobile"],
            "sticky_effects_offset": 10,
        })
    return template("PWH – Header", "header", [bar])


# --- Mega menus -----------------------------------------------------------

def mega_item(title, desc, link, boxed=False):
    return con(f"Item – {title}", [
        heading(title, "pwh-mega-link", tag="p", link=link),
        text(f"<p>{desc}</p>", "pwh-mega-desc"),
    ], cls="pwh-mega-item" + (" pwh-mega-box" if boxed else ""), full=True, gap_px=4 if boxed else 3,
        pad=box(14) if boxed else box(0))


def mega_col(name, items, group=None, gap_px=18):
    # Layout is also enforced by pwh.css (.pwh-mega-col), because JetMenu does not
    # always load the Elementor-generated CSS for its mega content.
    kids = []
    if group:
        kids.append(heading(group, "pwh-mega-group", tag="p"))
    kids += items
    return con(name, kids, cls="pwh-mega-col" + (" pwh-mega-col--tight" if gap_px == 12 else ""),
               full=True, gap_px=gap_px, width=pct(25), width_t=pct(50), width_m=pct(100),
               extra={"_flex_size": "grow"})


def mega_panel(name, cols):
    return con(name, cols, cls="pwh-mega", full=True, direction="row", gap_px=48, pad=box(44),
               dir_t="row", dir_m="column", gap_t=32, pad_m=box(24),
               extra={"flex_wrap_tablet": "wrap", "flex_align_items": "flex-start"})


def mega_products():
    panel = mega_panel("Mega Menu / Products", [
        mega_col("Domains", [
            mega_item("Search Domains", "Find and register your business name across every extension.", url("/domains/search/")),
            mega_item("Transfer Domains", "Move an existing domain across with zero downtime.", url("/domains/transfer/")),
        ], group="Domains"),
        mega_col("Hosting", [
            mega_item("cPanel Hosting", "Full control over your site with the industry-standard dashboard.", url("/web-hosting/cpanel/")),
            mega_item("Semi-managed WordPress", "We handle updates, backups and troubleshooting for you.", url("/web-hosting/wordpress/")),
        ], group="Hosting"),
        mega_col("Email", [
            mega_item("Email", "Business mailboxes on your own domain, POP3 or IMAP.", url("/email/")),
            mega_item("Microsoft 365", "Full Exchange mailboxes with Teams and cloud storage.", url("/email/microsoft-365/")),
        ], group="Email"),
        mega_col("Business", [
            mega_item("Reseller", "White-label hosting for agencies and freelancers.", url("/reseller-hosting/")),
            mega_item("VPS", "Coming soon. Join the waitlist for dedicated resources.", url("/vps-hosting/")),
        ]),
    ])
    return template("PWH – Mega Menu / Products", "section", [panel])


def mega_support():
    panel = mega_panel("Mega Menu / Support", [
        mega_col("Get in touch", [
            mega_item("Contact Us", "Call, email or chat with our Perth-based team.", url("/contact/")),
            mega_item("Remote Support", "Click to download remote support for Windows.", url("/support/remote-support/")),
            mega_item("Mac Remote Support", "Click to download remote support for Mac.", url("/support/mac-remote-support/")),
        ]),
        mega_col("Self help", [
            mega_item("Knowledge Base", "Guides and answers to common questions.", url("/knowledge-base/")),
            mega_item("Network Status", "Live status of our servers and network.", url("/network-status/")),
            mega_item("Hosting Transfer Request", "Ask us to migrate your site or email across.", url("/support/hosting-transfer-request/")),
        ]),
        mega_col("Policies & transfers", [
            mega_item("Service Level Agreement", "Our uptime commitment and support standards.", url("/service-level-agreement/")),
            mega_item("Microsoft Transfer", "Move your Microsoft 365 mailboxes across to us.", url("/support/microsoft-transfer-request/")),
        ]),
        mega_col("Account", [
            mega_item("MyToolbox", "Everything for managing your account in one place.",
                      url("/client-login/"), boxed=True),
            mega_item("Submit a Ticket", "Log a support request with our local team.",
                      url("/submit-a-ticket/"), boxed=True),
        ], gap_px=12),
    ])
    return template("PWH – Mega Menu / Support", "section", [panel])


def mega_about():
    links = [("About Us", "/about/"), ("Privacy Policy", "/privacy-policy/"),
             ("Terms of Service", "/terms-of-service/"), ("Acceptable Use Policy", "/acceptable-use-policy/")]
    col = con("Links", [heading(t, "pwh-mega-link", tag="p", link=url(u)) for t, u in links],
              cls="pwh-mega-col pwh-mega-col--list", full=True, gap_px=16)
    panel = con("Mega Menu / About", [col], cls="pwh-mega pwh-mega--narrow", full=True, pad=box(44), pad_m=box(24))
    return template("PWH – Mega Menu / About", "section", [panel])


# --- Footer ---------------------------------------------------------------

def link_list(title, items):
    return [
        heading(title, "pwh-footer-heading", tag="p"),
        widget("icon-list", {
            "view": "traditional",
            "icon_list": [
                {"_id": _id("li"), "text": t, "link": url(u, external=u.startswith("http")),
                 "selected_icon": {"value": "", "library": ""}}
                for t, u in items
            ],
        }, "pwh-footer-links"),
    ]


def contact_row(icon, html, name):
    return con(name, [
        image(icon, "pwh-contact-icon", width=px(24)),
        text(html, "pwh-contact-text"),
    ], cls="pwh-contact-row", direction="row", gap_px=12, align="flex-start",
        extra={"flex_wrap": "nowrap"})


def footer():
    brand = con("Brand", [
        image(LOGO_FOOTER, "pwh-footer-logo", link=url("/"), alt="Perth Web Hosting", width=px(201)),
        heading("Your local hosting partner.", "pwh-footer-tagline", tag="p"),
        text("<p>Website hosting, business email and domains for Western Australian small businesses, set up and supported locally.</p>",
             "pwh-footer-blurb"),
        con("Contact", [
            contact_row("icons/location-pin.svg", "<p>Suite 3, Level 3, 533 Hay Street,<br>Perth, WA 6000</p>", "Address"),
            contact_row("icons/phone.svg", '<p><a href="tel:+61863654522">08 6365 4522</a></p>', "Phone"),
            contact_row("icons/clock.svg", "<p>Mon–Fri 8:30am – 5:30pm AWST</p>", "Hours"),
        ], gap_px=12, extra={"margin": box(19, 0, 0, 0)}),
        con("Social", [
            image("icons/facebook.svg", "pwh-social", link=url("#facebook", True), alt="Facebook", width=px(34)),
            image("icons/linkedin.svg", "pwh-social", link=url("#linkedin", True), alt="LinkedIn", width=px(34)),
        ], direction="row", gap_px=10),
    ], gap_px=20, width=px(340), width_t=pct(100), width_m=pct(100))

    products = con("Products", [
        con("Products list", link_list("Products", [
            ("Domains", "/domains/"), ("Web Hosting", "/web-hosting/"), ("Email", "/email/")]), gap_px=11),
        con("Business list", link_list("Business Products", [
            ("VPS Hosting", "/vps-hosting/"), ("Reseller", "/reseller-hosting/")]), gap_px=11),
    ], gap_px=20, width_m=pct(100))

    support = con("Support", link_list("Support", [
        ("Contact Us", "/contact/"),
        ("MyToolbox", "/client-login/"),
        ("Submit a Ticket", "/submit-a-ticket/"),
        ("Remote Support", "/support/remote-support/"),
        ("Mac Remote Support", "/support/mac-remote-support/"),
        ("Knowledge Base", "/knowledge-base/"),
        ("Network Status", "/network-status/"),
        ("Hosting Transfer Request", "/support/hosting-transfer-request/"),
        ("Microsoft Transfer Request", "/support/microsoft-transfer-request/"),
        ("Service Level Agreement", "/service-level-agreement/"),
    ]), gap_px=11, width_m=pct(100))

    about = con("About", link_list("About PWH", [
        ("About Us", "/about/"), ("Privacy Policy", "/privacy-policy/"),
        ("Terms of Service", "/terms-of-service/"), ("Acceptable Use Policy", "/acceptable-use-policy/"),
    ]), gap_px=11, width_m=pct(100))

    top = con("Top", [brand, products, support, about], direction="row", justify="space-between",
              align="flex-start", dir_t="row", dir_m="column", gap_px=40, gap_m=32,
              extra={"flex_wrap_tablet": "wrap", "padding": box(0, 0, 28, 0)})

    bottom_row = con("BottomRow", [
        text("<p>Copyright © 2026 Perth Web Hosting. All Rights Reserved.</p>", "pwh-footer-small"),
        con("Credit", [
            text("<p>ABN: 13 412 527 483   |   Website by</p>", "pwh-footer-small"),
            image(LOGO_CREDIT, "pwh-credit", alt="Website by", width=px(84)),
        ], direction="row", gap_px=10, align="center"),
    ], direction="row", justify="space-between", align="center", dir_m="column", gap_px=16,
        extra={"flex_align_items_mobile": "flex-start"})

    bottom = con("Bottom", [bottom_row], cls="pwh-footer-rule", pad=box(24, 0, 0, 0))

    wrap = con("Footer", [top, bottom], cls="pwh-footer", boxed=1180, gap_px=40, tag="footer",
               pad=box(96, 0, 32, 0), pad_t=box(72, 24, 32, 24), pad_m=box(56, 20, 32, 20),
               extra={"background_background": "classic", "background_color": "#0B1629"})
    return template("PWH – Footer", "footer", [wrap])


# --- Home -----------------------------------------------------------------

SECTION_PAD = box(140, 0)
SECTION_PAD_T = box(96, 24)
SECTION_PAD_M = box(72, 20)


def media_card(title, body_html, img, link, overlay):
    extra = {
        "background_background": "classic",
        "background_color": "#0B1629",
        "background_image": asset(img),
        "background_position": "center center",
        "background_size": "cover",
        "background_repeat": "no-repeat",
        "border_radius": box(16),
        "_flex_size": "grow",
    }
    if overlay == "gradient":
        extra.update({
            "background_overlay_background": "gradient",
            "background_overlay_color": "rgba(11,22,41,0.8)",
            "background_overlay_color_stop": pct(0),
            "background_overlay_color_b": "rgba(11,22,41,0)",
            "background_overlay_color_b_stop": pct(100),
            "background_overlay_gradient_type": "linear",
            "background_overlay_gradient_angle": {"unit": "deg", "size": 180, "sizes": []},
        })
    else:  # photo at 80% over navy
        extra.update({
            "background_overlay_background": "classic",
            "background_overlay_color": "#0B1629",
            "background_overlay_opacity": {"unit": "px", "size": 0.2, "sizes": []},
        })
    return con(f"Card / Media – {title}", [
        con("TextBlock", [
            heading(title, "pwh-card-title pwh-text-cream", tag="h3"),
            text(body_html, "pwh-body pwh-text-cream"),
        ], gap_px=14),
        image("icons/arrow-right.svg", "pwh-card-arrow", alt="", align="right", width=px(30)),
    ], cls="pwh-media-card", justify="space-between", pad=box(40), pad_m=box(28),
        min_h=529, min_h_t=420, min_h_m=380, width=pct(33.33), width_t=pct(100),
        tag="a", link=link, extra=extra)


def testimonial(quote, name):
    return con(f"Testimonial – {name}", [
        image("icons/stars.svg", "pwh-stars", alt="5 out of 5 stars", width=px(126)),
        text(f"<p>{quote}</p>", "pwh-quote"),
        con("Who", [
            image("images/avatar-placeholder.png", "pwh-avatar", alt="", width=px(40)),
            con("NameCol", [
                heading(name, "pwh-who-name", tag="p"),
                text("<p>Google review, 5 stars</p>", "pwh-who-source"),
            ], gap_px=2),
        ], cls="pwh-who", direction="row", align="center", gap_px=12, pad=box(16, 0, 0, 0)),
    ], cls="pwh-testimonial", gap_px=16, pad=box(28), width=pct(33.33), width_t=pct(100),
        extra={"_flex_size": "grow"})


def home():
    hero = con("Hero", [
        con("Photo spacer", [], width=px(586), width_t=pct(100), min_h=545, min_h_t=420, min_h_m=300),
        con("Copy", [
            heading("Hosting,<br>right here in Australia.", "pwh-h1 pwh-text-cream", tag="h1"),
            text("<p>Website hosting, domains and business email, set up fast and backed by a real Perth team and servers in Australia.</p>",
                 "pwh-lead pwh-text-cream"),
            button("Get Started →", url("/get-started/"), "pwh-btn--amber"),
            text('<ul class="pwh-dots"><li>Trusted by 1,000+ WA businesses</li><li>99.9% uptime for over a decade</li><li>Local phone and email support</li></ul>',
                 "pwh-text-cream"),
        ], width=px(529), width_t=pct(100), gap_px=16, justify="center",
            extra={"flex_align_items": "flex-start"}),
    ], cls="pwh-hero", direction="row", boxed=1180, gap_px=64, align="center", dir_t="column",
        gap_t=32, pad=box(136, 0, 140, 0), pad_t=box(0, 24, 80, 24), pad_m=box(0, 20, 64, 20),
        tag="section", extra={"background_background": "classic", "background_color": "#0B1629",
                              "background_image": asset("images/hero-laptop.png")})

    clients = con("Clients", [
        heading("Trusted by Perth businesses and organisations", "pwh-eyebrow pwh-text-cream", tag="p", align="center"),
        con("Logos", [
            con(f"Logo slot – {n}", [heading(n, "", tag="p", align="center")], cls="pwh-logo-slot",
                min_h=64, justify="center", align="center", width=pct(16.66), width_t=pct(30), width_m=pct(46),
                extra={"_flex_size": "grow"})
            for n in ["Allduro", "gTurbo", "Nations Church", "Glowing Rooms", "Client logo", "Client logo"]
        ], direction="row", gap_px=24, gap_m=12, justify="center", extra={"flex_wrap": "wrap"}),
    ], boxed=1180, gap_px=24, align="center", pad=box(48, 0), pad_t=box(48, 24), pad_m=box(40, 20),
        tag="section", extra={"background_background": "classic", "background_color": "#1A315C"})

    products = con("Products", [
        con("Intro", [
            heading("Hosting, domains and email. One local team.", "pwh-h2 pwh-text-ink", tag="h2"),
            text("<p>It's all looked after by the same Perth team. One phone call, not three.</p>", "pwh-body pwh-text-ink"),
        ], direction="row", gap_px=28, align="center", dir_t="column", gap_t=16,
            extra={"flex_align_items_tablet": "flex-start"}),
        con("Cards", [
            media_card("Domains",
                       "<p>Your domain, sorted properly. Register, transfer or manage your domain, done right the first time.</p><p>No surprises.</p>",
                       "images/card-domains.png", url("/domains/"), "solid"),
            media_card("Website Hosting",
                       "<p>A site that doesn't let you down.</p><p>Fast, monitored hosting. If something's off, we're usually already on it.</p>",
                       "images/card-hosting.png", url("/web-hosting/"), "gradient"),
            media_card("Business Email",
                       "<p>Email that means business.</p><p>A proper @yourbusiness.com.au inbox, not a Gmail address that undersells you.</p>",
                       "images/card-email.png", url("/email/"), "gradient"),
        ], direction="row", gap_px=32, dir_t="column", gap_t=24),
    ], boxed=1180, gap_px=40, pad=SECTION_PAD, pad_t=SECTION_PAD_T, pad_m=SECTION_PAD_M, tag="section")

    # Intro widths: heading 780 / body 372 inside 1180.
    products["elements"][0]["elements"][0]["settings"].update({"_element_width": "initial", "_element_custom_width": px(780),
                                                                "_element_width_tablet": "inherit"})
    products["elements"][0]["elements"][1]["settings"].update({"_element_width": "initial", "_element_custom_width": px(372),
                                                                "_element_width_tablet": "inherit"})

    why = con("WhyPWH", [
        con("Copy", [
            heading("Not sure what you need? We'll figure it out with you.", "pwh-h2 pwh-text-cream", tag="h2"),
            text("<p>Getting online shouldn't mean learning how servers work first. Tell us a bit about your business and we'll walk you through exactly what you need: hosting, a domain, email, or all three. Then we set it up, so you don't have to.</p>",
                 "pwh-body pwh-text-mist"),
            button("Start my walkthrough →", url("/get-started/"), "pwh-btn--amber"),
        ], gap_px=24, width=pct(50), width_t=pct(100), extra={"_flex_size": "grow"}),
        con("Placeholder", [], width=pct(50), width_t=pct(100), min_h=350, min_h_t=0,
            extra={"_flex_size": "grow", "hide_tablet": "hidden-tablet", "hide_mobile": "hidden-mobile"}),
    ], cls="pwh-why", direction="row", boxed=1180, gap_px=64, align="center", dir_t="column",
        pad=SECTION_PAD, pad_t=SECTION_PAD_T, pad_m=SECTION_PAD_M, tag="section",
        extra={
            "background_background": "classic",
            "background_image": asset("images/why-pwh.png"),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "gradient",
            "background_overlay_color": "rgba(11,22,41,0.8)",
            "background_overlay_color_stop": pct(0),
            "background_overlay_color_b": "rgba(11,22,41,0)",
            "background_overlay_color_b_stop": pct(65),
            "background_overlay_gradient_type": "linear",
            "background_overlay_gradient_angle": {"unit": "deg", "size": 90, "sizes": []},
        })

    testimonials = con("Testimonials", [
        con("Intro", [
            heading("WA businesses who've<br>made the switch", "pwh-h2 pwh-text-ink", tag="h2"),
            text("<p>Here's what business owners say after switching.</p>", "pwh-body pwh-text-ink"),
        ], gap_px=8, width=px(744), width_t=pct(100)),
        con("Cards", [
            testimonial("Excellent service from the guys at Perth Web Hosting. Love that my website is locally hosted and looked after. After years of being with 'the big global guys' and running into issues, downtime and more, all of that's finally over.",
                        "Nathan Hurst"),
            testimonial("Best web hosting services in Perth. I have tried many providers and these guys are the absolute best. I never have to wait for support and my website speeds are blazingly fast.",
                        "Jack Hampton"),
            testimonial("Great Service, Great Price, Great Support and Fast Speeds.", "Sora Kiari"),
        ], direction="row", gap_px=32, align="stretch", dir_t="column", gap_t=24),
    ], boxed=1180, gap_px=40, pad=SECTION_PAD, pad_t=SECTION_PAD_T, pad_m=SECTION_PAD_M, tag="section")

    cta = con("NotSureCTA", [
        con("Image", [image("images/not-sure-cta.png", "pwh-cta-image", alt="The Perth Web Hosting team at work")],
            width=px(522), width_t=pct(100)),
        con("Copy", [
            heading("Feeling a bit lost?<br>That's what we're here for.", "pwh-h3 pwh-text-cream", tag="h2"),
            text("<p>You don't need to know the difference between hosting and a domain before you call us. Tell us what you're trying to do and we'll point you the right way. No jargon, no pressure.</p><p>Your local hosting partner.</p>",
                 "pwh-body pwh-text-cream"),
            con("Buttons", [
                button("Get Help →", url("/contact/"), "pwh-btn--outline-cream"),
                button("Call 08 6365 4522", url("tel:+61863654522", external=True), "pwh-btn--outline-cream"),
            ], direction="row", gap_px=44, gap_m=12, align="center", extra={"flex_wrap": "wrap"}),
        ], gap_px=24, width=pct(50), width_t=pct(100), extra={"_flex_size": "grow"}),
    ], cls="pwh-cta", direction="row", boxed=1180, gap_px=64, align="center", dir_t="column", gap_t=32,
        pad=box(60, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#1A315C"})

    return template("PWH – Home", "wp-page", [hero, clients, products, why, testimonials, cta],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- cPanel Plans ---------------------------------------------------------

# Media Library files for the plan pages, matched by file name on import.
# Upload these before running setup (see README).
CPANEL_HERO = MEDIA + "cpanel-hero.jpg"
PARTNER_LOGOS = [
    ("cPanel", "cpanel.png"), ("JetBackup", "jetbackups.png"), ("CloudLinux", "cloudlinux.png"),
    ("Imunify360", "imunify360.png"), ("SpamExperts", "spamexperts.png"), ("Softaculous", "softaculous.png"),
]


def rating_stars():
    """Same as the live Home page: Elementor Rating widget, 20px amber stars."""
    return widget("rating", {
        "rating_scale": {"unit": "px", "size": 5, "sizes": []},
        "rating_value": 5,
        "icon_size": px(20),
        "icon_gap": px(3),
        "__globals__": {"icon_marked_color": "globals/colors?id=accent"},
    }, "pwh-stars")


def avatar_dot():
    """Same as the live Home page: navy-soft circle icon as an avatar placeholder."""
    return widget("icon", {
        "selected_icon": {"value": "fas fa-circle", "library": "fa-solid"},
        "size": px(40),
        "_element_width": "initial",
        "__globals__": {"primary_color": "globals/colors?id=pwhnavysoft"},
    }, "pwh-avatar")


def review(quote, name, source):
    return con(f"Testimonial – {name}", [
        rating_stars(),
        text(f"<p>{quote}</p>", "pwh-quote"),
        con("Who", [
            avatar_dot(),
            con("NameCol", [
                heading(name, "pwh-who-name", tag="p"),
                text(f"<p>{source}</p>", "pwh-who-source"),
            ], gap_px=2),
        ], cls="pwh-who", direction="row", align="center", gap_px=12, pad=box(16, 0, 0, 0)),
    ], cls="pwh-testimonial", gap_px=16, pad=box(28), width=pct(33.33), width_t=pct(100),
        extra={"_flex_size": "grow"})


def plan(title, desc, monthly, features, featured=False, tag="", yearly="", yearly_note="", details=""):
    return widget("pwh-pricing-card", {
        "featured": "yes" if featured else "",
        "tag": tag,
        "title": title,
        "description": desc,
        "currency": "$",
        "monthly_price": monthly,
        "monthly_period": "/ month",
        "monthly_note": "Billed monthly. Cancel any time.",
        # Order links aren't in the design; set them per card in Elementor.
        "monthly_url": url("/client-login/"),
        "yearly_price": yearly,
        "yearly_period": "/ year",
        "yearly_note": yearly_note,
        "yearly_url": {"url": "", "is_external": "", "nofollow": "", "custom_attributes": ""},
        "button_text": "Order Now",
        "features": [{"_id": _id("feat"), "text": f} for f in features],
        "details": details,
    })


def cpanel():
    hero = con("Header", [
        heading("Pick the hosting plan (cPanel) that fits your business.", "pwh-h1 pwh-text-cream", tag="h1", align="center"),
        text("<p>Every plan runs on Perth servers we monitor ourselves, with free migration and local support. Switch plans any time as you grow.</p>",
             "pwh-body pwh-text-mist"),
        text("<p>New to cPanel? It's the dashboard you use to manage your site, email and files. Most hosting runs on it.</p>",
             "pwh-small pwh-text-mist"),
    ], cls="pwh-page-hero", boxed=1104, gap_px=12, align="center",
        pad=box(116, 0, 120, 0), pad_t=box(96, 24, 96, 24), pad_m=box(72, 20, 72, 20), tag="section",
        extra={
            "background_background": "classic",
            "background_color": "#0B1629",
            "background_image": asset(CPANEL_HERO),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_color": "#0B1629",
            "background_overlay_opacity": {"unit": "px", "size": 0.8, "sizes": []},
        })
    # Centre the hero copy (text-editor widgets have no align in our helper).
    for w in hero["elements"][1:]:
        w["settings"]["align"] = "center"

    toggle = con("Year Toggle", [
        widget("pwh-billing-toggle", {"monthly_label": "Monthly", "yearly_label": "Yearly",
                                      "yearly_badge": "Best value", "default": "monthly"}),
    ], boxed=1180, align="center", pad=box(56, 0), pad_t=box(48, 24), pad_m=box(40, 20), tag="section")

    common = ["Free SSL certificate", "Free migration from your current host"]
    cards = con("Cards", [
        plan("Starter", "For your first website.", "7.95",
             ["Email support only"] + common + ["5GB high-speed SSD storage", "50GB premium bandwidth",
                                                "3 add-on domains", "6-hourly, 21-day offsite backups"]),
        plan("Business", "For growing businesses with more than one site.", "14.95",
             ["Local phone & email support"] + common + ["10GB high-speed SSD storage", "200GB premium bandwidth",
                                                         "Unlimited add-on domains", "6-hourly, 21-day offsite backups"],
             featured=True, tag="Most popular", yearly="149.95",
             yearly_note="That's $12.50 a month. Save $29.45 a year.",
             details="SpamExperts filtering, 400% CPU, 12 MB/s I/O, 10GB RAM"),
        plan("Advanced", "For high-traffic sites and multiple domains.", "27.95",
             ["Local phone & email support"] + common + ["30GB high-speed SSD storage", "600GB premium bandwidth",
                                                         "Unlimited add-on domains", "6-hourly, 21-day offsite backups"]),
    ], cls="pwh-plans", boxed=1180, direction="row", gap_px=28, align="flex-start", dir_t="column",
        gap_t=24, pad=box(0, 0, 140, 0), pad_t=box(0, 24, 96, 24), pad_m=box(0, 20, 72, 20), tag="section")

    reviews = con("TestimonialStrip", [
        heading("What customers say", "pwh-h3 pwh-h3-amber", tag="h2", align="center"),
        con("Cards", [
            review("I had a nightmare dealing with the larger multinational companies, then I switched to PWH and wow what a difference. Quick and responsive support, extremely helpful.",
                   "Heath", "Local Guide, Google review"),
            review("I only have a very small footprint with mainly emails and a little web traffic, but they still valued me as a customer and welcomed me aboard. Pricing is more than reasonable.",
                   "Mark Vasile", "Local Guide, Google review"),
            review("Excellent service. Went above and beyond to help transfer multiple websites and email accounts, which was a difficult process.",
                   "Leon Yeap", "Local Guide, Google review"),
        ], direction="row", gap_px=24, align="stretch", dir_t="column"),
    ], boxed=1180, gap_px=24, pad=box(0, 0, 72, 0), pad_t=box(0, 24, 64, 24), pad_m=box(0, 20, 56, 20), tag="section")

    partners = con("Included", [
        heading("What’s available on all our cPanel plans", "pwh-h3 pwh-text-ink", tag="h2", align="center"),
        con("Logos", [
            image(MEDIA + f, "pwh-partner", alt=n, align="center", width=px(201))
            for n, f in PARTNER_LOGOS
        ], direction="row", gap_px=24, justify="center", width=px(900), width_t=pct(100),
            extra={"flex_wrap": "wrap"}),
    ], boxed=1180, gap_px=24, align="center", pad=box(0, 0, 72, 0), pad_t=box(0, 24, 64, 24), pad_m=box(0, 20, 56, 20), tag="section")
    # 3 per row: each logo slot is a third of the 900px grid.
    for w in partners["elements"][1]["elements"]:
        w["settings"].update({"_element_width": "initial", "_element_custom_width": pct(30),
                              "_element_custom_width_mobile": pct(45)})

    trust = con("TrustStrip", [
        text("<ul class=\"pwh-trust-list\"><li>Free migration on every plan</li><li>No lock-in contracts</li>"
             "<li>Perth-based support, every plan</li><li>30-day money-back guarantee on yearly plans</li></ul>", ""),
    ], cls="pwh-trust", boxed=1180, pad=box(28, 0), pad_t=box(28, 24), pad_m=box(24, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})

    return template("PWH – cPanel Plans", "wp-page", [hero, toggle, cards, reviews, partners, trust],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- Domains ---------------------------------------------------------------

# Same Figma image as the Home "Domains" card, already in the Media Library.
DOMAINS_HERO = MEDIA + "f3df1232345aad30c3209977ac09361515473c56.png"
DOMAINS_TRANSFER = MEDIA + "domains-transfer.jpg"

# Draft answers: written only from what the Figma pages already say. Not in
# the design; review before publishing.
DOMAIN_FAQ = [
    ("Which domain extension should I choose?",
     "<p>For most Western Australian businesses a .com.au is the safe choice. It tells customers you're a local business. Many also register the matching .com so nobody else can take it.</p>"
     "<p>Not sure? Send us your business name and we'll suggest the best domain and extension, free of charge.</p>"),
    ("How does transferring a domain to you work?",
     "<p>We handle the whole transfer for you: no downtime, no lost email and no chasing transfer codes (EPP codes) yourself. We manage it from your current domain provider (registrar), start to finish.</p>"
     "<p>Send us a quick enquiry and our Perth team will scope the transfer, usually the same day.</p>"),
    ("What is WHOIS privacy protection?",
     "<p>It hides your personal details from the public domain register (WHOIS). It's only available on international extensions (TLDs) like .com, .net and .org. Australian .au domains don't offer it.</p>"),
    ("Will you remind me before my domain expires?",
     "<p>Yes. We send renewal reminders so your domain never quietly expires.</p>"),
    ("Can I bundle a domain with hosting or email?",
     "<p>Yes. Hosting, domains and email are all looked after by the same Perth team, and we connect your domain to your hosting or email for you.</p>"),
]


def domains():
    hero = con("Hero", [
        con("Copy", [
            heading("Find your name.<br>Lock it in properly.", "pwh-h2 pwh-text-cream", tag="h1"),
            text("<p>Register, manage or transfer your .com.au, .com or any other domain, with reminders so it never quietly expires.</p>",
                 "pwh-body pwh-text-cream"),
            widget("pwh-domain-search", {"placeholder": "Search for your domain", "action": "", "param": "query", "whmcs": "yes"}),
        ], gap_px=16, width=pct(50), width_t=pct(100), extra={"_flex_size": "grow"}),
        con("Visual", [
            image(DOMAINS_HERO, "", alt="A phone showing a website built on Perth Web Hosting"),
        ], cls="pwh-domains-visual", width=pct(50), width_t=pct(100), min_h=380, min_h_t=0,
            extra={"_flex_size": "grow"}),
    ], cls="pwh-domains-hero", direction="row", boxed=1180, gap_px=64, align="center", dir_t="column",
        gap_t=40, pad=box(136, 0, 140, 0), pad_t=box(72, 24, 72, 24), pad_m=box(56, 20, 56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#0B1629"})

    chips = ".com.au .com .net.au .org.au .io .net .au .co .photos .org .store .biz .solutions .id.au".split()
    register = con("Register", [
        con("Copy", [
            heading("Search, register, done.", "pwh-h3 pwh-text-ink", tag="h2"),
            text("<p>Search your business name across every extension that matters in Australia. We'll flag if it's taken, suggest close alternatives, and register it in minutes.</p>",
                 "pwh-body pwh-text-ink"),
            con("Privacy note", [
                text('<div class="pwh-note-switch" aria-hidden="true"></div>', ""),
                con("Note text", [
                    heading("Domain privacy (WHOIS)", "pwh-note-title", tag="p"),
                    text("<p>Hides your personal details from the public domain register (WHOIS). Only available on international extensions (TLDs) like .com, .net and .org. Australian .au domains don't offer it.</p>",
                         "pwh-note-text"),
                ], gap_px=2, extra={"_flex_size": "grow"}),
            ], cls="pwh-note", direction="row", gap_px=16, align="flex-start", pad=box(18)),
        ], gap_px=16, width=px(638), width_t=pct(100), extra={"_flex_size": "none"}),
        con("Extensions", [
            heading(".com.au plus every other extension", "pwh-label", tag="p"),
            text('<ul class="pwh-chips">' + "".join(f"<li>{c}</li>" for c in chips) + '<li class="is-more">+ more</li></ul>', ""),
        ], gap_px=12, extra={"_flex_size": "grow"}),
    ], direction="row", boxed=1180, gap_px=60, align="flex-start", dir_t="column", gap_t=32,
        pad=box(80, 0, 40, 0), pad_t=box(64, 24, 40, 24), pad_m=box(56, 20, 32, 20), tag="section")

    steps = [
        "Search your business name across every extension that matters.",
        "Choose your domain, and any close alternatives worth grabbing too.",
        "Register: most domains are live within minutes.",
        "We connect it to your hosting or email for you.",
    ]
    how = con("HowItWorks", [
        heading("Four steps to your new domain.", "pwh-h3 pwh-text-ink", tag="h2"),
        text('<ol class="pwh-steps">' + "".join(f"<li>{t}</li>" for t in steps) + "</ol>", ""),
    ], boxed=1180, gap_px=40, pad=box(80, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})

    transfer = con("Transfer", [
        con("Copy", [
            heading("Bringing a domain across?<br>We'll handle the whole transfer.", "pwh-h3 pwh-text-cream", tag="h2"),
            text("<p>No downtime, no lost email, no chasing transfer codes (EPP codes) yourself. We manage the whole transfer from your current domain provider (registrar), start to finish.</p>",
                 "pwh-lead pwh-text-mist"),
            button("Ask Us About Transferring", url("/support/hosting-transfer-request/"), "pwh-btn--outline-cream"),
            text("<p>Sends a quick enquiry to our Perth team. We'll scope the transfer and come back to you, usually same day.</p>",
                 "pwh-small pwh-text-cream"),
        ], gap_px=16, width=px(760), width_t=pct(100), extra={"flex_align_items": "flex-start"}),
    ], boxed=1180, pad=box(100, 0), pad_t=box(80, 24), pad_m=box(64, 20), tag="section",
        extra={
            "background_background": "classic",
            "background_color": "#0B1629",
            "background_image": asset(DOMAINS_TRANSFER),
            "background_position": "center center",
            "background_size": "cover",
            "background_repeat": "no-repeat",
            "background_overlay_background": "classic",
            "background_overlay_color": "#0B1629",
            "background_overlay_opacity": {"unit": "px", "size": 0.8, "sizes": []},
        })

    faq = con("FAQ", [
        heading("Domain questions, answered.", "pwh-h3 pwh-text-ink", tag="h2"),
        con("Questions", [
            widget("toggle", {
                "tabs": [{"_id": _id("faq"), "tab_title": q, "tab_content": a} for q, a in DOMAIN_FAQ],
                "selected_icon": {"value": "fas fa-plus", "library": "fa-solid"},
                "selected_active_icon": {"value": "fas fa-minus", "library": "fa-solid"},
                "icon_align": "right",
                "title_html_tag": "h3",
                "faq_schema": "yes",
            }, "pwh-faq"),
        ], width=px(760), width_t=pct(100)),
    ], boxed=1180, gap_px=40, pad=box(80, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section")

    testimonials = con("Testimonials", [
        con("Intro", [
            heading("WA businesses who've<br>made the switch", "pwh-h2 pwh-text-ink", tag="h2"),
            text("<p>Here's what business owners say after switching.</p>", "pwh-body pwh-text-ink"),
        ], gap_px=8, width=px(744), width_t=pct(100)),
        con("Cards", [
            review("Excellent service from the guys at Perth Web Hosting. Love that my website is locally hosted and looked after. After years of being with 'the big global guys' and running into issues, downtime and more, all of that's finally over.",
                   "Nathan Hurst", "Google review, 5 stars"),
            review("Best web hosting services in Perth. I have tried many providers and these guys are the absolute best. I never have to wait for support and my website speeds are blazingly fast.",
                   "Jack Hampton", "Google review, 5 stars"),
            review("Great Service, Great Price, Great Support and Fast Speeds.", "Sora Kiari", "Google review, 5 stars"),
        ], direction="row", gap_px=32, align="stretch", dir_t="column", gap_t=24),
    ], boxed=1180, gap_px=40, pad=box(140, 0), pad_t=box(96, 24), pad_m=box(72, 20), tag="section")

    help_cta = con("HelpCTA", [
        heading("Not sure which extension is right for your business?", "pwh-h3 pwh-text-ink", tag="h2", align="center"),
        text("<p>Send us your business name and we'll suggest the best domain and extension, free of charge.</p>", "pwh-body pwh-text-ink"),
        button("Contact Us", url("/contact/"), "pwh-btn--amber", align="center"),
    ], boxed=494, gap_px=12, align="center", pad=box(101, 0), pad_t=box(80, 24), pad_m=box(64, 20), tag="section")
    help_cta["elements"][1]["settings"]["align"] = "center"

    return template("PWH – Domains", "wp-page", [hero, register, how, transfer, faq, testimonials, help_cta],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- About -----------------------------------------------------------------
# Built from the Figma REST API (Page / About, 157:2402).

ABOUT_HERO = MEDIA + "about-hero.jpg"        # Hero background (Cameron on the phone)
ABOUT_BACKUPS = MEDIA + "about-backups.jpg"  # "We're serious about backups." background


def photo_bg(img, opacity):
    return {
        "background_background": "classic",
        "background_color": "#0B1629",
        "background_image": asset(img),
        "background_position": "center center",
        "background_size": "cover",
        "background_repeat": "no-repeat",
        "background_overlay_background": "classic",
        "background_overlay_color": "#0B1629",
        "background_overlay_opacity": {"unit": "px", "size": opacity, "sizes": []},
    }


def about():
    hero = con("Hero", [
        con("Copy", [
            heading("A local Perth team you can actually get on the phone.", "pwh-h1 pwh-text-cream", tag="h1"),
            text("<p>We've been looking after websites, email and domains for Western Australian businesses for over 16 years. Same people who answer the phone, look after the servers, and fix the problem.</p>",
                 "pwh-lead pwh-lead--tight pwh-text-mist"),
        ], gap_px=14, width=px(760), width_t=pct(100)),
    ], boxed=1180, pad=box(116, 0, 120, 0), pad_t=box(96, 24, 96, 24), pad_m=box(72, 20, 72, 20), tag="section",
        extra=photo_bg(ABOUT_HERO, 0.6))

    story = con("Story", [
        heading("We're West Australian, through and through.", "pwh-h3 pwh-text-ink pwh-fixed", tag="h2"),
        text("<p>You're a growing business. Your website and email need to work hard, stay up, and be there when your customers are. That's the job we've been doing since 2006, for businesses right across WA.</p>",
             "pwh-body pwh-text-grey"),
    ], direction="row", boxed=1180, gap_px=12, dir_t="column", gap_t=16,
        pad=box(72, 0, 56, 0), pad_t=box(64, 24, 56, 24), pad_m=box(56, 20, 48, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})
    story["elements"][0]["settings"].update({"_element_width": "initial", "_element_custom_width": px(417),
                                             "_element_width_tablet": "inherit"})
    story["elements"][1]["settings"].update({"_flex_size": "grow"})

    video = con("IntroVideo", [
        con("Intro", [
            heading("Cameron, and a few of the businesses we look after.", "pwh-h2 pwh-text-ink", tag="h2", align="center"),
            text("<p>Two and a half minutes on why we do this locally, and a few Perth businesses on what it's been like since they switched.</p>",
                 "pwh-lead-17 pwh-text-grey"),
        ], gap_px=10, width=px(670), width_t=pct(100), align="center"),
        # Placeholder from the design. Swap for an Elementor Video widget once the video is ready.
        con("Video", [
            text('<span class="pwh-play" aria-hidden="true"></span>', ""),
            text("<p>VIDEO (2:30): Cameron on who we are,<br>plus customer stories</p>", "pwh-video-caption"),
        ], cls="pwh-video", gap_px=16, justify="center", align="center", min_h=495, min_h_t=360, min_h_m=240,
            extra={"background_background": "classic", "background_color": "#0B1629", "border_radius": box(16)}),
    ], boxed=1180, gap_px=24, align="center", pad=box(72, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section")
    video["elements"][0]["elements"][1]["settings"]["align"] = "center"

    infra = con("LocalInfrastructure", [
        con("Copy", [
            heading("Your data lives<br>in Perth.<br>So does the team.", "pwh-h2 pwh-text-ink", tag="h2"),
            text("<p>Your website and email are hosted on our servers in the NextDC data centre in Malaga. The people you talk to are the people who run those servers. No middleman, no offshore support desk, no ticket that sits for three days.</p>",
                 "pwh-lead-17 pwh-text-grey"),
        ], gap_px=12, width=px(558), width_t=pct(100), extra={"_flex_size": "none"}),
        image("images/about-infrastructure.jpg", "pwh-photo pwh-photo--300", alt="The Perth Web Hosting team working at the office"),
    ], direction="row", boxed=1180, gap_px=64, align="center", dir_t="column", gap_t=32,
        pad=box(72, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})
    infra["elements"][1]["settings"].update({"_flex_size": "grow"})

    backups = con("Security", [
        con("Copy", [
            heading("We're serious about backups.", "pwh-h2 pwh-text-cream", tag="h2"),
            text("<p>We back your site up every 3 hours to a separate Western Australian data centre. We're the only provider in Perth taking nightly snapshots of your website and holding them for 31 days. If something goes wrong, we roll you back to a recent version. Less lost work, less stress.</p>",
                 "pwh-lead-17 pwh-text-cream"),
        ], gap_px=12, width=px(700), width_t=pct(100)),
    ], boxed=1180, pad=box(72, 0, 56, 0), pad_t=box(64, 24, 56, 24), pad_m=box(56, 20, 48, 20), tag="section",
        extra=photo_bg(ABOUT_BACKUPS, 0.6))

    cameron = con("MeetCameron", [
        image("images/about-cameron.jpg", "pwh-photo pwh-photo--343 pwh-fixed", alt="Cameron Worts, founder of Perth Web Hosting, by the Swan River"),
        con("Copy", [
            heading("Meet the founder", "pwh-kicker", tag="p"),
            heading("Cameron Worts", "pwh-h2 pwh-text-cream", tag="h2"),
            text("<p>Cameron is the founder and the person behind Perth Web Hosting. He's passionate about technology and won't settle for second best on design, security or backups. His favourite part of the job is seeing a business click with how much easier a good website makes things. He's also a keen photographer, most of the shots on this site and around the office are his, usually taken while chasing a storm.</p>",
                 "pwh-lead-16 pwh-text-mist"),
        ], gap_px=12, pad=box(70, 0), pad_t=box(0), justify="center", extra={"_flex_size": "grow"}),
    ], direction="row", boxed=1180, gap_px=48, align="stretch", dir_t="column", gap_t=32,
        pad=box(72, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#0B1629"})
    cameron["elements"][0]["settings"].update({"_element_width": "initial", "_element_custom_width": px(514),
                                               "_element_width_tablet": "inherit"})

    cta = con("CTA", [
        heading("We'd love to work with you.", "pwh-h2 pwh-text-ink", tag="h2", align="center"),
        text("<p>Cameron and the team especially like finding the little wins that make a big difference. Get in touch today.<br>Your local hosting partner.</p>",
             "pwh-lead-17 pwh-text-grey"),
        button("Get in Touch", url("/contact/"), "pwh-btn--amber", align="center"),
    ], cls="pwh-cta-band", boxed=1180, gap_px=24, align="center", pad=box(64, 0), pad_t=box(56, 24), pad_m=box(48, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})
    cta["elements"][1]["settings"]["align"] = "center"

    return template("PWH – About", "wp-page", [hero, story, video, infra, backups, cameron, cta],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


def main():
    os.makedirs(OUT, exist_ok=True)
    files = {
        "header.json": header(),
        "footer.json": footer(),
        "home.json": home(),
        "mega-products.json": mega_products(),
        "mega-support.json": mega_support(),
        "mega-about.json": mega_about(),
        "cpanel.json": cpanel(),
        "domains.json": domains(),
        "about.json": about(),
    }
    for name, data in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("wrote", name)


if __name__ == "__main__":
    main()
