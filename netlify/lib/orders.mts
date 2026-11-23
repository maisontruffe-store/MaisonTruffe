import { getStore } from "@netlify/blobs"
export type Order = {
  no: string; date: string; status: string; name: string; email: string; phone: string
  delivery: string; relay: string; address: string; postal: string; country: string
  items: { name: string; qty: number; price: number; w: number | null }[]
  weight_g: number | null; total: number; shipping: number; message: string
  carrier: string; tracking: string; history: { at: string; status: string }[]
}
export const ordersStore = () => getStore({ name: "orders", consistency: "strong" })
