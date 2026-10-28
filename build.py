#!/usr/bin/env python3
"""Team ASAP static site generator.

Usage:
  python3 build.py            -> builds the production site into ./public (deploy this on Netlify)
  python3 build.py --preview  -> builds a preview copy into ./preview (relative links, form in demo mode)

All business details live in content/site.json, services in content/services.json,
portfolio in content/projects.json. Edit those, then rebuild.
"""
import json, sys, shutil, html, re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent
PREVIEW = "--preview" in sys.argv
OUT = ROOT / ("preview" if PREVIEW else "public")
SITE = json.loads((ROOT / "content/site.json").read_text())
SVCS = json.loads((ROOT / "content/services.json").read_text())["pages"]
PROJ = json.loads((ROOT / "content/projects.json").read_text())
SVC = {s["slug"]: s for s in SVCS}
PROJECTS = [p for p in PROJ["projects"] if p.get("published")]
CATS = PROJ["categories"]
e = html.escape
YEAR = date.today().year

# ---------- paths ----------
def href(slug):
    if slug in ("", "index"):
        return "index.html" if PREVIEW else "/"
    return f"{slug}.html" if PREVIEW else f"/{slug}"
def asset(p):
    return f"assets/{p}" if PREVIEW else f"/assets/{p}"
def img(name):
    return asset(f"img/{name}.webp")
def canon(slug):
    base = SITE["siteUrl"].rstrip("/")
    return base + ("/" if slug in ("", "index") else f"/{slug}")

PHONE = SITE["phone"]["display"]
TEL = "tel:" + SITE["phone"]["e164"]

def v(item, default="Confirm with owner"):
    """data-verify attribute for unconfirmed facts."""
    if isinstance(item, dict) and item.get("verified") is False:
        return f' data-verify="{e(item.get("note") or default)}"'
    return ""
VP = v(SITE["phone"], "Confirm phone number")

# ---------- icons (24px stroke) ----------
def ic(name):
    P = {
      "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
      "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
      "chev": '<path d="m6 9 6 6 6-6"/>',
      "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
      "close": '<path d="M6 6l12 12M18 6 6 18"/>',
      "drop": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
      "alert": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/><path d="M12 10v4M12 17h.01"/>',
      "pipe": '<path d="M3 8h8a3 3 0 0 1 3 3v10M3 12h6a1 1 0 0 1 1 1v8"/><path d="M14 4h7v4h-7z"/>',
      "wrench": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.2L3 17.8V21h3.2l6.3-6.3a4 4 0 0 0 5.2-5.4l-2.6 2.6-2.4-.6-.6-2.4z"/>',
      "drain": '<circle cx="12" cy="12" r="8"/><path d="M8 12h8M12 8v8M9.2 9.2l5.6 5.6M14.8 9.2l-5.6 5.6"/>',
      "heater": '<rect x="6" y="3" width="12" height="18" rx="3"/><path d="M12 9c1.5 1.6 2 2.7 2 3.6a2 2 0 0 1-4 0c0-.9.5-2 2-3.6z"/><path d="M9 21v1M15 21v1"/>',
      "shower": '<path d="M4 21V8a4 4 0 0 1 4-4h1a4 4 0 0 1 4 4"/><path d="M10 10h6M11 14v1M13 14v1M15 14v1M12 17v1M14 17v1M16 17v1"/>',
      "bath": '<path d="M3 12h18v3a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5z"/><path d="M6 12V6a2 2 0 0 1 3.5-1.3"/><path d="M7 20l-1 2M17 20l1 2"/>',
      "home": '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
      "check": '<path d="m5 12 4.5 4.5L19 7"/>',
      "pin": '<path d="M12 21s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',
      "chat": '<path d="M4 5h16v11H9l-5 4z"/>',
      "eye": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
      "broom": '<path d="M14 4 9.5 12.5M6 13h8l3 8H3z"/>',
      "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
      "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
      "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
      "plus": '<path d="M12 5v14M5 12h14"/>',
      "grid": '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
    }
    if name == "star":
        return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="m12 2.8 2.8 5.9 6.4.8-4.7 4.4 1.2 6.3L12 17.1l-5.7 3.1 1.2-6.3L2.8 9.5l6.4-.8z"/></svg>'
    return f'<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{P[name]}</svg>'

# ---------- shared chrome ----------
PLUMB_SUB = ["leak-detection-pipe-repair", "drain-sewer", "water-heaters", "fixtures-installation"]
IMPR_SUB = ["bathroom-remodeling"]
quote_label = "Get a Free Quote" if SITE.get("freeEstimates") else "Request a Quote"

def head(title, desc, slug, extra_ld=None, og_img=None):
    ld = [json.dumps(x, ensure_ascii=False) for x in (extra_ld or [])]
    og = SITE["siteUrl"].rstrip("/") + "/assets/" + (og_img or "brand/og-image.jpg")
    ga = SITE["analytics"].get("ga4Id", "")
    doc_open = "" if (PREVIEW and slug == "index") else '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
    return f'''{doc_open}<title>{e(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon(slug)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE['legalName'])}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon(slug)}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#071F39">
<link rel="icon" href="{asset('brand/icon_32px.png')}" sizes="32x32">
<link rel="icon" href="{asset('brand/icon.svg')}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{asset('brand/icon_180px.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap">
<link rel="stylesheet" href="{asset('site.css')}">
{''.join(f'<script type="application/ld+json">{x}</script>' for x in ld)}
<script>window.ASAP={{ga4:"{e(ga)}",preview:{str(PREVIEW).lower()}}};</script>
<script src="{asset('site.js')}" defer></script>
''' + ("" if (PREVIEW and slug == "index") else "</head>\n<body>\n")

