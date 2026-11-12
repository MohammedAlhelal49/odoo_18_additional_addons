/** @odoo-module **/

/**
 * صفحات الهبوط بنمط ale-: الإنجليزي والاختبارات (/english-ielts)
 * والدروس الخصوصية والدعم الأكاديمي (/private-tutoring)
 * - اختيار البرنامج / طريقة التدريب من الأزرار أو من الرابط (?program=ielts)
 * - فيديوهات يوتيوب بأسلوب facade (الـ iframe بيتحمّل بس عند الضغط)
 * - فورم الاستشارة → data-submit-url على الفورم (الافتراضي /english-ielts/submit) + تتبع التحويل
 * - حقول إضافية بالفورم: أي عنصر عليه data-ale-extra بينبعت باسمه،
 *   وإذا عليه required ورسالة data-err بيتفحص قبل الإرسال
 * - شريط CTA ثابت عالموبايل
 * بيشتغل بس إذا عنصر الفورم موجود — ما في أي فحص للـ URL.
 */
(function () {
    'use strict';

    const DEFAULT_SUBMIT_URL = '/english-ielts/submit';
    // بس مسارات داخلية بنفس الموقع
    const SUBMIT_URL_RE = /^\/[A-Za-z0-9\-_/]+\/submit$/;
    const YT_ID_RE = /^[A-Za-z0-9_-]{11}$/;
    const UTM_RE = /^[\w.\-]{1,50}$/u;
    const UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign'];
    const UTM_STORE = 'alomran_landing_utm';

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        // فيديو الهيرو: بأي صفحة فيها .ale-hero-video (صفحات الهبوط + الصفحة الرئيسية)
        document.querySelectorAll('.ale-hero-video').forEach(initHeroVideo);

        const root = document.querySelector('.ale-page');
        const form = document.getElementById('ale-lead-form');
        if (!root || !form) {
            return;
        }
        rememberUtm();
        initVideos(root);
        initPreselect(root, form);
        initForm(form);
        initSticky(root);
    }

    // ------------------------------------------------------------
    // UTM: من الرابط، أو من أول زيارة بنفس الجلسة
    // ------------------------------------------------------------
    function rememberUtm() {
        try {
            const params = new URLSearchParams(window.location.search);
            const found = {};
            UTM_KEYS.forEach((k) => {
                const v = (params.get(k) || '').trim();
                if (v && UTM_RE.test(v)) {
                    found[k] = v;
                }
            });
            if (Object.keys(found).length) {
                window.sessionStorage.setItem(UTM_STORE, JSON.stringify(found));
            }
        } catch (e) { /* storage blocked */ }
    }

    function getUtm() {
        try {
            return JSON.parse(window.sessionStorage.getItem(UTM_STORE) || '{}') || {};
        } catch (e) {
            return {};
        }
    }

    // ------------------------------------------------------------
    // YouTube facade
    // ------------------------------------------------------------
    function initVideos(root) {
        root.querySelectorAll('[data-ale-yt]').forEach((btn) => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-ale-yt') || '';
                if (!YT_ID_RE.test(id)) {
                    return;
                }
                const iframe = document.createElement('iframe');
                iframe.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0';
                iframe.title = btn.getAttribute('aria-label') || 'Video';
                iframe.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
                iframe.allowFullscreen = true;
                iframe.loading = 'lazy';
                const wrap = document.createElement('div');
                wrap.className = 'ale-video ale-video-playing';
                wrap.appendChild(iframe);
                btn.replaceWith(wrap);
            }, { once: true });
        });
    }

    // ------------------------------------------------------------
    // Hero video (autoplay muted loop):
    // - بيوقف لما يطلع من الشاشة وبيرجع لما يرجع (توفير CPU وبطارية)
    // - إذا المستخدم مفعّل "تقليل الحركة" بيوقف عالفريم الأول
    // ------------------------------------------------------------
    function initHeroVideo(root) {
        const video = root.querySelector('video.ale-hero-autoplay');
        if (!video) {
            return;
        }
        video.muted = true;   // احتياط لبعض المتصفحات قبل play()
        const tryPlay = () => {
            const p = video.play();
            if (p && typeof p.catch === 'function') {
                p.catch(() => { /* autoplay blocked (مثلاً وضع توفير الطاقة) — بيضل الغلاف ظاهر */ });
            }
        };

        // ---- زر الصوت ----
        const soundBtn = root.querySelector('.ale-sound-toggle');
        let firstUnmute = true;
        const setSoundUi = () => {
            if (!soundBtn) {
                return;
            }
            const on = !video.muted;
            const label = on ? soundBtn.dataset.labelMute : soundBtn.dataset.labelUnmute;
            soundBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
            soundBtn.setAttribute('aria-label', label);
            soundBtn.classList.toggle('is-on', on);
            const icon = soundBtn.querySelector('i');
            if (icon) {
                icon.className = 'fa ' + (on ? 'fa-volume-high' : 'fa-volume-xmark');
            }
            const text = soundBtn.querySelector('.ale-sound-label');
            if (text) {
                text.textContent = label;
            }
        };
        if (soundBtn) {
            soundBtn.addEventListener('click', () => {
                video.muted = !video.muted;
                if (!video.muted && firstUnmute) {
                    // أول مرة بيشغّل الصوت: منرجع للبداية ليسمع الفيديو من أوله
                    firstUnmute = false;
                    video.currentTime = 0;
                }
                // إذا كتم الصوت بإيده: ما منرجع نعرض الزر الكبير بباقي الصفحات بنفس الزيارة
                rememberMuted(video.muted);
                hideBigPrompt();
                tryPlay();
                setSoundUi();
            });
        }

        // ---- زر "اضغط لتشغيل الصوت" الكبير بنص الفيديو ----
        // بيظهر لما يبلش الفيديو صامت، وبيختفي بالضغط أو بعد BIG_PROMPT_MS
        // أو لما يستخدم الزر الصغير. ما بيغطي شي من الصفحة (جوا الفيديو بس).
        const BIG_PROMPT_MS = 7000;
        let bigBtn = null;
        let bigTimer = null;
        function rememberMuted(muted) {
            try {
                if (muted) {
                    window.sessionStorage.setItem('alomran_sound_off', '1');
                } else {
                    window.sessionStorage.removeItem('alomran_sound_off');
                }
            } catch (e) { /* storage مقفول — عادي */ }
        }
        function userMutedBefore() {
            try {
                return window.sessionStorage.getItem('alomran_sound_off') === '1';
            } catch (e) {
                return false;
            }
        }
        function hideBigPrompt() {
            if (!bigBtn) {
                return;
            }
            clearTimeout(bigTimer);
            bigBtn.classList.remove('is-visible');
            const btn = bigBtn;
            bigBtn = null;
            setTimeout(() => btn.remove(), 400);
        }
        function showBigPrompt() {
            if (!soundBtn || bigBtn || !video.muted || userMutedBefore()) {
                return;
            }
            const isAr = (document.documentElement.lang || '').toLowerCase().startsWith('ar');
            const label = soundBtn.dataset.labelBig || (isAr ? 'اضغط لتشغيل الصوت' : 'Tap to turn sound on');
            bigBtn = document.createElement('button');
            bigBtn.type = 'button';
            bigBtn.className = 'ale-sound-big';
            bigBtn.setAttribute('aria-label', label);
            const ring = document.createElement('span');
            ring.className = 'ale-sound-big-ring';
            ring.innerHTML = '<i class="fa fa-volume-high" aria-hidden="true"></i>';
            const text = document.createElement('span');
            text.className = 'ale-sound-big-label';
            text.textContent = label;
            bigBtn.append(ring, text);
            bigBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (video.muted) {
                    soundBtn.click();   // نفس منطق الزر الصغير (تشغيل الصوت + من البداية)
                } else {
                    hideBigPrompt();
                }
            });
            root.appendChild(bigBtn);
            // frame واحد قبل الـ class منشان يشتغل الـ fade-in
            requestAnimationFrame(() => bigBtn && bigBtn.classList.add('is-visible'));
            bigTimer = setTimeout(hideBigPrompt, BIG_PROMPT_MS);
        }

        const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
        if (reduceMotion && reduceMotion.matches) {
            // بلا حركة تلقائية — بيشتغل بس لما يضغط زر الصوت (الكبير أو الصغير)
            video.removeAttribute('autoplay');
            video.pause();
            showBigPrompt();
            return;
        }

        // أول ما يبلش الفيديو فعلاً (صامت): منعرض الزر الكبير مرة وحدة
        video.addEventListener('playing', showBigPrompt, { once: true });

        if ('IntersectionObserver' in window) {
            new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    tryPlay();
                } else {
                    video.pause();
                }
            }, { threshold: 0.2 }).observe(video);
        } else {
            tryPlay();
        }
    }

    // ------------------------------------------------------------
    // Preselect program / mode
    // ------------------------------------------------------------
    function checkRadio(form, name, value) {
        if (!value) {
            return false;
        }
        const input = Array.from(form.querySelectorAll('input[name="' + name + '"]'))
            .find((el) => el.value === value);
        const notify = () => {
            // الحقول الشرطية (data-ale-show-for) بتسمع لهالحدث
            form.dispatchEvent(new CustomEvent('ale:program-set'));
            return true;
        };
        if (input) {
            input.checked = true;
            return notify();
        }
        // نفس الحقل ممكن يكون <select> (صفحة الدروس الخصوصية)
        const select = form.querySelector('select[name="' + name + '"]');
        if (select && Array.from(select.options).some((o) => o.value === value)) {
            select.value = value;
            return notify();
        }
        return false;
    }

    function goToForm(form) {
        const section = document.getElementById('ale-form');
        if (section) {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        const name = form.querySelector('#ale-name');
        if (name) {
            window.setTimeout(() => name.focus({ preventScroll: true }), 500);
        }
    }

    function initPreselect(root, form) {
        checkRadio(form, 'program', root.getAttribute('data-program'));
        checkRadio(form, 'mode', root.getAttribute('data-mode'));

        root.addEventListener('click', (ev) => {
            const link = ev.target.closest('[data-ale-program], [data-ale-mode], a[href="#ale-form"]');
            if (!link) {
                return;
            }
            ev.preventDefault();
            checkRadio(form, 'program', link.getAttribute('data-ale-program'));
            checkRadio(form, 'mode', link.getAttribute('data-ale-mode'));
            goToForm(form);
        });
    }

    // ------------------------------------------------------------
    // Form
    // ------------------------------------------------------------
    async function jsonRpc(url, params) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params,
                id: Math.floor(Math.random() * 1e9),
            }),
        });
        const data = await response.json();
        if (data.error) {
            throw new Error((data.error.data && data.error.data.message) || data.error.message || 'RPC Error');
        }
        return data.result;
    }

    function radioValue(form, name) {
        const el = form.querySelector('input[name="' + name + '"]:checked');
        if (el) {
            return el.value;
        }
        const select = form.querySelector('select[name="' + name + '"]');
        return select ? select.value : '';
    }

    function validPhone(phone) {
        const digits = phone.replace(/\D/g, '');
        return digits.length >= 9 && digits.length <= 15;
    }

    function initForm(form) {
        const errorBox = form.querySelector('.ale-form-error');
        const submitBtn = form.querySelector('button[type="submit"]');
        const card = form.closest('.ale-form-card');
        const successBox = card ? card.querySelector('.ale-form-success') : null;
        let busy = false;

        function showError(message, field) {
            errorBox.textContent = message;
            errorBox.hidden = false;
            if (field) {
                field.focus();
            }
        }

        // حقول شرطية: <div data-ale-show-for="english"> بيظهر بس إذا الخدمة المختارة منها
        // (قائمة مفصولة بفاصلة). المخفي بيتعطّل، فما بيتفحص وما بينبعت.
        const conditionals = Array.from(form.querySelectorAll('[data-ale-show-for]'));
        function syncConditionals() {
            const program = radioValue(form, 'program');
            conditionals.forEach((box) => {
                const show = box.dataset.aleShowFor.split(',').map((x) => x.trim()).includes(program);
                box.hidden = !show;
                box.querySelectorAll('input, select, textarea').forEach((el) => {
                    el.disabled = !show;
                });
            });
        }
        if (conditionals.length) {
            form.querySelectorAll('[name="program"]').forEach((el) => {
                el.addEventListener('change', syncConditionals);
            });
            syncConditionals();
            // الاختيار المسبق (من بطاقة أو ?service=) بيصير بعد هالسطر — منعيد المزامنة
            form.addEventListener('ale:program-set', syncConditionals);
        }

        form.addEventListener('submit', async (ev) => {
            ev.preventDefault();
            if (busy) {
                return;
            }
            errorBox.hidden = true;

            const nameEl = form.querySelector('#ale-name');
            const phoneEl = form.querySelector('#ale-phone');
            const branchEl = form.querySelector('#ale-branch');
            const payload = {
                name: nameEl.value.trim(),
                phone: phoneEl.value.trim(),
                // بعض الصفحات ما فيها فرع (متل /saudi-online الأونلاين)
                branch: branchEl ? branchEl.value : '',
                program: radioValue(form, 'program'),
                mode: radioValue(form, 'mode'),
                website_url: (form.querySelector('[name="website_url"]') || {}).value || '',
            };

            if (!payload.name) {
                return showError(form.dataset.errName, nameEl);
            }
            if (!validPhone(payload.phone)) {
                return showError(form.dataset.errPhone, phoneEl);
            }
            if (branchEl && !payload.branch) {
                return showError(form.dataset.errBranch, branchEl);
            }
            if (!payload.program) {
                return showError(form.dataset.errProgram, form.querySelector('[name="program"]'));
            }
            if (form.querySelector('[name="mode"]') && !payload.mode) {
                return showError(form.dataset.errMode, form.querySelector('[name="mode"]'));
            }
            const extras = Array.from(form.querySelectorAll('[data-ale-extra][name]'));
            for (const el of extras) {
                if (el.disabled) {
                    continue;   // حقل شرطي مخفي (data-ale-show-for)
                }
                if (el.type === 'radio' && !el.checked) {
                    continue;   // من مجموعة radio بناخد المختار بس
                }
                const value = (el.value || '').trim();
                if (el.required && !value) {
                    return showError(el.dataset.err || form.dataset.errNetwork, el);
                }
                payload[el.name] = value;
            }

            Object.assign(payload, getUtm());
            if (typeof window.alomranGetClickIds === 'function') {
                Object.assign(payload, window.alomranGetClickIds());
            }

            busy = true;
            const originalHtml = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.textContent = form.dataset.sending || '...';

            try {
                const customUrl = form.dataset.submitUrl || '';
                const submitUrl = SUBMIT_URL_RE.test(customUrl) ? customUrl : DEFAULT_SUBMIT_URL;
                const result = await jsonRpc(submitUrl, payload);
                if (result && result.success) {
                    if (result.event_id && typeof window.alomranTrackLead === 'function') {
                        window.alomranTrackLead(result.event_id);
                    }
                    form.hidden = true;
                    if (successBox) {
                        successBox.hidden = false;
                        successBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                    form.reset();
                    return;
                }
                showError((result && result.error) || form.dataset.errNetwork);
            } catch (e) {
                showError(form.dataset.errNetwork);
            } finally {
                busy = false;
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalHtml;
            }
        });
    }

    // ------------------------------------------------------------
    // Sticky mobile CTA: بيظهر بعد الهيرو، وبيختفي لما الفورم ظاهر
    // ------------------------------------------------------------
    function initSticky(root) {
        const bar = root.querySelector('.ale-sticky');
        const hero = root.querySelector('.ale-hero, .alw-hero');
        const formSection = document.getElementById('ale-form');
        if (!bar || !hero || !formSection || !('IntersectionObserver' in window)) {
            return;
        }
        let heroVisible = true;
        let formVisible = false;
        const update = () => {
            const show = !heroVisible && !formVisible;
            bar.classList.toggle('is-visible', show);
            bar.setAttribute('aria-hidden', show ? 'false' : 'true');
            bar.querySelectorAll('a').forEach((a) => a.setAttribute('tabindex', show ? '0' : '-1'));
        };
        new IntersectionObserver((entries) => {
            heroVisible = entries[0].isIntersecting;
            update();
        }).observe(hero);
        new IntersectionObserver((entries) => {
            formVisible = entries[0].isIntersecting;
            update();
        }, { threshold: 0.15 }).observe(formSection);
    }
})();