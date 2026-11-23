# Maison Truffe — maisontruffe.fr

Site statique généré par `python3 src/build.py` dans `public/` (Netlify le construit automatiquement).

- Produits : `src/products.json`
- Articles du blog : `src/blog/*.md` (un article daté dans le futur n'est publié qu'à sa date)
- Paiement : `netlify/functions/checkout.mts` (variable d'environnement `STRIPE_SECRET_KEY`)
