# -*- coding: utf-8 -*-
"""
محتوى صفحة "تواصل معنا" (/contact) — عربي وإنجليزي بمكان واحد.
النصوص العربية نفس اللي كانت بـ ar.po. قيم "الموضوع" (subject) بتنحفظ بالإنجليزي
بالـ CRM متل ما كانت — الترجمة للعرض بس.
"""
from .site_facts import BRANCHES

PHONE_NUMBER = '+971505829697'
PHONE_DISPLAY = '+971 50 582 9697'
WHATSAPP_NUMBER = '971505829697'
EMAIL = 'alomran.td@gmail.com'

SOCIAL = [
    ('https://www.facebook.com/alomran.td/', 'fab fa-facebook-f', 'Facebook'),
    ('https://www.instagram.com/alomran.td/', 'fab fa-instagram', 'Instagram'),
    ('https://www.tiktok.com/@alomran.td', 'fab fa-tiktok', 'TikTok'),
]


def get_content(is_en):
    def t(en, ar):
        return en if is_en else ar

    return {
        'page_title': t('Contact Al Omran Training Center | Phone, WhatsApp & Branches',
                        'تواصل معنا | مركز العمران للتدريب والتطوير — هاتف وواتساب وفروع'),
        'page_description': t(
            f'Contact Al Omran Training and Development Center by phone, WhatsApp or email, or visit one of our '
            f'{BRANCHES} branches across the UAE. We respond within 24 hours.',
            f'تواصل مع مركز العمران للتدريب والتطوير عبر الهاتف أو واتساب أو البريد الإلكتروني، أو زرنا في أحد '
            f'فروعنا الـ {BRANCHES} في الإمارات. نرد خلال 24 ساعة.'),

        'hero': {
            'badge': t('We respond within 24 hours', 'نرد خلال 24 ساعة'),
            'title_1': t('Contact', 'تواصل'),
            'title_2': t('us', 'معنا'),
            'lead': t('We are here to answer all your questions and help you start your training journey',
                      'نحن هنا للإجابة على جميع أسئلتك ومساعدتك في بدء رحلتك التدريبية'),
        },

        'cards': [
            {'key': 'phone', 'icon': 'fa-phone', 'title': t('Call us', 'اتصل بنا'),
             'value': PHONE_DISPLAY, 'ltr': True, 'href': f'tel:{PHONE_NUMBER}',
             'note': t('Saturday to Thursday: 9:00 AM - 10:00 PM', 'السبت إلى الخميس: 9:00 ص - 10:00 م')},
            {'key': 'whatsapp', 'icon': 'fab fa-whatsapp', 'title': t('WhatsApp', 'واتساب'),
             'value': t('Chat with us now', 'راسلنا الآن'), 'ltr': False, 'href': f'https://wa.me/{WHATSAPP_NUMBER}',
             'note': t('Instant communication', 'تواصل فوري'), 'external': True},
            {'key': 'email', 'icon': 'fa-envelope', 'title': t('Email us', 'راسلنا عبر البريد'),
             'value': EMAIL, 'ltr': True, 'href': f'mailto:{EMAIL}',
             'note': t('We respond within 24 hours', 'نرد خلال 24 ساعة')},
            {'key': 'branches', 'icon': 'fa-location-dot', 'title': t('Our locations', 'مواقعنا'),
             'value': t(f'{BRANCHES} branches across the UAE', f'{BRANCHES} فرعًا في الإمارات'), 'ltr': False,
             'href': '/branches',
             'note': t('Al Ain - Dubai - Abu Dhabi - Ras Al Khaimah', 'العين - دبي - أبوظبي - رأس الخيمة')},
        ],

        'form': {
            'eyebrow': t('Contact form', 'نموذج الاتصال'),
            'title': t('Send us a message', 'أرسل لنا رسالة'),
            'subtitle': t('Fill out the form below and we will contact you as soon as possible',
                          'املأ النموذج أدناه وسنتواصل معك في أقرب وقت ممكن'),
            'name': t('Full name', 'الاسم الكامل'),
            'name_ph': t('Enter your full name', 'أدخل اسمك الكامل'),
            'phone': t('Phone number', 'رقم الهاتف'),
            'email': t('Email (optional)', 'البريد الإلكتروني (اختياري)'),
            'subject': t('Subject', 'الموضوع'),
            'subject_ph': t('Select subject', 'اختر الموضوع'),
            'branch': t('Branch', 'الفرع'),
            'branch_ph': t('Select branch', 'اختر الفرع'),
            'message': t('Message', 'الرسالة'),
            'message_ph': t('Write your message here...', 'اكتب رسالتك هنا...'),
            'submit': t('Send message', 'إرسال الرسالة'),
            'privacy': t('Your details are only used to reply to your message.',
                         'تُستخدم بياناتك فقط للرد على رسالتك.'),
        },
        # القيمة (إنجليزي — بتنحفظ بالـ CRM) ، النص المعروض
        'subjects': [
            ('Course Inquiry', t('Course inquiry', 'استفسار عن دورة')),
            ('Course Registration', t('Course registration', 'تسجيل دورة')),
            ('Certificate Inquiry', t('Certificate inquiry', 'استفسار عن شهادة')),
            ('Pricing Inquiry', t('Pricing inquiry', 'استفسار عن الأسعار')),
            ('Complaint', t('Complaint', 'شكوى')),
            ('Suggestion', t('Suggestion', 'اقتراح')),
            ('Other', t('Other', 'أخرى')),
        ],

        'side': {
            'title': t('We are happy to hear from you', 'يسعدنا تواصلك معنا'),
            'text': t('We are happy to hear from you through any of the following methods',
                      'يسعدنا التواصل معك من خلال أي من الطرق التالية'),
            'hours_label': t('Working hours', 'أوقات الدوام'),
            'hours': t('Saturday to Thursday: 9:00 AM - 10:00 PM', 'السبت إلى الخميس: 9:00 ص - 10:00 م'),
            'phone_label': t('Phone', 'الهاتف'),
            'email_label': t('Email', 'البريد الإلكتروني'),
            'follow': t('Follow us', 'تابعنا'),
            'branches_cta': t('Find the nearest branch', 'اعثر على أقرب فرع'),
        },

        'faq': {
            'eyebrow': t('FAQ', 'الأسئلة الشائعة'),
            'title': t('Answers to the most common questions', 'إجابات على الأسئلة الأكثر شيوعاً'),
            'items': [
                {'q': t('How can I register for a training course?', 'كيف يمكنني التسجيل في دورة تدريبية؟'),
                 'a': t(f'You can register by visiting any of our {BRANCHES} branches, contacting us via phone or '
                        'WhatsApp, or filling out the contact form on this page and our team will contact you to '
                        'complete the registration.',
                        f'يمكنك التسجيل بزيارة أي من فروعنا الـ{BRANCHES}، أو الاتصال بنا عبر الهاتف أو واتساب، أو '
                        'ملء نموذج الاتصال في هذه الصفحة وسيتصل بك فريقنا لإكمال التسجيل.')},
                {'q': t('Are the certificates accredited?', 'هل الشهادات معتمدة؟'),
                 'a': t('Yes, all our certificates are accredited by relevant authorities in the UAE and recognized '
                        'locally and internationally.',
                        'نعم، جميع شهاداتنا معتمدة من الجهات المختصة في الإمارات ومعترف بها محلياً ودولياً.')},
                {'q': t('What is the duration of training courses?', 'ما هي مدة الدورات التدريبية؟'),
                 'a': t('Course duration varies depending on specialization and level, ranging from one week to '
                        'several months. You can inquire about specific course duration when contacting us.',
                        'تختلف مدة الدورة حسب التخصص والمستوى، وتتراوح من أسبوع واحد إلى عدة أشهر. يمكنك '
                        'الاستفسار عن مدة دورة محددة عند الاتصال بنا.')},
                {'q': t('Do you provide corporate training?', 'هل تقدمون تدريباً للشركات؟'),
                 'a': t('Yes, we offer customized training programs for companies and government entities according '
                        'to their needs. Contact us for more details.',
                        'نعم، نقدم برامج تدريبية مخصصة للشركات والجهات الحكومية وفقاً لاحتياجاتهم. اتصل بنا '
                        'للحصول على مزيد من التفاصيل.')},
            ],
        },
    }


def get_result_content(is_en):
    """نصوص صفحتي النجاح والخطأ بعد إرسال الفورم."""
    def t(en, ar):
        return en if is_en else ar

    return {
        'ok_title': t('Thank you', 'شكراً لك'),
        'ok_text': t('Your message has been received successfully. We will contact you as soon as possible.',
                     'تم استلام رسالتك بنجاح. سنتواصل معك في أقرب وقت ممكن.'),
        'home': t('Back to home', 'العودة إلى الرئيسية'),
        'whatsapp': t('WhatsApp', 'واتساب'),
        'err_title': t('Sorry, an error occurred!', 'عذراً، حدث خطأ!'),
        'err_text': t('We could not send your message. Please try again.',
                      'لم نتمكن من إرسال رسالتك. يرجى المحاولة مرة أخرى.'),
        'retry': t('Try again', 'حاول مرة أخرى'),
    }