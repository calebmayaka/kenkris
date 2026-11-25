// KenKris admin panel: theme, mobile nav drawer, dropdowns, button loading states.
(function () {
  var root = document.documentElement;
  var media = window.matchMedia("(prefers-color-scheme: dark)");

  function getPref() {
    try { return localStorage.getItem("kk-theme") || "system"; } catch (e) { return "system"; }
  }
  function applyTheme(pref) {
    try { localStorage.setItem("kk-theme", pref); } catch (e) {}
    var dark = pref === "dark" || (pref === "system" && media.matches);
    root.classList.toggle("dark", dark);
    document.querySelectorAll("[data-theme-set]").forEach(function (el) {
      el.setAttribute("aria-checked", String(el.getAttribute("data-theme-set") === pref));
    });
  }
  applyTheme(getPref());
  media.addEventListener && media.addEventListener("change", function () {
    if (getPref() === "system") applyTheme("system");
  });

  document.addEventListener("click", function (e) {
    var t = e.target;
    var toggle = t.closest("[data-theme-toggle]");
    if (toggle) { applyTheme(root.classList.contains("dark") ? "light" : "dark"); return; }
    var set = t.closest("[data-theme-set]");
    if (set) { applyTheme(set.getAttribute("data-theme-set")); return; }
    if (t.closest("[data-nav-open]")) { document.body.classList.add("nav-open"); return; }
    if (t.closest("[data-nav-close]")) { document.body.classList.remove("nav-open"); return; }
    // Close open dropdowns when clicking elsewhere.
    document.querySelectorAll("details[data-dropdown][open]").forEach(function (d) {
      if (!d.contains(t)) d.removeAttribute("open");
    });
  });

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    document.body.classList.remove("nav-open");
    document.querySelectorAll("details[data-dropdown][open]").forEach(function (d) { d.removeAttribute("open"); });
  });

  // Show a spinner on the submit button and block double submits.
  document.addEventListener("submit", function (e) {
    var btn = e.target.querySelector("button[type=submit]");
    if (btn) {
      if (btn.classList.contains("is-loading")) { e.preventDefault(); return; }
      btn.classList.add("is-loading");
    }
  });
  // Restore buttons if the page is shown again from the back/forward cache.
  window.addEventListener("pageshow", function () {
    document.querySelectorAll(".is-loading").forEach(function (b) { b.classList.remove("is-loading"); });
  });
})();
