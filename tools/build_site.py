#!/usr/bin/env python3
"""Build The Great Brandomizer site.

Reads the machine from src/app.html, theme data from the THEMES array inside it,
theme guide copy from src/theme-guides.json and pages from src/pages/*.html,
then writes the static site into the repo root.

Run from the repo root:  python3 tools/build_site.py
Needs Node.js (to read the theme data) and Pillow (for the social image).
"""
import datetime, html, json, os, re, subprocess, sys

# ---------------------------------------------------------------- settings
# The public address of the site, with no trailing slash. Change this when the
# site moves to its own domain, then run the build again.
SITE_URL = "https://harrisongreener.github.io/TheGreatBrandomizer"

# Google AdSense. Leave as None until AdSense gives you a publisher ID.
# ADSENSE_CLIENT looks like "ca-pub-1234567890123456".
# ADSENSE_SLOT is the ID of one responsive display ad unit (digits only). With a
# client but no slot, only the AdSense script is added (for site verification
# and Auto ads).
ADSENSE_CLIENT = None
ADSENSE_SLOT = None

SITE_NAME = "The Great Brandomizer"
AUTHOR = "Harrison Greener"
AUTHOR_URL = "https://harrisongreener.co.uk/"
UPDATED = "24 November 2026"
TODAY = datetime.date(2026, 11, 24).isoformat()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
esc = lambda s: html.escape(str(s), quote=True)


# ---------------------------------------------------------------- data
def load_themes():
    app = open(os.path.join(SRC, "app.html"), encoding="utf-8").read()
    a = app.index("const THEMES = [")
    b = app.index("THEMES.sort(", a)
    b = app.index("\n", app.index("}", b))
    js = app[a:b] + "\nprocess.stdout.write(JSON.stringify({THEMES,CATS}));"
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    return app, data["THEMES"], data["CATS"]


def rgb(h):
    n = int(h[1:], 16)
    return (n >> 16) & 255, (n >> 8) & 255, n & 255


def lum(h):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (c(v) for v in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def roles(colors):
    by = sorted(colors, key=lum)
    out, n = {}, 1
    for c in colors:
        if c == by[0]:
            out[c] = "Ink"
        elif c == by[-1]:
            out[c] = "Paper"
        else:
            out[c] = f"Colour {n}"
            n += 1
    return out


def font_url(families):
    fams = []
    for f in families:
        if f not in fams:
            fams.append(f)
    q = "&".join("family=" + f.replace(" ", "+") for f in fams)
    return f"https://fonts.googleapis.com/css2?{q}&display=swap"


def specimen(f):
    return "https://fonts.google.com/specimen/" + f.replace(" ", "+")


# ---------------------------------------------------------------- page shell
UI_FONTS = "https://fonts.googleapis.com/css2?family=Bungee&family=VT323&family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@600;700&display=swap"


def adsense_head():
    if not ADSENSE_CLIENT:
        return ""
    return (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" '
            'crossorigin="anonymous"></script>\n')


def ad_unit():
    if not (ADSENSE_CLIENT and ADSENSE_SLOT):
        return ""
    return (f'<aside class="ad" aria-label="Advertisement"><span class="ad-label">Advertisement</span>'
            f'<ins class="adsbygoogle" style="display:block" data-ad-client="{ADSENSE_CLIENT}" data-ad-slot="{ADSENSE_SLOT}" '
            'data-ad-format="auto" data-full-width-responsive="true"></ins>'
            '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></aside>\n')


def head(path, title, desc, depth, extra_fonts=None, jsonld=None, og_type="website"):
    rel = "../" * depth
    url = SITE_URL + "/" + path
    ld = ""
    for block in (jsonld or []):
        ld += '<script type="application/ld+json">' + json.dumps(block, ensure_ascii=False) + "</script>\n"
    fonts = f'<link rel="stylesheet" href="{esc(extra_fonts)}">\n' if extra_fonts else ""
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(url)}">
<meta name="theme-color" content="#b4231c">
<link rel="icon" href="{rel}favicon.svg" type="image/svg+xml">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{UI_FONTS}">
{fonts}<link rel="stylesheet" href="{rel}site.css">
{adsense_head()}{ld}</head>
<body>
{header_html(rel)}"""


def header_html(rel):
    return f"""<header class="bar">
  <div class="wrap bar-in">
    <a class="logo" href="{rel}"><span class="logo-the">The Great </span><span>Brandomizer</span></a>
    <nav class="nav" aria-label="Main">
      <a href="{rel}themes/">Themes</a>
      <a href="{rel}guides/">Guides</a>
      <a class="nav-about" href="{rel}about/">About</a>
      <a class="nav-cta" href="{rel}spin/">Spin</a>
    </nav>
  </div>
