/** @odoo-module **/

/**
 * Alomran — Pop-up Offers
 * =======================
 * - السيرفر بيختار العرض حسب الصفحة: عرض خاص بصفحة الكورس أولاً، وإلا العرض العام
 * - تكرار الظهور حسب إعداد العرض:
 *     every_page → بكل صفحة، حتى لو سكّره الزائر
 *     session    → مرة بكل جلسة تصفح
 *     days       → مرة كل N يوم
 * - التواصل مباشرة عبر واتساب (بلا فورم)
 * - بلا Bootstrap modal: overlay خاص (Escape، focus، قفل التمرير)
 * - كل النصوص بتنحط بـ textContent (بلا innerHTML)
 */
(function () {
    'use strict';

    const STORE_PREFIX = 'alomran_offer_';

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------
    async function jsonRpc(url, params) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: params, id: Date.now() }),
        });
        const data = await response.json();
        if (data.error) {
            throw new Error((data.error.data && data.error.data.message) || data.error.message || 'RPC Error');
        }
        return data.result;
    }

    function track(offerId, event) {
        jsonRpc('/popup/track', { offer_id: offerId, event: event }).catch(() => {});
    }

    function storageGet(store, key) {
        try { return store.getItem(key); } catch (e) { return null; }
    }

    function storageSet(store, key, value) {
        try { store.setItem(key, value); } catch (e) { /* blocked */ }
    }

    /** هل لازم ما ينعرض العرض هلق حسب تكرار الظهور؟ */
    function isSuppressed(s) {
        const key = STORE_PREFIX + s.id;
        if (s.display_frequency === 'session') {
            return !!storageGet(window.sessionStorage, key);
        }
        if (s.display_frequency === 'days') {
            const ts = parseInt(storageGet(window.localStorage, key) || '0', 10);
            return ts > 0 && (Date.now() - ts) < s.cookie_duration * 24 * 3600 * 1000;
        }
        return false;   // every_page
    }

    function markShown(s) {
        const key = STORE_PREFIX + s.id;
        if (s.display_frequency === 'session') {
            storageSet(window.sessionStorage, key, '1');
        } else if (s.display_frequency === 'days') {
            storageSet(window.localStorage, key, String(Date.now()));
        }
    }

    function setText(el, text) {
        if (!el) {
            return;
        }
        const target = el.querySelector('span:not([class])') || el;
        target.textContent = text || '';
        el.hidden = !text;
    }

    // ------------------------------------------------------------
    // Main
    // ------------------------------------------------------------
    async function init() {
        const popup = document.getElementById('offerPopup');
        if (!popup) {
            return;
        }

        let s;
        try {
            s = await jsonRpc('/popup/settings', { path: window.location.pathname });
        } catch (e) {
            return;
        }
        if (!s || !s.active || isSuppressed(s)) {
            return;
        }

        populate(popup, s);

        let shown = false;
        let lastFocus = null;
        let countdownTimer = null;

        const open = () => {
            if (shown) {
                return;
            }
            shown = true;
            lastFocus = document.activeElement;
            popup.hidden = false;
            document.documentElement.classList.add('ao-popup-open');
            window.requestAnimationFrame(() => popup.classList.add('is-open'));
            const wa = popup.querySelector('.ao-popup-wa');
            if (wa) {
                wa.focus({ preventScroll: true });
            }
            if (s.show_countdown) {
                countdownTimer = startCountdown(popup, s.end_ms);
            }
            markShown(s);
            track(s.id, 'view');
        };

        const close = () => {
            popup.classList.remove('is-open');
            document.documentElement.classList.remove('ao-popup-open');
            if (countdownTimer) {
                window.clearInterval(countdownTimer);
            }
            window.setTimeout(() => { popup.hidden = true; }, 200);
            if (lastFocus && typeof lastFocus.focus === 'function') {
                lastFocus.focus({ preventScroll: true });
            }
            // every_page: ما منخزن شي — بيرجع يطلع بالصفحة الجاية
        };

        popup.addEventListener('click', (ev) => {
            if (ev.target.closest('[data-ao-close]')) {
                close();
            }
        });
        document.addEventListener('keydown', (ev) => {
            if (ev.key === 'Escape' && !popup.hidden) {
                close();
            }
        });

        const wa = popup.querySelector('.ao-popup-wa');
        if (wa) {
            wa.addEventListener('click', () => {
                track(s.id, 'click');
                window.setTimeout(close, 300);
            });
        }

        window.setTimeout(open, (s.delay_seconds || 0) * 1000);
        if (s.exit_intent) {
            document.addEventListener('mouseout', (ev) => {
                if (!ev.relatedTarget && ev.clientY <= 0) {
                    open();
                }
            });
        }
    }

    function populate(popup, s) {
        popup.setAttribute('dir', s.is_english ? 'ltr' : 'rtl');
        popup.setAttribute('lang', s.is_english ? 'en' : 'ar');

        const badge = popup.querySelector('.ao-popup-badge');
        if (badge && s.badge_text) {
            badge.querySelector('.ao-popup-badge-text').textContent = s.badge_text;
            badge.style.background = s.badge_color;
            badge.hidden = false;
        }
        popup.querySelector('.ao-popup-highlight').textContent = s.highlight || s.title || '';
        // العنوان بينعرض بس إذا مختلف عن نص العرض (بالعرض المخصص هني نفس الشي)
        setText(popup.querySelector('.ao-popup-title'), s.title !== s.highlight ? s.title : '');
        setText(popup.querySelector('.ao-popup-subtitle'), s.subtitle);
        setText(popup.querySelector('.ao-popup-desc'), s.description);
        setText(popup.querySelector('.ao-popup-terms'), s.terms);
        setText(popup.querySelector('.ao-popup-proof'), s.social_proof);

        const wa = popup.querySelector('.ao-popup-wa');
        if (wa && /^https:\/\/wa\.me\/\d+/.test(s.whatsapp_url || '')) {
            wa.href = s.whatsapp_url;
        }
        popup.querySelector('.ao-popup-wa-text').textContent = s.whatsapp_btn || '';
        popup.querySelector('.ao-popup-later').textContent = s.close_btn || '';

        if (s.show_countdown) {
            popup.querySelector('.ao-popup-countdown-title').textContent = s.countdown_title || '';
            popup.querySelector('[data-ao-label="days"]').textContent = s.days_label || '';
            popup.querySelector('[data-ao-label="hours"]').textContent = s.hours_label || '';
            popup.querySelector('[data-ao-label="mins"]').textContent = s.mins_label || '';
            popup.querySelector('.ao-popup-countdown').hidden = false;
        }
    }

    function startCountdown(popup, endMs) {
        const pad = (n) => String(Math.max(0, n)).padStart(2, '0');
        const tick = () => {
            const left = Math.max(0, endMs - Date.now());
            const mins = Math.floor(left / 60000);
            popup.querySelector('[data-ao-cd="days"]').textContent = pad(Math.floor(mins / 1440));
            popup.querySelector('[data-ao-cd="hours"]').textContent = pad(Math.floor((mins % 1440) / 60));
            popup.querySelector('[data-ao-cd="mins"]').textContent = pad(mins % 60);
            return left;
        };
        tick();
        const timer = window.setInterval(() => {
            if (tick() <= 0) {
                window.clearInterval(timer);
            }
        }, 30000);
        return timer;
    }
})();