#!/usr/bin/env python3
"""Génère le site statique Maison Truffe dans ../public — python3 src/build.py"""
import json, html, shutil, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "public"
SITE = "https://maisontruffe.fr"
EMAIL = "maisontruffe.boutique@outlook.fr"
BRAND = "Maison Truffe"
IMG_BASE = "https://latruffieredemarcel.com/cdn/shop/files/"

# ------------------------------------------------------------ réglages commerciaux
SHIP_PRICE = 6.90          # frais de port
FREE_SHIP = 59             # livraison offerte à partir de
PACKAGING_G = 90         # carton S35 vide (31 x 23 x 11 cm)
PARCEL = {"name": "S35", "length_cm": 31, "width_cm": 23, "height_cm": 11, "weight_g": 90}
GUARANTEE_TITLE = "Colis protégé"
GUARANTEE_TEXT = ("Un pot cassé ou un produit abîmé à la réception ? Envoyez-nous une photo sous 48 h : "
                  "on vous le remplace ou on vous le rembourse.")
# Offres « lot » : n articles du même groupe (mélange possible) pour un prix fixe
PROMOS = {
    "pot3": {"n": 3, "price": 40.0, "label": "Offre 3 produits au choix", "badge": "3 pour 40 €",
             "text": "Tous nos produits à 15 € (pots, petites huiles 100 ml, sel, petit condiment…) : 40 € les 3, à mélanger comme vous voulez."},
    "fuet3": {"n": 3, "price": 20.0, "label": "Offre 3 saucissons", "badge": "3 pour 20 €",
              "text": "Saucisson truffé : 10 € pièce, 20 € les 3."},
}
TODAY = datetime.date.today().isoformat()
VER = datetime.datetime.now().strftime("%Y%m%d%H%M")

P = json.loads((SRC / "products.json").read_text(encoding="utf-8"))
BYSLUG = {p["slug"]: p for p in P}
TESTS = [p for p in P if p.get("test")]
P = [p for p in P if not p.get("test")]
BUNDLES = [p for p in P if p.get("bundle")]
SINGLES = [p for p in P if not p.get("bundle")]
for b in BUNDLES:
    b["value"] = round(sum(BYSLUG[s]["price"] for s in b["bundle"]), 2)

CATS = {
    "coffrets-truffes": {"name": "Coffrets & Truffes", "h1": "Coffrets cadeaux et truffes d'été",
               "intro": "Des coffrets prêts à offrir et de la truffe d'été, entière ou en lamelles, pour faire plaisir ou se faire plaisir. Le cadeau gourmand qui marque les esprits, à Noël comme toute l'année."},
    "huiles-condiments": {"name": "Huiles & Condiments", "h1": "Huiles à la truffe, sels, miel et condiments",
               "intro": "Huile d'olive à la truffe noire ou blanche, sel de Guérande truffé, miel, moutarde et balsamique : les essentiels pour mettre de la truffe dans la cuisine de tous les jours, en un geste."},
    "cremes-tartinables": {"name": "Crèmes & Tartinables", "h1": "Crèmes de truffe et tartinables pour l'apéritif",
               "intro": "Crème de truffe d'été, sauce noire, sauce champignons, crème de cèpes et pesto à la truffe : l'apéritif chic en deux minutes, et des sauces express pour vos pâtes et risottos."},
    "epicerie-charcuterie": {"name": "Pâtes & Charcuterie", "h1": "Pâtes et charcuterie à la truffe",
               "intro": "Tagliatelles saveur truffe blanche et saucisson truffé : pour une planche apéro ou un plat de pâtes à la truffe en dix minutes."},
}

def e(s): return html.escape(str(s), quote=True)
def eur(x):
    s = f"{x:.2f}".replace(".", ",")
    return (s[:-3] if s.endswith(",00") else s) + " €"

def img(p, w=800):
    if p.get("bundle"):
        return img(BYSLUG[p["bundle"][0]], w) or img(BYSLUG[p["bundle"][1]], w)
    if not p["img"]:
        return ""
    if p["img"].startswith("/"):
        return f'{p["img"]}?v={VER}'
    return f"{IMG_BASE}{p['img']}{'&' if '?' in p['img'] else '?'}width={w}"

def jsonld(o): return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False) + "</script>"

ORG = {"@context": "https://schema.org", "@type": "OnlineStore", "@id": SITE + "/#org", "name": BRAND,
       "url": SITE + "/", "logo": SITE + "/assets/logo-maison-truffe.png",
       "description": "Épicerie fine en ligne spécialisée dans les produits à la truffe : huiles, crèmes, condiments, coffrets cadeaux et truffe d'été. Livraison en France.",
       "areaServed": "FR", "email": EMAIL, "contactPoint": {"@type": "ContactPoint", "contactType": "customer service", "email": EMAIL, "availableLanguage": "French"}, "currenciesAccepted": "EUR", "paymentAccepted": "Carte bancaire, Apple Pay, Google Pay"}
SHIPPING = {"@type": "OfferShippingDetails",
            "shippingRate": {"@type": "MonetaryAmount", "value": SHIP_PRICE, "currency": "EUR"},
            "shippingDestination": {"@type": "DefinedRegion", "addressCountry": "FR"},
            "deliveryTime": {"@type": "ShippingDeliveryTime",
                             "handlingTime": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 3, "unitCode": "DAY"},
                             "transitTime": {"@type": "QuantitativeValue", "minValue": 2, "maxValue": 4, "unitCode": "DAY"}}}

def page(path, title, desc, body, schema=None, og_img=None, noindex=False, cls=""):
    url = SITE + path
    og_img = og_img or SITE + "/assets/og-maison-truffe.jpg"
    robots = "noindex" if noindex else "index, follow, max-image-preview:large"
    doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="{robots}">
