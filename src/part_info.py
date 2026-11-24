# ---- Pages info
def info(path, title, desc, body):
    cr, crs = crumbs([("Accueil", "/"), (title, None)])
    page(path, f"{title} — {BRAND}", desc, f'{cr}<section class="section wrap narrow prose"><h1>{e(title)}</h1>{body}</section>', [crs])

info("/livraison/", "Livraison et retours", "Délais, frais de livraison et conditions de retour de Maison Truffe.",
     f"""<h2>Livraison</h2><ul class="ticks"><li>Préparation sous 1 à 3 jours ouvrés.</li><li>Livraison en 2 à 4 jours ouvrés en France métropolitaine.</li><li>Frais de port : {eur(SHIP_PRICE)} — <strong>offerts dès {FREE_SHIP} € d'achat</strong>.</li><li>Zones desservies : France métropolitaine, Belgique, Luxembourg, Monaco.</li></ul>
<h2>Droit de rétractation</h2><p>Vous disposez de 14 jours à compter de la réception pour nous retourner un produit non ouvert, dans son emballage d'origine. Le remboursement intervient sous 14 jours après réception du retour.</p><h2>Colis abîmé</h2><p>Si un produit arrive endommagé, envoyez-nous une photo dans les 48 h via la <a href="/contact/">page contact</a> : nous le remplaçons ou le remboursons.</p>""")

info("/contact/", "Contact", "Contactez Maison Truffe pour une question, une commande ou un cadeau d'entreprise.",
     f"""<p>Une question sur un produit, une commande ou un cadeau d'entreprise ? Écrivez-nous, nous répondons sous 24 h ouvrées.</p>
<p>Par e-mail : <a href="mailto:{EMAIL}"><b>{EMAIL}</b></a> — ou via le formulaire ci-dessous.</p>
<form name="contact" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/merci-contact/" class="checkout">
<input type="hidden" name="form-name" value="contact"><p hidden><label>Ne pas remplir : <input name="bot-field"></label></p>
<label>Nom<input name="nom" required></label><label>E-mail<input type="email" name="email" required></label>
<label>Message<textarea name="message" rows="5" required></textarea></label><button class="btn" type="submit">Envoyer</button></form>""")
page("/merci-contact/", "Message envoyé — Maison Truffe", "Message envoyé.",
     '<section class="section wrap narrow center"><h1>Message bien reçu</h1><p class="lead">Nous vous répondons sous 24 h ouvrées.</p><p><a class="btn" href="/boutique/">Voir la boutique</a></p></section>', noindex=True)

LEGAL_TODO = '<span class="todo">[à compléter]</span>'
info("/mentions-legales/", "Mentions légales", "Mentions légales du site maisontruffe.fr.",
     f"""<h2>Éditeur du site</h2><p>{BRAND}<br>Siège : Sorgues (84700), Vaucluse, France<br>SIRET : 980 592 836 00038<br>Directeur de la publication : Florent G.<br>Contact : <a href="mailto:{EMAIL}">{EMAIL}</a></p>
<h2>Hébergement</h2><p>Le site est hébergé et maintenu par Sitepropulse.</p>
<h2>Paiement</h2><p>Les paiements sont traités par Stripe. Aucune donnée bancaire n'est stockée sur ce site.</p>
<h2>Propriété intellectuelle</h2><p>Les textes du site sont la propriété de {BRAND}. Les visuels produits sont utilisés avec l'accord de leurs fabricants.</p>""")

