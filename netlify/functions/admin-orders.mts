import type { Context } from "@netlify/functions"
import { createHash, timingSafeEqual } from "node:crypto"
import { ordersStore, type Order } from "../lib/orders.mts"
import { send, layout, esc } from "./stripe-webhook.mts"

// Tableau de bord des commandes (page /admin/). Protégé par la variable ADMIN_PASSWORD.
// GET  → liste des commandes   ·   POST {no, status, tracking, carrier} → mise à jour (+ e-mail client si « Expédiée »)
const STATUSES = ["Nouvelle", "En préparation", "Expédiée", "Livrée", "Annulée"]
const h = (s: string) => createHash("sha256").update(s).digest()

function trackingUrl(o: Order) {
  if (!o.tracking) return ""
  if (/colissimo/i.test(o.carrier)) return `https://www.laposte.fr/outils/suivre-vos-envois?code=${encodeURIComponent(o.tracking)}`
  return `https://www.mondialrelay.fr/suivi-de-colis/?numeroExpedition=${encodeURIComponent(o.tracking)}&codePostal=${encodeURIComponent(o.postal)}`
}

export default async (req: Request, context: Context) => {
  const pass = Netlify.env.get("ADMIN_PASSWORD")
  const given = req.headers.get("x-admin-key") ?? ""
  if (!pass || !timingSafeEqual(h(pass), h(given))) return Response.json({ error: "Mot de passe incorrect" }, { status: 401 })
  const store = ordersStore()

  if (req.method === "GET") {
    const { blobs } = await store.list()
    const orders = (await Promise.all(blobs.map((b) => store.get(b.key, { type: "json" })))).filter(Boolean) as Order[]
    orders.sort((a, b) => b.date.localeCompare(a.date))
    return Response.json({ orders, statuses: STATUSES })
  }

  if (req.method === "POST") {
    const body = await req.json().catch(() => ({}))
    const o = (await store.get(String(body.no ?? ""), { type: "json" })) as Order | null
    if (!o) return Response.json({ error: "Commande introuvable" }, { status: 404 })
    if (typeof body.tracking === "string") o.tracking = body.tracking.trim().slice(0, 60)
    if (typeof body.carrier === "string" && body.carrier) o.carrier = body.carrier.slice(0, 40)
    let mailed = false
    if (body.status && STATUSES.includes(body.status) && body.status !== o.status) {
      o.status = body.status
      o.history.push({ at: new Date().toISOString(), status: o.status })
      if (o.status === "Expédiée" && o.email) {
        const url = trackingUrl(o)
        const first = o.name.split(" ")[0] || ""
        await send({ email: o.email, name: o.name }, `Votre commande n° ${o.no} est en route 🚚 — Maison Truffe`, layout(`
<h1 style="font-family:Georgia,serif;font-size:26px;margin:0 0 12px">Bonne nouvelle ${esc(first)} !</h1>
<p>Votre commande n° <b>${esc(o.no)}</b> vient d'être expédiée${o.carrier ? " avec <b>" + esc(o.carrier) + "</b>" : ""}.</p>
${o.relay ? `<p>Elle sera livrée dans votre Point Relais : <b>${esc(o.relay)}</b>. Vous recevrez un message du transporteur dès qu'elle y sera disponible.</p>` : `<p>Elle sera livrée à l'adresse : ${esc(o.address)}.</p>`}
${url ? `<p style="text-align:center;margin:24px 0"><a href="${url}" style="background:#c09a4e;color:#1b130b;text-decoration:none;font-weight:bold;padding:14px 26px;border-radius:999px;display:inline-block">Suivre mon colis</a></p><p style="font-size:13px;color:#75695b">Numéro de suivi : ${esc(o.tracking)}</p>` : ""}
<p>En attendant, voici <a href="https://maisontruffe.fr/recettes/" style="color:#8f6c2c;font-weight:bold">12 recettes à la truffe en 10 minutes</a> pour en profiter dès l'arrivée du colis.</p>
<p>À très bientôt,<br><b>L'équipe Maison Truffe</b></p>`))
        mailed = true
      }
    }
    await store.setJSON(o.no, o)
    return Response.json({ order: o, mailed })
  }
  return new Response("Method not allowed", { status: 405 })
}
