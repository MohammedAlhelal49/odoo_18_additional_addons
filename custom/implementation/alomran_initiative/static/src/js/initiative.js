(function() {
    'use strict';

    // ============================================================
    // POPUP
    // ============================================================
    function showPopup(type, title, msg) {
        var popup = document.getElementById('initiative-popup');
        var icon  = document.getElementById('popup-icon');
        var ttl   = document.getElementById('popup-title');
        var body  = document.getElementById('popup-msg');

        icon.textContent  = type === 'success' ? '✅' : '⚠️';
        ttl.textContent   = title;
        ttl.style.color   = type === 'success' ? '#2e7d32' : '#c62828';
        body.textContent  = msg;
        popup.style.display = 'flex';
    }

    function closePopup() {
        document.getElementById('initiative-popup').style.display = 'none';
    }

    window.closePopup = closePopup;

    // إغلاق عند الضغط خارج الـ box
    document.getElementById('initiative-popup').addEventListener('click', function(e) {
        if (e.target === this) closePopup();
    });

    // ============================================================
    // FORM AJAX SUBMIT
    // ============================================================
    var form = document.querySelector('.application-form__form');
    if (!form) return;

    var isEn = (document.documentElement.lang || '').toLowerCase().indexOf('en') === 0;
    var T = isEn ? {
        sending: 'Sending...',
        okTitle: 'Your application was submitted! 🎉',
        okMsg: 'Thank you for applying. The Al Omran team will review your application and contact you soon.\nPlease note that seats are limited to 500 beneficiaries.',
        errTitle: 'Could not submit the application',
        generic: 'Something went wrong, please try again',
        connTitle: 'Connection error',
        parseErr: 'Could not process the server response, please try again',
        netErr: 'Could not reach the server, please check your internet connection and try again'
    } : {
        sending: 'جاري الإرسال...',
        okTitle: 'تم إرسال طلبك بنجاح! 🎉',
        okMsg: 'شكراً لتقديمك. سيقوم فريق مركز العمران بمراجعة طلبك والتواصل معك قريباً.\nيرجى العلم أن عدد المقاعد محدود بـ500 مستفيدة.',
        errTitle: 'تعذّر إرسال الطلب',
        generic: 'حدث خطأ، يرجى المحاولة مرة أخرى',
        connTitle: 'خطأ في الاتصال',
        parseErr: 'تعذّر معالجة الرد من الخادم، يرجى المحاولة مرة أخرى',
        netErr: 'تعذّر الاتصال بالخادم، يرجى التحقق من الإنترنت والمحاولة مرة أخرى'
    };

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var btn = form.querySelector('button[type="submit"]');
        var originalText = btn.textContent;
        btn.textContent = T.sending;
        btn.disabled = true;

        var formData = new FormData(form);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/initiative/apply', true);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');

        xhr.onload = function() {
            try {
                var data = JSON.parse(xhr.responseText);
                if (data.success) {
                    showPopup('success', T.okTitle, T.okMsg);
                    // ChatGPT Ads: lead_created (نفس event_id تبع السيرفر)
                    if (window.alomranTrackLead) { window.alomranTrackLead(data.event_id); }
                    if (window.gtag) {
                        window.gtag('event', 'generate_lead', {
                            form_name: 'women_initiative',
                            language: isEn ? 'en' : 'ar'
                        });
                    }
                    form.reset();
                    btn.textContent = originalText;
                    btn.disabled = false;
                } else {
                    showPopup('error', T.errTitle, data.error || T.generic);
                    btn.textContent = originalText;
                    btn.disabled = false;
                }
            } catch(err) {
                showPopup('error', T.connTitle, T.parseErr);
                btn.textContent = originalText;
                btn.disabled = false;
            }
        };

        xhr.onerror = function() {
            showPopup('error', T.connTitle, T.netErr);
            btn.textContent = originalText;
            btn.disabled = false;
        };

        xhr.send(formData);
    });

})();
