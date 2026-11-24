/* Frame restore (injected in every page by scripts/seo.py).
 *
 * The 1998 Citeweb layout is a stack of nested framesets:
 *   index.htm > citeweb/milieu.htm > citeweb/centre.htm > citeweb/depart.htm > (a = the page)
 * A page opened on its own (a search result) is reloaded inside it: it goes to /index.htm#p=<page>
 * and each frameset hands the hash down to the right frame. location.replace keeps the back
 * button usable, a framed page never redirects again (no loop).
 */
(function () {
  "use strict";

  function up(p) {
    p = p.toLowerCase();
    if (p === "/index.htm") return null;
    if (p === "/citeweb/milieu.htm") return { parent: "/index.htm", frame: "milieu" };
    if (p === "/citeweb/centre.htm") return { parent: "/citeweb/milieu.htm", frame: "centre" };
    if (p === "/citeweb/haut.htm") return { parent: "/citeweb/milieu.htm", frame: "haut" };
    if (p === "/citeweb/depart.htm") return { parent: "/citeweb/centre.htm", frame: "depart" };
    if (p === "/citeweb/gauche.htm") return { parent: "/citeweb/centre.htm", frame: "gauche" };
    if (p === "/citeweb/gh.htm") return { parent: "/citeweb/gauche.htm", frame: "gh" };
    if (p === "/citeweb/gb.htm") return { parent: "/citeweb/gauche.htm", frame: "gb" };
    if (p === "/citeweb/pub.htm") return { parent: "/citeweb/depart.htm", frame: "pub" };
    if (p === "/citeweb/blanc.htm" || p === "/404.html" || p.indexOf("/aide/irc/") === 0) return null;
    return { parent: "/citeweb/depart.htm", frame: "a" };
  }

  function norm(p) { return p.replace(/\/{2,}/g, "/").replace(/\/$/, "/index.htm"); }

  function chain(p) {
    var steps = [], u, n = 0;
    while ((u = up(p)) && n++ < 8) {
      steps.unshift({ parent: u.parent, frame: u.frame, child: p });
      p = u.parent;
    }
    return steps;
  }

  function same(a, b) { return a.toLowerCase() === b.toLowerCase(); }

  function consume(enc) {
    var target, a = document.createElement("a");
    try { target = decodeURIComponent(enc); } catch (e) { return; }
    if (!/^\/(?![\/\\])/.test(target)) return;
    a.href = target;
    if (a.protocol !== location.protocol || a.host !== location.host) return;
    var final = norm(a.pathname), here = norm(location.pathname), steps = chain(final), step = null, i;
    for (i = 0; i < steps.length; i++) if (same(steps[i].parent, here)) { step = steps[i]; break; }
    if (!step) return;
    var url = same(step.child, final) ? target : step.child + "#p=" + enc;
    function apply() {
      var el = document.getElementsByName(step.frame)[0] || document.getElementById(step.frame);
      if (el) el.src = url;
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply);
    else apply();
  }

  var hash = /^#p=(.+)$/.exec(location.hash);
  if (hash) {
    consume(hash[1]);
  } else if (window.top === window.self) {
    var steps = chain(norm(location.pathname));
    if (steps.length) {
      location.replace(steps[0].parent + "#p=" +
        encodeURIComponent(location.pathname + location.search + location.hash));
    }
  }
})();
