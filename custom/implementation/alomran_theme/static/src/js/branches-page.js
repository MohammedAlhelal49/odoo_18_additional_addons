/**
 * صفحة الفروع (/branches): فلترة حسب الإمارة + بحث نصي.
 * بيشتغل بس إذا الصفحة فيها .alb-page
 */
(function () {
    'use strict';

    function init() {
        const page = document.querySelector('.alb-page');
        if (!page) {
            return;
        }
        const items = Array.from(page.querySelectorAll('.alb-item'));
        const filters = Array.from(page.querySelectorAll('.alb-filter'));
        const input = page.querySelector('.alb-search-input');
        const empty = page.querySelector('.alb-empty');
        let city = '';

        const apply = () => {
            const q = (input && input.value || '').trim().toLowerCase();
            let shown = 0;
            items.forEach((el) => {
                const okCity = !city || el.dataset.city === city;
                const okText = !q || (el.dataset.search || '').includes(q);
                const show = okCity && okText;
                el.hidden = !show;
                if (show) {
                    shown += 1;
                }
            });
            if (empty) {
                empty.hidden = shown > 0;
            }
            filters.forEach((btn) => {
                const active = (btn.dataset.city || '') === city;
                btn.classList.toggle('is-active', active);
                btn.setAttribute('aria-pressed', active ? 'true' : 'false');
            });
        };

        filters.forEach((btn) => {
            btn.addEventListener('click', () => {
                city = btn.dataset.city || '';
                apply();
            });
        });

        if (input) {
            input.addEventListener('input', apply);
        }

        // فلتر من الرابط: /branches?city=دبي (من بطاقات الإمارات بالرئيسية)
        try {
            const wanted = new URLSearchParams(window.location.search).get('city');
            if (wanted && filters.some((btn) => (btn.dataset.city || '') === wanted)) {
                city = wanted;
                apply();
            }
        } catch (e) { /* متصفح قديم — بتنعرض كل الفروع */ }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();