def header(cur):
    def a(slug, label):
        c = ' aria-current="page"' if cur == slug else ""
        return f'<a href="{href(slug)}"{c}>{label}</a>'
    def dd(hub, label, subs):
        isc = " current" if cur == hub or cur in subs else ""
        links = "".join(f'<a href="{href(s)}">{e(SVC[s]["nav"])}</a>' for s in subs)
        return f'''<div class="dd{isc}"><button type="button" aria-expanded="false" aria-controls="dd-{hub}">{label}{ic("chev")}</button>
<div class="dd-panel" id="dd-{hub}" hidden>{links}<a class="all" href="{href(hub)}">All {label.lower()}</a></div></div>'''
    drawer_links = (
        f'<a class="d-link" href="{href("")}">Home</a>'
        f'<a class="d-link" href="{href("plumbing")}">Plumbing</a>' +
        "".join(f'<a class="d-sub" href="{href(s)}">{e(SVC[s]["nav"])}</a>' for s in PLUMB_SUB) +
        f'<a class="d-link" href="{href("emergency-plumbing")}">Emergency plumbing</a>'
        f'<a class="d-link" href="{href("home-improvements")}">Home improvements</a>' +
        "".join(f'<a class="d-sub" href="{href(s)}">{e(SVC[s]["nav"])}</a>' for s in IMPR_SUB) +
        f'<a class="d-link" href="{href("our-work")}">Our work</a>'
        f'<a class="d-link" href="{href("about")}">About</a>'
        f'<a class="d-link" href="{href("contact")}">Contact</a>')
    review = ""
    if SITE.get("reviewMode"):
        review = f'''<button class="review-toggle" type="button" aria-pressed="false">{ic('eye')}Owner review</button>
<div class="review-note" role="status">Dashed outlines mark details Team ASAP needs to confirm before launch. Hover or tap one to see the note.</div>'''
    e247 = SITE.get("emergency247")
    util_left = (f'<span{v(SITE["trust"][3])}><span class="pulse" aria-hidden="true"></span>24/7 emergency plumbing</span>'
                 if e247 else '<span>Plumbing & home improvement</span>')
    return f'''<a class="skip" href="#main">Skip to content</a>
{review}
<div class="util"><div class="wrap">{util_left}<span class="hide-sm">New Rochelle &amp; Westchester County</span><a href="{TEL}" data-track="call_click" data-loc="util"{VP}>{PHONE}</a></div></div>
<header class="hdr"><div class="wrap">
<a class="logo" href="{href('')}" aria-label="Team ASAP Home Improvement, home"><img src="{asset('brand/logo-horizontal.png')}" alt="Team ASAP Home Improvement" width="640" height="142"></a>
<nav class="nav" aria-label="Main">{a('', 'Home')}{dd('plumbing', 'Plumbing', PLUMB_SUB)}{a('emergency-plumbing', 'Emergency')}{dd('home-improvements', 'Home Improvements', IMPR_SUB)}{a('our-work', 'Our Work')}{a('about', 'About')}{a('contact', 'Contact')}</nav>
<div class="hdr-cta"><a class="hdr-phone" href="{TEL}" data-track="call_click" data-loc="header"{VP}>{ic('phone')}{PHONE}</a><a class="btn sm" href="{href('contact')}" data-track="quote_cta" data-loc="header">{quote_label}</a></div>
<a class="call-btn" href="{TEL}" aria-label="Call Team ASAP at {PHONE}" data-track="call_click" data-loc="header-mobile">{ic('phone')}</a>
<button class="menu-btn" type="button" aria-label="Open menu" aria-controls="drawer" aria-expanded="false">{ic('menu')}</button>
</div></header>
<div class="drawer" id="drawer" hidden><div class="drawer-panel" role="dialog" aria-modal="true" aria-label="Menu">
<div class="drawer-top"><img src="{asset('brand/logo-horizontal.png')}" alt="" width="160" height="36" style="height:34px;width:auto"><button class="menu-btn" type="button" data-close aria-label="Close menu" style="display:inline-flex">{ic('close')}</button></div>
{drawer_links}
<a class="btn" href="{href('contact')}" data-track="quote_cta" data-loc="drawer">{quote_label}</a>
<a class="btn ghost" href="{TEL}" data-track="call_click" data-loc="drawer">{ic('phone')}Call {PHONE}</a>
</div></div>
<main id="main">
'''

def footer():
    plumbing = "".join(f'<li><a href="{href(s)}">{e(SVC[s]["nav"])}</a></li>' for s in ["plumbing"] + PLUMB_SUB)
    credit = SITE.get("credit", {})
    cr = (f'<a href="{e(credit["url"])}">{e(credit["name"])}</a>' if credit.get("url") else e(credit.get("name", "")))
    return f'''</main>
<footer class="ftr"><div class="wrap">
<div class="ftr-grid">
<div style="display:grid;gap:16px;align-content:start"><img src="{asset('brand/logo-horizontal-white.png')}" alt="Team ASAP Home Improvement" width="640" height="142"><p>Plumbing and home improvement for homeowners in {e(SITE['city'])} and surrounding Westchester communities.</p><a class="phone" href="{TEL}" data-track="call_click" data-loc="footer"{VP}>{PHONE}</a></div>
<div><h4>Plumbing</h4><ul>{plumbing}</ul></div>
<div><h4>Services</h4><ul><li><a href="{href('emergency-plumbing')}">Emergency plumbing</a></li><li><a href="{href('home-improvements')}">Home improvements</a></li><li><a href="{href('bathroom-remodeling')}">Bathroom remodeling</a></li><li><a href="{href('our-work')}">Our work</a></li></ul></div>
<div><h4>Company</h4><ul><li><a href="{href('about')}">About Team ASAP</a></li><li><a href="{href('contact')}">{quote_label}</a></li><li><a href="{href('contact')}">Contact</a></li><li><a href="{href('privacy')}">Privacy</a></li></ul></div>
</div>
<div class="ftr-bottom"><span>&copy; {YEAR} {e(SITE['legalName'])}. All rights reserved.</span><span>Website by {cr}</span></div>
</div></footer>
<div class="mbar"><a class="btn ghost" href="{TEL}" data-track="call_click" data-loc="mobile-bar">{ic('phone')}Call</a><a class="btn" href="{href('contact')}" data-track="quote_cta" data-loc="mobile-bar">{quote_label}</a></div>
''' + ("" if PREVIEW and False else "")

