import type { Context } from "@netlify/functions"
import { CATALOG, SHIP, PACKAGING_G, PROMOS } from "../lib/catalog.mts"

// Crée une session de paiement Stripe Checkout à partir du panier.
// Les prix viennent du catalogue côté serveur (jamais du navigateur).
// Sans STRIPE_SECRET_KEY, renvoie { mode: "manual" } : la commande reste
// enregistrée par e-mail via Netlify Forms et vous envoyez un lien de paiement.

type Item = { slug: string; qty: number }

export default async (req: Request, context: Context) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 })

  let body: { items?: Item[]; customer?: { name?: string; email?: string; phone?: string; message?: string } }
  try {
    body = await req.json()
  } catch {
    return Response.json({ error: "JSON invalide" }, { status: 400 })
  }

  const items = (body.items || [])
    .filter((i) => i && CATALOG[i.slug] && Number.isInteger(i.qty) && i.qty > 0 && i.qty <= 50)
    .slice(0, 40)
  if (!items.length) return Response.json({ error: "Panier vide" }, { status: 400 })

  const key = Netlify.env.get("STRIPE_SECRET_KEY")
  if (!key) return Response.json({ mode: "manual" })

  const origin = new URL(req.url).origin
  // Offres lot (ex. 3 pots au choix pour 40 €) : on regroupe les articles concernés en lots
  type Line = { name: string; cents: number; qty: number; img?: string; desc?: string }
  const lineItems: Line[] = []
  const rest: Record<string, number> = {}
  items.forEach((i) => { rest[i.slug] = (rest[i.slug] || 0) + i.qty })
  for (const [key, pr] of Object.entries(PROMOS)) {
    const units: string[] = []
    items.forEach((i) => { if (CATALOG[i.slug].promo === key) for (let k = 0; k < i.qty; k++) units.push(i.slug) })
    units.sort((a, b) => CATALOG[b].price - CATALOG[a].price)
    const lots = Math.floor(units.length / pr.n)
    if (!lots) continue
    const inLots = units.slice(0, lots * pr.n)
    inLots.forEach((sl) => { rest[sl] -= 1 })
    const count: Record<string, number> = {}
    inLots.forEach((sl) => { count[sl] = (count[sl] || 0) + 1 })
    lineItems.push({ name: `${pr.label} (${pr.n} pour ${String(pr.price).replace(".", ",")} €)`, cents: Math.round(pr.price * 100), qty: lots,
      desc: Object.entries(count).map(([sl, n]) => `${n} × ${CATALOG[sl].name}`).join(", ").slice(0, 490) })
  }
  Object.entries(rest).forEach(([sl, q]) => { if (q > 0) lineItems.push({ name: CATALOG[sl].name, cents: Math.round(CATALOG[sl].price * 100), qty: q, img: CATALOG[sl].img }) })
  const subtotal = lineItems.reduce((s, l) => s + l.cents * l.qty, 0) / 100
  const onlyTest = items.every((i) => CATALOG[i.slug].test)
  const shipCents = subtotal >= SHIP.free || onlyTest ? 0 : Math.round(SHIP.price * 100)

  const p = new URLSearchParams()
  p.set("mode", "payment")
  p.set("locale", "fr")
  p.set("success_url", `${origin}/merci/?session_id={CHECKOUT_SESSION_ID}`)
  p.set("cancel_url", `${origin}/panier/`)
  p.set("billing_address_collection", "auto")
  p.set("phone_number_collection[enabled]", "true")
  ;["FR", "BE", "LU", "MC"].forEach((c, n) => p.set(`shipping_address_collection[allowed_countries][${n}]`, c))
  p.set("shipping_options[0][shipping_rate_data][type]", "fixed_amount")
  p.set("shipping_options[0][shipping_rate_data][display_name]", shipCents ? "Livraison Colissimo" : "Livraison offerte")
  p.set("shipping_options[0][shipping_rate_data][fixed_amount][amount]", String(shipCents))
  p.set("shipping_options[0][shipping_rate_data][fixed_amount][currency]", "eur")
  p.set("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][unit]", "business_day")
  p.set("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][value]", "3")
  p.set("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][unit]", "business_day")
  p.set("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]", "7")

  const email = body.customer?.email?.trim()
  if (email && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) p.set("customer_email", email)

  lineItems.forEach((l, n) => {
    p.set(`line_items[${n}][quantity]`, String(l.qty))
    p.set(`line_items[${n}][price_data][currency]`, "eur")
    p.set(`line_items[${n}][price_data][unit_amount]`, String(l.cents))
    p.set(`line_items[${n}][price_data][product_data][name]`, l.name)
    if (l.desc) p.set(`line_items[${n}][price_data][product_data][description]`, l.desc)
    if (l.img && l.img.startsWith("https://")) p.set(`line_items[${n}][price_data][product_data][images][0]`, l.img)
  })

  // Numéro de commande lisible : MT-AAMMJJ-XXXX
  const d = new Date(), pad = (n: number) => String(n).padStart(2, "0")
  const rnd = Array.from(crypto.getRandomValues(new Uint8Array(4))).map((b) => "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"[b % 32]).join("")
  const orderNo = `MT-${String(d.getFullYear()).slice(2)}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${rnd}`
  p.set("client_reference_id", orderNo)
  p.set("metadata[commande_no]", orderNo)
  p.set("payment_intent_data[metadata][commande_no]", orderNo)
  const recap = items.map((i) => `${i.qty}x ${CATALOG[i.slug].name}`).join(" | ").slice(0, 490)
  p.set("metadata[items]", items.map((i) => `${i.slug}:${i.qty}`).join(";").slice(0, 490))
  const weights = items.map((i) => (CATALOG[i.slug].weight_g ? CATALOG[i.slug].weight_g! * i.qty : null))
  p.set("metadata[poids_g]", weights.every((w) => w !== null) ? String(weights.reduce((a, b) => a! + b!, 0)! + PACKAGING_G) : "inconnu")
  p.set("payment_intent_data[description]", `Commande ${orderNo} — ${recap}`.slice(0, 490))
  p.set("metadata[commande]", recap)
  if (body.customer?.name) p.set("metadata[nom]", String(body.customer.name).slice(0, 200))
  if (body.customer?.message) p.set("metadata[message]", String(body.customer.message).slice(0, 490))

  const res = await fetch("https://api.stripe.com/v1/checkout/sessions", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: p.toString(),
  })
  const data = await res.json()
  if (!res.ok || !data.url) {
    console.error("Stripe error", data?.error?.message)
    return Response.json({ mode: "manual" })
  }
  return Response.json({ url: data.url })
}
