// Mobile menu toggle and form error focus. The site works without this script.
(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    function setOpen(open) {
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    }
    toggle.addEventListener("click", function () {
      setOpen(!nav.classList.contains("is-open"));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setOpen(false);
    });
  }

  // After a failed submit the page reloads at the top; bring the form back into view.
  var firstError = document.querySelector(".has-error input, .has-error textarea");
  if (firstError) {
    document.getElementById("contact").scrollIntoView();
    firstError.focus({ preventScroll: true });
  }
})();
