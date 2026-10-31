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
import re
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
    return con(name, cols, cls="pwh-mega", full=True, direction="row", gap_px=48, pad=box(28, 32),
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
    panel = con("Mega Menu / About", [col], cls="pwh-mega pwh-mega--narrow", full=True, pad=box(24), pad_m=box(24))
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
            "background_overlay_opacity": {"unit": "px", "size": 1, "sizes": []},
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


# --- Semi-Managed WordPress Plans --------------------------------------------
# Built from the Figma REST API (Page / Semi-Managed Plans, 114:1567). Yearly
# prices and technical details come from the cards' hidden toggled layers.

WORDPRESS_HERO = MEDIA + "wordpress-hero.jpg"


def wordpress():
    hero = con("Header", [
        heading("Pick the WordPress plan that fits your business.", "pwh-h1 pwh-text-cream", tag="h1", align="center"),
        text("<p>Semi-managed WordPress hosting. We handle the updates, security and monitoring, so you don't have to.</p>",
             "pwh-lead-17 pwh-lead-17--regular pwh-text-mist pwh-narrow-486"),
        text("<p>Semi-managed means we look after the technical upkeep of your site, you just run the business.</p>",
             "pwh-small pwh-text-mist"),
    ], cls="pwh-page-hero", boxed=882, gap_px=12, align="center",
        pad=box(116, 0, 120, 0), pad_t=box(96, 24, 96, 24), pad_m=box(72, 20, 72, 20), tag="section",
        extra=photo_bg(WORDPRESS_HERO, 0.6))
    for w in hero["elements"][1:]:
        w["settings"]["align"] = "center"

    toggle = con("Year Toggle", [
        widget("pwh-billing-toggle", {"monthly_label": "Monthly", "yearly_label": "Yearly",
                                      "yearly_badge": "Best value", "default": "monthly"}),
    ], boxed=1180, align="center", pad=box(56, 0), pad_t=box(48, 24), pad_m=box(40, 20), tag="section")

    email = "Free SSL certificate and unlimited email accounts (IMAP/POP3)"
    cards = con("Cards", [
        plan("Basic", "For a single WordPress site you're happy to leave mostly on autopilot.", "24.95",
             ["Email support only", email,
              "Weekly malware scans, an initial security audit and basic site lockdown",
              "Monthly plugin and theme checks, one-time setup optimisation, no ongoing monitoring",
              "5GB high-speed SSD storage", "50GB premium bandwidth", "1 WordPress website",
              "6-hourly, 31-day offsite backups"],
             yearly="299.40", yearly_note="Billed annually. Same rate as monthly, locked in for the year.",
             details="SpamAssassin filtering, 200% CPU, 12 MB/s I/O, 4GB RAM"),
        plan("Silver", "Our most popular managed plan, for businesses running more than one site.", "49.95",
             ["Local phone & email support, plus 30 minutes plugin & theme support", email,
              "Daily malware scans, a 12-monthly security audit and full site lockdown",
              "Monthly plugin and theme checks, 6-monthly optimisation review, monitored every 5 minutes",
              "10GB high-speed SSD storage", "250GB premium bandwidth", "2 WordPress websites",
              "6-hourly, 31-day offsite backups"],
             featured=True, tag="Most popular", yearly="499.50",
             yearly_note="Pay for 10 months, get 12. That's 2 months free.",
             details="SpamExperts filtering, 400% CPU, 12 MB/s I/O, 6GB RAM"),
        plan("Premium", "For high-traffic sites that need the closest watch.", "79.95",
             ["Local phone & email support, plus 1 hour plugin & theme support", email,
              "Daily malware scans, a 3-monthly security audit and full site lockdown",
              "Weekly plugin and theme checks, 3-monthly optimisation review, monitored every 2 minutes",
              "30GB high-speed SSD storage", "500GB premium bandwidth", "3 WordPress websites",
              "6-hourly, 31-day, 2-location offsite backups"],
             yearly="799.50", yearly_note="Pay for 10 months, get 12. That's 2 months free.",
             details="SpamExperts filtering, 600% CPU, 12 MB/s I/O, 10GB RAM"),
    ], cls="pwh-plans", boxed=1180, direction="row", gap_px=28, align="flex-start", dir_t="column",
        gap_t=24, pad=box(0, 0, 96, 0), pad_t=box(0, 24, 80, 24), pad_m=box(0, 20, 64, 20), tag="section")

    reviews = con("TestimonialStrip", [
        heading("What customers say", "pwh-h3 pwh-h3-amber", tag="h2", align="center"),
        con("Cards", [
            review("Absolutely top notch service, brilliant support. There is no problems, only solutions.",
                   "Cameron P", "Google review, 5 stars"),
            review("Tim did a fantastic job communicating with me via email, with very fast and detailed responses. The web hosting transfer was actioned smoothly with no downtime.",
                   "Kathy Krcmar", "Local Guide, Google review"),
            review("After spending 4 years trying to make my site faster by changing every WordPress setting, Perth Web Hosting proved it was just bad hosting all along.",
                   "Mathew Sallur", "Local Guide, Google review"),
        ], direction="row", gap_px=24, align="stretch", dir_t="column"),
    ], boxed=1180, gap_px=24, pad=box(0, 0, 72, 0), pad_t=box(0, 24, 64, 24), pad_m=box(0, 20, 56, 20), tag="section")

    trust = con("TrustStrip", [
        text("<ul class=\"pwh-trust-list\"><li>Free migration on every plan</li><li>No lock-in contracts</li>"
             "<li>Perth-based support, every plan</li><li>30-day money-back guarantee on yearly plans</li></ul>", ""),
    ], cls="pwh-trust", boxed=1180, pad=box(28, 0), pad_t=box(28, 24), pad_m=box(24, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})

    return template("PWH – Semi-Managed WordPress Plans", "wp-page", [hero, toggle, cards, reviews, trust],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- Contact (standalone export) -------------------------------------------
# Built from the Figma REST API (Page / Contact, 155:2274). Exported to
# export/contact.json as a self-contained Elementor template: relative links,
# absolute Media Library image URLs, and its CSS in an HTML widget so it
# works without a theme update.

CONTACT_HERO = MEDIA + "contactus-hero.jpg"  # as uploaded to the Media Library

CONTACT_CSS = """
.pwh-c-card{border-radius:12px;border:1px solid var(--pwh-navy-pale,#c2d3e8);background:var(--pwh-cream,#fffef4)}
.pwh-c-card--dark{background:var(--pwh-navy-ink,#0b1629);border-color:var(--pwh-navy-ink,#0b1629)}
.pwh-c-kicker .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:12px;font-weight:700;line-height:15px}
.pwh-c-title .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:20px;font-weight:700;line-height:24px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-c-text,.pwh-c-text p{margin:0;font-family:Inter,sans-serif;font-size:14px;line-height:17px}
.pwh-c-link .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:14px;font-weight:700;line-height:17px}
.pwh-c-link .elementor-heading-title a{color:inherit;text-decoration:underline;text-underline-offset:3px}
.pwh-c-link .elementor-heading-title a:hover{text-decoration-thickness:2px}
.pwh-c-card--dark .pwh-c-title .elementor-heading-title,.pwh-c-card--dark .pwh-c-link .elementor-heading-title{color:var(--pwh-cream,#fffef4)}
.pwh-c-card--dark .pwh-c-kicker .elementor-heading-title,.pwh-c-card--dark .pwh-c-text{color:var(--pwh-navy-mist,#eaf0f8)}
.pwh-c-details{border-top:1px solid var(--pwh-navy-pale,#c2d3e8);border-bottom:1px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-c-info,.pwh-c-info p{margin:0;font-family:Inter,sans-serif;font-size:15px;line-height:18px;color:var(--pwh-grey-dark,#575557)}
.pwh-c-info strong,.pwh-c-info a{color:var(--pwh-navy-ink,#0b1629);font-weight:700;text-decoration:none}
.pwh-c-note,.pwh-c-note p{margin:0;font-family:Inter,sans-serif;font-size:13px;line-height:16px;color:var(--pwh-grey,#828082)}
.pwh-c-map iframe{display:block;border-radius:10px;border:2px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-c-formcard{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:16px;background:var(--pwh-cream,#fffef4)}
.pwh-form .elementor-field-group{margin-bottom:20px!important}
.pwh-form .elementor-field-label{margin-bottom:8px;padding:0;font-family:Inter,sans-serif;font-size:13px;font-weight:700;line-height:16px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-form .elementor-mark-required .elementor-field-label:after{color:var(--pwh-amber-deep,#9e6e25);padding-left:4px}
.pwh-form .elementor-field-textual,.pwh-form .elementor-select-wrapper select{min-height:46px;padding:14px 16px;border:1.5px solid var(--pwh-navy-pale,#c2d3e8)!important;border-radius:8px!important;background:var(--pwh-cream,#fffef4)!important;color:var(--pwh-navy-ink,#0b1629)!important;font-family:Inter,sans-serif;font-size:15px;line-height:18px}
.pwh-form textarea.elementor-field-textual{min-height:92px}
.pwh-form .elementor-field-textual::placeholder{color:var(--pwh-grey,#828082);opacity:1}
.pwh-form .elementor-field-textual:focus,.pwh-form select:focus{outline:2px solid var(--pwh-amber,#c89439);outline-offset:1px;box-shadow:none}
.pwh-form .elementor-select-wrapper .select-caret-down-wrapper{right:16px;color:var(--pwh-grey,#828082);font-size:12px}
.pwh-form .elementor-button{width:100%;min-height:48px;padding:15px 30px;border-radius:16px;background:var(--pwh-amber,#c89439)!important;color:var(--pwh-navy-ink,#0b1629)!important;font-family:Inter,sans-serif;font-size:15px;font-weight:700}
.pwh-form .elementor-button:hover{background:#b5832c!important}
.pwh-form .gform_wrapper{margin:0;font-family:Inter,sans-serif}
.pwh-form .gform_wrapper .gform_fields{grid-row-gap:20px}
.pwh-form .gform_wrapper .gfield_label{display:block;margin:0 0 8px;padding:0;font-family:Inter,sans-serif;font-size:13px;font-weight:700;line-height:16px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-form .gform_wrapper .gfield_required{display:inline;margin:0;padding-left:4px;color:var(--pwh-amber-deep,#9e6e25);font-size:inherit}
.pwh-form .gform_wrapper.gravity-theme input:not([type=submit]):not([type=hidden]):not([type=checkbox]):not([type=radio]),.pwh-form .gform_wrapper.gravity-theme select,.pwh-form .gform_wrapper.gravity-theme textarea{box-sizing:border-box;width:100%;min-height:46px;margin:0;padding:14px 16px;border:1.5px solid var(--pwh-navy-pale,#c2d3e8);border-radius:8px;background-color:var(--pwh-cream,#fffef4);color:var(--pwh-navy-ink,#0b1629);font-family:Inter,sans-serif;font-size:15px;line-height:18px;box-shadow:none}
.pwh-form .gform_wrapper.gravity-theme .gfield textarea,.pwh-form .gform_wrapper.gravity-theme .gfield textarea.large{height:92px;min-height:92px;resize:vertical}
.pwh-form .gform_wrapper.gravity-theme select{-webkit-appearance:none;appearance:none;padding-right:44px;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23828082' stroke-width='1.6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 16px center;background-size:12px 8px;cursor:pointer}
.pwh-form .gform_wrapper ::placeholder{color:var(--pwh-grey,#828082);opacity:1}
.pwh-form .gform_wrapper.gravity-theme input:focus,.pwh-form .gform_wrapper.gravity-theme select:focus,.pwh-form .gform_wrapper.gravity-theme textarea:focus{outline:2px solid var(--pwh-amber,#c89439);outline-offset:1px;box-shadow:none}
.pwh-form .gform_wrapper.gravity-theme .gform_footer{margin:20px 0 0;padding:0}
.pwh-form .gform_wrapper.gravity-theme .gform_footer input[type=submit],.pwh-form .gform_wrapper.gravity-theme .gform_footer button{width:100%;min-height:48px;margin:0;padding:15px 30px;border:0;border-radius:16px;background:var(--pwh-amber,#c89439);color:var(--pwh-navy-ink,#0b1629);font-family:Inter,sans-serif;font-size:15px;font-weight:700;line-height:18px;cursor:pointer;transition:background .2s}
.pwh-form .gform_wrapper.gravity-theme .gform_footer input[type=submit]:hover,.pwh-form .gform_wrapper.gravity-theme .gform_footer input[type=submit]:focus{background:#b5832c;color:var(--pwh-navy-ink,#0b1629)}
.pwh-form .gform_wrapper.gravity-theme .gform_footer input[type=submit]:focus-visible{outline:2px solid var(--pwh-navy-ink,#0b1629);outline-offset:2px}
.pwh-form .gform_wrapper .gform_ajax_spinner{margin-left:12px}
.pwh-form .gform_wrapper.gravity-theme .gfield.gfield_error input:not([type=submit]):not([type=hidden]):not([type=checkbox]):not([type=radio]),.pwh-form .gform_wrapper.gravity-theme .gfield.gfield_error select,.pwh-form .gform_wrapper.gravity-theme .gfield.gfield_error textarea{border-color:#b3261e}
.pwh-form .gform_wrapper.gravity-theme .gfield_error .gfield_label{color:var(--pwh-navy-ink,#0b1629)}
.pwh-form .gform_wrapper.gravity-theme .gfield_validation_message,.pwh-form .gform_wrapper.gravity-theme .validation_message{margin:6px 0 0;padding:0;border:0;background:none;color:#b3261e;font-size:13px;line-height:16px}
.pwh-form .gform_wrapper.gravity-theme .gform_validation_errors{margin:0 0 20px;padding:12px 16px;border:1.5px solid #b3261e;border-radius:8px;background:#fdf1f0;box-shadow:none}
.pwh-form .gform_wrapper.gravity-theme .gform_validation_errors>h2{margin:0;color:#b3261e;font-family:Inter,sans-serif;font-size:14px;font-weight:700;line-height:18px}
.pwh-form .gform_wrapper.gravity-theme .gform_validation_errors>h2 .gform-icon{display:none}
.pwh-form .gform_confirmation_message{padding:16px 20px;border-radius:8px;background:var(--pwh-navy-mist,#eaf0f8);color:var(--pwh-navy-ink,#0b1629);font-family:Inter,sans-serif;font-size:15px;line-height:22px}
.pwh-c-calendly{border:2px dashed var(--pwh-navy-pale,#c2d3e8);border-radius:16px;background:var(--pwh-navy-mist,#eaf0f8)}
.pwh-c-calendly-title .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:20px;font-weight:900;line-height:24px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-c-style{display:none!important}
.pwh-c-title--16 .elementor-heading-title{font-size:16px;line-height:19px}
.pwh-lead--tight,.pwh-lead--tight p{line-height:22px}
.pwh-lead-16,.pwh-lead-16 p{margin:0;font-family:Inter,sans-serif;font-size:16px;font-weight:300;line-height:19px}
.pwh-text-grey{color:var(--pwh-grey-dark,#575557)}
@media (min-width:1025px){.pwh-c-row>.e-con,.pwh-c-row>.e-con-inner>.e-con{flex:1 1 0!important;min-width:0}.pwh-c-row2>.e-con,.pwh-c-row2>.e-con-inner>.e-con{flex:0 0 calc(50% - 24px)!important;max-width:calc(50% - 24px);min-width:0}.pwh-c-map{flex:1 1 0!important;min-width:0}}
"""


def contact_card(kicker, kicker_color, title, body, link_text, link, dark=False, body_color=None):
    return con(f"Card – {title}", [
        widget("heading", {"title": kicker, "header_size": "p", "title_color": kicker_color}, "pwh-c-kicker"),
        heading(title, "pwh-c-title", tag="h2"),
        text(f"<p>{body}</p>", "pwh-c-text"),
        heading(link_text, "pwh-c-link", tag="p", link=link),
    ], cls="pwh-c-card" + (" pwh-c-card--dark" if dark else ""), gap_px=10, pad=box(28),
        width=pct(33.33), width_t=pct(100), extra={"_flex_size": "grow"})


def contact():
    style = widget("html", {"html": "<style>" + " ".join(CONTACT_CSS.split()) + "</style>"}, "pwh-c-style")

    hero = con("Header", [
        heading("Talk to a real person in Perth.", "pwh-h1 pwh-text-cream", tag="h1"),
        text("<p>No call centre, no ticket queue. Pick the quickest path for what you need, or send us a message.<br>Your local hosting partner.</p>",
             "pwh-lead pwh-lead--tight pwh-text-cream"),
    ], boxed=1180, gap_px=12, justify="center", pad=box(116, 0, 120, 0), pad_t=box(96, 24, 96, 24), pad_m=box(72, 20, 72, 20),
        min_h=504, min_h_t=0, tag="section", extra=photo_bg(CONTACT_HERO, 0.6))
    hero["elements"][0]["settings"].update({"_element_width": "initial", "_element_custom_width": px(580),
                                            "_element_width_tablet": "inherit"})

    cards = con("PriorityCTAs", [
        contact_card("Want to talk it through", "#C89439", "Book a Call back",
                     "Pick a time that suits and one of our team will call you. No pitch, just answers.",
                     "View plans →", url("#book-a-call")),
        contact_card("Not sure yet", "#9E6E25", "Take the 2-minute quiz",
                     "Answer a few quick questions and we'll recommend the right hosting, email and domain setup.",
                     "Start the quiz →", url("/get-started/")),
        contact_card("Already a customer?", "#EAF0F8", "Login to MyToolbox",
                     "Change this copy and all.", "Login to MyToolbox →", url("/client-login/"), dark=True),
    ], cls="pwh-c-row", direction="row", boxed=1180, gap_px=24, align="stretch", dir_t="column",
        pad=box(80, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section")
    # Body copy colours per card (Figma): navy / grey-dark / mist.
    cards["elements"][0]["elements"][2]["settings"]["text_color"] = "#0B1629"
    cards["elements"][1]["elements"][2]["settings"]["text_color"] = "#575557"

    details = con("Details", [
        con("Info", [
            heading("Perth Web Hosting", "pwh-c-title", tag="p"),
            text("<p>Suite 3, Level 3, 533 Hay Street, Perth WA 6000</p>", "pwh-c-info"),
            text('<p><a href="tel:+61863654522">08 6365 4522</a></p>', "pwh-c-info"),
            text("<p>Mon to Fri, 8:30am to 5:30pm<br>Perth time</p>", "pwh-c-info"),
            text("<p>After-hours support is available to logged-in clients through MyToolbox.</p>", "pwh-c-note"),
        ], gap_px=16, width=px(636), width_t=pct(100)),
        widget("google_maps", {"address": "533 Hay Street, Perth WA 6000", "zoom": px(16),
                               "height": px(220), "prevent_scroll": "yes"}, "pwh-c-map"),
    ], cls="pwh-c-details", direction="row", boxed=1180, gap_px=64, align="center", dir_t="column", gap_t=32,
        pad=box(56, 0), pad_t=box(56, 24), pad_m=box(48, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})
    details["elements"][0]["elements"][0]["settings"]["_css_classes"] = "pwh-c-title pwh-c-title--16"
    details["elements"][1]["settings"].update({"_flex_size": "grow"})

    # Gravity Forms "PWH Contact" (import export/gravityforms-contact.json, see gf_contact_form()).
    # Change id="1" to the form's ID if Gravity Forms gives it a different one on import.
    form = widget("shortcode", {"shortcode": GF_CONTACT_SHORTCODE}, "pwh-form")

    form_col = con("FormCol", [
        heading("Send us a message", "pwh-h3 pwh-text-ink", tag="h2"),
        text("<p>We reply to most enquiries the same business day.</p>", "pwh-c-text"),
        form,
    ], cls="pwh-c-formcard", gap_px=20, pad=box(36), pad_m=box(24), width=px(566), width_t=pct(100))
    form_col["elements"][1]["settings"]["text_color"] = "#575557"

    booking = con("BookingCol", [
        heading("Prefer we call you?", "pwh-h3 pwh-text-ink", tag="h2"),
        text("<p>Book a callback at a time that suits. One of our Perth team will phone you.</p>", "pwh-lead-16 pwh-text-grey"),
        # Placeholder from the design. Replace with your Calendly inline embed (HTML widget).
        con("Calendly", [
            heading("Calendly booking widget", "pwh-c-calendly-title", tag="p", align="center"),
            text("<p>Embedded Calendly callback scheduler to be integrated here.</p>", "pwh-c-text"),
        ], cls="pwh-c-calendly", gap_px=12, justify="center", align="center", min_h=520, min_h_m=360, pad=box(24)),
    ], gap_px=16, width=px(566), width_t=pct(100), extra={"_element_id": "book-a-call"})
    booking["elements"][2]["elements"][1]["settings"].update({"align": "center", "text_color": "#575557"})

    form_row = con("FormAndBooking", [form_col, booking], cls="pwh-c-row2", direction="row", boxed=1180, gap_px=48,
                   align="flex-start", dir_t="column", gap_t=40, pad=box(72, 0, 96, 0), pad_t=box(64, 24, 80, 24),
                   pad_m=box(56, 20, 64, 20), tag="section")

    hero["elements"].insert(0, style)
    return template("PWH – Contact", "page", [hero, cards, details, form_row],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- Microsoft 365 -----------------------------------------------------------
# Built from the Figma REST API (Page / Email — Microsoft 365, 159:2684) as a
# standalone template: page CSS travels inside the JSON.

M365_HERO = MEDIA + "778c8aaa03f6bb48282fd0777887a6c43c6c1b7e-scaled.jpg"  # as uploaded to the Media Library

M365_CSS = """
.pwh-m-style{display:none!important}
.pwh-lead--tight,.pwh-lead--tight p{line-height:22px}
.pwh-m-card{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:10px;background:var(--pwh-cream,#fffef4)}
.pwh-m-card-title .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:16px;font-weight:700;line-height:19px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-m-text,.pwh-m-text p{margin:0;font-family:Inter,sans-serif;font-size:14px;line-height:17px;color:var(--pwh-grey-dark,#575557)}
.pwh-m-note,.pwh-m-note p{margin:0;font-family:Inter,sans-serif;font-size:13px;line-height:16px;color:var(--pwh-grey,#828082)}
.pwh-m-plans{border-top:1px solid var(--pwh-navy-pale,#c2d3e8);border-bottom:1px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-m-plan{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:12px;background:var(--pwh-cream,#fffef4)}
.pwh-m-plan--featured{border:2px solid var(--pwh-navy-ink,#0b1629)}
.pwh-m-tag .elementor-heading-title{display:inline-block;margin:0;padding:5px 10px;border-radius:3px;background:var(--pwh-sand,#e8e0c8);color:var(--pwh-amber-deep,#9e6e25);font-family:Inter,sans-serif;font-size:11px;font-weight:700;line-height:13px}
.pwh-m-plan-title .elementor-heading-title{margin:0;font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:22px;font-weight:900;line-height:26px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-m-from .elementor-heading-title{margin:0;font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:12px;font-weight:700;line-height:16px;letter-spacing:1.8px;text-transform:uppercase;color:var(--pwh-navy-ink,#0b1629)}
.pwh-m-price .elementor-heading-title{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px;margin:0;color:var(--pwh-navy-ink,#0b1629)}
.pwh-m-amt{font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:40px;font-weight:900;line-height:46px;letter-spacing:-.9px}
.pwh-m-per{font-family:Inter,sans-serif;font-size:14px;font-weight:400;line-height:17px;color:var(--pwh-grey-dark,#575557)}
.pwh-m-rule{height:1px;background:var(--pwh-navy-pale,#c2d3e8)}
.pwh-m-list .elementor-icon-list-items{margin:0;padding:0}
.pwh-m-list .elementor-icon-list-item{align-items:flex-start!important}
.pwh-m-list .elementor-icon-list-item:not(:last-child){padding-bottom:10px!important}
.pwh-m-list .elementor-icon-list-icon{width:16px;height:17px;padding:0!important;margin-right:10px;justify-content:center;align-items:center;display:flex}
.pwh-m-list .elementor-icon-list-icon i{font-size:11px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-m-list .elementor-icon-list-icon svg{width:11px;height:11px;fill:var(--pwh-navy-ink,#0b1629)}
.pwh-m-list .elementor-icon-list-text{padding:0!important;font-family:Inter,sans-serif;font-size:14px;line-height:17px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-m-plan .pwh-btn{margin-top:auto}
.pwh-m-plan .pwh-btn .elementor-button{width:100%;min-height:48px;padding:15px 30px;border-radius:16px;font-family:Inter,sans-serif;font-size:15px;font-weight:700;line-height:18px}
.pwh-m-btn-amber .elementor-button{background:var(--pwh-amber,#c89439)!important;color:var(--pwh-navy-ink,#0b1629)!important}
.pwh-m-btn-amber .elementor-button:hover{background:#b5832c!important}
.pwh-m-btn-navy .elementor-button{background:var(--pwh-navy,#1a325b)!important;color:var(--pwh-cream,#fffef4)!important}
.pwh-m-btn-navy .elementor-button:hover{background:var(--pwh-navy-ink,#0b1629)!important}
.pwh-m-faq .elementor-toggle-item{margin:0!important;border:0;border-bottom:1px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-m-faq .elementor-tab-title{display:flex;align-items:center;gap:16px;padding:20px 0!important;border:0!important;cursor:pointer}
.pwh-m-faq .elementor-toggle-title{flex:1 1 auto;order:1;color:var(--pwh-navy-ink,#0b1629)!important;font-family:Inter,sans-serif;font-size:17px;font-weight:700;line-height:21px;text-decoration:none}
.pwh-m-faq .elementor-toggle-icon{order:2;flex:0 0 20px;width:20px!important;margin:0!important;color:var(--pwh-navy-ink,#0b1629);font-size:14px;text-align:center}
.pwh-m-faq .elementor-toggle-icon svg{width:14px;height:14px;fill:currentColor}
.pwh-m-faq .elementor-tab-content{padding:0 40px 20px 0!important;border:0!important;color:var(--pwh-grey-dark,#575557);font-family:Inter,sans-serif;font-size:16px;line-height:24px}
.pwh-m-faq .elementor-tab-content p{margin:0 0 8px}
.pwh-m-faq .elementor-tab-content p:last-child{margin-bottom:0}
.pwh-m-faq .elementor-tab-title:focus-visible{outline:2px solid var(--pwh-amber,#c89439);outline-offset:2px}
.pwh-m-grid>.e-con,.pwh-m-grid>.e-con-inner>.e-con{flex:0 0 calc((100% - 48px)/3)!important;max-width:calc((100% - 48px)/3);min-width:0}
.pwh-m-row>.e-con,.pwh-m-row>.e-con-inner>.e-con{flex:0 0 calc(50% - 12px)!important;max-width:calc(50% - 12px);min-width:0}
.pwh-m-hero .elementor-widget{max-width:100%}
@media (max-width:1024px){.pwh-m-row,.pwh-m-row>.e-con-inner{flex-direction:column!important}.pwh-m-grid>.e-con,.pwh-m-grid>.e-con-inner>.e-con{flex-basis:calc((100% - 24px)/2)!important;max-width:calc((100% - 24px)/2)}.pwh-m-row>.e-con,.pwh-m-row>.e-con-inner>.e-con{flex:0 0 auto!important;max-width:100%;width:100%}}
@media (max-width:767px){.pwh-m-grid>.e-con,.pwh-m-grid>.e-con-inner>.e-con{flex-basis:100%!important;max-width:100%}.pwh-m-amt{font-size:34px;line-height:40px}}
"""

# Draft answers: written only from what the Figma page already says. Not in
# the design; review before publishing.
M365_FAQ = [
    ("What's the difference between Plan 1 and Business?",
     "<p>Exchange Online Plan 1 is business email: a 50GB mailbox, shared calendars, contacts and tasks, webmail and the Android and Apple apps.</p>"
     "<p>Microsoft 365 Business gives you a 100GB mailbox and adds the Office apps (web and desktop) and SpamExperts spam and virus filtering. It comes in Basic, Standard and Premium tiers.</p>"),
    ("Can I mix basic email and Microsoft 365 across my team?",
     "<p>Often, yes, depending on how your email is set up. Call us on <a href=\"tel:+61863654522\">08 6365 4522</a> and we'll tell you what works for your domain and your team.</p>"),
    ("Do you move my existing mailboxes across?",
     "<p>Yes. Send us a <a href=\"/support/microsoft-transfer-request/\">Microsoft Transfer Request</a> and our Perth team will plan the move with you.</p>"),
    ("How long does it take to set up a licence?",
     "<p>Licences are set up by hand during business hours (Mon to Fri, 8:30am to 5:30pm Perth time).</p>"),
    ("Can I add or remove licences later?",
     "<p>Yes. Microsoft 365 is charged per licence, so just let us know when your team changes and we'll adjust it.</p>"),
]


def m365_card(title, body):
    return con(f"Card – {title}", [
        heading(title, "pwh-m-card-title", tag="h3"),
        text(f"<p>{body}</p>", "pwh-m-text"),
    ], cls="pwh-m-card", gap_px=8, pad=box(24), width_t=pct(100))


def m365_plan(title, amount, per, features, button_cls, featured=False, tag="", from_label=False):
    items = []
    if tag:
        items.append(heading(tag, "pwh-m-tag", tag="p"))
    items.append(heading(title, "pwh-m-plan-title", tag="h3"))
    price = heading(f'<span class="pwh-m-amt">{amount}</span><span class="pwh-m-per">{per}</span>', "pwh-m-price", tag="p")
    if from_label:
        items.append(con("Price", [heading("From", "pwh-m-from", tag="p"), price], gap_px=6))
    else:
        items.append(price)
    items.append(widget("divider", {"style": "solid", "weight": px(1), "color": "#C2D3E8", "gap": px(0)}, ""))
    items.append(widget("icon-list", {
        "icon_list": [{"_id": _id("li"), "text": f, "selected_icon": {"value": "fas fa-check", "library": "fa-solid"}}
                      for f in features],
        "space_between": px(10),
        "icon_size": px(11),
        "icon_color": "#0B1629",
        "text_color": "#0B1629",
    }, "pwh-m-list"))
    # Order links aren't in the design; set them per card in Elementor.
    items.append(button("Get a Licence", url("/contact/"), button_cls))
    return con(f"Plan – {title}", items,
               cls="pwh-m-plan" + (" pwh-m-plan--featured" if featured else ""),
               gap_px=14, pad=box(32), pad_m=box(24), width_t=pct(100))


def m365():
    style = widget("html", {"html": "<style>" + " ".join(M365_CSS.split()) + "</style>"}, "pwh-m-style")

    # Figma pads the hero 200px at the top because the nav overlaps it; the
    # sticky header sits above the page here, so 84px comes off.
    hero = con("Hero", [
        style,
        heading("Microsoft 365, set up and supported by your local team.", "pwh-h1 pwh-text-cream", tag="h1"),
        text("<p>Full business mailboxes (Exchange), shared calendars, and the Office apps your team already knows. "
             "Bought through us, you get a real Perth phone number for support instead of Microsoft's queue.</p>",
             "pwh-lead pwh-lead--tight pwh-text-mist"),
    ], cls="pwh-m-hero", boxed=1180, gap_px=14, justify="center", pad=box(116, 0, 120, 0), pad_t=box(96, 24, 96, 24),
        pad_m=box(72, 20, 72, 20), min_h=502, min_h_t=0, tag="section", extra=photo_bg(M365_HERO, 0.6))
    for w in hero["elements"][1:]:
        w["settings"].update({"_element_width": "initial", "_element_custom_width": px(760),
                              "_element_width_tablet": "inherit"})

    why = con("WhyUpgrade", [
        heading("What you get over basic email.", "pwh-h2 pwh-text-ink", tag="h2"),
        con("Cards", [
            m365_card("Bigger mailboxes", "50GB to 100GB per mailbox, so you're not deleting emails to make room."),
            m365_card("Shared calendars and contacts", "See when the team's free, book meetings, share a company address book."),
            m365_card("Works on every device, in sync", "Read an email on your phone, it's read on your laptop too. Same for your calendar."),
            m365_card("The Office apps", "Word, Excel, Outlook and Teams, on the web and installed on your machine (Business plans)."),
            m365_card("Local phone support", "Something not working? Call a Perth number and talk to someone who can fix it."),
            m365_card("Long-term archiving", "10-year archive backup available, handy if you need to keep records."),
        ], cls="pwh-m-grid", direction="row", gap_px=24, align="stretch", extra={"flex_wrap": "wrap"}),
    ], boxed=1180, gap_px=24, pad=box(72, 0, 56, 0), pad_t=box(64, 24, 56, 24), pad_m=box(56, 20, 48, 20), tag="section")

    plans = con("Plans", [
        heading("Two ways to buy.", "pwh-h2 pwh-text-ink", tag="h2"),
        text("<p>All prices exclude GST. Licenses are set up by hand during business hours. "
             "Month-to-month billing costs a little more than paying 12 months up front.</p>", "pwh-m-note"),
        con("Cards", [
            m365_plan("Exchange Online Plan 1", "$7.50", "/ user / month", [
                "50GB mailbox storage", "Shared calendars, contacts and tasks", "150MB attachment size",
                "Local Perth telephone support", "Webmail and Android / Apple apps", "10-year archive backup available",
            ], "pwh-m-btn-amber", featured=True, tag="Most popular"),
            m365_plan("Microsoft 365 Business", "$13.95", "/ licence / month", [
                "100GB mailbox storage", "Everything in Plan 1, plus:", "Office apps, web and desktop",
                "SpamExperts spam and virus filtering", "Basic, Standard and Premium tiers", "Charged per licence",
            ], "pwh-m-btn-navy", from_label=True),
        ], cls="pwh-m-row", direction="row", gap_px=24, align="stretch", dir_t="column"),
        text("<p>Need Project, SharePoint, Visio, OneDrive for Business or something else? We can sort that too, "
             '<a href="/contact/">just ask</a>.</p>', "pwh-m-text"),
    ], cls="pwh-m-plans", boxed=1180, gap_px=24, pad=box(72, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})
    plans["elements"][1]["settings"]["_margin"] = box(0, 0, 0, 0)

    faq = con("FAQ", [
        heading("Microsoft 365 questions.", "pwh-h2 pwh-text-ink", tag="h2"),
        con("Questions", [
            widget("toggle", {
                "tabs": [{"_id": _id("faq"), "tab_title": q, "tab_content": a} for q, a in M365_FAQ],
                "selected_icon": {"value": "fas fa-plus", "library": "fa-solid"},
                "selected_active_icon": {"value": "fas fa-minus", "library": "fa-solid"},
                "icon_align": "right",
                "title_html_tag": "h3",
                "faq_schema": "yes",
            }, "pwh-m-faq"),
        ], width=px(760), width_t=pct(100)),
    ], boxed=1180, gap_px=24, pad=box(72, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section")

    return template("PWH – Microsoft 365", "page", [hero, why, plans, faq],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- Reseller Plans ----------------------------------------------------------
# Built from the Figma REST API (Page / Reseller Plans, 117:1942) as a
# standalone template. It reuses the theme's pricing card, billing toggle,
# review and trust-strip styles (already on the live site); only the new
# pieces carry their CSS inside the JSON.

RESELLER_CSS = """
.pwh-r-style{display:none!important}
.pwh-r-measure{max-width:100%;margin-left:auto!important;margin-right:auto!important}
.pwh-r-chips{display:flex;flex-wrap:wrap;justify-content:center;gap:12px;margin:0;padding:0;list-style:none}
.pwh-r-chips li{padding:7px 15px;border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:999px;background:var(--pwh-navy-mist,#eaf0f8);color:var(--pwh-navy-ink,#0b1629);font-family:Inter,sans-serif;font-size:13px;font-weight:700;line-height:16px}
.pwh-r-included{border-top:1px solid var(--pwh-navy-pale,#c2d3e8);border-bottom:1px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-r-card{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:10px;background:var(--pwh-cream,#fffef4)}
.pwh-r-card-title .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:15px;font-weight:700;line-height:18px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-r-card-text,.pwh-r-card-text p{margin:0;font-family:Inter,sans-serif;font-size:13px;line-height:16px;color:var(--pwh-grey-dark,#575557)}
.pwh-r-eyebrow .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:13px;font-weight:700;line-height:16px;color:#e8c07a}
.pwh-r-fine,.pwh-r-fine p{margin:0;font-family:Inter,sans-serif;font-size:13px;line-height:16px;color:var(--pwh-navy-soft,#6b91be);opacity:.75}
.pwh-r-grid>.e-con,.pwh-r-grid>.e-con-inner>.e-con{flex:1 1 0!important;min-width:0}
@media (max-width:1024px){.pwh-r-grid{flex-wrap:wrap!important}.pwh-r-grid>.e-con,.pwh-r-grid>.e-con-inner>.e-con{flex:0 0 calc(50% - 12px)!important;max-width:calc(50% - 12px)}}
@media (max-width:767px){.pwh-r-grid>.e-con,.pwh-r-grid>.e-con-inner>.e-con{flex-basis:100%!important;max-width:100%}}
"""


def reseller_card(title, body):
    return con(f"Card – {title}", [
        heading(title, "pwh-r-card-title", tag="h3"),
        text(f"<p>{body}</p>", "pwh-r-card-text"),
    ], cls="pwh-r-card", gap_px=8, pad=box(20), width_t=pct(100))


def reseller():
    style = widget("html", {"html": "<style>" + " ".join(RESELLER_CSS.split()) + "</style>"}, "pwh-r-style")

    def centred(w, width):
        w["settings"]["align"] = "center"
        w["settings"]["_css_classes"] += " pwh-r-measure"
        w["settings"]["_element_width"] = "initial"
        w["settings"]["_element_custom_width"] = px(width)
        w["settings"]["_element_width_tablet"] = "inherit"
        return w

    # Figma pads the hero 200px at the top because the nav overlaps it; the
    # sticky header sits above the page here, so 84px comes off.
    hero = con("Header", [
        style,
        centred(heading("Pick the reseller plan that fits your client base.", "pwh-h1 pwh-text-cream", tag="h1"), 908),
        centred(text("<p>Host your clients under your own brand, backed by a real Perth team.</p>",
                     "pwh-lead-17 pwh-lead-17--regular pwh-text-mist"), 948),
        centred(text("<p>Reseller hosting lets you host client sites under your own brand, using one control panel (WHM) "
                     "to run every account from one place. Your clients never see our name.</p>", "pwh-small pwh-text-mist"), 948),
    ], cls="pwh-page-hero", boxed=1180, gap_px=12, align="center",
        pad=box(116, 0, 120, 0), pad_t=box(96, 24, 96, 24), pad_m=box(72, 20, 72, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#0B1629"})

    chips = ["Marketing agencies", "Freelance web designers", "WordPress developers", "IT support shops"]
    audience = con("Audience", [
        con("Copy", [
            heading("Built for agencies, web designers and IT shops.", "pwh-h2 pwh-text-ink", tag="h2", align="center"),
            centred(text("<p>If you build or manage websites for other people, reseller hosting lets you put every client on "
                         "fast Perth servers under your own brand. You set the prices, you own the relationship. We stay invisible.</p>",
                         "pwh-lead-17 pwh-text-grey"), 680),
        ], gap_px=10, align="center", width=px(680), width_t=pct(100)),
        text('<ul class="pwh-r-chips">' + "".join(f"<li>{c}</li>" for c in chips) + "</ul>", ""),
    ], boxed=1180, gap_px=24, align="center", pad=box(80, 0, 56, 0), pad_t=box(64, 24, 56, 24),
        pad_m=box(56, 20, 48, 20), tag="section")
    audience["elements"][1]["settings"]["_element_width"] = "inherit"

    included = con("WhatsIncluded", [
        centred(heading("Everything your clients expect, running under your name.", "pwh-h2 pwh-text-ink", tag="h2"), 863),
        con("Cards", [
            reseller_card("A dashboard for every client",
                          "Every client gets their own dashboard (cPanel). You manage the lot from one place (WHM)."),
            reseller_card("One-click installs",
                          "An app installer (Softaculous) is built in, so clients can add WordPress and 400+ other apps in a click."),
            reseller_card("SpamExperts filtering", "Premium spam and virus filtering on every mailbox, included."),
            reseller_card("White-label, top to bottom",
                          "Your logo, your own web addresses (name servers), your support email. Clients never see us."),
        ], cls="pwh-r-grid", direction="row", gap_px=24, align="stretch"),
    ], cls="pwh-r-included", boxed=1180, gap_px=32, align="center", pad=box(72, 0), pad_t=box(64, 24), pad_m=box(56, 20),
        tag="section", extra={"background_background": "classic", "background_color": "#F5F1E0"})
    included["elements"][1]["settings"]["width"] = pct(100)

    support = con("SupportClarity", [
        heading("Support", "pwh-r-eyebrow", tag="p", align="center"),
        centred(heading("You've got a real<br>team behind you.", "pwh-h2 pwh-text-cream", tag="h2"), 700),
        centred(text("<p>Every reseller plan comes with priority support from the same Perth team that runs the servers. "
                     "They know how reseller setups work, they pick up the phone, and they stick with a problem until it's sorted. "
                     "When you need a hand, you're talking to someone who can help.</p>", "pwh-lead-17 pwh-text-mist"), 640),
        centred(text("<p>One small thing: that support covers you as the account holder. Your clients come to you, "
                     "you come to us. It's what keeps your brand out front.</p>", "pwh-r-fine"), 600),
    ], boxed=1180, gap_px=14, align="center", pad=box(64, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#0B1629"})

    toggle = con("Year Toggle", [
        widget("pwh-billing-toggle", {"monthly_label": "Monthly", "yearly_label": "Yearly",
                                      "yearly_badge": "Best value", "default": "monthly"}),
    ], boxed=1180, align="center", pad=box(56, 0), pad_t=box(48, 24), pad_m=box(40, 20), tag="section")

    common = ["Completely white-labelled, your clients never see our name",
              "Full WHM access to manage every client account",
              "Priority local phone & email support"]
    backup = "6-hourly, 7-day offsite backup, plus 31-day secondary offsite backup"
    cards = con("Cards", [
        plan("Small", "For agencies just getting started with client hosting.", "54.95",
             common + ["15 cPanel accounts", "25GB high-speed SSD storage", "200GB premium bandwidth", backup]),
        plan("Medium", "Our most popular reseller plan, room to grow your client base.", "89.95",
             common + ["30 cPanel accounts", "50GB high-speed SSD storage", "600GB premium bandwidth", backup],
             featured=True, tag="Most popular"),
        plan("Large", "For established agencies running a large client portfolio.", "134.95",
             common + ["50 cPanel accounts", "75GB high-speed SSD storage", "1000GB premium bandwidth", backup]),
    ], cls="pwh-plans", boxed=1180, direction="row", gap_px=28, align="flex-start", dir_t="column",
        gap_t=24, pad=box(0, 0, 96, 0), pad_t=box(0, 24, 80, 24), pad_m=box(0, 20, 64, 20), tag="section")

    reviews = con("TestimonialStrip", [
        heading("What customers say", "pwh-h3 pwh-h3-amber", tag="h2", align="center"),
        con("Cards", [
            review("Cameron and his team at Perth Web Hosting really take it above and beyond in terms of customer service and experience. "
                   "I would definitely recommend this company to the wider community of Perth.",
                   "Kathy Krcmar", "Local Guide, Google review"),
            review("With scaleability they are world class, and I wouldn't hesitate in recommending that you trust your hosting to Perth Web Hosting.",
                   "Kim Epton", "Local Guide, Google review"),
            review("Highly recommend if you are looking for a great company that gives such great support and hosting.",
                   "Nichola Davenport", "Google review, 5 stars"),
        ], direction="row", gap_px=24, align="stretch", dir_t="column"),
    ], boxed=1180, gap_px=24, pad=box(0, 0, 72, 0), pad_t=box(0, 24, 64, 24), pad_m=box(0, 20, 56, 20), tag="section")

    trust = con("TrustStrip", [
        text("<ul class=\"pwh-trust-list\"><li>No lock-in contracts</li>"
             "<li>Perth-based support, every plan</li><li>30-day money-back guarantee on yearly plans</li></ul>", ""),
    ], cls="pwh-trust", boxed=1180, pad=box(28, 0), pad_t=box(28, 24), pad_m=box(24, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})

    return template("PWH – Reseller Plans", "page", [hero, audience, included, support, toggle, cards, reviews, trust],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- Email (IMAP / POP3) -----------------------------------------------------
# Built from the Figma REST API (Page / Email — IMAP POP3, 160:2838) as a
# standalone template. Shares the Microsoft 365 page's CSS (pwh-m-*).

EMAIL_CSS = M365_CSS + """
.pwh-e-list .elementor-icon-list-item:not(:last-child){padding-bottom:12px!important}
.pwh-e-list .elementor-icon-list-text{font-size:15px!important;line-height:18px!important}
.pwh-e-price-card{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:12px;background:var(--pwh-cream,#fffef4)}
.pwh-e-price-card .pwh-btn .elementor-button{width:100%;min-height:48px;padding:15px 30px;border-radius:16px;font-family:Inter,sans-serif;font-size:15px;font-weight:700;line-height:18px}
.pwh-e-title .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:18px;font-weight:700;line-height:22px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-e-label .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:15px;font-weight:700;line-height:18px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-e-body,.pwh-e-body p{margin:0;font-family:Inter,sans-serif;font-size:16px;font-weight:300;line-height:19px;color:var(--pwh-grey-dark,#575557)}
.pwh-e-note-band{border-top:1px solid var(--pwh-navy-pale,#c2d3e8);border-bottom:1px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-e-card{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:12px;background:var(--pwh-cream,#fffef4)}
.pwh-e-link .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:14px;font-weight:700;line-height:17px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-e-link .elementor-heading-title a{color:inherit;text-decoration:underline;text-underline-offset:3px}
.pwh-e-link .elementor-heading-title a:hover{text-decoration-thickness:2px}
@media (min-width:1025px){.pwh-e-split>.e-con:first-child,.pwh-e-split>.e-con-inner>.e-con:first-child{flex:1 1 0!important;min-width:0}.pwh-e-split>.e-con:last-child,.pwh-e-split>.e-con-inner>.e-con:last-child{flex:0 0 360px!important}}
"""

# Draft answers: written only from what the Figma page already says. Not in
# the design; review before publishing.
EMAIL_FAQ = [
    ("What's the difference between IMAP and POP3?",
     "<p>IMAP keeps your email on the server, so your inbox, folders and read messages stay in sync on every device. "
     "POP3 downloads email to one device and usually removes it from the server.</p>"
     "<p>For most teams IMAP is the better choice. Both are included.</p>"),
    ("Is 20 email accounts a hard limit?",
     "<p>The plan includes 20 email accounts on your domain. If your team needs more, give us a call on "
     "<a href=\"tel:+61863654522\">08 6365 4522</a> and we'll find the right setup.</p>"),
    ("Does my website hosting plan already include email?",
     "<p>Basic email runs on a hosting account (cPanel). If you host your website with us on a cPanel plan, your email sits alongside it.</p>"),
    ("Can you move my existing mailboxes across?",
     "<p>Yes. Send us a <a href=\"/support/hosting-transfer-request/\">Hosting Transfer Request</a> and our Perth team will plan the move with you.</p>"),
    ("Will it work with Outlook, Apple Mail and my phone?",
     "<p>Yes. IMAP and POP3 work with Outlook, Apple Mail and the mail apps on Android and Apple devices, and there's secure webmail too.</p>"),
]


def email_page():
    style = widget("html", {"html": "<style>" + " ".join(EMAIL_CSS.split()) + "</style>"}, "pwh-m-style")

    def capped(w, width):
        # Figma wraps these headings at a fixed width; keep the same line breaks.
        w["settings"].update({"_element_width": "initial", "_element_custom_width": px(width),
                              "_element_width_tablet": "inherit"})
        return w

    # Figma pads the hero 200px at the top because the nav overlaps it; the
    # sticky header sits above the page here, so 84px comes off.
    hero = con("Hero", [
        style,
        capped(heading("Basic email on your own domain.", "pwh-h1 pwh-text-cream", tag="h1"), 760),
        capped(text("<p>Simple mailboxes (IMAP and POP3) for businesses that just need email to work. One flat price for the whole team, "
                    "no per-mailbox fees, and the same SpamExperts filtering the bigger plans get.</p>",
                    "pwh-lead pwh-lead--tight pwh-text-mist"), 760),
    ], cls="pwh-m-hero", boxed=1180, gap_px=14, justify="center", pad=box(116, 0, 120, 0), pad_t=box(96, 24, 96, 24),
        pad_m=box(72, 20, 72, 20), min_h=440, min_h_t=0, tag="section",
        extra={"background_background": "classic", "background_color": "#0B1629"})

    features = ["20 email accounts on your domain", "20GB of fast storage (SSD), shared across the team",
                "SpamExperts spam and virus filtering", "40MB attachment size", "99.98% uptime",
                "Secure webmail, plus setup on Android and Apple devices", "21-day offsite backup"]
    included = con("Included", [
        con("Split", [
            con("List", [
                capped(heading("What's included", "pwh-h2 pwh-text-ink", tag="h2"), 244),
                widget("icon-list", {
                    "icon_list": [{"_id": _id("li"), "text": f, "selected_icon": {"value": "fas fa-check", "library": "fa-solid"}}
                                  for f in features],
                    "space_between": px(12), "icon_size": px(11), "icon_color": "#0B1629", "text_color": "#0B1629",
                }, "pwh-m-list pwh-e-list"),
            ], gap_px=14, width_t=pct(100)),
            con("Price", [
                heading("Basic email", "pwh-e-title", tag="h3"),
                heading('<span class="pwh-m-amt">$10.95</span><span class="pwh-m-per">/ month</span>', "pwh-m-price", tag="p"),
                text("<p>Or $90 a year. All prices exclude GST.</p>", "pwh-m-text"),
                # The order link isn't in the design; set it in Elementor.
                button("Order Now", url("/client-login/"), "pwh-m-btn-amber"),
            ], cls="pwh-e-price-card", gap_px=12, pad=box(32), pad_m=box(24), width=px(360), width_t=pct(100)),
        ], cls="pwh-e-split", direction="row", gap_px=48, align="flex-start", dir_t="column", gap_t=32),
    ], boxed=1180, pad=box(72, 0, 56, 0), pad_t=box(64, 24, 56, 24), pad_m=box(56, 20, 48, 20), tag="section")

    note = con("CPanelNote", [
        heading("One thing to know", "pwh-e-label", tag="h2"),
        text("<p>Basic email runs on a hosting account (cPanel). If you host your website with us on a cPanel plan, your email sits alongside it. "
             "If you only need email and no website, we'll set up a small hosting account to run it, just ask and we'll sort it.</p>",
             "pwh-e-body"),
    ], cls="pwh-e-note-band", boxed=1180, gap_px=24, pad=box(56, 0), pad_t=box(48, 24), pad_m=box(40, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})

    def which(title, body):
        return con(f"Card – {title}", [
            heading(title, "pwh-e-title", tag="h3"),
            text(f"<p>{body}</p>", "pwh-m-text"),
        ], cls="pwh-e-card", gap_px=8, pad=box(28), width_t=pct(100))

    compare = con("WhichIsRight", [
        capped(heading("Basic email or Microsoft 365?", "pwh-h2 pwh-text-ink", tag="h2"), 446),
        con("Cards", [
            which("Basic email is right if",
                  "You mostly send and receive email, you want one flat price for the team, and you don't need shared calendars "
                  "or the Office apps. It just works, on any device."),
            which("Microsoft 365 is right if",
                  "Your team shares calendars and contacts, you want bigger mailboxes, or you use Word, Excel and Teams. "
                  "Priced per mailbox, so you only pay for who needs it."),
        ], cls="pwh-m-row", direction="row", gap_px=24, align="stretch", dir_t="column"),
        heading("See Microsoft 365 →", "pwh-e-link", tag="p", link=url("/email/microsoft-365/")),
    ], boxed=1180, gap_px=24, pad=box(72, 0, 56, 0), pad_t=box(64, 24, 56, 24), pad_m=box(56, 20, 48, 20), tag="section")

    faq = con("FAQ", [
        capped(heading("Basic email questions.", "pwh-h2 pwh-text-ink", tag="h2"), 338),
        con("Questions", [
            widget("toggle", {
                "tabs": [{"_id": _id("faq"), "tab_title": q, "tab_content": a} for q, a in EMAIL_FAQ],
                "selected_icon": {"value": "fas fa-plus", "library": "fa-solid"},
                "selected_active_icon": {"value": "fas fa-minus", "library": "fa-solid"},
                "icon_align": "right",
                "title_html_tag": "h3",
                "faq_schema": "yes",
            }, "pwh-m-faq"),
        ], width=px(760), width_t=pct(100)),
    ], boxed=1180, gap_px=24, pad=box(72, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section")

    return template("PWH – Email", "page", [hero, included, note, compare, faq],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- Web Hosting (overview) -------------------------------------------------
# Built from the Figma REST API (Page / Hosting, 15:133, read from the file
# copy UyIKr0mEfBlQKS0wEU0ibY) as a standalone template.

HOSTING_HERO = MEDIA + "1a31b8031e0f1b430d5aca73df5d118da1cc78a2.jpg"  # same photo as Home, already uploaded
HOSTING_WHY = MEDIA + "hosting-why.jpg"  # Not in the Media Library yet; upload with this name.

HOSTING_CSS = """
.pwh-h-style{display:none!important}
.pwh-h-persona{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:16px;background:var(--pwh-cream,#fffef4)}
.pwh-h-persona--featured{border:2px solid var(--pwh-navy-ink,#0b1629);box-shadow:0 20px 40px rgba(11,22,41,.18)}
.pwh-h-tag .elementor-heading-title{display:inline-block;margin:0;padding:5px 10px;border-radius:3px;background:var(--pwh-sand,#e8e0c8);color:var(--pwh-amber-deep,#9e6e25);font-family:Inter,sans-serif;font-size:11px;font-weight:700;line-height:13px}
.pwh-h-title .elementor-heading-title{margin:0;font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:22px;font-weight:900;line-height:26px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-h-quote{border-radius:6px;background:var(--pwh-navy-mist,#eaf0f8)}
.pwh-h-quote-text .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:15px;font-weight:700;line-height:18px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-h-from .elementor-heading-title{margin:0;font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:12px;font-weight:700;line-height:16px;letter-spacing:1.8px;text-transform:uppercase;color:var(--pwh-grey-dark,#575557)}
.pwh-h-price .elementor-heading-title{display:flex;flex-wrap:wrap;align-items:flex-end;gap:6px;margin:0}
.pwh-h-amt{font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:40px;font-weight:900;line-height:46px;letter-spacing:-.9px;color:var(--pwh-amber-deep,#9e6e25)}
.pwh-h-per{padding-bottom:4px;font-family:Inter,sans-serif;font-size:15px;font-weight:700;line-height:18px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-h-persona .pwh-h-text{min-height:90px}
.pwh-h-text,.pwh-h-text p{margin:0;font-family:Inter,sans-serif;font-size:13px;line-height:18px;color:var(--pwh-grey-dark,#575557)}
.pwh-h-link .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:14px;font-weight:700;line-height:17px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-h-link .elementor-heading-title a{color:inherit;text-decoration:none;text-underline-offset:3px}
.pwh-h-link .elementor-heading-title a:hover{text-decoration:underline}
.pwh-h-link .elementor-heading-title a{display:flex;align-items:center;justify-content:space-between;gap:12px}
.pwh-h-link .elementor-heading-title a::after{content:"";flex:0 0 28px;height:18px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 28 18' fill='none' stroke='%230b1629' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M1.5 9h24M18 1.5 25.5 9 18 16.5'/%3E%3C/svg%3E") no-repeat center/contain}
.pwh-h-note,.pwh-h-note p{margin:0;font-family:Inter,sans-serif;font-size:14px;font-weight:300;line-height:17px;color:var(--pwh-grey-dark,#575557)}
.pwh-h-note a{color:var(--pwh-navy-ink,#0b1629);font-weight:700;text-decoration:underline;text-underline-offset:3px}
.pwh-h-tile{border:1px solid #d6cdb0;border-radius:16px;background:var(--pwh-cream-warm,#f5f1e0)}
.pwh-h-tile-icon{width:34px!important;max-width:34px}
.pwh-h-tile-icon .elementor-icon-wrapper{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border:1.5px dashed var(--pwh-amber-deep,#9e6e25);border-radius:6px}
.pwh-h-tile-icon .elementor-icon{font-size:15px;color:var(--pwh-amber,#c89439)}
.pwh-h-tile-icon .elementor-icon svg{width:15px;height:15px;fill:var(--pwh-amber,#c89439)}
.pwh-h-tile-text,.pwh-h-tile-text p{margin:0;font-family:Inter,sans-serif;font-size:14px;font-weight:300;line-height:17px;color:var(--pwh-grey-dark,#575557)}
.pwh-h-why-title .elementor-heading-title,.pwh-h-switch-title .elementor-heading-title{margin:0;font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:28px;font-weight:900;line-height:34px;color:var(--pwh-cream,#fffef4)}
.pwh-h-switch-text,.pwh-h-switch-text p{margin:0;font-family:Inter,sans-serif;font-size:18px;font-weight:300;line-height:22px;color:var(--pwh-navy-mist,#eaf0f8)}
.pwh-h-hero .pwh-lead,.pwh-h-hero .pwh-lead p{line-height:22px}
.pwh-h-faq-open .elementor-toggle-item:first-child .elementor-tab-content{display:block}
.pwh-h-row2>.e-con,.pwh-h-row2>.e-con-inner>.e-con{flex:0 0 calc(50% - 16px)!important;max-width:calc(50% - 16px);min-width:0}
.pwh-h-row4>.e-con,.pwh-h-row4>.e-con-inner>.e-con{flex:1 1 0!important;min-width:0}
.pwh-h-hero .elementor-widget{max-width:100%}
@media (max-width:1024px){.pwh-h-row2,.pwh-h-row2>.e-con-inner{flex-direction:column!important}.pwh-h-row2>.e-con,.pwh-h-row2>.e-con-inner>.e-con{flex:0 0 auto!important;width:100%;max-width:100%}.pwh-h-row4{flex-wrap:wrap!important}.pwh-h-row4>.e-con,.pwh-h-row4>.e-con-inner>.e-con{flex:0 0 calc(50% - 12px)!important;max-width:calc(50% - 12px)}}
@media (max-width:767px){.pwh-h-row4>.e-con,.pwh-h-row4>.e-con-inner>.e-con{flex-basis:100%!important;max-width:100%}.pwh-h-amt{font-size:34px;line-height:40px}}
"""

# The first answer is Figma's. Figma only has the questions for the rest, so
# those answers are drafts built from facts on the other plan pages; review
# before publishing.
HOSTING_FAQ = [
    ("What's the difference between cPanel, semi-managed and reseller hosting?",
     "<p>cPanel gives you full control and you manage everything yourself. Semi-managed means we handle the setup, updates and "
     "troubleshooting so you don’t have to. Reseller hosting is for anyone managing sites for clients, with your own branding and full account control.</p>"),
    ("Can you migrate my existing website across?",
     "<p>Yes, for free. We migrate your files, databases and email, and most sites move across with no downtime.</p>"),
    ("How much storage do I get?",
     "<p>It depends on the plan: 5GB to 30GB of high-speed SSD storage on cPanel and semi-managed WordPress plans, "
     "and 25GB to 75GB on reseller plans. You can switch plans any time as you grow.</p>"),
    ("Is a domain included with hosting?",
     "<p>Domains are registered separately. <a href=\"/domains/\">Search for your domain</a>, and we'll connect it to your hosting for you.</p>"),
    ("What happens if my site goes down?",
     "<p>Our servers are monitored around the clock from right here in Perth, so we're usually already on it. "
     "If you need us, call a real Perth number, <a href=\"tel:+61863654522\">08 6365 4522</a>, and talk to someone who can fix it.</p>"),
]


def hosting_persona(title, quote, price, body, link_text, link, featured=False):
    items = [heading("MOST POPULAR", "pwh-h-tag", tag="p")] if featured else []
    items += [
        heading(title, "pwh-h-title", tag="h3"),
        con("Quote", [heading(quote, "pwh-h-quote-text", tag="p")], cls="pwh-h-quote", pad=box(14)),
        con("Price", [
            heading("From", "pwh-h-from", tag="p"),
            heading(f'<span class="pwh-h-amt">${price}</span><span class="pwh-h-per">/month</span>', "pwh-h-price", tag="p"),
        ], gap_px=2),
        text(f"<p>{body}</p>", "pwh-h-text"),
        heading(link_text, "pwh-h-link", tag="p", link=link),
    ]
    return con(f"Persona – {title}", items,
               cls="pwh-h-persona" + (" pwh-h-persona--featured" if featured else ""),
               gap_px=14, pad=box(24), width_t=pct(100))


def hosting_tile(icon, title, body):
    return con(f"Tile – {title}", [
        widget("icon", {"selected_icon": {"value": icon, "library": "fa-solid"}, "align": "left",
                        "primary_color": "#C89439", "size": px(15)}, "pwh-h-tile-icon"),
        heading(title, "pwh-eyebrow pwh-text-ink", tag="h3"),
        text(f"<p>{body}</p>", "pwh-h-tile-text"),
    ], cls="pwh-h-tile", gap_px=10, pad=box(20), width_t=pct(100))


def hosting():
    style = widget("html", {"html": "<style>" + " ".join(HOSTING_CSS.split()) + "</style>"}, "pwh-h-style")

    # Figma pads the hero 220px at the top because the nav overlaps it; the
    # sticky header sits above the page here, so 84px comes off.
    hero = con("Hero", [
        con("Copy", [
            style,
            heading("Fast, reliable hosting. Real Perth support.", "pwh-h1 pwh-text-cream", tag="h1"),
            text("<p>Website hosting (cPanel), WordPress hosting we look after for you, and reseller hosting for agencies. "
                 "All on Perth servers our team monitors around the clock.</p>", "pwh-lead pwh-text-cream"),
            button("See hosting plans →", url("#plans"), "pwh-btn--amber"),
        ], gap_px=16, width=px(558), width_t=pct(100), extra={"flex_align_items": "flex-start"}),
        # Figma has an empty "Visual placeholder" here; the photo shows through.
        con("Visual", [], width=px(558), width_t=pct(100), min_h=380, min_h_t=0,
            extra={"hide_tablet": "hidden-tablet", "hide_mobile": "hidden-mobile"}),
    ], cls="pwh-h-hero", direction="row", boxed=1180, gap_px=64, align="center", dir_t="column",
        pad=box(136, 0, 140, 0), pad_t=box(96, 24, 96, 24), pad_m=box(72, 20, 72, 20), tag="section",
        extra=photo_bg(HOSTING_HERO, 0.6))

    plans = con("Plans", [
        heading("Which hosting is right for you?", "pwh-h2 pwh-text-ink", tag="h2"),
        con("Cards", [
            hosting_persona("cPanel Hosting",
                            "You manage your own website and just need somewhere solid to host it.", "7.95",
                            "Full control over your site via the industry-standard cPanel dashboard. Ideal for a single, self-managed website.",
                            "See cPanel plans", url("/web-hosting/cpanel/")),
            hosting_persona("Semi-Managed WordPress Hosting",
                            "You've got a website, but you'd rather leave the technical side to us.", "24.95",
                            "We handle setup, updates and troubleshooting, so you can focus on the business instead of the server. "
                            "Perfect for your WordPress website.",
                            "See semi-managed plans", url("/web-hosting/wordpress/"), featured=True),
        ], cls="pwh-h-row2", direction="row", gap_px=32, align="flex-start", dir_t="column", gap_t=24),
        text('<p>Looking for <a href="/reseller-hosting/">reseller hosting</a>, or need a private server (VPS)? '
             'Dedicated and VPS hosting is coming soon. <a href="/vps-hosting/">Join the waitlist.</a></p>', "pwh-h-note"),
    ], boxed=1180, gap_px=40, pad=box(140, 0), pad_t=box(96, 24), pad_m=box(72, 20), tag="section",
        extra={"_element_id": "plans"})

    includes = con("Includes", [
        heading("What's included, no matter which plan.", "pwh-h3 pwh-text-ink", tag="h2"),
        con("Tiles", [
            # Figma's tiles have an "icon" placeholder; these icons stand in.
            hosting_tile("fas fa-lock", "Free SSL", "Every site is secured with HTTPS from day one, at no extra cost."),
            hosting_tile("fas fa-cloud-upload-alt", "Daily backups", "Automatic daily backups, so a bad update is never a disaster."),
            hosting_tile("fas fa-signal", "99.9% uptime", "Monitored around the clock from right here in Perth."),
            hosting_tile("fas fa-truck-moving", "Free migration", "We move your site, email and domain across at no charge."),
        ], cls="pwh-h-row4", direction="row", gap_px=24, align="stretch"),
    ], boxed=1180, gap_px=40, pad=box(80, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})

    why = con("Why PWH", [
        con("Copy", [
            heading("Local infrastructure.<br>Local accountability.", "pwh-h-why-title", tag="h2"),
            text("<p>Your site runs on servers we monitor ourselves, not a support ticket routed through three time zones. "
                 "If something goes wrong, you call a real Perth number and talk to someone who can fix it.</p>",
                 "pwh-body pwh-text-cream"),
        ], gap_px=12, width=px(497), width_t=pct(100)),
    ], boxed=1180, pad=box(140, 0), pad_t=box(96, 24), pad_m=box(72, 20), tag="section",
        extra=photo_bg(HOSTING_WHY, 0.5))

    testimonials = con("Testimonials", [
        con("Intro", [
            heading("WA businesses who've<br>made the switch", "pwh-h2 pwh-text-cream", tag="h2"),
            text("<p>Here's what business owners say after switching.</p>", "pwh-body pwh-text-cream"),
        ], gap_px=8, width=px(744), width_t=pct(100)),
        con("Cards", [
            review("20 plus years dealing with hosting companies, and recently moved to PWH. The quality of the hosting and service is the best I have experienced.",
                   "Craig Clemmence", "Google review, 5 stars"),
            review("So far THE BEST client support I have ever seen. Cameron was very patient with me and went out of his way to answer all of my questions. "
                   "The web hosting transfer was actioned smoothly with no downtime.",
                   "Kathy Krcmar", "Local Guide, Google review"),
            review("Absolutely top notch service, brilliant support. There is no problems, only solutions.",
                   "Cameron P", "Google review, 5 stars"),
        ], direction="row", gap_px=32, align="stretch", dir_t="column", gap_t=24),
    ], boxed=1180, gap_px=40, pad=SECTION_PAD, pad_t=SECTION_PAD_T, pad_m=SECTION_PAD_M, tag="section",
        extra={"background_background": "classic", "background_color": "#0B1729"})

    faq = con("FAQ", [
        heading("Hosting questions, answered.", "pwh-h3 pwh-text-ink", tag="h2"),
        con("Questions", [
            widget("toggle", {
                "tabs": [{"_id": _id("faq"), "tab_title": q, "tab_content": a} for q, a in HOSTING_FAQ],
                "selected_icon": {"value": "fas fa-plus", "library": "fa-solid"},
                "selected_active_icon": {"value": "fas fa-minus", "library": "fa-solid"},
                "icon_align": "right",
                "title_html_tag": "h3",
                "faq_schema": "yes",
            }, "pwh-faq"),
        ], width=px(760), width_t=pct(100)),
    ], boxed=1180, gap_px=32, pad=box(80, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section")

    switching = con("Switching", [
        heading("Switching is easier than you think.", "pwh-h-switch-title", tag="h2"),
        text("<p>We migrate your files, databases and email for free. Most sites move across with no downtime.</p>", "pwh-h-switch-text"),
        button("Start my free migration →", url("/support/hosting-transfer-request/"), "pwh-btn--amber"),
    ], boxed=1180, gap_px=12, pad=box(64, 0), pad_t=box(56, 24), pad_m=box(48, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#1A325B", "flex_align_items": "flex-start"})

    return template("PWH – Web Hosting", "page",
                    [hero, plans, includes, why, testimonials, faq, switching],
                    {"hide_title": "yes", "template": "elementor_header_footer"})

# --- Email (overview) ----------------------------------------------------------
# Built from the Figma REST API (Page / Email, 16:324, file copy
# UyIKr0mEfBlQKS0wEU0ibY) as a standalone template. Shares the Web Hosting
# page's card styles (pwh-h-*).

EMAILS_HERO = MEDIA + "email-hero.jpg"  # Not in the Media Library yet; upload with this name.

EMAILS_CSS = HOSTING_CSS.replace(".pwh-h-style{display:none!important}", ".pwh-eo-style{display:none!important}") + """
.pwh-eo-card{border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:8px}
.pwh-eo-num{width:38px!important;max-width:38px}
.pwh-eo-num .elementor-heading-title{display:flex;align-items:center;justify-content:center;width:38px;height:38px;margin:0;border-radius:999px;background:var(--pwh-navy-ink,#0b1629);color:var(--pwh-cream,#fffef4);font-family:Inter,sans-serif;font-size:16px;font-weight:900;line-height:19px}
.pwh-eo-title .elementor-heading-title{margin:0;font-family:Inter,sans-serif;font-size:19px;font-weight:700;line-height:23px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-eo-text,.pwh-eo-text p{margin:0;font-family:Inter,sans-serif;font-size:15px;font-weight:300;line-height:18px;color:var(--pwh-grey-dark,#575557)}
.pwh-eo-plans .pwh-h-text,.pwh-eo-plans .pwh-h-text p{color:var(--pwh-navy-ink,#0b1629)}
.pwh-eo-spam{border-top:1px solid var(--pwh-navy-pale,#c2d3e8);border-bottom:1px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-h-switch-text a{color:var(--pwh-cream,#fffef4);text-decoration:underline;text-underline-offset:3px}
.pwh-eo-spam-text,.pwh-eo-spam-text p{margin:0;font-family:Inter,sans-serif;font-size:14px;line-height:17px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-eo-row3>.e-con,.pwh-eo-row3>.e-con-inner>.e-con{flex:1 1 0!important;min-width:0}
@media (max-width:1024px){.pwh-eo-row3,.pwh-eo-row3>.e-con-inner{flex-direction:column!important}.pwh-eo-row3>.e-con,.pwh-eo-row3>.e-con-inner>.e-con{flex:0 0 auto!important;width:100%}}
@media (max-width:767px){.pwh-eo-spam,.pwh-eo-spam>.e-con-inner{flex-direction:column!important;text-align:center}}
"""

# Figma only has the questions; these answers are drafts built from facts on
# the email pages. Review before publishing.
EMAILS_FAQ = [
    ("What's the difference between Exchange and POP3/IMAP?",
     "<p>Basic email (POP3/IMAP) gives you 20 email accounts and 20GB of shared storage on your own domain, for one flat price. "
     "Microsoft 365 runs on Exchange: full business mailboxes with 50GB each, shared calendars and contacts, Teams and the Office apps, priced per mailbox.</p>"),
    ("Can I add mailboxes for new staff later?",
     "<p>Yes. Basic email includes 20 accounts, so you can add new staff any time. Microsoft 365 is priced per mailbox, so you add only what you need.</p>"),
    ("Do you filter spam and viruses?",
     "<p>Yes. Premium SpamExperts spam and virus filtering is included on every email plan, at no extra cost.</p>"),
    ("Will it work on my phone?",
     "<p>Yes. There's secure webmail, and we can set your email up on Android and Apple devices.</p>"),
    ("Do I need a domain first?",
     "<p>Your email runs on your own domain, like name@yourbusiness.com.au. If you don't have one yet, "
     "<a href=\"/domains/\">search for your domain</a> and we'll connect it to your email for you.</p>"),
    ("Can I get Google email hosting?",
     "<p>Talk to us. Call <a href=\"tel:+61863654522\">08 6365 4522</a> and our Perth team will help you work out the right setup.</p>"),
]


def emails_reason(n, title, body):
    return con(f"Reason – {title}", [
        heading(str(n), "pwh-eo-num", tag="p"),
        heading(title, "pwh-eo-title", tag="h3"),
        text(f"<p>{body}</p>", "pwh-eo-text"),
    ], cls="pwh-eo-card", gap_px=10, pad=box(24), width_t=pct(100))


def emails_plan(title, price, per, body, link_text, link, featured=False):
    items = [heading("MOST POPULAR", "pwh-h-tag", tag="p")] if featured else []
    items += [
        heading(title, "pwh-h-title", tag="h3"),
        con("Price", [
            heading("From", "pwh-h-from", tag="p"),
            heading(f'<span class="pwh-h-amt">{price}</span><span class="pwh-h-per">{per}</span>', "pwh-h-price", tag="p"),
        ], gap_px=2),
        text(f"<p>{body}</p>", "pwh-h-text"),
        heading(f"{link_text} →", "pwh-h-link", tag="p", link=link),
    ]
    return con(f"Plan – {title}", items, cls="pwh-h-persona" + (" pwh-h-persona--featured" if featured else ""),
               gap_px=14, pad=box(24), width_t=pct(100))


def emails():
    style = widget("html", {"html": "<style>" + " ".join(EMAILS_CSS.split()) + "</style>"}, "pwh-eo-style")

    # Figma pads the hero 220px at the top because the nav overlaps it; the
    # sticky header sits above the page here, so 84px comes off.
    hero = con("Hero", [
        con("Copy", [
            style,
            heading("Email that carries your business name. Never look unprofessional again.", "pwh-h2 pwh-text-cream", tag="h1"),
            text("<p>Basic mailboxes give you 20 email accounts and 20GB of storage on your own domain. "
                 "Or step up to Microsoft 365 for 50GB per mailbox, calendars and Teams.</p>", "pwh-body pwh-text-cream"),
            button("Get Online →", url("#plans"), "pwh-btn--amber"),
        ], gap_px=16, width=px(694), width_t=pct(100), extra={"flex_align_items": "flex-start"}),
        # Figma has an empty "Visual placeholder" here; the photo shows through.
        con("Visual", [], width=px(422), width_t=pct(100), min_h=380, min_h_t=0,
            extra={"hide_tablet": "hidden-tablet", "hide_mobile": "hidden-mobile"}),
    ], cls="pwh-h-hero", direction="row", boxed=1180, gap_px=64, align="center", dir_t="column",
        pad=box(136, 0, 140, 0), pad_t=box(96, 24, 96, 24), pad_m=box(72, 20, 72, 20), tag="section",
        extra=photo_bg(EMAILS_HERO, 0.5))
    hero["elements"][0]["elements"][1]["settings"].update({"_element_width": "initial", "_element_custom_width": px(675),
                                                          "_element_width_tablet": "inherit"})

    why = con("WhyDomain", [
        heading("Why your own domain, not a free inbox.", "pwh-h3 pwh-text-ink", tag="h2"),
        con("Cards", [
            emails_reason(1, "Look like you mean business",
                          "A name@yourbusiness.com.au address builds instant trust with customers and suppliers."),
            emails_reason(2, "Never lose an address",
                          "When staff come and go, the mailbox stays with the business, not the person."),
            emails_reason(3, "Everything in sync",
                          "Calendar, contacts and mail stay in sync across your whole team, on any device."),
        ], cls="pwh-eo-row3", direction="row", gap_px=32, align="stretch", dir_t="column", gap_t=24),
    ], boxed=1180, gap_px=40, pad=box(80, 0, 40, 0), pad_t=box(64, 24, 40, 24), pad_m=box(56, 20, 32, 20), tag="section")

    plans = con("FeatureCards", [
        con("Cards", [
            emails_plan("Basic email (POP3 / IMAP)", "$10.95", "/month",
                        "20 email accounts and 20GB of shared storage, all on your own business domain. One flat price, no per-mailbox fees.",
                        "See email plans", url("/e-mail/imap-pop3/")),
            emails_plan("Microsoft 365", "$7.50", "/ mailbox / mo",
                        "Full Exchange mailboxes with 50GB each, shared calendars, Teams and Office apps. Priced per mailbox, add only what you need.",
                        "See Microsoft 365", url("/e-mail/microsoft-365/"), featured=True),
            # Placeholder card in the design: price and copy still to come.
            emails_plan("Gmail", "$XX", "/ mailbox / mo", "Information about Gmail", "See Google", url("/contact-us/")),
        ], cls="pwh-eo-row3 pwh-eo-plans", direction="row", gap_px=32, align="flex-start", dir_t="column", gap_t=24),
    ], boxed=1180, gap_px=40, pad=box(140, 0), pad_t=box(96, 24), pad_m=box(72, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0", "_element_id": "plans"})

    spam = con("SpamExpertsStrip", [
        image(MEDIA + "spamexperts.png", "", alt="SpamExperts", align="center", width=px(143)),
        text("<p>Premium SpamExperts spam and virus filtering is included on every email plan, at no extra cost.</p>", "pwh-eo-spam-text"),
    ], cls="pwh-eo-spam", direction="row", boxed=1180, gap_px=20, justify="center", align="center",
        pad=box(28, 0), pad_t=box(28, 24), pad_m=box(24, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#F5F1E0"})
    spam["elements"][0]["settings"].update({"_element_width": "initial", "_element_custom_width": px(154)})

    faq = con("FAQ", [
        heading("Email questions, answered.", "pwh-h3 pwh-text-ink", tag="h2"),
        con("Questions", [
            widget("toggle", {
                "tabs": [{"_id": _id("faq"), "tab_title": q, "tab_content": a} for q, a in EMAILS_FAQ],
                "selected_icon": {"value": "fas fa-plus", "library": "fa-solid"},
                "selected_active_icon": {"value": "fas fa-minus", "library": "fa-solid"},
                "icon_align": "right",
                "title_html_tag": "h3",
                "faq_schema": "yes",
            }, "pwh-faq"),
        ], width=px(760), width_t=pct(100)),
    ], boxed=1180, gap_px=40, pad=box(80, 0), pad_t=box(64, 24), pad_m=box(56, 20), tag="section")

    switching = con("Switching", [
        heading("Already have email somewhere else?", "pwh-h-switch-title", tag="h2"),
        text("<p>We'll migrate your existing mailboxes, contacts and calendar across with no lost messages and minimal downtime. "
             '<a href="/contact-us/">Talk to us about it.</a><br>Your local hosting partner.</p>', "pwh-h-switch-text"),
    ], boxed=1180, gap_px=12, pad=box(64, 0), pad_t=box(56, 24), pad_m=box(48, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#1A325B"})

    return template("PWH – Email", "page", [hero, why, plans, spam, faq, switching],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


# --- VPS application form ------------------------------------------------------
# Figma: Page / VPS (gated) 161:2991, "Application" band. A section template that
# replaces the Apply section on the live /vps-hosting/ page (the rest of that page
# is already built), with the live page's wording. The form is Gravity Forms
# (see gf_vps_form()).
VPS_CSS = """
.pwh-v-apply{border-top:1px solid var(--pwh-navy-pale,#c2d3e8);border-bottom:1px solid var(--pwh-navy-pale,#c2d3e8)}
.pwh-v-formcard .pwh-form .gform_wrapper .gform_fields{grid-row-gap:18px}
.pwh-v-formcard .pwh-form .gform_wrapper.gravity-theme .gform_footer{margin-top:18px}
.pwh-v-note,.pwh-v-note p{margin:0;font-family:Inter,sans-serif;font-size:13px;line-height:16px;color:var(--pwh-grey,#828082)}
"""

# Change id="5" to the form's ID if Gravity Forms gives it a different one on import.
GF_VPS_SHORTCODE = '[gravityform id="5" title="false" description="false" ajax="true" theme="gravity-theme"]'


def vps_apply():
    style = widget("html", {"html": "<style>" + " ".join((CONTACT_CSS + VPS_CSS).split()) + "</style>"}, "pwh-v-style")
    card = con("FormCard", [
        style,
        heading("Apply for a private server (VPS).", "pwh-h3 pwh-text-ink", tag="h2"),
        text("<p>Tell us what you need and we’ll come back with a spec and a price. "
             "Have your business name and ABN handy.</p>", "pwh-c-text"),
        widget("shortcode", {"shortcode": GF_VPS_SHORTCODE}, "pwh-form"),
        text("<p>We reply to most enquiries the same business day.</p>", "pwh-v-note"),
    ], cls="pwh-c-formcard pwh-v-formcard", gap_px=18, pad=box(40), pad_m=box(24), width=px(560), width_m=pct(100))
    card["elements"][1]["settings"].update({"_element_width": "initial", "_element_custom_width": px(360),
                                            "_element_width_mobile": "inherit"})
    card["elements"][2]["settings"]["text_color"] = "#575557"

    apply = con("Apply", [card], cls="pwh-v-apply", boxed=1180, align="center",
                pad=box(72, 0), pad_t=box(64, 24), pad_m=box(48, 20), tag="section",
                extra={"background_background": "classic", "background_color": "#F5F1E0", "_element_id": "apply"})
    return template("PWH – VPS Application Form", "section", [apply])


# --- Legal pages ---------------------------------------------------------------
# Old-site legal copy (content/*.html, copied verbatim) in the new design: a
# navy title band, then the text in a 760px reading column. CSS travels inside
# the JSON.

LEGAL_CSS = """
.pwh-l-style{display:none!important}
.pwh-l-body{max-width:760px}
.pwh-l-body,.pwh-l-body p,.pwh-l-body li{font-family:Inter,sans-serif;font-size:16px;font-weight:400;line-height:24px;color:var(--pwh-grey-dark,#575557)}
.pwh-l-body p{margin:0 0 16px}
.pwh-l-body h2,.pwh-l-body h3{margin:40px 0 12px;font-family:var(--pwh-font-display,"Archivo",sans-serif);font-stretch:125%;font-size:22px;font-weight:900;line-height:28px;color:var(--pwh-navy-ink,#0b1629)}
.pwh-l-body ul,.pwh-l-body ol{margin:0 0 16px;padding-left:22px}
.pwh-l-body li{margin:0 0 6px;padding-left:4px}
.pwh-l-body li::marker{color:var(--pwh-amber,#c89439)}
.pwh-l-body a{color:var(--pwh-navy-ink,#0b1629);font-weight:700;text-decoration:underline;text-underline-offset:3px;overflow-wrap:anywhere;word-break:break-word}
.pwh-l-body a:hover{text-decoration-thickness:2px}
.pwh-l-body strong{color:var(--pwh-navy-ink,#0b1629)}
.pwh-l-body>.elementor-widget-container>:first-child,.pwh-l-body>:first-child{margin-top:0}
.pwh-l-body .pwh-l-clause{position:relative;padding-left:52px}
.pwh-l-body .pwh-l-num{position:absolute;left:0;top:0;font-weight:700;color:var(--pwh-navy-ink,#0b1629)}
.pwh-l-body .pwh-l-items{margin:-4px 0 16px 52px;padding-left:24px;list-style-type:lower-alpha}
.pwh-l-body .pwh-l-items li::marker{color:var(--pwh-navy-ink,#0b1629);font-weight:700}
.pwh-l-table-wrap{margin:12px 0 4px;overflow-x:auto;border:1px solid var(--pwh-navy-pale,#c2d3e8);border-radius:12px}
.pwh-l-table{width:100%;min-width:480px;margin:0;border-collapse:collapse;font-family:Inter,sans-serif;font-size:15px;line-height:20px}
.pwh-l-table th{padding:12px 16px;background:var(--pwh-navy-ink,#0b1629);color:var(--pwh-cream,#fffef4);font-weight:700;text-align:left}
.pwh-l-table td{padding:12px 16px;border:0;border-top:1px solid var(--pwh-navy-pale,#c2d3e8);color:var(--pwh-grey-dark,#575557);background:var(--pwh-cream,#fffef4)}
.pwh-l-table tbody tr:nth-child(even) td{background:var(--pwh-cream-warm,#f5f1e0)}
.pwh-l-table th:last-child,.pwh-l-table td:last-child{text-align:right;white-space:nowrap}
.pwh-l-table td:first-child{color:var(--pwh-navy-ink,#0b1629);font-weight:700;white-space:nowrap}
.pwh-l-updated,.pwh-l-updated p{margin:0;font-family:Inter,sans-serif;font-size:15px;line-height:20px;color:var(--pwh-navy-pale,#c2d3e8)}
@media (max-width:767px){.pwh-l-items .pwh-l-table-wrap{margin-left:-60px}.pwh-l-table{min-width:0;font-size:14px;line-height:18px}.pwh-l-table th,.pwh-l-table td{padding:10px}.pwh-l-table th:last-child{white-space:normal}.pwh-l-body h2,.pwh-l-body h3{margin-top:32px;font-size:20px;line-height:26px}.pwh-l-body .pwh-l-clause{padding-left:40px}.pwh-l-body .pwh-l-items{margin-left:40px;padding-left:20px}}
"""


def legal_page(title, content_file, updated=None):
    with open(os.path.join(os.path.dirname(__file__), "..", "content", content_file), encoding="utf-8") as fh:
        body_html = fh.read().strip()
    style = widget("html", {"html": "<style>" + " ".join(LEGAL_CSS.split()) + "</style>"}, "pwh-l-style")
    hero = con("Header", [
        style,
        heading(title, "pwh-h1 pwh-text-cream", tag="h1"),
    ] + ([text(f"<p>Document updated: {updated}</p>", "pwh-l-updated")] if updated else []),
        cls="pwh-page-hero", boxed=1180, gap_px=12, pad=box(96, 0, 80, 0), pad_t=box(80, 24, 64, 24),
        pad_m=box(56, 20, 48, 20), tag="section",
        extra={"background_background": "classic", "background_color": "#0B1629"})
    body = con("Policy", [
        text(body_html, "pwh-l-body"),
    ], boxed=1180, pad=box(72, 0, 96, 0), pad_t=box(56, 24, 80, 24), pad_m=box(48, 20, 64, 20), tag="section")
    return template(f"PWH – {title}", "page", [hero, body],
                    {"hide_title": "yes", "template": "elementor_header_footer"})


def strip_page_styles(elements):
    """Drop the hidden <style> widgets: their CSS ships in the theme (pwh-pages.css)."""
    keep = []
    for el in elements:
        cls = el.get("settings", {}).get("_css_classes", "")
        if el.get("widgetType") == "html" and re.fullmatch(r"pwh-[a-z]+-style", cls):
            continue
        el["elements"] = strip_page_styles(el.get("elements", []))
        keep.append(el)
    return keep


def page_css():
    """All standalone-page and snippet CSS, for assets/css/pwh-pages.css."""
    snippets = os.path.join(os.path.dirname(__file__), "..", "snippets")
    parts = [
        ("Contact", CONTACT_CSS),
        ("Microsoft 365", M365_CSS),
        ("Email (IMAP / POP3)", EMAIL_CSS[len(M365_CSS):]),
        ("Reseller Plans", RESELLER_CSS),
        ("Web Hosting", HOSTING_CSS),
        ("Email overview", EMAILS_CSS[len(HOSTING_CSS):]),
        ("Legal pages", LEGAL_CSS),
        ("VPS application", VPS_CSS),
    ]
    with open(os.path.join(snippets, "home-products-slider.css"), encoding="utf-8") as fh:
        parts.append(("Home products slider (phones)", fh.read()))
    # Home reviews carousel (mobile Listing Grid widget 35e1d3f): dots like the Products slider.
    with open(os.path.join(snippets, "reviews-slider-dots.css"), encoding="utf-8") as fh:
        dots = re.sub(r"/\*.*?\*/\s*", "", fh.read(), count=1, flags=re.S)
    parts.append(("Home reviews carousel dots", dots.replace("selector ", ".elementor-element-35e1d3f ")))
    for name, label in (("mobile-menu", "Mobile menu (snippets/mobile-menu.html)"),
                        ("footer-mobile-links", "Phone footer (snippets/footer-mobile-links.html)")):
        with open(os.path.join(snippets, name + ".css"), encoding="utf-8") as fh:
            parts.append((label, fh.read()))
    out = ["/*\n * Perth Web Hosting: page and snippet styles.\n *\n"
           " * GENERATED by tools/build-templates.py; edit the CSS there (or in\n"
           " * snippets/*.css) and rebuild rather than editing this file.\n */\n"]
    for label, css in parts:
        out.append(f"\n/* ---- {label} ---- */\n" + css.strip() + "\n")
    return "".join(out)


def export_standalone(data):
    """Resolve importer placeholders so the JSON imports straight into Elementor."""
    data = dict(data, content=strip_page_styles(data["content"]))
    raw = json.dumps(data, ensure_ascii=False)
    raw = re.sub(r"\{\{PWH_URL:([^}]*)\}\}", lambda m: m.group(1), raw)
    raw = re.sub(r"\{\{PWH_ASSET:([^}]*)\}\}",
                 lambda m: "https://dev.perthhosting.net/wp-content/themes/pwh-child/assets/" + m.group(1), raw)
    return json.loads(raw)


# --- Gravity Forms: contact form ---------------------------------------------
GF_CONTACT_SHORTCODE = '[gravityform id="1" title="false" description="false" ajax="true" theme="gravity-theme"]'


def gf_field(fid, kind, label, required=False, **extra):
    f = {"type": kind, "id": fid, "formId": 1, "label": label, "adminLabel": "", "isRequired": required,
         "size": "large", "errorMessage": "", "visibility": "visible", "inputs": None, "description": "",
         "allowsPrepopulate": False, "inputMask": False, "inputMaskValue": "", "inputMaskIsCustom": False,
         "maxLength": "", "inputType": "", "labelPlacement": "", "descriptionPlacement": "",
         "subLabelPlacement": "", "placeholder": "", "cssClass": "", "inputName": "", "noDuplicates": False,
         "defaultValue": "", "enableAutocomplete": False, "autocompleteAttribute": "", "choices": "",
         "conditionalLogic": "", "productField": "", "layoutGridColumnSpan": 12, "enableEnhancedUI": 0,
         "fields": "", "displayOnly": ""}
    f.update(extra)
    return f


def gf_export(title, fields, button, subject, reply_to, confirmation, ids):
    """A Gravity Forms export file (Forms > Import/Export > Import Forms) holding one form."""
    form = {
        "title": title,
        "description": "",
        "labelPlacement": "top_label",
        "descriptionPlacement": "below",
        "subLabelPlacement": "below",
        "validationPlacement": "below",
        "validationSummary": False,
        "requiredIndicator": "asterisk",
        "customRequiredIndicator": "(Required)",
        "button": {"type": "text", "text": button, "imageUrl": "", "width": "full",
                   "location": "bottom", "layoutGridColumnSpan": 12, "id": "submit"},
        "fields": fields,
        "version": "2.9.29",
        "markupVersion": 2,
        "nextFieldId": len(fields) + 1,
        "cssClass": "",
        "enableHoneypot": True,
        "enableAnimation": False,
        "save": {"enabled": False, "button": {"type": "link", "text": "Save and Continue Later"}},
        "limitEntries": False,
        "scheduleForm": False,
        "requireLogin": False,
        "is_active": "1",
        "is_trash": "0",
        "notifications": {
            ids[0]: {
                "id": ids[0], "isActive": True, "name": "Admin Notification", "service": "wordpress",
                "event": "form_submission", "toType": "email", "to": "{admin_email}",
                "subject": subject, "message": "{all_fields}", "from": "{admin_email}",
                "fromName": "Perth Web Hosting website", "replyTo": reply_to, "bcc": "",
                "disableAutoformat": False, "routing": None, "conditionalLogic": None,
            },
        },
        "confirmations": {
            ids[1]: {
                "id": ids[1], "name": "Default Confirmation", "isDefault": True, "type": "message",
                "message": confirmation, "url": "", "pageId": "", "queryString": "",
                "disableAutoformat": False, "conditionalLogic": [],
            },
        },
    }
    return {"0": form, "version": "2.9.29"}


def gf_contact_form():
    """Gravity Forms export for the Contact page."""
    choices = [{"text": t, "value": t, "isSelected": False, "price": ""}
               for t in ("New sales enquiry", "Support issue", "Feedback or review", "Something else")]
    return gf_export("PWH Contact", [
        gf_field(1, "text", "Full Name", True, placeholder="Your name",
                 enableAutocomplete=True, autocompleteAttribute="name"),
        gf_field(2, "email", "Email Address", True, placeholder="you@business.com.au",
                 emailConfirmEnabled=False, enableAutocomplete=True, autocompleteAttribute="email"),
        gf_field(3, "phone", "Phone Number (optional)", placeholder="04XX XXX XXX", phoneFormat="international",
                 enableAutocomplete=True, autocompleteAttribute="tel"),
        gf_field(4, "select", "Enquiry Type", choices=choices),
        gf_field(5, "textarea", "Message", True, placeholder="Tell us a bit about what you need.",
                 useRichTextEditor=False),
    ], "Send Message", "New website enquiry from {Full Name:1}", "{Email Address:2}",
        "Thanks, we've got your message. We'll be in touch, usually the same business day.",
        ("6a1f0c2e9b7d4", "6a1f0c2e9b7d5"))


def gf_vps_form():
    """Gravity Forms export for the VPS application page."""
    return gf_export("PWH VPS Application", [
        gf_field(1, "text", "Business Name", True, placeholder="Registered business name",
                 enableAutocomplete=True, autocompleteAttribute="organization"),
        # ABNs are 11 digits, shown as 12 345 678 901.
        gf_field(2, "text", "ABN", True, placeholder="Australian Business Number",
                 inputMask=True, inputMaskIsCustom=True, inputMaskValue="99 999 999 999"),
        gf_field(3, "text", "Contact Name", True, placeholder="Your name",
                 enableAutocomplete=True, autocompleteAttribute="name"),
        gf_field(4, "email", "Email", True, placeholder="you@business.com.au",
                 emailConfirmEnabled=False, enableAutocomplete=True, autocompleteAttribute="email"),
        gf_field(5, "textarea", "What will you use the VPS for?", True,
                 placeholder="Tell us about the sites, traffic and any technical requirements",
                 useRichTextEditor=False),
    ], "Submit Application", "VPS application from {Business Name:1}", "{Email:4}",
        "Thanks, we've got your application. We'll be in touch with a spec and a price.",
        ("6a1f0c2e9b7e1", "6a1f0c2e9b7e2"))


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
        "wordpress.json": wordpress(),
    }
    exports = {"contact.json": export_standalone(contact()), "microsoft-365.json": export_standalone(m365()),
               "reseller.json": export_standalone(reseller()),
               "email.json": export_standalone(email_page()),
               "web-hosting.json": export_standalone(hosting()),
               "email-overview.json": export_standalone(emails()),
               "vps-application-form.json": export_standalone(vps_apply()),
               "privacy-policy.json": export_standalone(legal_page("Privacy Policy", "privacy-policy.html")),
               "terms-of-service.json": export_standalone(legal_page("Terms of Service", "terms-of-service.html", updated="17/10/2026")),
               "acceptable-use-policy.json": export_standalone(legal_page("Acceptable Use Policy", "acceptable-use-policy.html", updated="17/10/2026")),
               "service-level-agreement.json": export_standalone(legal_page("Service Level Agreement", "service-level-agreement.html", updated="17/10/2026"))}
    exports["gravityforms-contact.json"] = gf_contact_form()
    exports["gravityforms-vps-application.json"] = gf_vps_form()
    os.makedirs(os.path.join(OUT, "..", "export"), exist_ok=True)
    with open(os.path.join(OUT, "..", "assets", "css", "pwh-pages.css"), "w", encoding="utf-8") as fh:
        fh.write(page_css())
    print("wrote assets/css/pwh-pages.css")
    for name, data in exports.items():
        with open(os.path.join(OUT, "..", "export", name), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("wrote export/" + name)
    for name, data in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("wrote", name)


if __name__ == "__main__":
    main()
