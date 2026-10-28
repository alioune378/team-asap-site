/* Team ASAP site script: navigation, quote workflow, portfolio, analytics events, owner review mode. */
(function () {
  "use strict";
  var CFG = window.ASAP || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  function store(kind) { try { return window[kind]; } catch (e) { return null; } }
  function sget(k) { try { var s = store("sessionStorage"); return s ? s.getItem(k) : null; } catch (e) { return null; } }
  function sset(k, v) { try { var s = store("sessionStorage"); if (s) s.setItem(k, v); } catch (e) {} }
  function lget(k) { try { var s = store("localStorage"); return s ? s.getItem(k) : null; } catch (e) { return null; } }
  function lset(k, v) { try { var s = store("localStorage"); if (s) s.setItem(k, v); } catch (e) {} }

  /* ---------- analytics ---------- */
  window.dataLayer = window.dataLayer || [];
  function track(name, params) {
    params = params || {};
    window.dataLayer.push(Object.assign({ event: name }, params));
    if (typeof window.gtag === "function") window.gtag("event", name, params);
  }
  function loadGA() {
    if (!CFG.ga4 || window.gtag) return;
    var s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(CFG.ga4);
    document.head.appendChild(s);
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", CFG.ga4);
  }
  function consent() {
    if (!CFG.ga4) return;
    var c = lget("asap-consent");
    if (c === "yes") return loadGA();
    if (c === "no") return;
    var b = document.createElement("div");
    b.className = "cbanner"; b.setAttribute("role", "region"); b.setAttribute("aria-label", "Cookie choice");
    b.innerHTML = '<p>We use analytics cookies to understand how visitors use this site. No data is sold.</p><div class="btn-row"><button class="btn sm" type="button" data-c="yes">Accept</button><button class="btn sm ghost" type="button" data-c="no">Decline</button></div>';
    b.addEventListener("click", function (ev) {
      var v = ev.target.getAttribute && ev.target.getAttribute("data-c");
      if (!v) return; lset("asap-consent", v); b.remove(); if (v === "yes") loadGA();
    });
    document.body.appendChild(b);
  }
  document.addEventListener("click", function (ev) {
    var t = ev.target.closest && ev.target.closest("[data-track]");
    if (t) track(t.getAttribute("data-track"), { location: t.getAttribute("data-loc") || "", page: location.pathname });
  });

  /* ---------- UTM / referral capture ---------- */
  (function () {
    var q = new URLSearchParams(location.search);
    ["utm_source", "utm_medium", "utm_campaign", "utm_content"].forEach(function (k) { if (q.get(k)) sset(k, q.get(k)); });
    if (!sget("landing_page")) sset("landing_page", location.pathname + location.search);
    if (!sget("referrer") && document.referrer && document.referrer.indexOf(location.host) === -1) sset("referrer", document.referrer);
  })();

  /* ---------- header: dropdowns + drawer ---------- */
  $$(".dd > button").forEach(function (btn) {
    var panel = document.getElementById(btn.getAttribute("aria-controls"));
    function set(open) { btn.setAttribute("aria-expanded", String(open)); panel.hidden = !open; }
    btn.addEventListener("click", function (e) { e.stopPropagation(); var o = btn.getAttribute("aria-expanded") === "true"; $$(".dd > button").forEach(function (b) { if (b !== btn) { b.setAttribute("aria-expanded", "false"); document.getElementById(b.getAttribute("aria-controls")).hidden = true; } }); set(!o); });
    btn.parentElement.addEventListener("keydown", function (e) { if (e.key === "Escape") { set(false); btn.focus(); } });
  });
  document.addEventListener("click", function (e) { if (!e.target.closest(".dd")) $$(".dd > button").forEach(function (b) { b.setAttribute("aria-expanded", "false"); document.getElementById(b.getAttribute("aria-controls")).hidden = true; }); });
  var drawer = $("#drawer"), opener = $(".hdr .menu-btn");
  if (drawer && opener) {
    var openD = function () { drawer.hidden = false; opener.setAttribute("aria-expanded", "true"); document.body.style.overflow = "hidden"; var c = $("[data-close]", drawer); if (c) c.focus(); };
    var closeD = function () { drawer.hidden = true; opener.setAttribute("aria-expanded", "false"); document.body.style.overflow = ""; opener.focus(); };
    opener.addEventListener("click", openD);
    drawer.addEventListener("click", function (e) { if (e.target === drawer || e.target.closest("[data-close]")) closeD(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !drawer.hidden) closeD(); });
  }

  /* ---------- portfolio ---------- */
  var lb = $("#lb");
  if (lb) {
    var body = $(".lb-body", lb);
    $$("[data-project]").forEach(function (card) {
      card.addEventListener("click", function () {
        var tpl = document.getElementById("tpl-" + card.getAttribute("data-project"));
        if (!tpl) return;
        body.innerHTML = ""; body.appendChild(tpl.content.cloneNode(true));
        if (typeof lb.showModal === "function") lb.showModal(); else lb.setAttribute("open", "");
      });
    });
    $(".lb-close", lb).addEventListener("click", function () { lb.close ? lb.close() : lb.removeAttribute("open"); });
    lb.addEventListener("click", function (e) { if (e.target === lb && lb.close) lb.close(); });
  }
  var filters = $$(".filters button");
  filters.forEach(function (b) {
    b.addEventListener("click", function () {
      var f = b.getAttribute("data-filter"), shown = 0;
      filters.forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      $$("#work-grid [data-cat]").forEach(function (c) { var ok = f === "all" || c.getAttribute("data-cat") === f; c.hidden = !ok; if (ok) shown++; });
      var empty = $("#work-empty"); if (empty) empty.hidden = shown > 0;
      track("portfolio_filter", { filter: f });
    });
  });

  /* ---------- owner review mode ---------- */
  var rt = $(".review-toggle");
  if (rt) rt.addEventListener("click", function () {
    var on = !document.body.classList.contains("review");
    document.body.classList.toggle("review", on); rt.setAttribute("aria-pressed", String(on));
  });

  /* ---------- quote workflow ---------- */
  var form = $("#quote");
  if (form) initQuote(form);

  function initQuote(form) {
    var steps = $$(".q-step[data-step]", form).filter(function (s) { return s.getAttribute("data-step") !== "done"; });
    var done = $('.q-step[data-step="done"]', form);
    var bars = $$(".qprog span", form);
    var back = $("#q-back"), next = $("#q-next"), submit = $("#q-submit"), nav = $("#qnav");
    var cur = 0, started = false, sending = false;
    var photos = []; // File objects, max 3

    // preselect from #svc-xxx
    var h = (location.hash || "").replace("#", "");
    if (h.indexOf("svc-") === 0) { var r = document.getElementById(h); if (r) { r.checked = true; } }

    function show(i) {
      steps.forEach(function (s, j) { s.hidden = j !== i; });
      bars.forEach(function (b, j) { b.className = j < i ? "done" : j === i ? "cur" : ""; });
      $("#q-count").textContent = "Step " + (i + 1) + " of " + steps.length;
      $("#q-name").textContent = steps[i].getAttribute("data-name");
      back.hidden = i === 0;
      next.hidden = i === steps.length - 1;
      submit.hidden = i !== steps.length - 1;
      cur = i;
      track("quote_step_view", { step: i + 1, name: steps[i].getAttribute("data-name") });
    }
    function startOnce() { if (!started) { started = true; track("quote_form_start", { page: location.pathname }); } }
    form.addEventListener("input", startOnce); form.addEventListener("change", startOnce);

    function setErr(field, msg) {
      var wrap = field.closest(".field");
      var p = wrap ? $(".err", wrap) : null;
      if (wrap) wrap.classList.toggle("invalid", !!msg);
      if (p) p.textContent = msg || "";
      field.setAttribute("aria-invalid", msg ? "true" : "false");
      if (p && msg) { if (!p.id) p.id = "e-" + field.id; field.setAttribute("aria-describedby", p.id); }
    }
    function digits(s) { return (s || "").replace(/\D/g, ""); }
    function validate(i) {
      var s = steps[i], ok = true, firstBad = null;
      if (i === 0) {
        var any = $('input[name="service"]:checked', form);
        $("#err-service").textContent = any ? "" : "Choose the option that best fits your request.";
        if (!any) { ok = false; firstBad = $('input[name="service"]', form); }
      }
      $$("input:not([type=radio]):not([type=checkbox]):not([type=file]):not([type=hidden]), textarea, select", s).forEach(function (f) {
        var msg = "";
        var val = f.value.trim();
        if (f.required && !val) msg = "This field is required.";
        else if (f.name === "description" && val.length < 10) msg = "Please add a little more detail (at least 10 characters).";
        else if (f.name === "zip" && !/^\d{5}$/.test(val)) msg = "Enter a 5-digit ZIP code.";
        else if (f.name === "phone") { var d = digits(val); if (d.length === 11 && d[0] === "1") d = d.slice(1); if (d.length !== 10) msg = "Enter a 10-digit phone number."; }
        else if (f.type === "email" && val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) msg = "Enter a valid email address, or leave it blank.";
        setErr(f, msg);
        if (msg) { ok = false; firstBad = firstBad || f; }
      });
      if (i === steps.length - 1) {
        var em = $('input[name="contact_method"]:checked', form);
        var emailF = $("#q-em");
        if (em && em.value === "Email" && !emailF.value.trim()) { setErr(emailF, "Add an email address, or choose call or text."); ok = false; firstBad = firstBad || emailF; }
        var c = $("#q-consent");
        $("#err-consent").textContent = c.checked ? "" : "Please confirm we may contact you about this request.";
        if (!c.checked) { ok = false; firstBad = firstBad || c; }
      }
      if (firstBad) firstBad.focus();
      return ok;
    }
    next.addEventListener("click", function () { if (validate(cur)) { show(cur + 1); steps[cur].querySelector("legend").scrollIntoView({ block: "nearest" }); var f = $("input:not([type=hidden]),textarea", steps[cur]); if (f && f.type !== "file") f.focus({ preventScroll: true }); } });
    back.addEventListener("click", function () { show(cur - 1); });
    // Enter key advances instead of submitting early
    form.addEventListener("keydown", function (e) { if (e.key === "Enter" && e.target.tagName === "INPUT" && cur < steps.length - 1) { e.preventDefault(); next.click(); } });

    // emergency callout
    function emerg() { var c = $('input[name="service"]:checked', form); $("#emerg-callout").hidden = !(c && c.getAttribute("data-key") === "emergency"); if (c) $("#err-service").textContent = ""; }
    $$('input[name="service"]', form).forEach(function (r) { r.addEventListener("change", emerg); }); emerg();

    // photos
    var pick = $("#q-pick"), drop = $("#drop"), thumbs = $("#thumbs"), perr = $("#err-photos");
    var MAX_TOTAL = 7.5 * 1024 * 1024;
    function compress(file) {
      return new Promise(function (resolve) {
        if (!/^image\//.test(file.type) || file.size < 900 * 1024) return resolve(file);
        var url = URL.createObjectURL(file), im = new Image();
        im.onload = function () {
          var m = 1800, w = im.naturalWidth, hh = im.naturalHeight, k = Math.min(1, m / Math.max(w, hh));
          var cv = document.createElement("canvas"); cv.width = Math.round(w * k); cv.height = Math.round(hh * k);
          cv.getContext("2d").drawImage(im, 0, 0, cv.width, cv.height);
          cv.toBlob(function (b) { URL.revokeObjectURL(url); if (!b) return resolve(file); resolve(new File([b], file.name.replace(/\.\w+$/, "") + ".jpg", { type: "image/jpeg" })); }, "image/jpeg", 0.82);
        };
        im.onerror = function () { URL.revokeObjectURL(url); resolve(file); };
        im.src = url;
      });
    }
    function sync() {
      var inputs = ["photo1", "photo2", "photo3"].map(function (n) { return form.querySelector('input[name="' + n + '"]'); });
      inputs.forEach(function (inp, i) {
        try { var dt = new DataTransfer(); if (photos[i]) dt.items.add(photos[i]); inp.files = dt.files; } catch (e) {}
      });
      thumbs.innerHTML = "";
      photos.forEach(function (f, i) {
        var d = document.createElement("div"), im = document.createElement("img"), b = document.createElement("button");
        im.alt = "Selected photo " + (i + 1); im.src = URL.createObjectURL(f);
        b.type = "button"; b.setAttribute("aria-label", "Remove photo " + (i + 1));
        b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>';
        b.addEventListener("click", function () { photos.splice(i, 1); sync(); });
        d.appendChild(im); d.appendChild(b); thumbs.appendChild(d);
      });
    }
    function addFiles(list) {
      perr.textContent = "";
      var arr = Array.prototype.slice.call(list).filter(function (f) { return /^image\//.test(f.type) || /\.(heic|heif)$/i.test(f.name); });
      if (!arr.length && list.length) { perr.textContent = "Only image files can be attached."; return; }
      var room = 3 - photos.length;
      if (arr.length > room) perr.textContent = "You can attach up to 3 photos.";
      Promise.all(arr.slice(0, room).map(compress)).then(function (files) {
        var total = photos.concat(files).reduce(function (a, f) { return a + f.size; }, 0);
        if (total > MAX_TOTAL) { perr.textContent = "These photos are too large to send together. Try fewer or smaller photos."; return; }
        photos = photos.concat(files); sync(); track("quote_photos_added", { count: photos.length });
      });
    }
    pick.addEventListener("change", function () { addFiles(pick.files); pick.value = ""; });
    ["dragenter", "dragover"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.remove("over"); }); });
    drop.addEventListener("drop", function (e) { if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files); });

    function summary() {
      var fd = new FormData(form), rows = [["Service", fd.get("service")], ["Location", (fd.get("city") || "") + " " + (fd.get("zip") || "")], ["Photos", photos.length ? photos.length + " attached" : "None"], ["Name", fd.get("name")], ["Phone", fd.get("phone")], ["Contact by", fd.get("contact_method")]];
      return '<dl class="summary">' + rows.map(function (r) { var dd = document.createElement("dd"); dd.textContent = r[1] || ""; return "<div><dt>" + r[0] + "</dt>" + dd.outerHTML + "</div>"; }).join("") + "</dl>";
    }
    var PHONE = (document.querySelector(".big-phone .num, .side-card .num") || {}).textContent || "";
    function finish(kind) {
      steps.forEach(function (s) { s.hidden = true; });
      nav.hidden = true; $(".qprog", form).hidden = true; $(".qmeta", form).hidden = true;
      if (kind === "ok") {
        bars.forEach(function (b) { b.className = "done"; });
        done.innerHTML = '<span class="ok"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="m5 12 4.5 4.5L19 7"/></svg></span><h2 style="font-size:1.8rem">Request sent. Thank you.</h2><p class="lead">Team ASAP has received your request and will contact you to discuss the job. If the problem becomes urgent, call ' + PHONE + '.</p>' + summary();
      } else {
        done.innerHTML = '<span class="note"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/></svg></span><h2 style="font-size:1.8rem">Preview: nothing was sent</h2><p class="lead">This is a preview of the website. On the live site, this request and its photos go straight to Team ASAP by email. Here is what would have been sent:</p>' + summary() + '<button type="button" class="btn ghost" id="q-restart" style="justify-self:start">Start over</button>';
        $("#q-restart").addEventListener("click", function () { location.reload(); });
      }
      done.hidden = false; done.focus();
    }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (sending) return;
      if (!validate(cur)) return;
      ["utm_source", "utm_medium", "utm_campaign", "utm_content", "landing_page", "referrer"].forEach(function (k) { var f = form.querySelector('input[name="' + k + '"]'); if (f) f.value = sget(k) || ""; });
      if (CFG.preview) { track("quote_preview_submit"); return finish("preview"); }
      sending = true; submit.disabled = true; submit.textContent = "Sending…"; $("#err-submit").textContent = "";
      var fd = new FormData(form);
      fd.delete("bot-field") ; fd.append("bot-field", form.querySelector('[name="bot-field"]').value);
      fetch("/", { method: "POST", body: fd })
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); track("quote_form_submit", { service: fd.get("service") || "" }); finish("ok"); })
        .catch(function () {
          sending = false; submit.disabled = false; submit.textContent = "Send request";
          $("#err-submit").textContent = "We couldn't send your request. Check your connection and try again, or call " + PHONE + ".";
          track("quote_form_error");
        });
    });
    show(0);
  }

  consent();
})();