def close_doc(slug):
    return "" if (PREVIEW and slug == "index") else "</body>\n</html>\n"

def page(slug, title, desc, body, ld=None, cur=None):
    return head(title, desc, slug, ld) + header(cur if cur is not None else slug) + body + footer() + close_doc(slug)

# ---------- schema ----------
def business_ld():
    areas = [{"@type": "City", "name": f'{a["name"]}, NY'} for a in SITE["serviceAreas"]]
    d = {
      "@context": "https://schema.org", "@type": "Plumber",
      "@id": SITE["siteUrl"].rstrip("/") + "/#business",
      "name": SITE["legalName"], "alternateName": [SITE["brandName"], SITE["alsoKnownAs"]],
      "url": SITE["siteUrl"], "telephone": SITE["phone"]["e164"],
      "logo": SITE["siteUrl"].rstrip("/") + "/assets/brand/logo-primary.png",
      "image": SITE["siteUrl"].rstrip("/") + "/assets/img/shower-matte-black-1.webp",
      "address": {"@type": "PostalAddress", "addressLocality": SITE["city"], "addressRegion": SITE["region"], "addressCountry": "US"},
      "areaServed": areas,
    }
    if SITE["streetAddress"]:
        d["address"]["streetAddress"] = SITE["streetAddress"]
    if SITE.get("emergency247"):
        d["openingHoursSpecification"] = [{"@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], "opens": "00:00", "closes": "23:59"}]
    if SITE["email"]["value"]:
        d["email"] = SITE["email"]["value"]
    return d

def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": canon(s)} for i, (n, s) in enumerate(items)]}

def crumbs_html(items):
    lis = "".join((f'<li><a href="{href(s)}">{e(n)}</a></li>' if i < len(items) - 1 else f'<li aria-current="page">{e(n)}</li>') for i, (n, s) in enumerate(items))
    return f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{lis}</ol></nav>'

# ---------- blocks ----------
def trust_strip():
    lis = []
    for t in SITE["trust"]:
        val = e(t["value"])
        if t["label"].lower().startswith("google rating"):
            val += ' <small aria-hidden="true">&#9733;</small>'
        lis.append(f'<li><span class="fit"{v(t)}><span class="v">{val}</span></span><span class="l">{e(t["label"])}</span></li>')
    return f'<section class="pipe-run" aria-label="Why homeowners choose Team ASAP"><div class="wrap"><ul>{"".join(lis)}</ul></div></section>'

def emergency_band():
    e247 = SITE.get("emergency247")
    when = "day or night" if e247 else "as soon as possible"
    return f'''<section class="band" aria-labelledby="em-h"><div class="wrap">
<div style="display:grid;gap:18px"><span class="eyebrow">Emergency plumbing</span><h2 id="em-h">Plumbing emergency? We're here to help.</h2>
<p>Burst pipe, water coming through the ceiling, or a sewer backup: shut off the main water valve if you can, then call Team ASAP {when}. Calling is the fastest way to reach us.</p>
<div class="btn-row"><a class="btn on-dark ghost" href="{href('emergency-plumbing')}">What to do right now</a></div></div>
<div class="big-phone"><small>Call Team ASAP</small><span class="num"{VP}>{PHONE}</span><a class="btn white" href="{TEL}" data-track="emergency_call_click" data-loc="band">{ic('phone')}Call now</a><small{v(SITE["trust"][3]) if e247 else ""}>{"Emergency service available 24/7" if e247 else ""}</small></div>
</div></section>'''

def final_cta(svc_key=None):
    target = href("contact") + (f"#svc-{svc_key}" if svc_key else "")
    return f'''<section class="final"><div class="wrap"><div><h2>Let's get your project moving.</h2><p>Tell us what you need and send a few photos, or call and talk it through with Team ASAP.</p></div>
<div class="btn-row"><a class="btn white" href="{target}" data-track="quote_cta" data-loc="final">{quote_label}</a><a class="btn on-dark ghost" href="{TEL}" data-track="call_click" data-loc="final"{VP}>{ic('phone')}{PHONE}</a></div></div></section>'''

def project_card(p, eager=False):
    first = p["photos"][0]
    n = len(p["photos"])
    count = f'<span class="count">{n} photos</span>' if n > 1 else ""
    return f'''<button type="button" class="work" data-cat="{p['category']}" data-project="{p['id']}" data-track="portfolio_open"{v(p, 'Confirm this is Team ASAP work and the caption is accurate')}>
<img src="{img(first)}" alt="{e(p['title'])}" loading="{'eager' if eager else 'lazy'}" width="594" height="742">{count}
<span class="cap"><span>{e(CATS[p['category']])}</span><b>{e(p['title'])}</b></span></button>'''

def project_templates():
    out = []
    for p in PROJECTS:
        pics = "".join(f'<img src="{img(ph)}" alt="{e(p["title"])}, photo {i+1}" loading="lazy">' for i, ph in enumerate(p["photos"]))
        loc = f'<p class="crumbs">{e(p["location"])}</p>' if p.get("location") else ""
        out.append(f'''<template id="tpl-{p['id']}"><div class="lb-in"><div class="lb-pics">{pics}</div><div class="lb-text"><span class="eyebrow">{e(CATS[p['category']])}</span><h3 style="font-size:1.5rem">{e(p['title'])}</h3>{loc}<p style="color:var(--muted)">{e(p['description'])}</p><a class="btn sm" href="{href('contact')}" data-track="quote_cta" data-loc="lightbox">Start a similar project</a></div></div></template>''')
    return "".join(out) + f'<dialog class="lb" id="lb" aria-label="Project photos"><div class="lb-body"></div><button class="lb-close" type="button" aria-label="Close">{ic("close")}</button></dialog>'

def svc_card(slug, blurb, icon_name=None):
    s = SVC.get(slug)
    title = s["nav"] if s else slug
    tag = '<span class="illus">Illustration</span>' if s and s.get("illustration") else ""
    pic = f'<div class="ph"><img src="{img(s["image"])}" alt="{e(s["imageAlt"])}" loading="lazy" width="1400" height="933">{tag}</div>'
    return f'<a class="svc" href="{href(slug)}"><div class="ph-wrap">{pic}</div><div class="body"><h3>{e(title)}</h3><p>{e(blurb)}</p><span class="link-arrow">Learn more {ic("arrow")}</span></div></a>'

# ---------- HOME ----------
def build_home():
    feat = [p for p in PROJECTS if p.get("featured")][:4]
    t = SITE["trust"]
    r = SITE["googleRating"]
    reviews_url = SITE.get("googleReviewsUrl") or "https://www.google.com/search?q=Team+ASAP+Home+Improvement+New+Rochelle+NY+reviews"
    areas = "".join(
        (f'<li class="primary"{v(a)}>{ic("pin")}<span>{e(a["name"])}<small>Home base</small></span></li>' if a.get("primary")
         else f'<li{v(a, "Confirm Team ASAP serves this town")}>{ic("pin")}{e(a["name"])}</li>')
        for a in SITE["serviceAreas"])
    e247 = SITE.get("emergency247")
    urgent_card = f'''<a class="svc urgent" href="{href('emergency-plumbing')}"><div class="ph">{ic('alert')}</div><div class="body"><h3>Emergency plumbing</h3><p>Burst pipes, active leaks and sewer backups. Call and we'll help you stop the damage{', any time of day' if e247 else ''}.</p><span class="link-arrow">Emergency help {ic('arrow')}</span></div></a>'''
    cards = urgent_card + "".join([
        svc_card("leak-detection-pipe-repair", "Hidden leaks, damaged or corroded pipe, and section replacement."),
        svc_card("drain-sewer", "Slow drains, recurring clogs and main line backups, traced to the cause."),
        svc_card("water-heaters", "No hot water, a leaking tank or a heater near the end of its life."),
        svc_card("fixtures-installation", "Faucets, toilets, shower valves and trim, vanities and disposals."),
        svc_card("bathroom-remodeling", "Showers, vanities and fixtures, with the plumbing behind the tile done right."),
    ])
    ld = [business_ld(), {"@context": "https://schema.org", "@type": "WebSite", "name": SITE["legalName"], "url": SITE["siteUrl"]}]
    body = f'''
<section class="hero"><div class="wrap">
<div class="hero-copy">
<span class="eyebrow">Plumbing &amp; home improvement &middot; {e(SITE['city'])}, NY</span>
<h1>Plumbing done right. <span>Homes made better.</span></h1>
<p class="lead">From urgent plumbing repairs to thoughtful home improvements, Team ASAP brings reliable workmanship and personal service to homeowners across {e(SITE['city'])} and surrounding communities.</p>
<div class="btn-row"><a class="btn" href="{href('contact')}" data-track="quote_cta" data-loc="hero">{quote_label}{ic('arrow')}</a><a class="btn ghost" href="{TEL}" data-track="call_click" data-loc="hero"{VP}>{ic('phone')}Call Team ASAP</a></div>
<div class="emerg-line"><span class="pulse" aria-hidden="true"></span><strong>Plumbing emergency?</strong><a href="{TEL}" data-track="emergency_call_click" data-loc="hero"{VP}>Call {PHONE}</a></div>
</div>
<div class="collage">
<figure class="c1"><img src="{img('shower-matte-black-1')}" alt="Matte-black shower controls, body jets and handheld shower on large white tile" width="594" height="990" fetchpriority="high"><figcaption class="tag"><b>Recent work</b>Matte-black shower with body jets</figcaption></figure>
<figure class="c2"><img src="{img('vanity-black-marble')}" alt="Black vanity with marble top and matte-black faucet" width="594" height="594"></figure>
<figure class="c3"><img src="{img('shower-bronze-subway')}" alt="Bronze shower head and valve on white subway tile" width="594" height="990"></figure>
</div>
</div></section>
{trust_strip()}

<section class="section" aria-labelledby="svc-h"><div class="wrap">
<div class="sec-head split"><div style="display:grid;gap:14px"><span class="eyebrow">What we do</span><h2 id="svc-h">From a dripping faucet to a full bathroom</h2></div><a class="link-arrow" href="{href('plumbing')}">All plumbing services {ic('arrow')}</a></div>
<div class="svc-grid">{cards}</div>
</div></section>

<section class="section soft" aria-labelledby="det-h"><div class="wrap detail">
<div class="detail-pics"><figure><img src="{img('shower-valve-trim')}" alt="Chrome single-handle shower valve trim on white tile" loading="lazy" width="594" height="744"></figure><figure><img src="{img('shower-valve-rough-in')}" alt="Shower valve set in a mortar bed before tile" loading="lazy" width="594" height="744"></figure></div>
<div><span class="eyebrow">How we work</span><h2 id="det-h" style="margin-top:14px">The difference is in the details.</h2>
<p class="lead" style="margin-top:18px">The trim you see on the wall is only as good as the valve behind it. We take the same care with the parts that get covered up as with the finished work you'll look at every day.</p>
<div class="principles">
<div class="principle"><span class="ic">{ic('chat')}</span><div><h3>Clear communication</h3><p>We explain what we find and what we recommend before work starts.</p></div></div>
<div class="principle"><span class="ic">{ic('wrench')}</span><div><h3>Careful workmanship</h3><p>Valves, drains and connections are done properly and tested.</p></div></div>
<div class="principle"><span class="ic">{ic('broom')}</span><div><h3>Respect for your home</h3><p>We protect the work area and leave it clean.</p></div></div>
</div></div>
</div></section>

<section class="section" aria-labelledby="work-h"><div class="wrap">
<div class="sec-head split"><div style="display:grid;gap:14px"><span class="eyebrow">Our work</span><h2 id="work-h">Real projects by Team ASAP</h2></div><a class="link-arrow" href="{href('our-work')}">See all projects {ic('arrow')}</a></div>
<div class="work-grid">{''.join(project_card(p) for p in feat)}</div>
</div></section>

{emergency_band()}

<section class="section soft" aria-labelledby="rev-h"><div class="wrap">
<div class="rating"{v(r, 'Re-check rating and review count on Google before launch')}>
<div><div class="score">{e(r['rating'])}</div><div class="stars" aria-label="{e(r['rating'])} out of 5 stars">{ic('star')*5}</div><p class="src">Google rating &middot; {e(r['count'])} reviews</p></div>
<div style="display:grid;gap:16px"><span class="eyebrow">Reviews</span><h2 id="rev-h">Trusted by homeowners across {e(SITE['city'])}</h2><p class="lead">Team ASAP's reputation was built one job at a time. Read what customers say in their own words on Google.</p><div class="btn-row"><a class="btn ghost" href="{e(reviews_url)}" target="_blank" rel="noopener" data-track="reviews_click"{'' if SITE.get('googleReviewsUrl') else ' data-verify="Replace with the direct Google reviews link"'}>Read our Google reviews {ic('arrow')}</a></div></div>
</div>
</div></section>

<section class="section" aria-labelledby="area-h"><div class="wrap area">
<div style="display:grid;gap:16px"><span class="eyebrow">Service area</span><h2 id="area-h">Rooted in {e(SITE['city'])}</h2><p class="lead">Team ASAP is based in {e(SITE['city'])} and works with homeowners in nearby Westchester communities. Not sure if we cover your town? Call and ask.</p><div><a class="link-arrow" href="{TEL}" data-track="call_click" data-loc="area">Call {PHONE} {ic('arrow')}</a></div></div>
<ul class="towns">{areas}</ul>
</div></section>
{final_cta()}
{project_templates()}
'''
    return page("index", "Team ASAP | Plumbing & Home Improvement in New Rochelle, NY",
                "Team ASAP Home Improvement: plumbing repairs, emergency plumbing, water heaters, drains and bathroom remodeling for homeowners in New Rochelle and Westchester County.",
                body, ld, cur="")

# ---------- SERVICE PAGES ----------
def build_service(s):
    slug = s["slug"]
    if s["group"] == "plumbing" and not s.get("hub"):
        trail = [("Home", ""), ("Plumbing", "plumbing"), (s["nav"], slug)]
    elif s["group"] == "improvements" and not s.get("hub"):
        trail = [("Home", ""), ("Home improvements", "home-improvements"), (s["nav"], slug)]
    else:
        trail = [("Home", ""), (s["nav"], slug)]
    urgent = s.get("emergency")
    tall = s["image"].startswith("shower-") or s["image"] in ("drain-lines-basement",)
    cap = '<figcaption>Illustration</figcaption>' if s.get("illustration") else '<figcaption>Team ASAP project</figcaption>'
    pv = "" if s.get("illustration") else ' data-verify="Confirm this photo shows Team ASAP work"'
    if urgent:
        ctas = f'<div class="btn-row"><a class="btn" href="{TEL}" data-track="emergency_call_click" data-loc="emergency-hero"{VP}>{ic("phone")}Call {PHONE}</a><a class="btn on-dark ghost" href="#first-steps">What to do now</a></div>'
    else:
        ctas = f'<div class="btn-row"><a class="btn" href="{href("contact")}#svc-{s["quoteKey"]}" data-track="quote_cta" data-loc="service-hero">{quote_label}{ic("arrow")}</a><a class="btn ghost" href="{TEL}" data-track="call_click" data-loc="service-hero"{VP}>{ic("phone")}{PHONE}</a></div>'
    hero = f'''<section class="phero{' urgent' if urgent else ''}"><div class="wrap"><div class="copy">{crumbs_html(trail)}<span class="eyebrow">{e(s['eyebrow'])}</span><h1>{e(s['h1'])}</h1><p class="lead">{e(s['intro'])}</p>{ctas}</div>
<figure class="{'tall' if tall else ''}"{pv}><img src="{img(s['image'])}" alt="{e(s['imageAlt'])}" width="1400" height="933" fetchpriority="high">{cap}</figure></div></section>'''
    first = ""
    if s.get("firstSteps"):
        fs = "".join(f'<li><h3>{e(a)}</h3><p>{e(b)}</p></li>' for a, b in s["firstSteps"])
        first = f'<section class="section first-steps" id="first-steps" aria-labelledby="fs-h"><div class="wrap"><div class="sec-head"><span class="eyebrow">Right now</span><h2 id="fs-h">What to do while you wait</h2></div><ol class="steps">{fs}</ol></div></section>'
    signs = "".join(f'<li>{ic("drop")}<span>{e(x)}</span></li>' for x in s["signs"])
    steps = "".join(f'<li><h3>{e(a)}</h3><p>{e(b)}</p></li>' for a, b in s["approach"])
    inc = "".join(f'<li>{ic("check")}<span>{e(x)}</span></li>' for x in s["includes"])
    # hub: list subpages
    hub_cards = ""
    if s.get("hub"):
        subs = PLUMB_SUB if slug == "plumbing" else IMPR_SUB + ["fixtures-installation"]
        hub_cards = '<section class="section soft"><div class="wrap"><div class="sec-head"><span class="eyebrow">Services</span><h2>Explore by service</h2></div><div class="svc-grid">' + "".join(
            svc_card(x, SVC[x]["intro"].split(". ")[0] + ".") for x in subs) + "</div></div></section>"
    gal = ""
    if s.get("gallery"):
        gal = '<div class="mini-gal">' + "".join(f'<img src="{img(g)}" alt="Team ASAP bathroom project" loading="lazy" data-verify="Confirm Team ASAP work">' for g in s["gallery"]) + f'</div><p style="margin-top:12px"><a class="link-arrow" href="{href("our-work")}">See all projects {ic("arrow")}</a></p>'
    faq = "".join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in s["faq"])
    rel = "".join(f'<a href="{href(r)}">{e(SVC[r]["nav"])}{ic("arrow")}</a>' for r in s["related"])
    body = f'''{hero}
{first}
<section class="section{' soft' if not first else ''}" aria-labelledby="signs-h"><div class="wrap cols-2">
<div style="display:grid;gap:16px"><span class="eyebrow">Common problems</span><h2 id="signs-h">{'Call right away if you have' if urgent else 'Signs it is time to call'}</h2><p class="lead">{'These problems get worse quickly. Shut off the water if you can, then call.' if urgent else 'Catching these early usually means a simpler repair.'}</p></div>
<ul class="signs">{signs}</ul>
</div></section>
<section class="section{' soft' if first else ''}" aria-labelledby="how-h"><div class="wrap"><div class="sec-head"><span class="eyebrow">How it works</span><h2 id="how-h">How we handle it</h2></div><ol class="steps">{steps}</ol></div></section>
{hub_cards}
<section class="section" aria-labelledby="inc-h"><div class="wrap cols-2">
<div style="display:grid;gap:18px"><span class="eyebrow">What we cover</span><h2 id="inc-h">{'Emergencies we handle' if urgent else 'Services include'}</h2><ul class="checks">{inc}</ul>{gal}</div>
<div class="local"><span class="eyebrow">Local know-how</span><h3>Plumbing in {e(SITE['city'])} homes</h3><p>{e(s['local'])}</p><p>Not sure whether we cover your town? <a href="{TEL}" data-track="call_click" data-loc="local">Call {PHONE}</a> and ask.</p></div>
</div></section>
<section class="section soft" aria-labelledby="faq-h"><div class="wrap"><div class="sec-head"><span class="eyebrow">Questions</span><h2 id="faq-h">Frequently asked questions</h2></div><div class="faq">{faq}</div></div></section>
<section class="section" aria-labelledby="rel-h"><div class="wrap"><div class="sec-head"><h2 id="rel-h" style="font-size:1.6rem">Related services</h2></div><div class="rel">{rel}</div></div></section>
{emergency_band() if not urgent else ''}
{final_cta(s['quoteKey'])}'''
    ld = [crumbs_ld(trail), {"@context": "https://schema.org", "@type": "Service", "name": s["h1"], "serviceType": s["nav"],
          "provider": {"@id": SITE["siteUrl"].rstrip("/") + "/#business"}, "areaServed": {"@type": "City", "name": f'{SITE["city"]}, NY'},
          "description": s["metaDescription"]}, business_ld()]
    return page(slug, s["metaTitle"], s["metaDescription"], body, ld)

# ---------- OUR WORK ----------
def build_work():
    used = [c for c in CATS if any(p["category"] == c for p in PROJECTS)]
    filt = '<button type="button" aria-pressed="true" data-filter="all">All</button>' + "".join(
        f'<button type="button" aria-pressed="false" data-filter="{c}">{e(CATS[c])}</button>' for c in used)
    trail = [("Home", ""), ("Our work", "our-work")]
    body = f'''<section class="phero"><div class="wrap" style="grid-template-columns:1fr"><div class="copy">{crumbs_html(trail)}<span class="eyebrow">Our work</span><h1>Real projects, photographed on the job</h1><p class="lead">Every photo here is from a Team ASAP job: finished bathrooms, fixture installations and plumbing work in progress. Tap a project to see more.</p></div></div></section>
<section class="section" style="padding-top:24px"><div class="wrap">
<div class="filters" role="group" aria-label="Filter projects">{filt}</div>
<div class="work-grid" id="work-grid">{''.join(project_card(p, i < 4) for i, p in enumerate(PROJECTS))}</div>
<p id="work-empty" hidden style="color:var(--muted)">No projects in this category yet.</p>
</div></section>
{final_cta()}
{project_templates()}'''
    return page("our-work", "Our Work | Bathroom & Plumbing Projects | Team ASAP, New Rochelle NY",
                "See real bathroom, fixture and plumbing projects completed by Team ASAP Home Improvement in New Rochelle and Westchester County.",
                body, [crumbs_ld(trail)])

# ---------- ABOUT ----------
def build_about():
    o = SITE["owner"]
    initials = "".join(w[0] for w in o["name"].replace(".", "").split()[:2])
    trail = [("Home", ""), ("About", "about")]
    t = SITE["trust"]
    body = f'''<section class="phero"><div class="wrap"><div class="copy">{crumbs_html(trail)}<span class="eyebrow">About Team ASAP</span><h1>Great work starts with taking responsibility for the details.</h1><p class="lead">Team ASAP Home Improvement is an owner-led plumbing and home improvement company based in {e(SITE['city'])}, New York. We've built our reputation one home at a time, on careful work, straight answers and showing up when customers need us.</p><div class="btn-row"><a class="btn" href="{href('contact')}" data-track="quote_cta" data-loc="about">{quote_label}</a><a class="btn ghost" href="{href('our-work')}">See our work</a></div></div>
<figure class="tall" data-verify="Replace with a genuine photo of the owner or crew on a job"><img src="{img('shower-bronze-subway')}" alt="Bronze shower fixtures on white subway tile, a Team ASAP project" width="594" height="990"><figcaption>Team ASAP project</figcaption></figure></div></section>
{trust_strip()}
<section class="section" aria-labelledby="ab-h"><div class="wrap cols-2">
<div class="prose"><span class="eyebrow">Who we are</span><h2 id="ab-h">An owner-led local business</h2>
<p>When you call Team ASAP, you're dealing with a local business whose owner is personally accountable for the work. We've grown through referrals and repeat customers, and we treat every job, large or small, as the reason the next customer will call.</p>
<p>Our work covers everyday plumbing repairs, urgent problems that can't wait, and home improvement projects like bathroom renovations, where good plumbing and good finish work have to come together.</p>
<h3>How we work</h3>
<ul class="checks"><li>{ic('check')}<span>We explain what we find and what we recommend, in plain terms, before work begins.</span></li><li>{ic('check')}<span>We take care with the parts you'll never see, not just the parts you will.</span></li><li>{ic('check')}<span>We protect your home while we work and clean up when we're done.</span></li><li>{ic('check')}<span>We answer the phone when you have a problem.</span></li></ul>
</div>
<div style="display:grid;gap:20px">
<div class="owner-card"{v(o)}><div class="mono" aria-hidden="true">{e(initials)}</div><div><h3>{e(o['name'])}</h3><p>{e(o['title'])}, {e(SITE['legalName'])}</p><blockquote data-verify="Draft message: owner to write or approve in his own words">“Every job carries our name. I want customers to feel they can call us again, and recommend us to their neighbors.”</blockquote></div></div>
<div class="local" data-verify="Owner to confirm any licenses, certifications or insurance to list here"><span class="eyebrow">Credentials</span><h3>Licensing &amp; insurance</h3><p>Ask us about our licensing and insurance when you request a quote. Verified details will be listed here.</p></div>
</div>
</div></section>
{emergency_band()}
{final_cta()}'''
    return page("about", "About Team ASAP | Owner-Led Plumbing & Home Improvement, New Rochelle NY",
                "Team ASAP Home Improvement is an owner-led plumbing and home improvement company based in New Rochelle, NY, serving homeowners in Westchester County.",
                body, [crumbs_ld(trail), business_ld()])

# ---------- CONTACT / QUOTE ----------
QOPTS = [
    ("emergency", "Emergency plumbing", "Active leak, burst pipe, backup", "alert"),
    ("repair", "Plumbing repair", "Leaks, drains, toilets, faucets", "wrench"),
    ("installation", "Installation", "Fixtures, vanities, disposals", "shower"),
    ("water-heater", "Water heater", "Repair or replacement", "heater"),
    ("bathroom", "Bathroom remodeling", "Full or partial renovation", "bath"),
    ("other", "Other home improvement", "Tell us about your project", "home"),
]
def build_contact():
    trail = [("Home", ""), ("Contact", "contact")]
    opts = "".join(f'''<div class="opt{' emerg' if k=='emergency' else ''}"><input type="radio" name="service" id="svc-{k}" value="{e(t)}" data-key="{k}" required><label for="svc-{k}"><span class="ic">{ic(i)}</span><span><b>{e(t)}</b><small>{e(d)}</small></span></label></div>''' for k, t, d, i in QOPTS)
    e247 = SITE.get("emergency247")
    email_line = (f'<p>Email: <a href="mailto:{e(SITE["email"]["value"])}">{e(SITE["email"]["value"])}</a></p>' if SITE["email"]["value"] else "")
    body = f'''<section class="phero" style="padding-bottom:0"><div class="wrap" style="grid-template-columns:1fr;padding-bottom:12px"><div class="copy">{crumbs_html(trail)}<span class="eyebrow">Contact &amp; quotes</span><h1>Tell us what you need.</h1><p class="lead">Answer a few quick questions and add photos if you have them. For an active leak or emergency, call instead. It's faster.</p></div></div></section>
<section class="section" style="padding-top:28px;background:linear-gradient(180deg,var(--soft),#fff)"><div class="wrap quote-layout">
<div class="qcard">
<form id="quote" name="quote" method="POST" action="{href('contact')}" data-netlify="true" netlify-honeypot="bot-field" enctype="multipart/form-data" novalidate>
<input type="hidden" name="form-name" value="quote">
<p class="hp"><label>Leave this empty <input name="bot-field" tabindex="-1" autocomplete="off"></label></p>
<input type="hidden" name="utm_source"><input type="hidden" name="utm_medium"><input type="hidden" name="utm_campaign"><input type="hidden" name="utm_content"><input type="hidden" name="landing_page"><input type="hidden" name="referrer">
<input type="file" name="photo1" accept="image/*" hidden><input type="file" name="photo2" accept="image/*" hidden><input type="file" name="photo3" accept="image/*" hidden>
<div class="qprog" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
<div class="qmeta"><span id="q-count" aria-live="polite">Step 1 of 5</span><span id="q-name">Service</span></div>

<fieldset class="q-step" data-step="1" data-name="Service"><legend>What can we help you with?</legend><p class="hint">Choose the option that fits best.</p>
<div class="opts" role="radiogroup">{opts}</div>
<div class="callout" id="emerg-callout" hidden><strong>For an active leak or emergency, call now:</strong><span style="font:800 1.4rem/1 var(--f-display);user-select:all"{VP}>{PHONE}</span><a class="btn sm" href="{TEL}" data-track="emergency_call_click" data-loc="quote-form" style="justify-self:start">{ic('phone')}Call Team ASAP</a><span>You can still send this form for a non-urgent follow-up.</span></div>
<p class="err" id="err-service"></p>
</fieldset>

<fieldset class="q-step" data-step="2" data-name="Details" hidden><legend>Describe the problem or project</legend><p class="hint">A few sentences is plenty. Where is it, what's happening, and since when?</p>
<div class="field"><label for="q-desc">Description</label><textarea id="q-desc" name="description" required minlength="10" maxlength="2000" placeholder="Example: Water is dripping from the kitchen ceiling under the upstairs bathroom. Started yesterday."></textarea><p class="err"></p></div>
</fieldset>

<fieldset class="q-step" data-step="3" data-name="Location" hidden><legend>Where is the job?</legend><p class="hint">We use this to confirm the job is in our service area.</p>
<div class="grid-2"><div class="field"><label for="q-zip">ZIP code</label><input id="q-zip" name="zip" inputmode="numeric" autocomplete="postal-code" required pattern="[0-9]{{5}}" maxlength="5" placeholder="10801"><p class="err"></p></div>
<div class="field"><label for="q-city">City or town</label><input id="q-city" name="city" autocomplete="address-level2" required placeholder="New Rochelle"><p class="err"></p></div></div>
</fieldset>

<fieldset class="q-step" data-step="4" data-name="Photos" hidden><legend>Add photos <span class="opt-l" style="font:500 1rem var(--f-body)">(optional)</span></legend><p class="hint">Photos help us understand the job before we arrive. Up to 3 images.</p>
<label class="drop" id="drop" for="q-pick">{ic('camera')}<b>Tap to add photos</b><small>or drag them here &middot; JPG, PNG or HEIC &middot; large photos are resized automatically</small></label>
<input type="file" id="q-pick" accept="image/*" multiple class="sr-only">
<div class="thumbs" id="thumbs"></div><p class="err" id="err-photos"></p>
</fieldset>

<fieldset class="q-step" data-step="5" data-name="Contact" hidden><legend>How can we reach you?</legend>
<div class="grid-2"><div class="field"><label for="q-nm">Name</label><input id="q-nm" name="name" autocomplete="name" required><p class="err"></p></div>
<div class="field"><label for="q-ph">Phone</label><input id="q-ph" name="phone" type="tel" autocomplete="tel" required placeholder="(914) 555-0123"><p class="err"></p></div></div>
<div class="field"><label for="q-em">Email <span class="opt-l">(optional)</span></label><input id="q-em" name="email" type="email" autocomplete="email"><p class="err"></p></div>
<div class="field"><span class="lbl" id="pref-l">Preferred contact method</span><div class="chips" role="radiogroup" aria-labelledby="pref-l">
<div class="chip"><input type="radio" name="contact_method" id="cm-call" value="Phone call" checked><label for="cm-call">Phone call</label></div>
<div class="chip"><input type="radio" name="contact_method" id="cm-text" value="Text message"><label for="cm-text">Text message</label></div>
<div class="chip"><input type="radio" name="contact_method" id="cm-email" value="Email"><label for="cm-email">Email</label></div></div></div>
<div class="field"><label for="q-win">Preferred appointment window <span class="opt-l">(optional)</span></label><select id="q-win" name="appointment_window"><option value="">No preference</option><option>Weekday morning</option><option>Weekday afternoon</option><option>Weekday evening</option><option>Weekend</option><option>As soon as possible</option></select></div>
<label class="consent"><input type="checkbox" name="consent" value="yes" required id="q-consent"><span>I agree that Team ASAP may contact me about this request by phone, text or email. See our <a href="{href('privacy')}">privacy notice</a>.</span></label><p class="err" id="err-consent"></p>
</fieldset>

<div class="q-step q-done" data-step="done" hidden tabindex="-1"></div>

<div class="qnav" id="qnav"><button type="button" class="btn ghost" id="q-back" hidden>Back</button><span class="spacer"></span><button type="button" class="btn" id="q-next">Continue{ic('arrow')}</button><button type="submit" class="btn" id="q-submit" hidden>Send request{ic('arrow')}</button></div>
<p class="err" id="err-submit" role="alert"></p>
</form>
</div>
<aside class="side">
<div class="side-card dark"><span class="eyebrow" style="color:#7cc8ff">{'Emergency &middot; 24/7' if e247 else 'Call us'}</span><h3>Plumbing emergency?</h3><p>Call now. Don't wait on a form.</p><span class="num"{VP}>{PHONE}</span><a class="btn white" href="{TEL}" data-track="emergency_call_click" data-loc="contact-side">{ic('phone')}Call Team ASAP</a></div>
<div class="side-card"><h3>Contact</h3><p>Phone: <a href="{TEL}" data-track="call_click" data-loc="contact-side"{VP}>{PHONE}</a></p>{email_line}<p>Based in {e(SITE['city'])}, NY, serving nearby Westchester communities.</p></div>
<div class="side-card"><h3>What happens next</h3><ul class="checks" style="font-size:.95rem"><li>{ic('check')}<span>Team ASAP reviews your request and photos.</span></li><li>{ic('check')}<span>We contact you the way you prefer to discuss the job.</span></li><li>{ic('check')}<span>If a visit is needed, we schedule a time that works for you.</span></li></ul></div>
</aside>
</div></section>'''
    return page("contact", "Contact & Request a Quote | Team ASAP, New Rochelle NY",
                "Request a plumbing or home improvement quote from Team ASAP in New Rochelle, NY. Describe the job, add photos, or call for emergencies.",
                body, [crumbs_ld(trail), business_ld()])

def build_privacy():
    trail = [("Home", ""), ("Privacy", "privacy")]
    body = f'''<section class="section"><div class="wrap"><div class="prose">{crumbs_html(trail)}<h1 style="font-size:2.4rem">Privacy notice</h1>
<p data-verify="Have the owner review this notice; consider legal review">Last updated {date.today():%B %Y}.</p>
<h2>What we collect</h2><p>When you request a quote, we collect the information you enter: your name, phone number, email address if given, ZIP code and town, a description of the job, your contact preferences, and any photos you attach. We also record which page you started from and any campaign tags in the link you used, so we know how customers find us.</p>
<h2>How we use it</h2><p>We use this information only to respond to your request, schedule and carry out work, and keep records of jobs. We do not sell your information.</p>
<h2>Service providers</h2><p>Form submissions are processed and stored by our website host, Netlify, Inc., and delivered to us by email. If analytics is enabled, Google Analytics measures website visits only after you accept analytics cookies.</p>
<h2>Your choices</h2><p>To ask what information we hold about you, or to have it deleted, call us at {PHONE}.</p></div></div></section>'''
    return page("privacy", "Privacy Notice | Team ASAP", "How Team ASAP Home Improvement handles information submitted through this website.", body, [crumbs_ld(trail)])

def build_404():
    body = f'''<section class="section"><div class="wrap" style="display:grid;gap:18px;max-width:640px"><span class="eyebrow">Page not found</span><h1>We couldn't find that page.</h1><p class="lead">It may have moved. Try one of these instead, or call {PHONE}.</p><div class="btn-row"><a class="btn" href="{href('')}">Go to the homepage</a><a class="btn ghost" href="{href('contact')}">{quote_label}</a></div></div></section>'''
    return page("404", "Page not found | Team ASAP", "Page not found.", body)

# ---------- write ----------
def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    files = {"index": build_home(), "our-work": build_work(), "about": build_about(), "contact": build_contact(), "privacy": build_privacy(), "404": build_404()}
    for s in SVCS:
        files[s["slug"]] = build_service(s)
    for k, html_ in files.items():
        (OUT / f"{k}.html").write_text(html_)
    if not PREVIEW:
        base = SITE["siteUrl"].rstrip("/")
        urls = [k for k in files if k not in ("404",)]
        sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
            f"  <url><loc>{canon(u)}</loc><lastmod>{date.today().isoformat()}</lastmod></url>\n" for u in urls) + "</urlset>\n"
        (OUT / "sitemap.xml").write_text(sm)
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")
    print(f"Built {len(files)} pages into {OUT}")

if __name__ == "__main__":
    main()