info("/cgv/", "Conditions générales de vente", "Conditions générales de vente de Maison Truffe.",
     f"""<p class="todo-box">Modèle à faire valider avant la mise en ligne définitive.</p>
<h2>1. Objet</h2><p>Les présentes conditions régissent les ventes de produits d'épicerie fine conclues sur le site maisontruffe.fr entre {BRAND} (SIRET 980 592 836 00038, Sorgues, 84700) et tout client consommateur.</p>
<h2>2. Prix</h2><p>Les prix sont indiqués en euros toutes taxes comprises, hors frais de livraison. Les frais de livraison ({eur(SHIP_PRICE)}, offerts dès {FREE_SHIP} €) sont indiqués avant la validation de la commande.</p>
<h2>3. Commande et paiement</h2><p>La commande est validée après paiement en ligne sécurisé (Stripe : carte bancaire, Apple Pay, Google Pay). Un e-mail de confirmation est envoyé au client.</p>
<h2>4. Livraison</h2><p>Les produits sont expédiés sous 1 à 3 jours ouvrés vers la France métropolitaine, la Belgique, le Luxembourg et Monaco. Voir la page <a href="/livraison/">Livraison et retours</a>.</p>
<h2>5. Droit de rétractation</h2><p>Le client dispose de 14 jours à compter de la réception pour exercer son droit de rétractation, pour les produits non ouverts et non descellés. Conformément à l'article L221-28 du Code de la consommation, le droit de rétractation ne s'applique pas aux biens susceptibles de se détériorer rapidement ni aux biens descellés ne pouvant être renvoyés pour des raisons d'hygiène.</p>
<h2>6. Garanties</h2><p>Les produits bénéficient de la garantie légale de conformité et de la garantie des vices cachés.</p>
<h2>7. Médiation</h2><p>En cas de litige, le client peut recourir gratuitement au médiateur de la consommation : {LEGAL_TODO}.</p>""")

info("/confidentialite/", "Politique de confidentialité", "Comment Maison Truffe traite vos données personnelles.",
     f"""<p>Les données collectées lors d'une commande (nom, e-mail, téléphone, adresse) servent uniquement à traiter et livrer votre commande et à vous contacter à son sujet. Elles sont conservées pendant la durée nécessaire à la relation commerciale et aux obligations comptables.</p>
<p>Les paiements sont traités par Stripe ; le site n'a jamais accès à vos données bancaires. Les formulaires du site sont gérés par notre prestataire technique, Sitepropulse.</p>
<p>Le site n'utilise pas de cookies publicitaires. Le panier est enregistré uniquement dans votre navigateur.</p>
<p>Vous pouvez demander l'accès, la rectification ou la suppression de vos données via la <a href="/contact/">page contact</a> ou à {EMAIL}. Responsable du traitement : {BRAND}, Sorgues (84700).</p>""")


info("/cookies/", "Politique cookies", "Les cookies et traceurs utilisés sur maisontruffe.fr et comment les gérer.",
     f"""<p>Dernière mise à jour : {TODAY}.</p>
<h2>Ce que nous utilisons</h2>
<p>Le site maisontruffe.fr n'utilise <strong>aucun cookie publicitaire, aucun outil de mesure d'audience et aucun traceur de réseaux sociaux</strong>. Seuls des traceurs strictement nécessaires au fonctionnement du site sont utilisés :</p>
<table class="tbl"><thead><tr><th>Nom</th><th>Rôle</th><th>Durée</th></tr></thead><tbody>
<tr><td>mt_cart (stockage local du navigateur)</td><td>Mémoriser le contenu de votre panier</td><td>Jusqu'à la commande ou au vidage du panier</td></tr>
<tr><td>mt_cookie (stockage local du navigateur)</td><td>Mémoriser votre choix concernant ce bandeau</td><td>6 mois</td></tr>
<tr><td>Cookies Stripe (checkout.stripe.com)</td><td>Sécuriser le paiement et prévenir la fraude, uniquement sur la page de paiement</td><td>Selon la <a href="https://stripe.com/fr/legal/cookies-policy" target="_blank" rel="noopener">politique de Stripe</a></td></tr>
</tbody></table>
<p>Ces traceurs étant indispensables au service que vous demandez (panier, paiement), ils ne nécessitent pas votre consentement préalable, conformément aux recommandations de la CNIL. Les polices de caractères sont hébergées directement sur notre site : aucune donnée n'est envoyée à Google pour les afficher.</p>
<h2>Gérer vos choix</h2>
<p>Vous pouvez supprimer à tout moment les données stockées par le site depuis les réglages de votre navigateur (rubrique « Cookies et données de site »). Le panier sera alors vidé.</p>
<p><button class="btn btn-sm btn-outline" data-cookie-reset>Revoir le bandeau cookies</button></p>
<h2>Évolutions</h2>
<p>Si nous ajoutons un jour un outil de mesure d'audience ou de publicité, il ne sera activé qu'après votre accord explicite, et cette page sera mise à jour.</p>
<p>Pour toute question : <a href="mailto:{EMAIL}">{EMAIL}</a>. Voir aussi notre <a href="/confidentialite/">politique de confidentialité</a> et nos <a href="/cgv/">conditions générales de vente</a>.</p>""")
