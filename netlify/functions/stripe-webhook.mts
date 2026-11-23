import type { Context } from "@netlify/functions"
import { createHmac, timingSafeEqual } from "node:crypto"
import { CATALOG, PACKAGING_G, OWNER_EMAIL } from "../lib/catalog.mts"
import { ordersStore, type Order } from "../lib/orders.mts"

// Reçoit l'événement Stripe « checkout.session.completed » (paiement réussi) et envoie, via Brevo :
//  1) au client : l'e-mail « Merci pour votre commande »
//  2) à la boutique : la fiche d'expédition (adresse ou Point Relais, contenu, poids)
// Variables d'environnement : STRIPE_WEBHOOK_SECRET, BREVO_API_KEY, MAIL_SENDER (ex. commandes@maisontruffe.fr)

const eur = (cents: number) => (cents / 100).toFixed(2).replace(".", ",") + " €"
export const esc = (s: unknown) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!)

function verify(raw: string, header: string | null, secret: string): boolean {
  if (!header) return false
  const parts = Object.fromEntries(header.split(",").map((kv) => kv.split("=") as [string, string]))
  const t = parts["t"], sig = header.split(",").filter((kv) => kv.startsWith("v1=")).map((kv) => kv.slice(3))
  if (!t || !sig.length) return false
  if (Math.abs(Date.now() / 1000 - Number(t)) > 600) return false
  const expected = createHmac("sha256", secret).update(`${t}.${raw}`).digest("hex")
  return sig.some((s) => s.length === expected.length && timingSafeEqual(Buffer.from(s), Buffer.from(expected)))
}

export async function send(to: { email: string; name?: string }, subject: string, html: string) {
  const key = Netlify.env.get("BREVO_API_KEY"), sender = Netlify.env.get("MAIL_SENDER")
  if (!key || !sender) { console.log("Brevo non configuré : e-mail non envoyé →", to.email, subject); return }
  const r = await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: { "api-key": key, "Content-Type": "application/json", accept: "application/json" },
    body: JSON.stringify({ sender: { name: "Maison Truffe", email: sender }, replyTo: { email: OWNER_EMAIL, name: "Maison Truffe" },
      to: [to], subject, htmlContent: html }),
  })
  if (!r.ok) console.error("Brevo", r.status, await r.text())
}

export function layout(inner: string) {
  return `<!doctype html><html lang="fr"><body style="margin:0;background:#f6efe2;font-family:Arial,Helvetica,sans-serif;color:#1d1712">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f6efe2;padding:24px 0"><tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fffcf6;border-radius:16px;overflow:hidden">
<tr><td align="center" style="padding:28px 24px 8px"><img src="https://maisontruffe.fr/assets/logo-maison-truffe.png" width="220" alt="Maison Truffe" style="display:block;max-width:220px"></td></tr>
<tr><td style="padding:8px 32px 28px;font-size:15px;line-height:1.6">${inner}</td></tr>
<tr><td style="background:#16110d;color:#cbbd9f;padding:18px 32px;font-size:12px;line-height:1.5">Maison Truffe — Spécialités à la truffe · <a href="https://maisontruffe.fr" style="color:#e2c88f">maisontruffe.fr</a><br>Une question ? Répondez simplement à cet e-mail ou écrivez à ${OWNER_EMAIL}.</td></tr>
</table></td></tr></table></body></html>`
}

