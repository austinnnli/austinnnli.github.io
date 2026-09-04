/* ============================================================
   Austin Li — portfolio interactions
   Header auto-hide · contact modal · scroll reveals ·
   lagging timeline rail · "skip to next project"
   ============================================================ */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------------------------------------------------- header hide/show */
  (function header() {
    var el = $('.site-header');
    if (!el) return;
    var last = window.pageYOffset;
    var ticking = false;

    function update() {
      var y = window.pageYOffset;
      var dy = y - last;
      if (Math.abs(dy) > 4) {
        if (dy > 0 && y > 140) el.classList.add('is-hidden');
        else el.classList.remove('is-hidden');
        last = y;
      }
      if (y <= 40) el.classList.remove('is-hidden');
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
  })();

  /* ---------------------------------------------------- contact modal */
  (function modal() {
    var m = $('#contact-modal');
    if (!m) return;
    var opener = null;

    function open(e) {
      if (e) { e.preventDefault(); opener = e.currentTarget; }
      m.classList.add('is-open');
      m.setAttribute('aria-hidden', 'false');
      document.body.classList.add('modal-open');
      var f = m.querySelector('.modal__close');
      if (f) setTimeout(function () { f.focus(); }, 60);
    }
    function close() {
      m.classList.remove('is-open');
      m.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      if (opener) { opener.focus(); opener = null; }
    }

    $$('[data-contact-open]').forEach(function (b) { b.addEventListener('click', open); });
    $$('[data-contact-close]').forEach(function (b) { b.addEventListener('click', close); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && m.classList.contains('is-open')) close();
      if (e.key === 'Tab' && m.classList.contains('is-open')) {
        var f = $$('a[href], button:not([disabled])', m);
        if (!f.length) return;
        var first = f[0], lastEl = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); lastEl.focus(); }
        else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); first.focus(); }
      }
    });
  })();

  /* ---------------------------------------------------- scroll reveals */
  (function reveals() {
    var items = $$('.reveal');
    if (!items.length) return;
    if (reduced || !('IntersectionObserver' in window)) {
      items.forEach(function (i) { i.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });
    items.forEach(function (i) { io.observe(i); });
  })();

  /* ---------------------------------------------------- eased scrolling */
  function easeInOutCubic(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

  function scrollToY(targetY, done) {
    if (reduced) { window.scrollTo(0, targetY); if (done) done(); return; }
    var startY = window.pageYOffset;
    var delta = targetY - startY;
    if (Math.abs(delta) < 2) { if (done) done(); return; }
    var dur = Math.min(1500, Math.max(680, Math.abs(delta) * 0.62));
    var t0 = null;
    function step(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min(1, (ts - t0) / dur);
      window.scrollTo(0, startY + delta * easeInOutCubic(p));
      if (p < 1) requestAnimationFrame(step); else if (done) done();
    }
    requestAnimationFrame(step);
  }

  function headerOffset() {
    var v = getComputedStyle(document.documentElement).getPropertyValue('--header-h');
    return (parseFloat(v) || 116) + 26;
  }

  /* ---------------------------------------------------- timeline rail */
  (function rail() {
    var section = $('[data-rail-section]');
    var rail = $('.rail');
    if (!section || !rail) return;

    var fill    = $('.rail__fill', rail);
    var blocks  = $$('[data-project]', section);
    var dots    = [];
    var current = 0;       // smoothed fill height, px
    var target  = 0;
    var live    = false;

    // build a dot per project
    blocks.forEach(function (b, i) {
      var d = document.createElement('div');
      d.className = 'dot';
      d.textContent = b.getAttribute('data-project-no') || ((i + 1 < 10 ? '0' : '') + (i + 1));
      d.setAttribute('aria-hidden', 'true');
      rail.appendChild(d);
      dots.push({ el: d, block: b, y: 0, on: false, title: $('.project__title', b) });
    });

    function measure() {
      var railTop = rail.getBoundingClientRect().top + window.pageYOffset;
      dots.forEach(function (d) {
        var h = d.title || d.block;
        var r = h.getBoundingClientRect();
        d.y = r.top + window.pageYOffset - railTop + Math.min(r.height / 2, 26);
        d.el.style.top = d.y + 'px';
      });
      railHeight = rail.offsetHeight;
    }
    var railHeight = 0;

    function compute() {
      var railTop = rail.getBoundingClientRect().top + window.pageYOffset;
      var read = window.pageYOffset + window.innerHeight * 0.64;
      target = Math.max(0, Math.min(railHeight, read - railTop));
      if (!live && window.pageYOffset + window.innerHeight > railTop + 40) {
        live = true; rail.classList.add('is-live');
      }
    }

    function tick() {
      compute();
      // lag: the fill eases toward the scroll position, always a beat behind
      current += (target - current) * (reduced ? 1 : 0.075);
      if (Math.abs(target - current) < 0.4) current = target;
      fill.style.height = current.toFixed(1) + 'px';

      dots.forEach(function (d) {
        var on = current >= d.y - 6;
        if (on !== d.on) {
          d.on = on;
          d.el.classList.toggle('is-on', on);
          if (d.title) d.title.classList.toggle('is-on', on);
        }
      });
      requestAnimationFrame(tick);
    }

    measure();
    if (reduced) {
      dots.forEach(function (d) { d.el.classList.add('is-on'); if (d.title) d.title.classList.add('is-on'); });
      rail.classList.add('is-live');
      fill.style.height = '100%';
    } else {
      requestAnimationFrame(tick);
    }

    var rt;
    window.addEventListener('resize', function () {
      clearTimeout(rt); rt = setTimeout(measure, 140);
    });
    window.addEventListener('load', measure);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);

    /* ------------------------------------------------ skip to next */
    var skip = $('.skip-next');
    if (!skip) return;

    function nextIndex() {
      var y = window.pageYOffset + headerOffset() + 8;
      for (var i = 0; i < blocks.length; i++) {
        if (blocks[i].getBoundingClientRect().top + window.pageYOffset > y + 12) return i;
      }
      return -1;
    }

    skip.addEventListener('click', function () {
      var i = nextIndex();
      if (i < 0) return;
      var y = blocks[i].getBoundingClientRect().top + window.pageYOffset - headerOffset();
      scrollToY(y);
    });

    function skipVisibility() {
      var r = section.getBoundingClientRect();
      var inSection = r.top < window.innerHeight * 0.6 && r.bottom > window.innerHeight * 0.55;
      skip.classList.toggle('is-shown', inSection && nextIndex() >= 0);
    }
    skipVisibility();
    window.addEventListener('scroll', skipVisibility, { passive: true });
    window.addEventListener('resize', skipVisibility);
  })();

  /* ---------------------------------------------------- in-page anchors */
  $$('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var id = a.getAttribute('href');
      if (id === '#' || id.length < 2) return;
      var t = document.getElementById(id.slice(1));
      if (!t) return;
      e.preventDefault();
      var y = t.getBoundingClientRect().top + window.pageYOffset - (id === '#top' ? 0 : headerOffset());
      scrollToY(Math.max(0, y));
      history.replaceState(null, '', id);
    });
  });

  /* ---------------------------------------------------- dive deeper */
  (function dive() {
    var panels = $$('.deep');
    if (!panels.length) return;

    panels.forEach(function (d) {
      d.style.height = '0px';
      d.setAttribute('aria-hidden', 'true');
      if ('inert' in d) d.inert = true;
    });

    function settle() { window.dispatchEvent(new Event('resize')); }

    function open(d, btn) {
      d.classList.add('is-open');
      d.classList.remove('is-done');
      d.removeAttribute('aria-hidden');
      if ('inert' in d) d.inert = false;
      d.style.height = d.scrollHeight + 'px';
      btn.setAttribute('aria-expanded', 'true');
      $('.dive__label', btn).textContent = 'show less';
      var done = function (e) {
        if (e && e.propertyName !== 'height') return;
        d.removeEventListener('transitionend', done);
        if (d.classList.contains('is-open')) d.classList.add('is-done');
        settle();
      };
      d.addEventListener('transitionend', done);
      setTimeout(done, 850);
    }

    function close(d, btn) {
      d.classList.remove('is-done');
      d.style.height = d.scrollHeight + 'px';   // fix the height before collapsing
      void d.offsetHeight;                       // force a reflow
      d.classList.remove('is-open');
      d.style.height = '0px';
      d.setAttribute('aria-hidden', 'true');
      if ('inert' in d) d.inert = true;
      btn.setAttribute('aria-expanded', 'false');
      $('.dive__label', btn).textContent = 'dive deeper';
      setTimeout(settle, 760);
    }

    $$('[data-dive]').forEach(function (btn) {
      var d = document.getElementById(btn.getAttribute('aria-controls'));
      if (!d) return;
      btn.addEventListener('click', function () {
        if (btn.getAttribute('aria-expanded') === 'true') {
          close(d, btn);
          var top = btn.getBoundingClientRect().top + window.pageYOffset - headerOffset();
          if (window.pageYOffset > top) scrollToY(Math.max(0, top));
        } else {
          open(d, btn);
        }
      });
    });

    // keep an open panel the right height when images finish loading or the
    // viewport changes
    var rt;
    window.addEventListener('resize', function () {
      clearTimeout(rt);
      rt = setTimeout(function () {
        panels.forEach(function (d) {
          if (d.classList.contains('is-open') && !d.classList.contains('is-done')) {
            d.style.height = d.scrollHeight + 'px';
          }
        });
      }, 160);
    });
  })();

  /* ---------------------------------------------------- playback speed */
  (function speed() {
    $$('[data-speed]').forEach(function (btn) {
      var rates = [1, 2];
      var i = 0;
      btn.addEventListener('click', function () {
        var wrap = btn.closest('.video-wrap');
        var v = wrap && wrap.querySelector('video');
        if (!v) return;
        i = (i + 1) % rates.length;
        v.playbackRate = rates[i];
        btn.textContent = rates[i] + '\u00d7';
        btn.classList.toggle('is-fast', rates[i] !== 1);
      });
    });
  })();

  /* ---------------------------------------------------- replay a video */
  (function replay() {
    $$('[data-replay]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var wrap = btn.closest('.video-wrap');
        var v = wrap && wrap.querySelector('video');
        if (!v) return;
        var rate = v.playbackRate;
        try { v.currentTime = 0; } catch (e) {}
        v.playbackRate = rate;
        var pr = v.play();
        if (pr && pr.catch) pr.catch(function () {});
        btn.classList.add('is-spun');
        setTimeout(function () { btn.classList.remove('is-spun'); }, 520);
      });
    });
  })();

  /* ---------------------------------------------------- lazy video play */
  (function videos() {
    var vids = $$('video[data-autoplay]');
    if (!vids.length || !('IntersectionObserver' in window)) {
      vids.forEach(function (v) { v.play().catch(function () {}); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var v = en.target;
        if (en.isIntersecting) { v.play().catch(function () {}); }
        else if (!v.paused) { v.pause(); }
      });
    }, { threshold: 0.22 });
    vids.forEach(function (v) { io.observe(v); });
  })();
})();
