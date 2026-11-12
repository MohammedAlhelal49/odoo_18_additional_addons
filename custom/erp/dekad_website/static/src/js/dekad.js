// Dekad Custom JS

// Sticky navbar on scroll
window.addEventListener('scroll', function() {
    var header = document.getElementById('ve-sticky');
    if (header) {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }
});

// Mobile menu toggle
var toggler = document.getElementById('ve-toggle');
var mobileMenu = document.getElementById('ve-mobile-menu');
if (toggler && mobileMenu) {
    toggler.addEventListener('click', function() {
        mobileMenu.classList.toggle('open');
    });
}

// Counter animation
function animateCounters() {
    var counters = document.querySelectorAll('.counter');
    counters.forEach(function(counter) {
        var target = parseInt(counter.getAttribute('data-count'));
        var count = 0;
        var duration = 2000;
        var step = target / (duration / 16);
        var timer = setInterval(function() {
            count += step;
            if (count >= target) {
                counter.textContent = target.toLocaleString();
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(count).toLocaleString();
            }
        }, 16);
    });
}

// Trigger counters when in view
var counterSection = document.querySelector('.ve-counter-section');
if (counterSection) {
    var triggered = false;
    var observer = new IntersectionObserver(function(entries) {
        if (entries[0].isIntersecting && !triggered) {
            triggered = true;
            animateCounters();
        }
    }, { threshold: 0.3 });
    observer.observe(counterSection);
}

// FAQ accordion toggle
document.querySelectorAll('.ve-faq-q').forEach(function(q) {
    q.addEventListener('click', function() {
        var item = this.closest('.ve-faq-item');
        var wasOpen = item.classList.contains('open');
        document.querySelectorAll('.ve-faq-item').forEach(function(i) { i.classList.remove('open'); });
        if (!wasOpen) item.classList.add('open');
    });
});


// Top bar EN | AR language switch.
// Mirrors Odoo's own language selector handler (website_root.js
// _onLangChangeClick): go through /website/lang/<url_code> so Odoo sets
// the frontend_lang cookie, then redirect to the localized URL (href).
// Plain vanilla JS on purpose, so it can't be affected by the bundled
// old jQuery or by Odoo's publicWidget loading order.
document.addEventListener('click', function (ev) {
    var link = ev.target.closest ? ev.target.closest('.dk-lang-link') : null;
    if (!link) { return; }
    ev.preventDefault();
    if (document.body.classList.contains('editor_enable')) { return; }
    if (link.classList.contains('active')) { return; }
    var lang = encodeURIComponent(link.getAttribute('data-url_code'));
    var url = encodeURIComponent(
        (link.getAttribute('href') || '/').replace(/[&?]edit_translations[^&?]+/, '')
    );
    var hash = encodeURIComponent(window.location.hash);
    window.location.href = '/website/lang/' + lang + '?r=' + url + hash;
});

// User account dropdown in the header (data-dk-dropdown).
// Vanilla on purpose: the header is now shared by every page of the site,
// including Odoo's own pages (/my/*, /shop...) where our legacy
// jQuery/Bootstrap 4 scripts aren't loaded - so it can't rely on either
// Bootstrap version's data-toggle / data-bs-toggle.
(function () {
    function closeAll(except) {
        document.querySelectorAll('.ve-user-dropdown.show').forEach(function (wrap) {
            if (wrap === except) { return; }
            wrap.classList.remove('show');
            var menu = wrap.querySelector('.dropdown-menu');
            if (menu) { menu.classList.remove('show'); }
            var toggle = wrap.querySelector('[data-dk-dropdown]');
            if (toggle) { toggle.setAttribute('aria-expanded', 'false'); }
        });
    }
    document.addEventListener('click', function (ev) {
        var toggle = ev.target.closest ? ev.target.closest('[data-dk-dropdown]') : null;
        if (toggle) {
            ev.preventDefault();
            var wrap = toggle.parentElement;
            var willOpen = !wrap.classList.contains('show');
            closeAll(wrap);
            wrap.classList.toggle('show', willOpen);
            var menu = wrap.querySelector('.dropdown-menu');
            if (menu) { menu.classList.toggle('show', willOpen); }
            toggle.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
            return;
        }
        if (!(ev.target.closest && ev.target.closest('.ve-user-menu'))) {
            closeAll(null);
        }
    });
    document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') { closeAll(null); }
    });
})();