export default async (req: Request, context: Context) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 })
  const secret = Netlify.env.get("STRIPE_WEBHOOK_SECRET")
  const raw = await req.text()
  if (!secret || !verify(raw, req.headers.get("stripe-signature"), secret)) return new Response("Signature invalide", { status: 400 })

  const evt = JSON.parse(raw)
  if (evt.type !== "checkout.session.completed") return Response.json({ ignored: evt.type })
  const s = evt.data.object
  if (s.payment_status && s.payment_status !== "paid") return Response.json({ ignored: "unpaid" })

  const md = s.metadata || {}
  const no = md.commande_no || s.client_reference_id || String(s.id).slice(-8).toUpperCase()
  const lines = String(md.items || "").split(";").filter(Boolean).map((x: string) => {
    const [slug, q] = x.split(":"); const p = CATALOG[slug]
    return { name: p?.name ?? slug, qty: Number(q) || 1, price: p?.price ?? 0, w: p?.weight_g ?? null }
  })
  const cust = s.customer_details || {}
  const ship = s.shipping_details || s.collected_information?.shipping_details || {}
  const addr = ship.address || cust.address || {}
  const name = ship.name || cust.name || md.nom || ""
  const first = String(name).split(" ")[0] || ""
  const rows = lines.map((l) => `<tr><td style="padding:6px 0;border-bottom:1px solid #e8dcc6">${l.qty} × ${esc(l.name)}</td><td align="right" style="padding:6px 0;border-bottom:1px solid #e8dcc6">${eur(Math.round(l.price * 100) * l.qty)}</td></tr>`).join("")
  const shipCost = s.total_details?.amount_shipping ?? 0
  const addrHtml = [name, addr.line1, addr.line2, `${addr.postal_code ?? ""} ${addr.city ?? ""}`, ({ FR: "France", BE: "Belgique", LU: "Luxembourg", MC: "Monaco" } as Record<string, string>)[addr.country] ?? addr.country].filter(Boolean).map(esc).join("<br>")
  const relay = md.relais ? `<p><b>Point Relais choisi :</b> ${esc(md.relais)}</p>` : ""

  // 1) Client
  if (cust.email) {
    await send({ email: cust.email, name }, `Merci pour votre commande n° ${no} — Maison Truffe`, layout(`
<h1 style="font-family:Georgia,serif;font-size:26px;margin:0 0 12px">Merci ${esc(first)} !</h1>
<p style="background:#f6efe2;border-radius:10px;padding:10px 14px;font-size:16px">Commande n° <b>${esc(no)}</b></p>
<p>Votre commande est bien confirmée et votre paiement a été reçu. Nous la préparons avec soin : elle sera expédiée sous <b>1 à 3 jours ouvrés</b>, et vous recevrez un e-mail avec le suivi du colis dès son départ.</p>
<h2 style="font-family:Georgia,serif;font-size:19px;margin:22px 0 6px">Votre commande</h2>
<table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px">${rows}
<tr><td style="padding:6px 0">Livraison</td><td align="right">${shipCost ? eur(shipCost) : "Offerte"}</td></tr>
<tr><td style="padding:8px 0;font-weight:bold">Total payé</td><td align="right" style="font-weight:bold">${eur(s.amount_total ?? 0)}</td></tr></table>
${relay}${addrHtml ? `<p><b>Livraison :</b><br>${addrHtml}</p>` : ""}
<h2 style="font-family:Georgia,serif;font-size:19px;margin:22px 0 6px">En attendant votre colis…</h2>
<p>Découvrez nos <a href="https://maisontruffe.fr/recettes/" style="color:#8f6c2c;font-weight:bold">12 recettes à la truffe en 10 minutes</a> : tagliatelles crémeuses, œufs brouillés truffés, planche apéro… chaque recette indique quel produit utiliser.</p>
<p>Un pot abîmé à la réception ? Envoyez-nous une photo sous 48 h en rappelant votre numéro de commande, on le remplace.</p>
<p>À très bientôt,<br><b>L'équipe Maison Truffe</b></p>`))
  }

  // 2) Boutique : fiche d'expédition
  const wKnown = lines.every((l) => l.w)
  const wTotal = wKnown ? lines.reduce((a, l) => a + (l.w as number) * l.qty, 0) + PACKAGING_G : null
  await send({ email: OWNER_EMAIL, name: "Maison Truffe" }, `🛒 Commande ${no} à expédier — ${eur(s.amount_total ?? 0)} — ${name}`, layout(`
<h1 style="font-family:Georgia,serif;font-size:24px;margin:0 0 12px">Commande n° ${esc(no)} — payée</h1>
<p><b>Client :</b> ${esc(name)} · ${esc(cust.email)} · ${esc(cust.phone || "")}</p>
<p><b>Mode de livraison :</b> ${esc(md.livraison || "Domicile")}</p>${relay}
<p><b>Adresse :</b><br>${addrHtml || "—"}</p>
<table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px">${lines.map((l) => `<tr><td style="padding:5px 0;border-bottom:1px solid #e8dcc6">${l.qty} × ${esc(l.name)}</td><td align="right" style="border-bottom:1px solid #e8dcc6">${l.w ? (l.w * l.qty) + " g" : "poids ?"}</td></tr>`).join("")}</table>
<p style="font-size:18px"><b>Poids du colis à déclarer : ${wTotal ? (wTotal / 1000).toFixed(2).replace(".", ",") + " kg" : "à peser (poids produit manquant)"}</b>${wTotal ? ` <span style="color:#75695b;font-size:13px">(produits + ${PACKAGING_G} g d'emballage)</span>` : ""}</p>
<p><b>Total payé :</b> ${eur(s.amount_total ?? 0)} (dont livraison ${eur(shipCost)})</p>
${md.message ? `<p><b>Message du client :</b> ${esc(md.message)}</p>` : ""}
<p>➜ Créez l'étiquette sur <a href="https://www.boxtal.com" style="color:#8f6c2c">Boxtal</a> avec ce poids et cette adresse.</p>`))

  // 3) Enregistrement dans le tableau de bord des commandes
  try {
    const store = ordersStore()
    if (!(await store.get(no))) {
      const order: Order = {
        no, date: new Date((s.created ?? Date.now() / 1000) * 1000).toISOString(), status: "Nouvelle",
        name, email: cust.email ?? "", phone: cust.phone ?? "", delivery: md.livraison || "Domicile", relay: md.relais || "",
        address: [addr.line1, addr.line2, `${addr.postal_code ?? ""} ${addr.city ?? ""}`].filter(Boolean).join(", "),
        postal: addr.postal_code ?? "", country: addr.country ?? "FR",
        items: lines, weight_g: wTotal, total: (s.amount_total ?? 0) / 100, shipping: shipCost / 100, message: md.message || "",
        carrier: "Mondial Relay", tracking: "", history: [{ at: new Date().toISOString(), status: "Nouvelle" }],
      }
      await store.setJSON(no, order)
    }
  } catch (e) { console.error("Enregistrement commande", e) }

  return Response.json({ ok: true })
}
