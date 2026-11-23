(function () {
  var KEY = "mt_cart";
  var C = window.MT_CATALOG || {};
  var S = window.MT_SHIP || { price: 6.9, free: 59 };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  function load() { try { var c = JSON.parse(localStorage.getItem(KEY) || "{}"); return c && typeof c === "object" ? c : {}; } catch (e) { return {}; } }
  function save(c) { try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {} render(); }
  function eur(x) { var s = x.toFixed(2).replace(".", ","); return (s.slice(-3) === ",00" ? s.slice(0, -3) : s) + " €"; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]; }); }
  function lines(c) { return Object.keys(c).filter(function (k) { return C[k] && c[k] > 0; }).map(function (k) { return { slug: k, qty: c[k], p: C[k] }; }); }
  function totals(c) {
    var sub = lines(c).reduce(function (s, l) { return s + l.p.price * l.qty; }, 0);
    var ship = sub === 0 ? 0 : (sub >= S.free ? 0 : S.price);
    return { sub: sub, ship: ship, total: sub + ship };
  }
  function toast(msg) {
    var t = $("[data-toast]"); if (!t) return;
    t.innerHTML = msg; t.classList.add("show");
    clearTimeout(t._h); t._h = setTimeout(function () { t.classList.remove("show"); }, 3400);
  }

  function render() {
    var c = load(), ls = lines(c), t = totals(c);
    var n = ls.reduce(function (s, l) { return s + l.qty; }, 0);
    $$("[data-cart-count]").forEach(function (el) {
      if (el.textContent !== String(n)) { el.textContent = n; el.classList.remove("bump"); void el.offsetWidth; el.classList.add("bump"); }
    });
    var fc = $("[data-float-cart]");
    if (fc) {
      var onCart = location.pathname.indexOf("/panier") === 0;
      fc.hidden = n === 0 || onCart || !!$("[data-sticky].show");
      $("[data-fc-n]").textContent = n; $("[data-fc-t]").textContent = eur(t.total);
    }
    var box = $("[data-cart-lines]");
    if (!box) return;
    box.innerHTML = ls.map(function (l) {
      var im = l.p.img ? '<img src="' + l.p.img + '" alt="">' : '<div class="ph">◆</div>';
      return '<div class="line">' + im +
        '<div><a href="/produit/' + l.slug + '/">' + esc(l.p.name) + '</a><br><span class="muted small">' + eur(l.p.price) + '</span> · <button class="rm" data-rm="' + l.slug + '">Retirer</button></div>' +
        '<label class="qty"><button type="button" data-dec="' + l.slug + '" aria-label="Moins">−</button><input type="number" value="' + l.qty + '" min="1" max="50" data-set="' + l.slug + '" aria-label="Quantité"><button type="button" data-inc="' + l.slug + '" aria-label="Plus">+</button></label>' +
        '<strong>' + eur(l.p.price * l.qty) + '</strong></div>';
    }).join("");
    var empty = ls.length === 0;
    $("[data-cart-empty]").hidden = !empty;
    $("[data-cart-summary]").style.display = empty ? "none" : "";
    $("[data-meter]").style.display = empty ? "none" : "";
    $("[data-subtotal]").textContent = eur(t.sub);
    $("[data-shipping]").textContent = t.ship === 0 ? "Offerte" : eur(t.ship);
    $("[data-total]").textContent = eur(t.total);
    $("[data-meter-bar]").style.width = Math.min(100, t.sub / S.free * 100) + "%";
    $("[data-free-hint]").textContent = t.sub >= S.free ? "🎉 Bravo, la livraison est offerte !" : "Plus que " + eur(S.free - t.sub) + " pour la livraison offerte";
    // suggestions pour atteindre la livraison offerte
    var bump = $("[data-bump]"), gap = S.free - t.sub;
    if (!empty && gap > 0) {
      var picks = Object.keys(C).filter(function (k) { return !c[k] && C[k].cat !== "offres"; })
        .sort(function (a, b) { return Math.abs(C[a].price - gap) - Math.abs(C[b].price - gap); }).slice(0, 3);
      $("[data-bump-items]").innerHTML = picks.map(function (k) {
        return '<div class="bump-item">' + (C[k].img ? '<img src="' + C[k].img + '" alt="">' : "") + '<span><a href="/produit/' + k + '/">' + esc(C[k].name) + '</a></span><b>' + eur(C[k].price) + '</b><button class="btn btn-sm" data-add="' + k + '">+ Ajouter</button></div>';
      }).join("");
      bump.hidden = false;
    } else bump.hidden = true;
  }

  document.addEventListener("click", function (ev) {
    var b = ev.target.closest("button"); if (!b) return;
    var c = load(), d = b.dataset;
    if (d.add) {
      var q = 1;
      if (d.withQty !== undefined) { var inp = $("[data-qty]"); q = Math.max(1, parseInt(inp && inp.value, 10) || 1); }
      c[d.add] = (c[d.add] || 0) + q; save(c);
      var txt = b.textContent; b.classList.add("added"); b.textContent = "✓ Ajouté";
      setTimeout(function () { b.classList.remove("added"); b.textContent = txt; }, 1400);
      var t = totals(load()), gap = S.free - t.sub;
      toast("Ajouté au panier ✓ " + (gap > 0 ? "· plus que " + eur(gap) + " pour la livraison offerte" : "· livraison offerte !") + ' <a href="/panier/">Panier →</a>');
    } else if (d.inc) { c[d.inc] = (c[d.inc] || 0) + 1; save(c); }
    else if (d.dec) { c[d.dec] = Math.max(1, (c[d.dec] || 1) - 1); save(c); }
    else if (d.rm) { delete c[d.rm]; save(c); }
    else if (d.qplus !== undefined || d.qminus !== undefined) {
      var i = $("[data-qty]"), v = parseInt(i.value, 10) || 1;
      i.value = Math.min(20, Math.max(1, v + (d.qplus !== undefined ? 1 : -1)));
    } else if (d.filter) {
      var wrap = b.closest("[data-tabs]");
      $$(".tab", wrap).forEach(function (x) { x.classList.toggle("active", x === b); });
      var grid = wrap.nextElementSibling;
      $$(".card", grid).forEach(function (card) {
        card.classList.toggle("hide", d.filter !== "all" && card.dataset.cat !== d.filter);
        card.classList.add("in");
      });
    }
  });
  document.addEventListener("change", function (ev) {
    var s = ev.target.dataset && ev.target.dataset.set;
    if (s) { var c = load(); c[s] = Math.max(1, parseInt(ev.target.value, 10) || 1); save(c); }
  });

  // ---------- Quiz
  var quiz = $("[data-quiz]");
  if (quiz) {
    var ans = [], steps = $$(".q-step", quiz), bar = $("[data-q-bar]", quiz);
    var R = {
      offrir: { l: "grand-coffret-truffe", m: "coffret-gourmand-autour-de-la-truffe", s: "creme-de-truffe-ete" },
      pates: { l: "kit-pates-truffees", m: "huile-olive-vierge-extra-truffe-blanche", s: "creme-de-truffe-ete" },
      apero: { l: "box-apero-truffe", m: "coffret-gourmand-autour-de-la-truffe", s: "delice-artichaut-truffes-ete" },
      quotidien: { l: "grand-coffret-truffe", m: "huile-olive-vierge-extra-truffe-noire", s: "condiment-saveur-truffe-ete-poudre" },
      fromage: { l: "box-apero-truffe", m: "miel-acacia-saveur-truffe-ete", s: "miel-acacia-saveur-truffe-ete" }
    };
    var WHY = {
      pates: "Pour des pâtes à la truffe dignes d'un restaurant, en 10 minutes.",
      apero: "Pour un apéritif qui impressionne vos invités, sans rien cuisiner.",
      quotidien: "Pour mettre de la truffe dans vos plats de tous les jours, en un geste.",
      fromage: "L'accord sucré-salé qui sublime chèvre, brebis et fromages affinés."
    };
    function go(i) {
      steps.forEach(function (s, k) { s.classList.toggle("active", k === i); });
      bar.style.width = (i / 3 * 100) + "%";
    }
    quiz.addEventListener("click", function (ev) {
      var b = ev.target.closest("button"); if (!b) return;
      if (b.hasAttribute("data-q-restart")) { ans = []; go(0); return; }
      if (!b.dataset.a) return;
      ans.push(b.dataset.a);
      if (ans.length < 3) { go(ans.length); return; }
      var who = ans[0], want = ans[1], bud = ans[2];
      var slug = (who === "offrir" && bud !== "s") ? R.offrir[bud] : (who === "offrir" && want === "fromage") ? "miel-acacia-saveur-truffe-ete" : (who === "offrir" ? R.offrir.s : R[want][bud]);
      var p = C[slug];
      var why = who === "offrir" ? "Un cadeau gourmand qui fait toujours son effet. " + (WHY[want] || "") : WHY[want];
      $("[data-q-result]", quiz).innerHTML = '<p class="eyebrow">Notre recommandation pour vous</p><div class="q-reco">' +
        (p.img ? '<img src="' + p.img.replace("width=200", "width=400") + '" alt="">' : '<div class="img-ph">◆</div>') +
        '<div><h4>' + esc(p.name) + '</h4><p>' + esc(why) + '</p><span class="price">' + eur(p.price) + '</span>' +
        '<button class="btn btn-gold" data-add="' + slug + '">Ajouter au panier</button> <a class="link" href="/produit/' + slug + '/">Voir le détail →</a></div></div>';
      go(3); bar.style.width = "100%";
    });
  }

  // ---------- Compte à rebours Noël
  var top = $("[data-noel]");
  if (top) {
    var end = new Date(top.dataset.noel + "T23:59:59");
    var cd = $("[data-countdown]"), msg = $("[data-noel-msg]"), def = $("[data-default-msg]"), pill = $("[data-noel-pill]");
    var tick = function () {
      var ms = end - new Date();
      if (ms <= 0) { msg.hidden = true; def.hidden = false; if (pill) pill.style.display = "none"; return; }
      var d = Math.floor(ms / 864e5), h = Math.floor(ms / 36e5) % 24, m = Math.floor(ms / 6e4) % 60, s = Math.floor(ms / 1e3) % 60;
      cd.textContent = "encore " + d + " j " + String(h).padStart(2, "0") + " h " + String(m).padStart(2, "0") + " min " + String(s).padStart(2, "0") + " s";
    };
    tick(); setInterval(tick, 1000);
  }

  // ---------- Apparition au scroll
  var rev = $$(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add("in"); io.unobserve(x.target); } }); }, { rootMargin: "0px 0px -8% 0px" });
    rev.forEach(function (el) { io.observe(el); });
  } else rev.forEach(function (el) { el.classList.add("in"); });

  // ---------- Barre d'achat collante (fiche produit)
  var sticky = $("[data-sticky]"), buy = $("[data-buy]");
  if (sticky && buy && "IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { sticky.classList.toggle("show", !es[0].isIntersecting && es[0].boundingClientRect.top < 0); render(); }).observe(buy);
  }

  // ---------- Commande : 1) récap par e-mail (Netlify Forms) 2) paiement Stripe
  var form = $("[data-checkout]");
  if (form) form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var c = load(), ls = lines(c), t = totals(c);
    if (!ls.length) return;
    form.elements.commande.value = ls.map(function (l) { return l.qty + " × " + l.p.name + " (" + eur(l.p.price * l.qty) + ")"; }).join("\n") +
      "\nLivraison : " + (t.ship ? eur(t.ship) : "offerte");
    form.elements.total.value = eur(t.total);
    var btn = $("[data-pay]", form); btn.disabled = true; btn.textContent = "Redirection vers le paiement…";
    var fd = new FormData(form);
    var customer = { name: fd.get("nom"), email: fd.get("email"), phone: fd.get("telephone"), message: fd.get("message") || "" };
    fetch("/", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: new URLSearchParams(fd).toString() })
      .catch(function () {})
      .then(function () {
        return fetch("/.netlify/functions/checkout", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ items: ls.map(function (l) { return { slug: l.slug, qty: l.qty }; }), customer: customer })
        }).then(function (r) { return r.json(); }).catch(function () { return {}; });
      })
      .then(function (res) {
        if (res && res.url) { window.location.href = res.url; return; }
        try { localStorage.removeItem(KEY); } catch (e) {}
        window.location.href = "/merci/?mode=manuel";
      });
  });

  if (location.pathname.indexOf("/merci") === 0 && $("[data-merci-paid]")) {
    var manual = /mode=manuel/.test(location.search);
    $("[data-merci-paid]").hidden = manual;
    $("[data-merci-manual]").hidden = !manual;
    if (/session_id=/.test(location.search)) { try { localStorage.removeItem(KEY); } catch (e) {} }
  }

  render();
})();