</header>
"""


def foot(depth):
    rel = "../" * depth
    return f"""<footer class="foot">
  <div class="wrap foot-in">
    <p class="foot-logo">The Great Brandomizer</p>
    <p>A free colour palette and font pairing generator for brand identities. Made by <a href="{AUTHOR_URL}" rel="author">{AUTHOR}</a>.</p>
    <nav class="foot-nav" aria-label="Footer">
      <a href="{rel}">Home</a><a href="{rel}spin/">Spin</a><a href="{rel}themes/">Themes</a><a href="{rel}guides/">Guides</a><a href="{rel}about/">About</a><a href="{rel}privacy/">Privacy</a>
    </nav>
    <p class="small">Fonts are from Google Fonts. &copy; 2026 {AUTHOR}.</p>
  </div>
</footer>
</body>
</html>
"""


def crumbs(items, depth):
    rel = "../" * depth
    parts = [f'<a href="{rel}">Home</a>']
    for name, href in items:
        parts.append(f'<a href="{rel}{href}">{esc(name)}</a>' if href is not None else f'<span aria-current="page">{esc(name)}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + " / ".join(parts) + "</nav>"


def crumb_ld(items):
    lst = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"}]
    for i, (name, href) in enumerate(items, start=2):
        e = {"@type": "ListItem", "position": i, "name": name}
        if href is not None:
            e["item"] = SITE_URL + "/" + href
        lst.append(e)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": lst}


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full) or ROOT, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------- pages
# header styles for the machine page, which doesn't load site.css
SPIN_HEADER_CSS = """<style>
:root{--hdr:52px}
html,body{margin:0}img{max-width:100%}
.bar{position:fixed;top:0;left:0;right:0;z-index:30;height:calc(var(--hdr) + env(safe-area-inset-top,0px));padding-top:env(safe-area-inset-top,0px);
  background:#b4231c;box-shadow:0 2px 0 #86160f;box-sizing:border-box}
.bar .wrap{max-width:1040px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));height:var(--hdr)}
.bar-in{display:flex;align-items:center;justify-content:space-between;gap:12px}
.bar .logo{font-family:"Bungee",Impact,system-ui,sans-serif;font-size:17px;color:#fff3d8;text-decoration:none;white-space:nowrap}
.bar .logo span:last-child{color:#ffd977}
.bar .nav{display:flex;align-items:center;gap:16px;font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-weight:700;font-size:14px;letter-spacing:.14em;text-transform:uppercase}
.bar .nav a{color:#fff3d8;text-decoration:none}
.bar .nav a:hover{color:#ffd977}
.bar .nav .nav-cta{background:#ffd977;color:#3a1500;border-radius:5px;padding:4px 10px}
.bar .nav a[aria-current]{color:#ffd977}
.bar .nav .nav-cta[aria-current]{background:#fff3b0;color:#3a1500}
.loader{top:var(--hdr)!important}
@media (max-width:520px){.bar .logo-the,.bar .nav-about{display:none}.bar .nav{gap:12px;font-size:13px}}
</style>
"""


def build_spin(app, themes):
    path = "spin/"
    body = app
    body = re.sub(r"<title>.*?</title>\n", "", body, count=1)
    body = body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
    body = body.replace("  <!--SITE-NAV-->\n", "")
    hdr = header_html("../").replace('class="nav-cta" href="../spin/"', 'class="nav-cta" href="../spin/" aria-current="page"')
    title = "Spin the Brandomizer: Colour Palette and Font Pairing Generator"
    desc = (f"Pull the handle on a 3D vintage fruit machine to spin brand colour palettes and Google Fonts pairings "
            f"from {len(themes)} design themes. Hold what you like, check WCAG contrast and download your brand card. Free.")
    ld = app_ld(desc)
    page = f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE_URL}/{path}">
<meta name="theme-color" content="#b4231c">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE_URL}/{path}">
<meta property="og:image" content="{SITE_URL}/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
{adsense_head()}<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{SPIN_HEADER_CSS}</head>
<body>
{hdr}{body}
</body>
</html>
"""
    write(path + "index.html", page)


def app_ld(desc):
    return {
        "@context": "https://schema.org", "@type": "WebApplication", "name": SITE_NAME, "url": SITE_URL + "/spin/",
        "description": desc, "applicationCategory": "DesignApplication", "operatingSystem": "Any (web browser)",
        "browserRequirements": "Requires WebGL", "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "GBP"},
        "image": SITE_URL + "/og-image.png",
        "creator": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
    }


def build_home(themes, cats, guides):
    groups = ""
    for c, _ in cats:
        items = "".join(f'<li><a class="tlink" href="themes/{t["id"]}/">{swatch_strip(t["house"]["colors"])}<span>{esc(t["name"])}</span></a></li>'
                        for t in themes if t["cat"] == c)
        groups += f'<h3>{c}</h3><ul class="tgrid">{items}</ul>\n'
    gl = "".join(f'<li><a class="glink" href="{g["path"]}"><span class="g-t">{esc(g["h1"])}</span><span class="g-d">{esc(g["description"])}</span></a></li>' for g in guides)
    title = "The Great Brandomizer: Free Colour Palette and Font Pairing Generator"
    desc = (f"Spin brand colour palettes and Google Fonts pairings on a 3D vintage fruit machine. {len(themes)} design themes, "
            "from Bauhaus and Art Deco to Y2K and Acid Rave, with contrast checks and a downloadable brand card. Free.")
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": SITE_URL + "/", "description": desc},
          app_ld(desc)]
    page = head("", title, desc, 0, None, ld).replace(f'<link rel="canonical" href="{SITE_URL}/">',
        f'<link rel="canonical" href="{SITE_URL}/">\n<script>if(/^#theme-[a-z0-9-]+$/.test(location.hash))location.replace("spin/"+location.hash);</script>') + f"""<section class="hero">
  <div class="wrap hero-in">
    <div class="hero-copy">
      <p class="kicker">Free colour palette and font pairing generator</p>
      <h1>The Great Brandomizer</h1>
      <p class="lede">Pick a design style, pull the handle of a vintage fruit machine, and spin a brand colour palette and Google Fonts pairing to match. Hold what you like, check the contrast, then cash out your brand card.</p>
      <p class="hero-cta"><a class="btn btn-big" href="spin/">Spin</a> <a class="btn btn-ghost" href="themes/">Browse {len(themes)} themes</a></p>
    </div>
    <a class="hero-img" href="spin/" aria-label="Spin the Brandomizer"><img src="assets/hero-machine.png" width="390" height="470" alt="The Great Brandomizer fruit machine with colour reels, font reels and a chrome handle"></a>
  </div>
</section>
<main class="wrap page">
<section aria-labelledby="how">
  <h2 id="how">How it works</h2>
  <ol class="steps">
    <li><strong>Pick a theme.</strong> Choose from {len(themes)} styles in the Themes menu or on the machine's chart.</li>
    <li><strong>Pull the handle.</strong> Five to seven colour reels, a headline font and a body font spin and land.</li>
    <li><strong>Hold what you like.</strong> Press HOLD under any reel to keep it, then spin again to change the rest.</li>
    <li><strong>Cash out.</strong> Get a brand card with HEX codes, a contrast check, CSS variables, a font embed and a PNG download.</li>
  </ol>
  <p><a class="btn" href="spin/">Spin the Brandomizer</a></p>
</section>
<section aria-labelledby="styles">
  <h2 id="styles">Start from a style</h2>
  <p>Every theme has its own colour rules and its own set of Google Fonts. Open one to see its palette, fonts and tips, or spin straight from there.</p>
  {groups}
</section>
{ad_unit()}<section aria-labelledby="g">
  <h2 id="g">Guides</h2>
  <ul class="glist">{gl}</ul>
</section>
</main>
""" + foot(0)
    write("index.html", page)


def swatch_strip(colors):
    return '<span class="strip">' + "".join(f'<span style="background:{c}"></span>' for c in colors) + "</span>"


def build_theme_pages(themes, cats, guides):
    by_cat = {c: [t for t in themes if t["cat"] == c] for c, _ in cats}
    for t in themes:
        g = guides[t["id"]]
        path = f"themes/{t['id']}/"
        house = t["house"]
        cols = house["colors"]
        rl = roles(cols)
        fams = [house["head"], house["body"]] + t["heads"] + t["bodies"]
        pairs = []
        for i, a in enumerate(cols):
            for b in cols[i + 1:]:
                r = ratio(a, b)
                bg, fg = (a, b) if lum(a) > lum(b) else (b, a)
                pairs.append((r, bg, fg))
        pairs.sort(reverse=True)
        good = [p for p in pairs if p[0] >= 3][:8]
        aaa = sum(1 for p in pairs if p[0] >= 7)
        aa = sum(1 for p in pairs if p[0] >= 4.5)
        name = t["name"]
        title = f"{name} Colour Palette and Fonts: {house['name']} | The Great Brandomizer"
        desc = (f"{name} colour palette with HEX codes, plus {name} Google Fonts pairings like "
                f"{house['head']} and {house['body']}. Spin your own {name} brand palette for free.")
        sw = "".join(
            f'<li class="sw"><span class="chip" style="background:{c}"></span>'
            f'<span class="sw-role">{rl[c]}</span><span class="hex">{c.upper()}</span>'
            f'<span class="rgbv">RGB {" ".join(map(str, rgb(c)))}</span></li>' for c in cols)
        heads = "".join(f'<li><span class="fs" style="font-family:\'{esc(f)}\',serif">{esc(name)}</span>'
                        f'<a href="{specimen(f)}" rel="noopener" target="_blank">{esc(f)}</a></li>' for f in t["heads"])
        bodies = "".join(f'<li><span class="fs fs-body" style="font-family:\'{esc(f)}\',sans-serif">The quick brown fox jumps over the lazy dog.</span>'
                         f'<a href="{specimen(f)}" rel="noopener" target="_blank">{esc(f)}</a></li>' for f in t["bodies"])
        crow = "".join(
            f'<li class="ct" style="background:{bg};color:{fg}"><span class="ct-aa">Aa</span>'
            f'<span class="ct-meta">{r:.2f}:1 <b>{"AAA" if r >= 7 else "AA" if r >= 4.5 else "AA large"}</b></span>'
            f'<span class="ct-hex">{fg.upper()} on {bg.upper()}</span></li>' for r, bg, fg in good)
        rel_list = [x for x in by_cat[t["cat"]] if x["id"] != t["id"]]
        related = "".join(f'<li><a class="tlink" href="../{x["id"]}/">{swatch_strip(x["house"]["colors"])}<span>{esc(x["name"])}</span></a></li>' for x in rel_list)
        tips = "".join(f"<li>{esc(x)}</li>" for x in g["tips"])
        dark, light = sorted(cols, key=lum)[0], sorted(cols, key=lum)[-1]
        accent = next((c for c in cols if c not in (dark, light) and ratio(c, light) >= 3), cols[1])
        lockup_fg = light if ratio(light, accent) >= ratio(dark, accent) else dark
        ld = [crumb_ld([("Themes", "themes/"), (name, None)]),
              {"@context": "https://schema.org", "@type": "Article", "headline": f"{name} colour palette and font pairings",
               "description": desc, "url": SITE_URL + "/" + path, "image": SITE_URL + "/og-image.png",
               "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
               "publisher": {"@type": "Person", "name": AUTHOR}, "datePublished": TODAY, "dateModified": TODAY}]
        page = head(path, title, desc, 2, font_url(fams), ld, "article") + f"""<main class="wrap page">
{crumbs([("Themes", "themes/"), (name, None)], 2)}
<p class="kicker">{esc(t["cat"])} theme</p>
<h1>{esc(name)} colour palette and fonts</h1>
<p class="lede">{esc(g["intro"])}</p>
<p><a class="btn" href="../../spin/#theme-{t["id"]}">Spin the {esc(name)} reels</a></p>

<section class="card" aria-labelledby="house">
  <div class="card-top"><span>Brandomizer house pick</span><span>{esc(name)}</span></div>
  <div class="lockup" style="background:{dark};color:{light}">
    <p class="lk-name" style="font-family:'{esc(house["head"])}',serif">{esc(house["name"])}</p>
    <p class="lk-tag" style="font-family:'{esc(house["body"])}',sans-serif;color:{light}">{esc(t["tag"])}</p>
    <span class="lk-btn" style="background:{accent};color:{lockup_fg};font-family:'{esc(house["body"])}',sans-serif">{esc(name)} brand</span>
  </div>
  <h2 id="house">The {esc(house["name"])} palette</h2>
  <ul class="swatches">{sw}</ul>
  <p class="note">Pairing: <strong>{esc(house["head"])}</strong> for headlines with <strong>{esc(house["body"])}</strong> for body text.</p>
</section>

{ad_unit()}
<section aria-labelledby="fonts">
  <h2 id="fonts">{esc(name)} fonts on Google Fonts</h2>
  <p>The headline reels spin through these {len(t["heads"])} display faces. Each one sets the tone, so pick the one that suits your brand's voice.</p>
  <ul class="fonts">{heads}</ul>
  <h3>Body fonts</h3>
  <p>These are the body reel's options. They're chosen to stay readable in paragraphs next to {esc(name)} headlines.</p>
  <ul class="fonts">{bodies}</ul>
</section>

<section aria-labelledby="contrast">
  <h2 id="contrast">Contrast check</h2>
  <p>Of the {len(pairs)} colour pairs in this palette, {aaa} pass WCAG AAA and {aa} pass AA for body text. These are the strongest pairs for text:</p>
  <ul class="contrast">{crow}</ul>
  <p class="note">AA needs 4.5:1 for body text and 3:1 for large text. AAA needs 7:1. <a href="../../guides/colour-contrast-for-designers/">How colour contrast works</a>.</p>
</section>

<section aria-labelledby="use">
  <h2 id="use">Where the {esc(name)} look works</h2>
  <p>{esc(g["use"])}</p>
  <h3>Tips for using it</h3>
  <ul class="tips">{tips}</ul>
</section>

<section class="cta-band">
  <h2>Make your own {esc(name)} palette</h2>
  <p>Every spin gives you a new {esc(name)} palette and font pairing. Hold the colours you like, re-spin the rest, and cash out a brand card with all the codes.</p>
  <p><a class="btn" href="../../spin/#theme-{t["id"]}">Spin the {esc(name)} reels</a></p>
</section>

{ad_unit()}
<section aria-labelledby="more">
  <h2 id="more">More {esc(t["cat"].lower())} themes</h2>
  <ul class="tgrid">{related}</ul>
  <p><a href="../">See all {len(themes)} themes</a></p>
</section>
</main>
""" + foot(2)
        write(path + "index.html", page)


def build_themes_index(themes, cats):
    path = "themes/"
    intros = {
        "Eras": "Palettes and type from a particular decade or period, from Victorian woodtype to the turn of the millennium.",
        "Movements": "Art and design movements that changed how posters, books and brands look.",
        "Styles": "Present-day brand looks, from calm and minimal to loud and luxurious.",
        "Scenes": "Subcultures and internet aesthetics with a strong visual identity.",
    }
    sections = ""
    for c, ids in cats:
        items = [t for t in themes if t["cat"] == c]
        cards = "".join(
            f'<li><a class="tcard" href="{t["id"]}/">{swatch_strip(t["house"]["colors"])}'
            f'<span class="tc-name" style="font-family:\'{esc(t["house"]["head"])}\',serif">{esc(t["name"])}</span>'
            f'<span class="tc-tag">{esc(t["tag"])}</span>'
            f'<span class="tc-fonts">{esc(t["house"]["head"])} + {esc(t["house"]["body"])}</span></a></li>' for t in items)
        sections += f'<section aria-labelledby="c-{c.lower()}"><h2 id="c-{c.lower()}">{c}</h2><p>{intros[c]}</p><ul class="tcards">{cards}</ul></section>\n'
    title = f"{len(themes)} Design Themes: Colour Palettes and Google Fonts Pairings | The Great Brandomizer"
    desc = (f"Browse {len(themes)} design styles, from Bauhaus and Art Deco to Y2K and Cyberpunk, each with a colour palette, "
            "HEX codes and Google Fonts pairings you can spin into your own brand.")
    ld = [crumb_ld([("Themes", None)]),
          {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Design themes", "url": SITE_URL + "/" + path,
           "description": desc,
           "hasPart": [{"@type": "Article", "name": t["name"] + " colour palette and fonts", "url": f"{SITE_URL}/themes/{t['id']}/"} for t in themes]}]
    page = head(path, title, desc, 1, font_url([t["house"]["head"] for t in themes]), ld) + f"""<main class="wrap page">
{crumbs([("Themes", None)], 1)}
<p class="kicker">Themes</p>
<h1>{len(themes)} design themes, each with its own palette and fonts</h1>
<p class="lede">Every theme on the Brandomizer has its own colour rules and its own set of Google Fonts, so a spin always stays inside a look that works. Open a theme to see its house palette, HEX codes, font options and contrast check, or jump straight into the machine.</p>
<p><a class="btn" href="../spin/">Spin the Brandomizer</a></p>
{ad_unit()}{sections}</main>
""" + foot(1)
    write(path + "index.html", page)


def read_page(fn):
    raw = open(os.path.join(SRC, "pages", fn), encoding="utf-8").read()
    m = re.match(r"<!--\n(.*?)\n-->\n", raw, re.S)
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines())
    return meta, raw[m.end():]


def build_content_pages():
    guides = []
    for fn in sorted(os.listdir(os.path.join(SRC, "pages"))):
        meta, body = read_page(fn)
        path = meta["path"]
        depth = path.count("/")
        is_guide = path.startswith("guides/")
        trail = [("Guides", "guides/"), (meta["h1"], None)] if is_guide else [(meta["h1"], None)]
        ld = [crumb_ld(trail)]
        if is_guide:
            guides.append(meta)
            ld.append({"@context": "https://schema.org", "@type": "Article", "headline": meta["h1"], "description": meta["description"],
                       "url": SITE_URL + "/" + path, "image": SITE_URL + "/og-image.png",
                       "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL},
                       "publisher": {"@type": "Person", "name": AUTHOR}, "datePublished": TODAY, "dateModified": TODAY})
        if meta.get("faq"):
            qa = re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", body, re.S)
            ld.append({"@context": "https://schema.org", "@type": "FAQPage",
                       "mainEntity": [{"@type": "Question", "name": html.unescape(q),
                                       "acceptedAnswer": {"@type": "Answer", "text": html.unescape(re.sub("<.*?>", "", a))}} for q, a in qa]})
        # an ad after the third section heading of a guide
        if is_guide and ad_unit():
            parts = body.split("<h2>")
            if len(parts) > 3:
                body = "<h2>".join(parts[:3]) + ad_unit() + "<h2>" + "<h2>".join(parts[3:])
        page = head(path, meta["title"], meta["description"], depth, None, ld, "article" if is_guide else "website") + f"""<main class="wrap page prose">
{crumbs(trail, depth)}
<p class="kicker">{esc(meta.get("kicker", ""))}</p>
<h1>{esc(meta["h1"])}</h1>
{body}
{ad_unit() if is_guide else ""}</main>
""" + foot(depth)
        write(path + "index.html", page)
    # guides index
    path = "guides/"
    items = "".join(f'<li><a class="glink" href="../{g["path"]}"><span class="g-t">{esc(g["h1"])}</span><span class="g-d">{esc(g["description"])}</span></a></li>' for g in guides)
    title = "Brand Design Guides: Colour Palettes, Font Pairing and Contrast | The Great Brandomizer"
    desc = "Short, practical guides to building a brand: choosing a colour palette, pairing Google Fonts and checking colour contrast."
    page = head(path, title, desc, 1, None, [crumb_ld([("Guides", None)])]) + f"""<main class="wrap page">
{crumbs([("Guides", None)], 1)}
<p class="kicker">Guides</p>
<h1>Guides to colour and type for brands</h1>
<p class="lede">Short, practical reads on the decisions behind every spin of the Brandomizer.</p>
<ul class="glist">{items}</ul>
</main>
""" + foot(1)
    write(path + "index.html", page)
    return guides


def build_privacy():
    path = "privacy/"
    ads = ""
    if ADSENSE_CLIENT:
        ads = """<h2>Advertising</h2>
<p>This site shows adverts from Google AdSense to help cover its running costs. Google and its partners may use cookies and similar technologies to show adverts based on your visits to this and other websites, and to measure how adverts perform.</p>
<p>If you're in the UK, the European Economic Area or Switzerland, you'll be asked whether you consent to personalised adverts before any are shown, and you can change your choice at any time from the privacy link Google shows on the page. If you don't consent, you may still see non-personalised adverts.</p>
<p>You can read <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">how Google uses information from sites that use its services</a> and manage personalised adverts in <a href="https://myadcenter.google.com/" rel="noopener">My Ad Center</a>.</p>
"""
    body = f"""<p class="lede">The Great Brandomizer is a free tool run by {AUTHOR}. This page explains what information is used when you visit it.</p>
<p class="note">Last updated {UPDATED}.</p>
<h2>What stays on your device</h2>
<p>Your saved spins and your sound setting are stored in your browser's local storage on your own device. They're never sent to me or to any server, and clearing your browser data deletes them.</p>
<p>There are no accounts, and nothing you type into the machine, such as your brand name, leaves your browser.</p>
<h2>Services the site uses</h2>
<ul>
  <li><strong>GitHub Pages</strong> hosts the site. GitHub may log technical information such as your IP address to keep the service running and secure. See <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="noopener">GitHub's privacy statement</a>.</li>
  <li><strong>Google Fonts</strong> provides the typefaces. Your browser downloads them from Google, which receives your IP address. See <a href="https://developers.google.com/fonts/faq/privacy" rel="noopener">Google Fonts' privacy FAQ</a>.</li>
  <li><strong>jsDelivr</strong> serves the three.js 3D engine that draws the machine. See <a href="https://www.jsdelivr.com/terms/privacy-policy-jsdelivr-net" rel="noopener">jsDelivr's privacy policy</a>.</li>
</ul>
{ads}<h2>Your rights</h2>
<p>Under UK data protection law you can ask what personal information is held about you and ask for it to be corrected or deleted. As the site itself doesn't collect personal information, most requests will be about the services above. You can contact me through <a href="{AUTHOR_URL}work-with-me/">my website</a>.</p>
"""
    title = "Privacy | The Great Brandomizer"
    desc = "How The Great Brandomizer handles your information: what stays on your device, the services the site uses and your choices."
    page = head(path, title, desc, 1, None, [crumb_ld([("Privacy", None)])]) + f"""<main class="wrap page prose">
{crumbs([("Privacy", None)], 1)}
<p class="kicker">Privacy</p>
<h1>Privacy</h1>
{body}</main>
""" + foot(1)
    write(path + "index.html", page)


def build_404():
    page = head("404.html", "Page not found | The Great Brandomizer", "This page doesn't exist.", 0).replace('href="site.css"', f'href="{SITE_URL}/site.css"')
    page = re.sub(r'href="(?!https?:|#)([^"]*)"', lambda m: f'href="{SITE_URL}/{m.group(1)}"', page)
    page = page.replace('<link rel="canonical"', '<meta name="robots" content="noindex">\n<link rel="canonical"')
    page += f"""<main class="wrap page">
<p class="kicker">404</p>
<h1>No jackpot here</h1>
<p class="lede">That page doesn't exist. The reels are still spinning on the home page.</p>
<p><a class="btn" href="{SITE_URL}/spin/">Spin the Brandomizer</a> <a class="btn btn-ghost" href="{SITE_URL}/themes/">Browse themes</a></p>
</main>
""" + foot(0).replace('href="', f'href="{SITE_URL}/').replace(f'href="{SITE_URL}/https://', 'href="https://')
    write("404.html", page)


def build_meta(themes, guides):
    urls = ["", "spin/", "themes/", "guides/", "about/", "privacy/"] + [f"themes/{t['id']}/" for t in themes] + [g["path"] for g in guides]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url><loc>{SITE_URL}/{u}</loc><lastmod>{TODAY}</lastmod></url>\n"
    write("sitemap.xml", xml + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    if ADSENSE_CLIENT:
        write("ads.txt", f"google.com, {ADSENSE_CLIENT.replace('ca-', '')}, DIRECT, f08c47fec0942fa0\n")
    elif os.path.exists(os.path.join(ROOT, "ads.txt")):
        os.remove(os.path.join(ROOT, "ads.txt"))
    write(".nojekyll", "")


def main():
    app, themes, cats = load_themes()
    guides_copy = json.load(open(os.path.join(SRC, "theme-guides.json"), encoding="utf-8"))
    missing = [t["id"] for t in themes if t["id"] not in guides_copy]
    if missing:
        sys.exit("Missing guide copy for: " + ", ".join(missing))
    build_spin(app, themes)
    build_theme_pages(themes, cats, guides_copy)
    build_themes_index(themes, cats)
    guides = build_content_pages()
    build_home(themes, cats, guides)
    build_privacy()
    build_404()
    build_meta(themes, guides)
    print(f"Built {len(themes)} theme pages, {len(guides)} guides, for {SITE_URL}")


if __name__ == "__main__":
    main()
