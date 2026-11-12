/** @odoo-module **/
/**
 * صفحة الدورات (/courses): فورم التسجيل بالموديل → /course/register
 * - أزرار التسجيل: [data-register-course="اسم الدورة"]
 * - رسائل الأخطاء من data-* على الموديل (عربي/إنجليزي حسب اللغة)
 * - البحث والفلترة بـ branches-page.js
 */
(function () {
    'use strict';

    // بس بصفحة /courses (مع أو بدون بادئة اللغة)
    if (!/^\/(?:[a-z]{2}(?:_[A-Za-z0-9]+)?\/)?courses\/?$/.test(window.location.pathname)) {
        return;
    }

    async function jsonRpc(url, params) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params,
                id: Math.floor(Math.random() * 1000000000),
            }),
        });
        const data = await response.json();
        if (data.error) {
            throw new Error((data.error.data && data.error.data.message) || data.error.message || 'RPC Error');
        }
        return data.result;
    }

    // فتح/سكّر الموديل: Bootstrap 5 إذا موجود، وإلا jQuery، وإلا يدوي
    function modalApi(modal) {
        const BsModal = (window.bootstrap && window.bootstrap.Modal) || window.Modal;
        if (BsModal && BsModal.getOrCreateInstance) {
            const inst = BsModal.getOrCreateInstance(modal);
            return { show: () => inst.show(), hide: () => inst.hide() };
        }
        if (window.$ && window.$.fn && window.$.fn.modal) {
            return { show: () => window.$(modal).modal('show'), hide: () => window.$(modal).modal('hide') };
        }
        return {
            show: () => {
                modal.style.display = 'block';
                modal.classList.add('show');
                modal.removeAttribute('aria-hidden');
                document.body.classList.add('modal-open');
            },
            hide: () => {
                modal.classList.remove('show');
                modal.style.display = 'none';
                modal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('modal-open');
                modal.dispatchEvent(new Event('hidden.bs.modal'));
            },
        };
    }

    function init() {
        const modal = document.getElementById('registrationModalGeneral');
        const form = document.getElementById('courseRegistrationFormGeneral');
        if (!modal || !form) {
            return;
        }
        const api = modalApi(modal);
        const formBox = document.getElementById('registrationFormGeneral');
        const successBox = document.getElementById('registrationSuccessGeneral');
        const titleEl = document.getElementById('modalCourseNameGeneral');
        const hiddenInput = document.getElementById('courseNameGeneral');
        const submitBtn = form.querySelector('button[type="submit"]');
        const submitHtml = submitBtn ? submitBtn.innerHTML : '';

        const resetModal = () => {
            if (formBox) { formBox.style.display = ''; }
            if (successBox) { successBox.style.display = 'none'; }
            form.reset();
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = submitHtml;
            }
        };

        document.querySelectorAll('[data-register-course]').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const name = btn.dataset.registerCourse || '';
                resetModal();
                if (titleEl) { titleEl.textContent = name; }
                if (hiddenInput) { hiddenInput.value = name; }
                api.show();
            });
        });

        // زر الإغلاق اليدوي (لو ما في Bootstrap JS)
        modal.querySelectorAll('[data-bs-dismiss="modal"]').forEach((btn) => {
            btn.addEventListener('click', () => {
                if (!((window.bootstrap && window.bootstrap.Modal) || window.Modal || (window.$ && window.$.fn && window.$.fn.modal))) {
                    api.hide();
                }
            });
        });
        modal.addEventListener('hidden.bs.modal', resetModal);

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fd = new FormData(form);
            const name = (fd.get('name') || '').trim();
            const phone = (fd.get('phone') || '').trim();
            const email = (fd.get('email') || '').trim();
            const courseName = fd.get('course_name') || '';
            const branch = fd.get('branch') || '';

            if (!name || !phone) {
                alert(modal.dataset.errRequired);
                return;
            }
            if (!branch) {
                alert(modal.dataset.errBranch);
                const el = form.querySelector('[name="branch"]');
                if (el) { el.focus(); }
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = modal.dataset.sending || '…';
            }
            try {
                const result = await jsonRpc('/course/register', {
                    name, phone, email, course_name: courseName, branch,
                });
                if (result && result.success) {
                    // ChatGPT Ads: lead_created (نفس event_id تبع السيرفر)
                    if (window.alomranTrackLead) { window.alomranTrackLead(result.event_id); }
                    if (formBox) { formBox.style.display = 'none'; }
                    if (successBox) { successBox.style.display = ''; }
                } else {
                    alert((result && result.error) || modal.dataset.errNetwork);
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = submitHtml;
                    }
                }
            } catch (err) {
                alert(modal.dataset.errNetwork);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = submitHtml;
                }
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();