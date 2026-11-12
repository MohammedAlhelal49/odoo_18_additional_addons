(function () {
    'use strict';

    // ============================================================
    // POPUP
    // ============================================================
    function showPopup(type, title, msg) {
        var popup = document.getElementById('homat-popup');
        var icon  = document.getElementById('popup-icon');
        var ttl   = document.getElementById('popup-title');
        var body  = document.getElementById('popup-msg');
        icon.textContent = type === 'success' ? '✅' : '⚠️';
        ttl.textContent  = title;
        ttl.style.color  = type === 'success' ? '#2e7d32' : '#c62828';
        body.textContent = msg;
        popup.style.display = 'flex';
    }

    function closePopup() {
        document.getElementById('homat-popup').style.display = 'none';
    }
    window.closePopup = closePopup;

    var popupEl = document.getElementById('homat-popup');
    if (popupEl) {
        popupEl.addEventListener('click', function (e) {
            if (e.target === this) closePopup();
        });
    }

    // ============================================================
    // VIDEO SOUND TOGGLE
    // ============================================================
    var video    = document.getElementById('heroVideo');
    var soundBtn = document.getElementById('soundToggle');
    if (video && soundBtn) {
        var iconOn  = soundBtn.querySelector('.icon-sound-on');
        var iconOff = soundBtn.querySelector('.icon-sound-off');
        soundBtn.addEventListener('click', function () {
            video.muted = !video.muted;
            iconOn.style.display  = video.muted ? 'none'  : 'block';
            iconOff.style.display = video.muted ? 'block' : 'none';
        });
    }

    // ============================================================
    // MOBILE MENU
    // ============================================================
    var toggle = document.querySelector('.mobile-menu-toggle');
    var nav    = document.querySelector('.main-nav');
    var scrim  = null;
    function setMenu(open) {
        document.body.classList.toggle('menu-open', open);
        if (toggle) toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (nav) nav.classList.toggle('nav--open', open);
        if (open && !scrim) {
            scrim = document.createElement('div');
            scrim.className = 'menu-scrim';
            scrim.addEventListener('click', function () { setMenu(false); });
            document.body.appendChild(scrim);
        } else if (!open && scrim) {
            scrim.remove();
            scrim = null;
        }
    }
    if (toggle && nav) {
        toggle.addEventListener('click', function () {
            setMenu(!nav.classList.contains('nav--open'));
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') setMenu(false);
        });
        nav.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', function () { setMenu(false); });
        });
        window.addEventListener('resize', function () {
            if (window.innerWidth > 768) setMenu(false);
        });
    }

    // ============================================================
    // SCROLL PROGRESS + HEADER
    // ============================================================
    try {
        var bar    = document.createElement('div');
        bar.className = 'scroll-progress';
        document.body.appendChild(bar);
        var header = document.querySelector('.site-header');
        function onScroll() {
            var doc = document.documentElement;
            var max = doc.scrollHeight - window.innerHeight;
            var p   = max > 0 ? window.scrollY / max : 0;
            bar.style.width = (p * 100).toFixed(2) + '%';
            if (header) header.classList.toggle('is-scrolled', window.scrollY > 8);
        }
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    } catch (e) {}

    // ============================================================
    // INTERSECTION OBSERVER (reveal animations)
    // ============================================================
    var prefersReduced = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReduced) document.documentElement.classList.add('reveal-ready');

    var targets = document.querySelectorAll(
        '.section-header, .stat-card, .feature-card, .why-text, .why-stat,' +
        '.requirement-item, .process-step, .process-highlight, .emirate-chip,' +
        '.emotional-content, .statement-content, .video-wrapper'
    );
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-in');
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });
        targets.forEach(function (el) {
            el.classList.add('reveal');
            io.observe(el);
        });
    } else {
        targets.forEach(function (el) { el.classList.add('is-in'); });
    }

    // ============================================================
    // WHATSAPP WIDGET
    // ============================================================
    var widget   = document.getElementById('joinchat-widget');
    var floatBtn = document.getElementById('whatsapp-float-btn');
    var closeBtn = document.querySelector('.joinchat__close');
    if (widget && floatBtn && closeBtn) {
        setTimeout(function () {
            widget.classList.add('joinchat__chatbox--show');
        }, 3000);
        floatBtn.addEventListener('click', function (e) {
            e.preventDefault();
            widget.classList.toggle('joinchat__chatbox--show');
        });
        closeBtn.addEventListener('click', function () {
            widget.classList.remove('joinchat__chatbox--show');
        });
    }

    // ============================================================
    // FORM AJAX SUBMIT
    // ============================================================
    var form = document.querySelector('.application-form__form');
    if (!form) return;

    var isEn = (document.documentElement.lang || '').toLowerCase().indexOf('en') === 0;
    var T = isEn ? {
        sending: 'Sending...',
        okTitle: 'Your application was submitted! 🎉',
        okMsg: 'Thank you for applying. The Al Omran team will review your application and contact you soon.\nPlease note that seats are limited.',
        errTitle: 'Could not submit the application',
        generic: 'Something went wrong, please try again',
        connTitle: 'Connection error',
        parseErr: 'Could not process the response, please try again',
        netErr: 'Could not reach the server, please check your internet connection'
    } : {
        sending: 'جاري الإرسال...',
        okTitle: 'تم إرسال طلبك بنجاح! 🎉',
        okMsg: 'شكراً لتقديمك. سيقوم فريق مركز العمران بمراجعة طلبك والتواصل معك قريباً.\nيرجى العلم أن عدد المقاعد محدود.',
        errTitle: 'تعذّر إرسال الطلب',
        generic: 'حدث خطأ، يرجى المحاولة مرة أخرى',
        connTitle: 'خطأ في الاتصال',
        parseErr: 'تعذّر معالجة الرد، يرجى المحاولة مرة أخرى',
        netErr: 'تعذّر الاتصال بالخادم، يرجى التحقق من الإنترنت'
    };

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        e.stopPropagation();

        var btn = form.querySelector('button[type="submit"]');
        var originalText = btn.textContent;
        btn.textContent = T.sending;
        btn.disabled = true;

        var formData = new FormData(form);
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/homat-alwatan/apply', true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

        xhr.onload = function () {
            try {
                var data = JSON.parse(xhr.responseText);
                if (data.success) {
                    showPopup('success', T.okTitle, T.okMsg);
                    // ChatGPT Ads: lead_created (نفس event_id تبع السيرفر)
                    if (window.alomranTrackLead) { window.alomranTrackLead(data.event_id); }
                    if (window.gtag) {
                        window.gtag('event', 'generate_lead', {
                            form_name: 'homat_alwatan',
                            language: isEn ? 'en' : 'ar'
                        });
                    }
                    form.reset();
                } else {
                    showPopup('error', T.errTitle, data.error || T.generic);
                }
            } catch (err) {
                showPopup('error', T.connTitle, T.parseErr);
            }
            btn.textContent = originalText;
            btn.disabled = false;
        };

        xhr.onerror = function () {
            showPopup('error', T.connTitle, T.netErr);
            btn.textContent = originalText;
            btn.disabled = false;
        };

        xhr.send(formData);
    });
})();