<meta property="og:type" content="website"><meta property="og:locale" content="fr_FR"><meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{e(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#16110d">
<link rel="icon" href="/assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="Blog Maison Truffe" href="/feed.xml">
<link rel="preload" href="/assets/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/style.css?v={VER}">
{''.join(jsonld(s) for s in [ORG] + (schema or []))}
</head>
<body class="{cls}">
<div class="topbar">3 pots au choix = 40 € · Expédition sous 1 à 3 jours ouvrés · Paiement sécurisé</div>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="/" aria-label="{BRAND} — accueil"><img class="logo-mark" src="/assets/logo-emblem.png" alt="" width="58" height="47"><span class="logo-txt">Maison Truffe<small>Spécialités à la truffe</small></span></a>
    <nav class="nav" aria-label="Navigation principale">
      <a href="/categorie/offres/" class="nav-hot">3 pots = 40 €</a>
      <a href="/boutique/">Boutique</a>
      <a href="/#quiz">Quiz</a>
      <a href="/recettes/">Recettes</a>
      <a href="/blog/">Blog</a>
    </nav>
    <a class="btn btn-gold btn-sm head-cta" href="/boutique/">Commander</a>
    <a class="cart-btn" href="/panier/" aria-label="Voir le panier"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12l-1 13H7L6 7zm3 0a3 3 0 016 0"/></svg><span class="cart-count" data-cart-count>0</span></a>
  </div>
</header>
<nav class="catbar" aria-label="Catégories"><div class="wrap catbar-inner">
  <a href="/boutique/" class="cb-all">🛒 Tous les produits</a>
  <a href="/categorie/offres/">🔥 3 pots = 40 €</a>
  <a href="/categorie/coffrets-truffes/">Coffrets & truffes</a>
  <a href="/categorie/huiles-condiments/">Huiles & condiments</a>
  <a href="/categorie/cremes-tartinables/">Crèmes & tartinables</a>
  <a href="/categorie/epicerie-charcuterie/">Pâtes & charcuterie</a>
</div></nav>
<main>
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <div class="logo logo-footer"><img class="logo-mark" src="/assets/logo-emblem.png" alt="" width="58" height="47"><span class="logo-txt">Maison Truffe<small>Spécialités à la truffe</small></span></div>
      <p>Épicerie fine en ligne dédiée à la truffe : des plats de chef en 10 minutes, sans savoir cuisiner. Livraison partout en France.</p>
      <p>✉️ <a href="mailto:{EMAIL}">{EMAIL}</a></p>
    </div>
    <div><h3>La boutique</h3><ul>
      {''.join(f'<li><a href="/categorie/{k}/">{e(v["name"])}</a></li>' for k, v in CATS.items())}
      <li><a href="/boutique/">Tous les produits</a></li></ul></div>
    <div><h3>Bien choisir</h3><ul>
      <li><a href="/#quiz">Quiz : quel produit pour moi ?</a></li>
      <li><a href="/recettes/">Recettes à la truffe en 10 min</a></li>
      <li><a href="/guides/differences-truffe-ete-noire-blanche/">Truffe d'été, noire ou blanche ?</a></li>
      <li><a href="/guides/idees-cadeaux-truffe/">Idées cadeaux à la truffe</a></li>
      <li><a href="/blog/">Le blog de la truffe</a></li>
      <li><a href="/faq/">Questions fréquentes</a></li></ul></div>
    <div><h3>Informations</h3><ul>
      <li><a href="/livraison/">Livraison & retours</a></li>
      <li><a href="/cgv/">Conditions générales de vente</a></li>
      <li><a href="/mentions-legales/">Mentions légales</a></li>
      <li><a href="/confidentialite/">Confidentialité</a></li>
      <li><a href="/cookies/">Cookies</a></li>
      <li><a href="/contact/">Contact</a></li></ul></div>
  </div>
  <div class="wrap footer-bottom"><span>© {datetime.date.today().year} {BRAND} · Paiement sécurisé par Stripe</span><span>Site réalisé par <a href="https://sitepropulse.fr" target="_blank" rel="noopener">Site Propulse</a></span></div>
</footer>
<a class="float-cart" href="/panier/" data-float-cart hidden><span>🛒 <b data-fc-n>0</b> article(s) · <b data-fc-t>0 €</b></span><span class="fc-go">Commander →</span></a>
<div class="cookie-bar" data-cookie hidden role="dialog" aria-label="Cookies">
  <p>🍪 Ce site utilise uniquement des cookies et traceurs <b>nécessaires</b> à son fonctionnement (panier, paiement sécurisé). Aucun cookie publicitaire ni de mesure d'audience. <a href="/cookies/">Politique cookies</a> · <a href="/cgv/">CGV</a> · <a href="/confidentialite/">Confidentialité</a></p>
  <div class="cookie-btns"><button class="btn btn-sm btn-outline" data-cookie-ok="refuse">Refuser</button><button class="btn btn-sm btn-gold" data-cookie-ok="accept">Accepter</button></div>
</div>
<div class="toast" data-toast role="status" aria-live="polite"></div>
<script src="/assets/catalog.js?v={VER}"></script>
<script src="/assets/cart.js?v={VER}"></script>
</body>
</html>"""
    target = OUT / path.strip("/") if path.endswith(".html") else (OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc, encoding="utf-8")

def crumbs(items):
    lis = " <span>/</span> ".join(f'<a href="{u}">{e(n)}</a>' if u else f'<span aria-current="page">{e(n)}</span>' for n, u in items)
    schema = {"@context": "https://schema.org", "@type": "BreadcrumbList",
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, **({"item": SITE + u} if u else {})}
                                  for i, (n, u) in enumerate(items)]}
    return f'<nav class="crumbs wrap" aria-label="Fil d\'Ariane">{lis}</nav>', schema

def pic(p, w=600, cls=""):
    if p.get("bundle"):
        uniq = list(dict.fromkeys(p["bundle"]))[:4]
        cells = "".join(
            (f'<img src="{img(BYSLUG[s], 300)}" alt="" loading="lazy">' if img(BYSLUG[s]) else '<span class="ph">◆</span>')
            for s in uniq)
        return f'<div class="stack stack-{len(uniq)} {cls}" role="img" aria-label="{e(p["name"])}">{cells}</div>'
    im = img(p, w)
    return (f'<img class="{cls}" src="{im}" alt="{e(p["name"])}" loading="lazy" width="{w}" height="{w}">' if im
            else f'<div class="img-ph {cls}" aria-hidden="true">◆</div>')

def card(p):
    badge = (f'<span class="badge badge-promo">{PROMOS[p["promo"]]["badge"]}</span>' if p.get("promo")
             else f'<span class="badge">{e(p.get("tag") or "Best-seller")}</span>' if p.get("bestseller") else "")
    was = f'<s>{eur(p["value"])}</s>' if p.get("bundle") else ""
    return f"""<article class="card" data-cat="{p['cat']}">
  <a href="/produit/{p['slug']}/" class="card-img">{badge}{pic(p)}</a>
  <div class="card-body">
    <h3><a href="/produit/{p['slug']}/">{e(p['name'])}</a></h3>
    <p class="card-short">{e(p['short'])}</p>
    <p class="price">{was}{eur(p['price'])}</p>
    <p class="stock">● En stock · expédié sous 1 à 3 jours</p>
    <button class="btn btn-gold btn-block" data-add="{p['slug']}" aria-label="Ajouter {e(p['name'])} au panier">Ajouter au panier</button>
  </div>
</article>"""

def grid(items): return '<div class="grid">' + "".join(card(p) for p in items) + "</div>"

def itemlist(items):
    return {"@context": "https://schema.org", "@type": "ItemList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}/produit/{p['slug']}/", "name": p["name"]}
                                for i, p in enumerate(items)]}

def offer_card(b, featured=False):
    counts = {}
    for s in b["bundle"]:
        counts[s] = counts.get(s, 0) + 1
    rows = "".join(f'<li><span>{(str(n) + " × ") if n > 1 else ""}{e(BYSLUG[s]["name"])}</span><span>{eur(BYSLUG[s]["price"] * n)}</span></li>' for s, n in counts.items())
    save = b["value"] - b["price"]
    return f"""<article class="offer reveal{' offer-featured' if featured else ''}">
  {'<div class="offer-flag">' + e(b.get("tag", "")) + '</div>' if b.get("tag") else ''}
  <a href="/produit/{b['slug']}/" class="offer-visual">{pic(b)}</a>
  <h3><a href="/produit/{b['slug']}/">{e(b['name'])}</a></h3>
  <p class="offer-promise">{e(b['short'])}</p>
  <ul class="stack-list">{rows}
    <li class="bonus"><span>🎁 Carnet « 12 recettes truffe en 10 min »</span><span>offert</span></li>
    <li class="bonus"><span>🚚 Livraison en France</span><span>offerte</span></li>
    <li class="bonus"><span>📦 Colis protégé, casse remplacée</span><span>inclus</span></li>
  </ul>
  <div class="offer-price"><span class="was">Au détail : {eur(b['value'])}</span><span class="now">{eur(b['price'])}</span><span class="save">Vous économisez {eur(save)} + la livraison</span></div>
  <button class="btn btn-block{' btn-gold' if featured else ''}" data-add="{b['slug']}">Je prends ce coffret</button>
</article>"""

exec((SRC / "part_faq.py").read_text(encoding="utf-8"))
FAQ.insert(0, ("Que se passe-t-il si mon colis arrive abîmé ?", GUARANTEE_TEXT))
FAQ.insert(1, ("Comment fonctionne l'offre 3 pots pour 40 € ?",
               "Tous nos produits à 15 € (crèmes, sauces, pesto, miel, moutarde, sel, crème balsamique, petites huiles 100 ml, petit condiment en poudre 30 g) sont à 40 € les 3, en mélangeant comme vous voulez. La remise s'applique automatiquement dans le panier, par lot de 3. Le saucisson truffé est à 10 € pièce ou 20 € les 3."))

def faq_schema(items):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}
def faq_html(items):
    return "".join(f'<details class="faq"><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in items)

GUARANTEE_BLOCK = f"""<section class="guarantee reveal"><div class="wrap guarantee-inner">
  <div class="seal" aria-hidden="true"><span>📦</span></div>
  <div><h2>{GUARANTEE_TITLE}</h2><p>{e(GUARANTEE_TEXT)}</p><p class="muted small">Chaque commande est emballée avec soin et calée pour voyager sans casse.</p></div>
</div></section>"""

# ------------------------------------------------------------ recettes (bonus)
RECETTES = [
    ("Tagliatelles crémeuses à la truffe", "10 min", ["tagliatelle-saveur-truffe-blanche", "creme-de-truffe-ete", "huile-olive-vierge-extra-truffe-blanche"],
     ["Cuire les tagliatelles dans une grande casserole d'eau salée.", "Réserver une louche d'eau de cuisson, égoutter.", "Hors du feu, mélanger les pâtes avec 2 cuillères à soupe de crème de truffe et un peu d'eau de cuisson.", "Servir avec du parmesan et quelques gouttes d'huile à la truffe blanche."]),
    ("Œufs brouillés à la truffe", "5 min", ["sel-de-guerande-saveur-truffe-noire", "huile-olive-vierge-extra-truffe-noire", "truffe-ete-en-lamelles"],
     ["Battre 3 œufs, cuire à feu très doux en remuant sans cesse avec une noix de beurre.", "Retirer du feu quand c'est encore crémeux.", "Assaisonner avec le sel truffé, un filet d'huile à la truffe noire et quelques lamelles de truffe."]),
    ("Planche apéro truffée", "5 min", ["creme-de-truffe-ete", "sauce-noire-truffe-ete", "saucisson-truffe", "miel-acacia-saveur-truffe-ete"],
     ["Toaster des tranches de baguette ou de pain de campagne.", "Tartiner moitié crème de truffe, moitié sauce noire à la truffe.", "Trancher finement le saucisson truffé.", "Ajouter 2 fromages et un petit bol de miel truffé à côté."]),
    ("Purée truffée de fête", "20 min", ["huile-olive-vierge-extra-truffe-noire", "sel-de-guerande-saveur-truffe-noire"],
     ["Cuire 800 g de pommes de terre épluchées à l'eau salée.", "Écraser avec 60 g de beurre et 15 cl de lait chaud.", "Hors du feu, ajouter 1 cuillère à soupe d'huile à la truffe noire.", "Finir avec une pincée de sel truffé au moment de servir."]),
    ("Risotto aux cèpes et truffe", "25 min", ["sauce-champignons-truffe-ete", "creme-de-cepes-truffe-blanche", "huile-olive-vierge-extra-truffe-blanche"],
     ["Faire revenir un oignon émincé, ajouter 300 g de riz arborio et le nacrer 2 minutes.", "Mouiller louche par louche avec 1 litre de bouillon chaud, en remuant.", "Hors du feu, ajouter 2 cuillères à soupe de crème de cèpes et truffe, du parmesan et une noix de beurre.", "Servir avec un filet d'huile à la truffe blanche."]),
    ("Toasts chèvre, miel truffé", "8 min", ["miel-acacia-saveur-truffe-ete"],
     ["Disposer des rondelles de chèvre sur des tranches de pain.", "Passer 5 minutes sous le gril du four.", "Napper d'un filet de miel d'acacia saveur truffe et d'un tour de poivre."]),
    ("Carpaccio de bœuf truffé", "10 min", ["huile-olive-vierge-extra-truffe-blanche", "creme-vinaigre-balsamique-modene-truffe"],
     ["Disposer de fines tranches de bœuf sur une assiette froide.", "Arroser d'huile à la truffe blanche, saler, poivrer.", "Ajouter roquette et copeaux de parmesan.", "Finir par quelques traits de crème de balsamique à la truffe."]),
    ("Pop-corn truffé du film du soir", "5 min", ["condiment-saveur-truffe-ete-poudre", "huile-olive-vierge-extra-truffe-noire"],
     ["Faire éclater le maïs dans une casserole couverte avec un peu d'huile neutre.", "Arroser d'une cuillère à soupe d'huile à la truffe noire.", "Saupoudrer de condiment saveur truffe d'été et mélanger."]),
    ("Croque-monsieur à la truffe", "12 min", ["creme-de-truffe-ete"],
     ["Tartiner 4 tranches de pain de mie de crème de truffe d'été.", "Ajouter jambon et comté, refermer.", "Cuire 4 minutes de chaque côté dans une poêle beurrée."]),
    ("Vinaigrette truffée", "2 min", ["huile-olive-vierge-extra-truffe-noire", "moutarde-brisures-truffe-brumale-poivre-noir"],
     ["Mélanger 1 cuillère à café de moutarde à la truffe et 1 cuillère à soupe de vinaigre.", "Ajouter 3 cuillères à soupe d'huile à la truffe noire en fouettant.", "Parfait sur une salade de mâche, pommes de terre tièdes ou endives."]),
    ("Bruschetta pesto truffe", "8 min", ["pesto-saveur-truffe-ete"],
     ["Griller des tranches de pain ciabatta.", "Tartiner de pesto saveur truffe d'été.", "Ajouter tomates cerises coupées et burrata."]),
    ("Volaille rôtie au beurre truffé", "1 h", ["condiment-saveur-truffe-ete-poudre", "sel-de-guerande-saveur-truffe-noire"],
     ["Mélanger 50 g de beurre mou avec 1 cuillère à café de condiment truffe d'été en poudre.", "Glisser le beurre sous la peau d'un poulet.", "Rôtir 1 h à 200 °C en arrosant.", "Saler au sel truffé à la sortie du four."]),
]
def recette_html(i, r):
    t, d, prods, steps = r
    plinks = "".join(f'<li><a href="/produit/{s}/">{e(BYSLUG[s]["name"])}</a> <button class="link-add" data-add="{s}">+ panier</button></li>' for s in prods if s in BYSLUG)
    return f"""<details class="recette reveal"{' open' if i == 0 else ''}>
  <summary><span class="r-num">{i + 1:02d}</span><span class="r-title">{e(t)}</span><span class="r-time">⏱ {d}</span></summary>
  <div class="r-body"><div><h4>Les produits</h4><ul class="r-prods">{plinks}</ul></div>
  <div><h4>La recette</h4><ol>{''.join(f'<li>{e(s)}</li>' for s in steps)}</ol></div></div>
</details>"""

# ------------------------------------------------------------ build
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "assets").mkdir(parents=True)
for f in (SRC / "assets").iterdir():
    (shutil.copytree if f.is_dir() else shutil.copy)(f, OUT / "assets" / f.name)
(OUT / "admin").mkdir(parents=True, exist_ok=True)
shutil.copy(SRC / "admin.html", OUT / "admin" / "index.html")   # tableau de bord des commandes
for f in (SRC / "static").glob("*"):
    shutil.copy(f, OUT / f.name)   # fichiers à la racine (vérifications Google, Bing…)

def weight_of(p):
    if p.get("bundle"):
        ws = [BYSLUG[s].get("weight_g") for s in p["bundle"]]
        return sum(ws) if all(w for w in ws) else None
    return p.get("weight_g")
def absimg(p, w=200):
    u = img(p, w)
    return SITE + u if u.startswith("/") else u
cat_js = {p["slug"]: {"name": p["name"], "price": p["price"], "img": img(p, 200), "cat": p["cat"], **({"promo": p["promo"]} if p.get("promo") else {}), **({"test": True} if p.get("test") else {})} for p in P + TESTS}
cat_srv = {p["slug"]: {"name": p["name"], "price": p["price"], "img": absimg(p, 200), "cat": p["cat"], "weight_g": weight_of(p), "promo": p.get("promo"), "test": bool(p.get("test"))} for p in P + TESTS}
PROMOS_PUB = {k: {"n": v["n"], "price": v["price"], "label": v["label"]} for k, v in PROMOS.items()}
(OUT / "assets" / "catalog.js").write_text(
    "window.MT_CATALOG=" + json.dumps(cat_js, ensure_ascii=False) +
    f";window.MT_SHIP={{price:{SHIP_PRICE},free:{FREE_SHIP}}};window.MT_PROMOS=" + json.dumps(PROMOS_PUB, ensure_ascii=False) + ";", encoding="utf-8")
(ROOT / "netlify" / "lib").mkdir(parents=True, exist_ok=True)
(ROOT / "netlify" / "lib" / "catalog.mts").write_text(
    "// Généré par src/build.py — ne pas modifier à la main\n"
    "export const CATALOG: Record<string, { name: string; price: number; img: string; cat: string; weight_g: number | null; promo: string | null; test: boolean }> = " +
    json.dumps(cat_srv, ensure_ascii=False, indent=1) + f";\nexport const SHIP = {{ price: {SHIP_PRICE}, free: {FREE_SHIP} }};\n"
    "export const PROMOS: Record<string, { n: number; price: number; label: string }> = " + json.dumps(PROMOS_PUB, ensure_ascii=False) + ";\n"
    "export const PARCEL = " + json.dumps(PARCEL) + ";\n"
    f"export const PACKAGING_G = {PACKAGING_G};\nexport const OWNER_EMAIL = {json.dumps(EMAIL)};\n",
    encoding="utf-8")

# ---- Accueil
best = [p for p in SINGLES if p.get("bestseller")]
POTS = [p for p in SINGLES if p.get("promo") == "pot3"]
def promo_block(compact=False):
    thumbs = "".join(f'<a href="/produit/{p["slug"]}/" class="pm-thumb" title="{e(p["name"])}">{pic(p, 160)}</a>' for p in POTS[:8])
    return f"""<section class="promo-band reveal"><div class="wrap promo-inner">
  <div class="promo-txt"><p class="pill">🔥 Offre permanente · mélange libre</p>
  <h2>3 pots au choix = <span class="gold">40 €</span> <s>45 €</s></h2>
  <p class="lead">Crèmes, sauces, pesto, miel, moutarde, sel, balsamique, petites huiles 100 ml, petit condiment : tout ce qui est à 15 €. Prenez-en 3, mélangez comme vous voulez, la remise s'applique toute seule dans le panier.</p>
  <p class="promo-sub">+ <b>Saucisson truffé</b> : 10 € pièce, <b>20 € les 3</b>.</p>
  <div class="hero-cta"><a class="btn btn-gold btn-lg" href="/categorie/offres/">Je compose mes 3 pots</a>{'' if compact else '<a class="btn btn-ghost-light btn-lg" href="/produit/saucisson-truffe/">Voir le saucisson</a>'}</div></div>
  <div class="promo-thumbs">{thumbs}</div>
</div></section>"""
tabs = '<div class="tabs" role="tablist" data-tabs><button class="tab active" data-filter="all">Tout</button>' + "".join(
    f'<button class="tab" data-filter="{k}">{e(v["name"])}</button>' for k, v in CATS.items() if k != "offres") + "</div>"
quiz = """
<section class="quiz-sec" id="quiz">
  <div class="wrap narrow">
    <p class="eyebrow center">Quiz · 20 secondes</p>
    <h2 class="center">Quel produit truffe est fait pour vous ?</h2>
    <div class="quiz" data-quiz>
      <div class="q-progress"><span data-q-bar></span></div>
      <div class="q-step active" data-step="0">
        <h3>C'est pour…</h3>
        <div class="q-opts"><button data-a="moi">🍽️ Me faire plaisir</button><button data-a="offrir">🎁 Offrir</button></div>
      </div>
      <div class="q-step" data-step="1">
        <h3>Vous rêvez plutôt de…</h3>
        <div class="q-opts"><button data-a="pates">🍝 Pâtes & risottos</button><button data-a="apero">🥂 Apéritif entre amis</button><button data-a="quotidien">🍳 Truffe au quotidien</button><button data-a="fromage">🧀 Plateau de fromages</button></div>
      </div>
      <div class="q-step" data-step="2">
        <h3>Votre budget ?</h3>
        <div class="q-opts"><button data-a="s">Moins de 15 €</button><button data-a="m">15 à 30 €</button><button data-a="l">Plus de 30 €</button></div>
      </div>
      <div class="q-step q-result" data-step="3"><div data-q-result></div><button class="link" data-q-restart>↺ Recommencer</button></div>
    </div>
  </div>
</section>"""
home = f"""
<section class="shop-hero">
  <div class="wrap shop-hero-inner">
    <div class="sh-text">
      <p class="pill">🛒 Boutique en ligne · Livraison partout en France</p>
      <h1>Produits à la truffe : commandez en ligne, livrés chez vous.</h1>
      <p class="lead">Huiles, crèmes, sauces, condiments, saucisson et coffret cadeau à la truffe. <b>Tous les pots à 15 €, et 40 € les 3</b> au choix. Livraison en France : {eur(SHIP_PRICE)}.</p>
      <div class="hero-cta"><a class="btn btn-gold btn-lg" href="#meilleures-ventes">Commander maintenant</a><a class="btn btn-outline btn-lg" href="/categorie/offres/">3 pots = 40 €</a></div>
      <ul class="trust"><li><b>🚚</b> Expédié sous 1 à 3 jours</li><li><b>🎁</b> 3 pots au choix = 40 €</li><li><b>🔒</b> Paiement CB, Apple Pay</li><li><b>📦</b> Colis protégé</li></ul>
    </div>
    <div class="sh-feature">
      <a href="/produit/creme-de-truffe-ete/" class="feat-img">{pic(BYSLUG['creme-de-truffe-ete'])}<span class="badge">Le plus vendu</span></a>
      <div class="feat-body"><h2>Crème de truffe d'été</h2><p>Sur des pâtes, un toast ou un risotto : la truffe en 2 minutes.</p>
      <p class="price">{eur(BYSLUG['creme-de-truffe-ete']['price'])} <small>ou 40 € les 3 pots au choix</small></p>
      <button class="btn btn-gold btn-block btn-lg" data-add="creme-de-truffe-ete">Ajouter au panier</button></div>
    </div>
  </div>
</section>

<section class="section wrap" id="meilleures-ventes">
  <div class="section-head"><h2>Meilleures ventes</h2><a href="/boutique/" class="btn btn-outline btn-sm">Voir tous les produits →</a></div>
  {grid(best)}
</section>

<section class="section-tight wrap">
  <div class="cat-tiles">
    {''.join(f'<a class="cat-tile" href="/categorie/{k}/">{pic([p for p in P if p["cat"]==k][0], 300)}<span><b>{e(v["name"])}</b>{len([p for p in P if p["cat"]==k])} produits · Commander →</span></a>' for k, v in CATS.items())}
  </div>
</section>

{promo_block()}

<section class="section wrap shop-all" id="boutique">
  <div class="section-head"><h2>Tous nos produits</h2><a href="/panier/" class="btn btn-outline btn-sm">Voir mon panier →</a></div>
  {tabs}
  <div data-tab-grid>{grid(SINGLES)}</div>
</section>

{quiz}

<section class="section wrap recipes-teaser">
  <div class="two-col">
    <div><h2>12 recettes à la truffe en 10 minutes</h2>
    <p class="lead">Gratuites, pour bien utiliser vos produits. Chaque recette indique le produit à utiliser, avec un bouton pour l'ajouter au panier.</p>
    <a class="btn btn-gold" href="/recettes/">Voir les recettes</a></div>
    <div>{recette_html(0, RECETTES[0])}{recette_html(1, RECETTES[2])}</div>
  </div>
</section>

{GUARANTEE_BLOCK}

<section class="section wrap narrow">
  <h2 class="center">Questions fréquentes</h2>
  {faq_html(FAQ[:6])}
  <p class="center"><a class="btn btn-outline" href="/faq/">Toutes les questions</a></p>
</section>

<section class="final-cta"><div class="wrap center">
  <h2>Prêt à commander ?</h2>
  <p class="lead">Expédition sous 1 à 3 jours ouvrés, livraison en France : {eur(SHIP_PRICE)}.</p>
  <div class="hero-cta center-cta"><a class="btn btn-gold btn-lg" href="#meilleures-ventes">Commander maintenant</a><a class="btn btn-ghost-light btn-lg" href="#quiz">Faire le quiz</a></div>
</div></section>"""
page("/", "Maison Truffe — Produits à la truffe : huiles, crèmes, sauces | 3 pots = 40 €",
     f"Huile d'olive à la truffe, crème de truffe d'été, sauces, condiments et saucisson truffé. Pots à 15 €, 40 € les 3 au choix. Expédition sous 1 à 3 jours partout en France.",
     home, [faq_schema(FAQ[:6]), itemlist(best),
            {"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": SITE + "/", "inLanguage": "fr-FR"}],
     cls="home")

# ---- Boutique
cr, crs = crumbs([("Accueil", "/"), ("Boutique", None)])
page("/boutique/", "Boutique produits à la truffe — Maison Truffe",
     "Tous nos produits à la truffe : huiles à la truffe noire et blanche, crèmes, sauces, condiments, pâtes, saucisson truffé. Pots à 15 €, 40 € les 3 au choix.",
     f"""{cr}<section class="section wrap"><h1>Tous nos produits à la truffe</h1>
<p class="lead">{len(P)} spécialités à la truffe d'été, noire, blanche, bianchetto et brumale. <b>Tous les pots à 15 € : 40 € les 3 au choix.</b></p>
<div class="tabs" data-tabs><button class="tab active" data-filter="all">Tout</button>{''.join(f'<button class="tab" data-filter="{k}">{e(v["name"])}</button>' for k, v in CATS.items())}</div>
<div data-tab-grid>{grid(P)}</div></section>{promo_block(True)}{GUARANTEE_BLOCK}""",
     [crs, itemlist(P)])

for k, v in CATS.items():
    items = [p for p in P if p["cat"] == k]
    cr, crs = crumbs([("Accueil", "/"), ("Boutique", "/boutique/"), (v["name"], None)])
    body = grid(items)
    page(f"/categorie/{k}/", f"{v['h1']} — {BRAND}", v["intro"][:155],
         f"""{cr}<section class="section wrap"><h1>{e(v['h1'])}</h1><p class="lead">{e(v['intro'])}</p>{body}</section>{GUARANTEE_BLOCK}""",
         [crs, itemlist(items)])

# ---- Page offre 3 pots (ancienne URL des coffrets, conservée)
cr, crs = crumbs([("Accueil", "/"), ("Boutique", "/boutique/"), ("Offre 3 pots = 40 €", None)])
FUETS = [p for p in SINGLES if p.get("promo") == "fuet3"]
page("/categorie/offres/", "Offre 3 pots à la truffe pour 40 € au choix — Maison Truffe",
     "Crèmes, sauces, pesto, miel, moutarde, sel, petites huiles 100 ml : tous nos produits à 15 €, 40 € les 3 en mélangeant comme vous voulez. Saucisson truffé 20 € les 3.",
     f"""{cr}<section class="section wrap"><p class="eyebrow">Offre permanente</p><h1>3 produits à 15 € au choix pour 40 €</h1>
<p class="lead">Tous ces produits sont à 15 € pièce. <b>Prenez-en 3, mélangez comme vous voulez : vous payez 40 € au lieu de 45 €.</b> La remise s'applique automatiquement dans le panier, pour chaque lot de 3 (6 pots = 80 €, 9 pots = 120 €…).</p>
<ol class="steps-inline"><li>Ajoutez 3 produits (ou plus) de cette page</li><li>Le panier calcule la remise tout seul</li><li>Expédition sous 1 à 3 jours</li></ol>
{grid(POTS)}
<h2 style="margin-top:2.5rem">Et le saucisson truffé : 20 € les 3</h2>
<p class="lead">10 € pièce, 20 € les 3. Idéal pour compléter une planche apéro.</p>
{grid(FUETS)}</section>{GUARANTEE_BLOCK}""",
     [crs, itemlist(POTS + FUETS)])

# ---- Fiches produit
def compo_html(p):
    rows = [("Contenance", p.get("net")), ("Ingrédients", p.get("ingredients")), ("Allergènes", p.get("allergens")), ("Conservation", p.get("conservation"))]
    rows = [(k, v) for k, v in rows if v]
    if not rows:
        return ""
    return '<h2>Composition et conservation</h2><dl class="specs compo">' + "".join(f"<dt>{k}</dt><dd>{e(v)}</dd>" for k, v in rows) + "</dl>"
for p in P:
    c = CATS[p["cat"]]
    cr, crs = crumbs([("Accueil", "/"), (c["name"], f"/categorie/{p['cat']}/"), (p["name"], None)])
    in_bundles = [b for b in BUNDLES if p["slug"] in b["bundle"]]
    related = [q for q in SINGLES if q["cat"] == p["cat"] and q["slug"] != p["slug"]][:4]
    if len(related) < 4:
        related += [q for q in best if q["slug"] != p["slug"] and q not in related][: 4 - len(related)]
    pfaq = [
        (f"Comment utiliser : {p['name']} ?", "Idées d'utilisation : " + " ; ".join(p["uses"]) + "."),
        ("Et si le colis arrive abîmé ?", GUARANTEE_TEXT),
        ("Quel est le délai de livraison ?", f"Expédition sous 1 à 3 jours ouvrés, livraison en 2 à 4 jours en France. Frais de port : {eur(SHIP_PRICE)} par commande."),
        ("Comment le conserver ?", "Avant ouverture, à l'abri de la chaleur et de la lumière. Après ouverture, bien refermer et suivre la mention de conservation de l'étiquette."),
    ]
    schema = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "description": p["desc"],
              "sku": p["slug"], "category": c["name"], "url": f"{SITE}/produit/{p['slug']}/",
              "offers": {"@type": "Offer", "price": f"{p['price']:.2f}", "priceCurrency": "EUR",
                         "availability": "https://schema.org/InStock", "itemCondition": "https://schema.org/NewCondition",
                         "url": f"{SITE}/produit/{p['slug']}/", "seller": {"@id": SITE + "/#org"}, "shippingDetails": SHIPPING,
                         "hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "FR",
                                                     "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                                                     "merchantReturnDays": 14, "returnMethod": "https://schema.org/ReturnByMail",
                                                     "returnFees": "https://schema.org/ReturnShippingFees"}}}
    if img(p):
        schema["image"] = [absimg(p, 1000)] + [SITE + g for g in p.get("gallery", [])]

    if p.get("bundle"):
        counts = {}
        for s in p["bundle"]:
            counts[s] = counts.get(s, 0) + 1
        inside = "".join(f'<li><a href="/produit/{s}/">{(str(n) + " × ") if n > 1 else ""}{e(BYSLUG[s]["name"])}</a><span>{eur(BYSLUG[s]["price"] * n)}</span></li>' for s, n in counts.items())
        price_html = f'<p class="price big"><s>{eur(p["value"])}</s> {eur(p["price"])} <small>TTC · livraison offerte</small></p>'
        extra = f"""<div class="value-stack"><h2>Ce que vous recevez</h2><ul class="stack-list">{inside}
<li class="bonus"><span>🎁 Carnet « 12 recettes truffe en 10 min »</span><span>offert</span></li>
<li class="bonus"><span>🚚 Livraison en France</span><span>offerte</span></li>
<li class="bonus"><span>📦 Colis protégé, casse remplacée</span><span>inclus</span></li>
<li class="total"><span>Au détail</span><span><s>{eur(p['value'])}</s></span></li>
<li class="total now"><span>Votre prix</span><span>{eur(p['price'])}</span></li></ul></div>"""
    else:
        price_html = f'<p class="price big">{eur(p["price"])} <small>TTC</small></p>'
        extra = ""
    if p.get("formats"):
        sib = sorted([q for q in SINGLES if q.get("formats") == p["formats"]], key=lambda q: q["price"])
        price_html += '<div class="formats"><span>Format :</span>' + "".join(
            (f'<span class="fmt on">{e(q["format_label"])} · {eur(q["price"])}</span>' if q is p else
             f'<a class="fmt" href="/produit/{q["slug"]}/">{e(q["format_label"])} · {eur(q["price"])}</a>') for q in sib) + "</div>"
    if p.get("promo"):
        pr = PROMOS[p["promo"]]
        price_html += f'<a class="promo-pill" href="/categorie/offres/">🔥 <b>{pr["badge"]}</b> · {e(pr["text"])} →</a>'
    upsell = ""
    if in_bundles:
        b = in_bundles[0]
        upsell = f"""<a class="upsell" href="/produit/{b['slug']}/"><div class="upsell-img">{pic(b)}</div><div><b>Mieux : {e(b['name'])}</b><span>{e(b['short'])}</span><span class="up-price"><s>{eur(b['value'])}</s> {eur(b['price'])} · livraison et carnet offerts →</span></div></a>"""
    body = f"""{cr}
<section class="wrap product">
  <div class="product-img">{pic(p, 1000)}{''.join(f'<img src="{g}" alt="{e(p["name"])}" loading="lazy" width="1000" height="1000">' for g in p.get("gallery", []))}</div>
  <div class="product-info">
    <p class="eyebrow">{e(c['name'])}</p>
    <h1>{e(p['name'])}</h1>
    {price_html}
    <p class="lead">{e(p['short'])}</p>
    <div class="buy" data-buy>
      <label class="qty"><button type="button" data-qminus aria-label="Moins">−</button><input type="number" min="1" max="20" value="1" data-qty aria-label="Quantité"><button type="button" data-qplus aria-label="Plus">+</button></label>
      <button class="btn btn-gold btn-lg" data-add="{p['slug']}" data-with-qty>Ajouter au panier</button>
    </div>
    <ul class="mini-reassure"><li>Livraison {eur(SHIP_PRICE)}</li><li>Expédié sous 1 à 3 jours</li><li>Colis protégé</li><li>Paiement sécurisé</li></ul>
    {upsell}
    {extra}
    <h2>Description</h2><p>{e(p['desc'])}</p>
    <dl class="specs"><dt>Truffe</dt><dd>{e(p['truffle'])}</dd><dt>Prix</dt><dd>{eur(p['price'])} TTC</dd><dt>Livraison</dt><dd>France métropolitaine, Monaco</dd></dl>
    {compo_html(p)}
    <h2>Comment l'utiliser</h2><ul class="ticks">{''.join(f'<li>{e(u)}</li>' for u in p['uses'])}</ul>
  </div>
</section>
<section class="section wrap narrow"><h2>Questions sur ce produit</h2>{faq_html(pfaq)}</section>
{GUARANTEE_BLOCK}
<section class="section wrap"><h2>Vous aimerez aussi</h2>{grid(related)}</section>
<div class="sticky-buy" data-sticky><span><b>{e(p['name'])}</b> · {eur(p['price'])}</span><button class="btn btn-gold btn-sm" data-add="{p['slug']}">Ajouter</button></div>"""
    page(f"/produit/{p['slug']}/", f"{p['name']} — {eur(p['price'])} | {BRAND}",
         f"{p['short']} {p['name']} à {eur(p['price'])}. Expédition sous 1 à 3 jours.",
         body, [crs, schema, faq_schema(pfaq)], og_img=absimg(p, 1200) or None)

# ---- Page de test (non référencée)
for t in TESTS:
    page(f"/produit/{t['slug']}/", f"{t['name']} — {BRAND}", t["short"],
         f"""<section class="section wrap narrow center"><h1>{e(t['name'])}</h1><p class="lead">{e(t['short'])}</p>
<p class="price big">{eur(t['price'])} <small>livraison offerte</small></p>
<p><button class="btn btn-gold btn-lg" data-add="{t['slug']}">Ajouter au panier</button> <a class="btn btn-outline btn-lg" href="/panier/">Voir le panier</a></p></section>""", noindex=True)

# ---- Recettes
cr, crs = crumbs([("Accueil", "/"), ("Recettes", None)])
rec_schema = {"@context": "https://schema.org", "@type": "ItemList", "name": "12 recettes à la truffe en 10 minutes",
              "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                   "item": {"@type": "Recipe", "name": r[0], "totalTime": "PT" + r[1].replace(" min", "M").replace(" h", "H"),
                                            "recipeIngredient": [BYSLUG[s]["name"] for s in r[2]],
                                            "recipeInstructions": [{"@type": "HowToStep", "text": s} for s in r[3]],
                                            "author": {"@type": "Organization", "name": BRAND}}}
                                  for i, r in enumerate(RECETTES)]}
page("/recettes/", "12 recettes à la truffe faciles et rapides — Maison Truffe",
     "Tagliatelles à la truffe, œufs brouillés truffés, risotto, planche apéro, purée truffée : 12 recettes à la truffe en 10 minutes, avec les produits à utiliser.",
     f"""{cr}<section class="section wrap narrow"><p class="eyebrow">Le carnet Maison Truffe</p><h1>12 recettes à la truffe en 10 minutes</h1>
<p class="lead">Des recettes simples, testées, où chaque produit a son rôle. Cliquez sur une recette pour l'ouvrir, et ajoutez les produits au panier en un clic.</p>
{''.join(recette_html(i, r) for i, r in enumerate(RECETTES))}
<p class="cta-line center"><a class="btn btn-gold btn-lg" href="/categorie/offres/">3 pots au choix pour 40 €</a></p></section>""",
     [crs, rec_schema])

# ---- Guides
exec((SRC / "part_guides.py").read_text(encoding="utf-8"))
gl = "".join(f'<li class="reveal"><a href="/guides/{k}/"><strong>{e(g["title"])}</strong><span>{e(g["desc"])}</span></a></li>' for k, g in GUIDES.items())
gl += '<li class="reveal"><a href="/recettes/"><strong>12 recettes à la truffe en 10 minutes</strong><span>Le carnet de recettes Maison Truffe, avec les produits à utiliser.</span></a></li>'
cr, crs = crumbs([("Accueil", "/"), ("Guides", None)])
page("/guides/", "Guides de la truffe : choisir, cuisiner, offrir — Maison Truffe",
     "Nos guides pour tout savoir sur la truffe : différences entre truffe d'été, noire et blanche, utilisation de l'huile de truffe, idées cadeaux et recettes.",
     f'{cr}<section class="section wrap narrow"><h1>Guides de la truffe</h1><ul class="guide-list">{gl}</ul></section>', [crs])
for k, g in GUIDES.items():
    cr, crs = crumbs([("Accueil", "/"), ("Guides", "/guides/"), (g["title"], None)])
    art = {"@context": "https://schema.org", "@type": "Article", "headline": g["title"], "description": g["desc"], "inLanguage": "fr-FR",
           "datePublished": TODAY, "dateModified": TODAY, "author": {"@type": "Organization", "name": BRAND},
           "publisher": {"@id": SITE + "/#org"}, "mainEntityOfPage": f"{SITE}/guides/{k}/"}
    page(f"/guides/{k}/", f"{g['title']} | {BRAND}", g["desc"],
         f'{cr}<article class="section wrap narrow prose"><h1>{e(g["title"])}</h1>{g["body"]}'
         f'<div class="inline-offer"><b>Envie d\'essayer sans vous tromper ?</b><span>Tous nos pots sont à 15 €, et 40 € les 3 au choix.</span><a class="btn btn-gold" href="/categorie/offres/">Je compose mes 3 pots</a></div></article>',
         [crs, art])

# ---- FAQ
cr, crs = crumbs([("Accueil", "/"), ("FAQ", None)])
page("/faq/", "Questions fréquentes sur la truffe et nos produits — Maison Truffe",
     "Différences entre truffes, utilisation de l'huile de truffe, conservation, livraison, garantie, paiement : toutes les réponses.",
     f'{cr}<section class="section wrap narrow"><h1>Questions fréquentes</h1>{faq_html(FAQ)}</section>', [crs, faq_schema(FAQ)])

# ---- Panier
panier = f"""
<section class="section wrap">
  <h1>Votre panier</h1>
  
  <div class="cart-layout">
    <div>
      <div data-cart-lines></div>
      <div data-promo-hint></div>
      <div class="empty" data-cart-empty hidden><p class="lead">Votre panier est vide.</p><a class="btn btn-gold" href="/categorie/offres/">Voir l'offre 3 pots = 40 €</a></div>
      <div class="bump" data-bump hidden><h3>Complétez votre lot de 3 pots</h3><div data-bump-items></div></div>
    </div>
    <aside class="summary" data-cart-summary>
      <h2>Récapitulatif</h2>
      <dl><dt>Sous-total</dt><dd data-subtotal>0 €</dd><dt data-promo-dt hidden>Remise offres</dt><dd data-promo hidden class="promo-off">0 €</dd><dt>Livraison</dt><dd data-shipping>—</dd><dt class="total">Total</dt><dd class="total" data-total>0 €</dd></dl>
      <ul class="summary-perks"><li>📦 Colis protégé</li><li>🎁 Carnet de recettes offert</li><li>🔒 Paiement sécurisé Stripe</li></ul>
      <form name="commande" method="POST" data-netlify="true" netlify-honeypot="bot-field" class="checkout" data-checkout>
        <input type="hidden" name="form-name" value="commande">
        <input type="hidden" name="subject" value="Nouvelle commande Maison Truffe">
        <p hidden><label>Ne pas remplir : <input name="bot-field"></label></p>
        <h3>Vos coordonnées</h3>
        <label>Nom et prénom<input name="nom" required autocomplete="name"></label>
        <label>E-mail<input type="email" name="email" required autocomplete="email"></label>
        <label>Téléphone<input type="tel" name="telephone" required autocomplete="tel"></label>
        <label>Adresse<input name="adresse" required autocomplete="street-address"></label>
        <div class="row2"><label>Code postal<input name="code_postal" required autocomplete="postal-code"></label><label>Ville<input name="ville" required autocomplete="address-level2"></label></div>
        <label>Pays<select name="pays"><option>France</option><option>Monaco</option></select></label>
        <label>Message (cadeau, mot à glisser…)<textarea name="message" rows="2"></textarea></label>
        <input type="hidden" name="commande"><input type="hidden" name="total">
        <label class="check"><input type="checkbox" required> J'accepte les <a href="/cgv/" target="_blank">conditions générales de vente</a>.</label>
        <button class="btn btn-gold btn-block btn-lg" type="submit" data-pay>Payer ma commande</button>
        <p class="muted small center">Carte bancaire · Apple Pay · Google Pay</p>
      </form>
    </aside>
  </div>
</section>"""
page("/panier/", "Votre panier — Maison Truffe", "Votre panier de produits à la truffe.", panier, noindex=True)

page("/merci/", "Merci pour votre commande — Maison Truffe", "Confirmation de commande.",
     """<section class="section wrap narrow center"><div class="seal big-seal" aria-hidden="true"><span>✓</span></div><h1>Merci pour votre commande !</h1>
<p class="lead" data-merci-paid>Votre paiement est confirmé. Vous recevez un reçu par e-mail, et votre colis part sous 1 à 3 jours ouvrés.</p>
<p class="lead" data-merci-manual hidden>Votre commande est bien enregistrée. Nous vous envoyons très vite par e-mail un lien de paiement sécurisé pour la finaliser.</p>
<div class="inline-offer"><b>🎁 Votre bonus : le carnet « 12 recettes truffe en 10 minutes »</b><span>Gardez cette page en favori pour vos premières recettes.</span><a class="btn btn-gold" href="/recettes/">Ouvrir le carnet</a></div></section>""", noindex=True)

exec((SRC / "part_info.py").read_text(encoding="utf-8"))

page("/404.html", "Page introuvable — Maison Truffe", "Page introuvable.",
     '<section class="section wrap narrow center"><h1>Page introuvable</h1><p class="lead">Cette page n\'existe pas ou plus.</p><p><a class="btn" href="/boutique/">Voir la boutique</a></p></section>', noindex=True)


# ---- Blog
import markdown as _md, yaml as _yaml, re as _re
POSTS = []
for f in sorted((SRC / "blog").glob("*.md")):
    raw = f.read_text(encoding="utf-8")
    _, fm, body = raw.split("---", 2)
    meta = _yaml.safe_load(fm)
    meta["slug"] = f.stem
    meta["date"] = str(meta["date"])
    if meta["date"] > TODAY:          # articles programmés : publiés à leur date
        continue
    meta["html"] = _md.markdown(body.strip(), extensions=["extra", "sane_lists"])
    meta["words"] = len(_re.findall(r"\w+", body))
    POSTS.append(meta)
POSTS.sort(key=lambda m: (m["date"], m.get("order", 0)), reverse=True)
BLOG_CATS = sorted({m["category"] for m in POSTS})

def fr_date(d):
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    y, m_, dd = d.split("-")
    return f"{int(dd)} {mois[int(m_) - 1]} {y}"

def post_card(m):
    first = next((BYSLUG[s] for s in m.get("products", []) if s in BYSLUG), None)
    vis = pic(first, 400) if first else '<div class="img-ph">◆</div>'
    return f"""<article class="card post" data-cat="{e(m['category'])}">
  <a href="/blog/{m['slug']}/" class="card-img post-img">{vis}<span class="badge">{e(m['category'])}</span></a>
  <div class="card-body"><h3><a href="/blog/{m['slug']}/">{e(m['title'])}</a></h3>
  <p class="card-short">{e(m['description'])}</p>
  <a class="link" href="/blog/{m['slug']}/">Lire l'article →</a></div>
</article>"""

cr, crs = crumbs([("Accueil", "/"), ("Blog", None)])
btabs = '<div class="tabs" data-tabs><button class="tab active" data-filter="all">Tous</button>' + "".join(
    f'<button class="tab" data-filter="{e(c)}">{e(c)}</button>' for c in BLOG_CATS) + "</div>"
page("/blog/", "Blog de la truffe : recettes, guides et idées cadeaux — Maison Truffe",
     "Recettes à la truffe faciles, guides pour choisir et cuisiner la truffe, accords mets-vins et idées cadeaux gourmands. Le blog Maison Truffe.",
     f"""{cr}<section class="section wrap"><h1>Le blog de la truffe</h1>
<p class="lead">Recettes faciles, guides pour bien choisir, accords et idées cadeaux. {len(POSTS)} articles pour cuisiner la truffe au quotidien.</p>
{btabs}<div data-tab-grid><div class="grid">{''.join(post_card(m) for m in POSTS)}</div></div></section>""",
     [crs, {"@context": "https://schema.org", "@type": "Blog", "name": "Blog Maison Truffe", "url": SITE + "/blog/", "inLanguage": "fr-FR",
            "blogPost": [{"@type": "BlogPosting", "headline": m["title"], "url": f"{SITE}/blog/{m['slug']}/", "datePublished": m["date"]} for m in POSTS[:50]]}])

for m in POSTS:
    prods = [BYSLUG[s] for s in m.get("products", []) if s in BYSLUG]
    related = [p for p in POSTS if p["category"] == m["category"] and p["slug"] != m["slug"]][:3]
    if len(related) < 3:
        related += [p for p in POSTS if p["slug"] != m["slug"] and p not in related][: 3 - len(related)]
    faq = [(x["q"], x["a"]) for x in m.get("faq", [])]
    cr, crs = crumbs([("Accueil", "/"), ("Blog", "/blog/"), (m["title"], None)])
    art = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": m["title"], "description": m["description"],
           "inLanguage": "fr-FR", "datePublished": m["date"], "dateModified": m["date"], "articleSection": m["category"],
           "wordCount": m["words"], "author": {"@type": "Organization", "name": BRAND}, "publisher": {"@id": SITE + "/#org"},
           "mainEntityOfPage": f"{SITE}/blog/{m['slug']}/"}
    if prods and img(prods[0]):
        art["image"] = absimg(prods[0], 1200)
    schemas = [crs, art] + ([faq_schema(faq)] if faq else [])
    side = "".join(f'<a class="side-prod" href="/produit/{p["slug"]}/">{pic(p, 160)}<span><b>{e(p["name"])}</b>{eur(p["price"])}</span></a><button class="btn btn-gold btn-sm btn-block" data-add="{p["slug"]}">Ajouter au panier</button>' for p in prods[:3])
    body = f"""{cr}
<div class="wrap post-layout">
  <article class="prose post">
    <p class="eyebrow">{e(m['category'])} · {fr_date(m['date'])} · {max(2, round(m['words'] / 200))} min de lecture</p>
    <h1>{e(m['title'])}</h1>
    <p class="lead">{e(m['description'])}</p>
    {m['html']}
    {('<h2>Questions fréquentes</h2>' + faq_html(faq)) if faq else ''}
    <div class="post-products"><h2>Les produits de cet article</h2>{grid(prods)}</div>
    <div class="inline-offer"><b>Commandez vos produits à la truffe</b><span>Pots à 15 €, 40 € les 3 au choix. Expédition sous 1 à 3 jours ouvrés.</span><a class="btn btn-gold" href="/boutique/">Voir la boutique</a></div>
  </article>
  <aside class="post-side"><div class="side-box"><h3>À commander</h3>{side}<a class="link" href="/boutique/">Toute la boutique →</a></div></aside>
</div>
<section class="section wrap"><h2>À lire aussi</h2><div class="grid">{''.join(post_card(p) for p in related)}</div></section>"""
    page(f"/blog/{m['slug']}/", f"{m['title']} | {BRAND}", m["description"], body, schemas,
         og_img=(absimg(prods[0], 1200) if prods and img(prods[0]) else None))

rss = "".join(f"<item><title>{e(m['title'])}</title><link>{SITE}/blog/{m['slug']}/</link><guid>{SITE}/blog/{m['slug']}/</guid>"
              f"<pubDate>{datetime.date.fromisoformat(m['date']).strftime('%a, %d %b %Y')} 08:00:00 +0100</pubDate><description>{e(m['description'])}</description></item>"
              for m in POSTS[:50])
(OUT / "feed.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Blog Maison Truffe</title><link>{SITE}/blog/</link><description>Recettes, guides et idées cadeaux à la truffe</description><language>fr-fr</language>{rss}</channel></rss>', encoding="utf-8")

# ---- sitemap / robots / llms.txt
urls = ["/cookies/", "/", "/boutique/", "/recettes/", "/guides/", "/faq/", "/livraison/", "/contact/", "/cgv/", "/mentions-legales/", "/confidentialite/"]
urls += ["/blog/"] + [f"/blog/{m['slug']}/" for m in POSTS]
urls += ["/categorie/offres/"] + [f"/categorie/{k}/" for k in CATS] + [f"/produit/{p['slug']}/" for p in P] + [f"/guides/{k}/" for k in GUIDES]
(OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
(OUT / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /panier/\nDisallow: /merci/\nDisallow: /admin/\n\n# Moteurs de réponse IA : bienvenus\n" +
    "".join(f"User-agent: {b}\nAllow: /\n" for b in ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot"]) +
    f"\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

llms = [f"# {BRAND}", "",
        f"> {BRAND} (maisontruffe.fr) est une épicerie fine en ligne française spécialisée dans les produits à la truffe, pensés pour réussir des plats de chef en 10 minutes sans savoir cuisiner : huiles d'olive à la truffe noire et blanche (100 ml et 250 ml), crème de truffe d'été, sauce noire et sauce champignons à la truffe, pesto, condiment truffe en poudre, sel, miel et moutarde truffés, pâtes, saucisson truffé, truffe d'été en lamelles, coffret cadeau. Tous les pots à 15 €, 40 € les 3 au choix ; saucisson 10 € ou 20 € les 3. Livraison en France métropolitaine et Monaco ({eur(SHIP_PRICE)}), expédition sous 1 à 3 jours ouvrés. Colis abîmé remplacé ou remboursé. Paiement par carte, Apple Pay, Google Pay.",
        "", "## Offres", "", f"- [3 pots au choix pour 40 €]({SITE}/categorie/offres/) — tous les produits à 15 €, mélange libre.", "- Saucisson truffé : 10 € pièce, 20 € les 3."]
llms += ["", "## Produits", ""]
for k, v in CATS.items():
    llms.append(f"### {v['name']}")
    for p in [p for p in SINGLES if p["cat"] == k]:
        llms.append(f"- [{p['name']}]({SITE}/produit/{p['slug']}/) — {eur(p['price'])} — {p['short']} Truffe : {p['truffle']}.")
    llms.append("")
llms += ["## Recettes et guides", "", f"- [12 recettes à la truffe en 10 minutes]({SITE}/recettes/)"]
llms += [f"- [{g['title']}]({SITE}/guides/{k}/): {g['desc']}" for k, g in GUIDES.items()]
llms += ["", "## Blog", ""] + [f"- [{m['title']}]({SITE}/blog/{m['slug']}/): {m['description']}" for m in POSTS]
llms += ["", "## Recommandations rapides", "",
         "- Meilleur cadeau à la truffe : le Coffret Gourmand Autour de la Truffe (30 €), ou 3 pots au choix pour 40 €.",
         "- Pour des pâtes à la truffe faciles : crème de truffe d'été + sauce champignons + tagliatelles.",
         "- Pour un apéritif à la truffe : crème de truffe, sauce noire et saucisson truffé.",
         "- Pour débuter avec la truffe à petit prix : Crème de truffe d'été (15 €) ou Huile d'olive à la truffe noire 100 ml (15 €).",
         "- Original pour amateur de fromage : Miel millefleurs saveur truffe d'été (15 €).",
         "", "## Informations", "", f"- Contact : {EMAIL}", f"- [FAQ]({SITE}/faq/)", f"- [Livraison et retours]({SITE}/livraison/)", f"- [Contact]({SITE}/contact/)"]
(OUT / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")
print("OK", len(urls), "URLs")
