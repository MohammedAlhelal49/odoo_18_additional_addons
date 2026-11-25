/* Al Omran Engineering website — vanilla JS, no dependencies.
   Loaded as a plain deferred <script> from views/layout.xml (not through
   the Odoo module bundle), so it runs exactly once after the DOM is parsed. */
(function () {
    'use strict';

    var root = document.querySelector('.aoe');
    if (!root) { return; }
    root.classList.add('aoe-js');

    var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ---------- Sticky header ----------
    var header = document.getElementById('aoeHeader');
    function onScroll() {
        if (header) { header.classList.toggle('is-scrolled', window.scrollY > 24); }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // ---------- Mobile drawer ----------
    var burger = document.getElementById('aoeBurger');
    if (burger && header) {
        burger.addEventListener('click', function () {
            var open = header.classList.toggle('is-open');
            burger.setAttribute('aria-expanded', open ? 'true' : 'false');
            document.body.style.overflow = open ? 'hidden' : '';
        });
        header.querySelectorAll('.aoe-drawer a').forEach(function (a) {
            a.addEventListener('click', function () {
                header.classList.remove('is-open');
                burger.setAttribute('aria-expanded', 'false');
                document.body.style.overflow = '';
            });
        });
    }

    // ---------- Reveal on scroll + counters ----------
    function countUp(el) {
        var to = parseInt(el.getAttribute('data-to'), 10);
        if (isNaN(to) || reduceMotion) { return; }
        var start = null;
        var duration = 1400;
        function step(ts) {
            if (!start) { start = ts; }
            var p = Math.min((ts - start) / duration, 1);
            el.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
            if (p < 1) { window.requestAnimationFrame(step); }
        }
        window.requestAnimationFrame(step);
    }

    var revealEls = root.querySelectorAll('.aoe-reveal');
    var counters = root.querySelectorAll('.aoe-count');
    if ('IntersectionObserver' in window && !reduceMotion) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) { return; }
                var el = entry.target;
                if (el.classList.contains('aoe-count')) {
                    countUp(el);
                } else {
                    // small stagger for siblings revealed together
                    var siblings = Array.prototype.indexOf.call(el.parentNode.children, el);
                    el.style.transitionDelay = Math.min(siblings, 6) * 70 + 'ms';
                    el.classList.add('is-visible');
                    // drop the delay afterwards so hover transitions stay instant
                    window.setTimeout(function () { el.style.transitionDelay = ''; }, 1400);
                }
                io.unobserve(el);
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
        revealEls.forEach(function (el) { io.observe(el); });
        counters.forEach(function (el) { io.observe(el); });
    } else {
        revealEls.forEach(function (el) { el.classList.add('is-visible'); });
    }

    // ---------- Project filter ----------
    var filters = root.querySelectorAll('.aoe-filters button');
    filters.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var cat = btn.getAttribute('data-filter');
            filters.forEach(function (b) { b.classList.toggle('is-active', b === btn); });
            root.querySelectorAll('.aoe-project-cell').forEach(function (cell) {
                var show = cat === 'all' || cell.getAttribute('data-category') === cat;
                cell.classList.toggle('is-hidden', !show);
                if (show) { cell.classList.add('is-visible'); }
            });
        });
    });

    // ---------- Services index: highlight current section ----------
    var indexLinks = root.querySelectorAll('.aoe-service-index a');
    if (indexLinks.length && 'IntersectionObserver' in window) {
        var linkFor = {};
        indexLinks.forEach(function (a) { linkFor[a.getAttribute('href').slice(1)] = a; });
        var spy = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) { return; }
                indexLinks.forEach(function (a) { a.classList.remove('is-active'); });
                var link = linkFor[entry.target.id];
                if (link) { link.classList.add('is-active'); }
            });
        }, { rootMargin: '-45% 0px -50% 0px' });
        root.querySelectorAll('.aoe-service-row').forEach(function (row) { spy.observe(row); });
    }

    // ---------- Back to top ----------
    root.querySelectorAll('a[href="#top"]').forEach(function (a) {
        a.addEventListener('click', function (ev) {
            ev.preventDefault();
            window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
        });
    });
})();
