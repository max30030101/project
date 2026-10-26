/* FitForge AI: small progressive enhancements. The site works without JavaScript. */
(function () {
  "use strict";

  // Mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Sorting applies immediately
  document.querySelectorAll("[data-autosubmit]").forEach(function (el) {
    el.addEventListener("change", function () { if (el.form) el.form.submit(); });
  });

  // Favourites: toggle without reloading the page
  var favCount = document.querySelector("[data-fav-count]");
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form.matches || !form.matches(".fav-form, .fav-form-inline")) return;
    event.preventDefault();
    var btn = form.querySelector(".fav-btn");
    btn.disabled = true;
    fetch(form.action, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: new FormData(form),
      credentials: "same-origin"
    }).then(function (res) {
      return res.json().then(function (data) { return { status: res.status, data: data }; });
    }).then(function (r) {
      if (r.status === 401 && r.data.login) { window.location.href = r.data.login; return; }
      btn.classList.toggle("is-on", r.data.favourited);
      btn.setAttribute("aria-pressed", r.data.favourited ? "true" : "false");
      var label = btn.querySelector("[data-fav-label]");
      if (label) label.textContent = r.data.favourited ? "Saved to favourites" : "Save to favourites";
      if (favCount) { favCount.textContent = r.data.count; favCount.hidden = !r.data.count; }
      btn.disabled = false;
    }).catch(function () { form.submit(); });
  });

  // Dashboard: weight trend drawn as inline SVG
  var chart = document.getElementById("weight-chart");
  var dataEl = document.getElementById("weight-data");
  if (chart && dataEl) {
    var points = JSON.parse(dataEl.textContent || "[]");
    if (points.length < 2) {
      chart.innerHTML = '<p class="empty-chart">Add two or more weight entries to see your trend.</p>';
      return;
    }
    var W = 320, H = 140, P = 22;
    var vals = points.map(function (p) { return p.kg; });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    if (hi === lo) { hi += 1; lo -= 1; }
    var x = function (i) { return P + (W - 2 * P) * i / (points.length - 1); };
    var y = function (v) { return H - P - (H - 2 * P) * (v - lo) / (hi - lo); };
    var line = points.map(function (p, i) { return (i ? "L" : "M") + x(i).toFixed(1) + " " + y(p.kg).toFixed(1); }).join(" ");
    var dots = points.map(function (p, i) {
      return '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(p.kg).toFixed(1) + '" r="3.5" fill="#1c3fdb"><title>' + p.date + ": " + p.kg + ' kg</title></circle>';
    }).join("");
    chart.innerHTML = '<svg viewBox="0 0 ' + W + " " + H + '" aria-hidden="true">' +
      '<line x1="' + P + '" y1="' + (H - P) + '" x2="' + (W - P) + '" y2="' + (H - P) + '" stroke="#d8ddd6"/>' +
      '<path d="' + line + '" fill="none" stroke="#1c3fdb" stroke-width="2.5" stroke-linejoin="round"/>' + dots +
      '<text x="' + P + '" y="12" font-size="10" fill="#5b6770">' + hi.toFixed(1) + ' kg</text>' +
      '<text x="' + P + '" y="' + (H - 6) + '" font-size="10" fill="#5b6770">' + lo.toFixed(1) + " kg</text></svg>";
  }
})();
