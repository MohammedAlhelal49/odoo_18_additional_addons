# -*- coding: utf-8 -*-
"""
نصوص صفحة الفروع (/branches) — عربي وإنجليزي بمكان واحد.
بيانات الفروع نفسها (الأسماء، الأرقام، الخرائط) بـ _get_branches_data بـ main.py.
"""


def get_content(is_en, count):
    def t(en, ar):
        return en if is_en else ar

    return {
        'badge': t(f'{count} branches across the UAE', f'{count} فرعًا في الإمارات'),
        # SEO: نفس الـ H1 العربي القديم
        'h1': t('Our Branches', 'فروعنا في العين والإمارات'),
        'lead': t('We are always close to you wherever you are in the Emirates.',
                  'نحن دائمًا قريبون منك أينما كنت في الإمارات.'),
        # SEO: نفس الفقرة العربية القديمة عن العين
        'seo': t('', 'مركز العمران للتدريب والتطوير في العين من أفضل مراكز تعليم اللغة الإنجليزية في العين، '
                     'مع دورات انجليزي في العين على يد نخبة من المدربين المعتمدين.'),
        'search_ph': t('Search by branch, mall or area…', 'ابحث باسم الفرع أو المول أو المنطقة…'),
        'all': t('All', 'الكل'),
        'list_eyebrow': t('Our locations', 'مواقعنا'),
        # SEO: نفس الـ H2 العربي القديم
        'list_title': t('Choose the nearest branch', 'مركز العمران في العين والإمارات'),
        'list_sub': t('Call the branch directly, get directions, or open the branch page for details.',
                      'اتصل بالفرع مباشرة، أو افتح الاتجاهات، أو ادخل إلى صفحة الفرع للاطلاع على التفاصيل.'),
        'details': t('Details', 'التفاصيل'),
        'call': t('Call', 'اتصال'),
        'directions': t('Directions', 'الاتجاهات'),
        'empty': t('No branch matches your search.', 'لا يوجد فرع يطابق بحثك.'),
        'cta_title': t('Have a question?', 'عندك سؤال؟'),
        'cta_text': t('Our team is ready to answer all your questions and help you choose the nearest branch.',
                      'فريقنا جاهز للإجابة على جميع أسئلتك ومساعدتك في اختيار الفرع الأقرب.'),
        'cta_contact': t('Send your inquiry', 'أرسل استفسارك'),
        'cta_whatsapp': t('WhatsApp', 'واتساب'),
        'wa_message': t('Hello, I would like to ask about the nearest Al Omran branch.',
                        'مرحباً، أود الاستفسار عن أقرب فرع لمركز العمران.'),
    }


def count_label(n, is_en):
    if is_en:
        return f'{n} branch' if n == 1 else f'{n} branches'
    if n == 1:
        return 'فرع واحد'
    if n == 2:
        return 'فرعان'
    return f'{n} فروع' if n <= 10 else f'{n} فرعًا'


def get_detail_content(is_en):
    """نصوص صفحة الفرع الواحد (/branch/<slug>)."""
    def t(en, ar):
        return en if is_en else ar

    return {
        'back': t('All branches', 'كل الفروع'),
        'home': t('Home', 'الرئيسية'),
        'branches': t('Branches', 'الفروع'),
        'call': t('Call now', 'اتصل الآن'),
        'whatsapp': t('WhatsApp', 'واتساب'),
        'directions': t('Directions', 'الاتجاهات'),
        'open_now_hint': t('Working hours', 'أوقات الدوام'),
        'info_title': t('Branch information', 'معلومات الفرع'),
        'address': t('Address', 'العنوان'),
        'phone': t('Phone', 'الهاتف'),
        'hours': t('Working hours', 'أوقات الدوام'),
        'emirate': t('Emirate', 'الإمارة'),
        'map_title': t('Find us on the map', 'موقعنا على الخريطة'),
        'map_open': t('Open in Google Maps', 'افتح في خرائط غوغل'),
        'programs_title': t('Explore our programs', 'استكشف برامجنا'),
        'programs': [
            {'icon': 'fa-language', 'link': '/english-ielts',
             'title': t('English & Standardized Tests', 'اللغة الإنجليزية والاختبارات القياسية')},
            {'icon': 'fa-chalkboard-user', 'link': '/private-tutoring',
             'title': t('Private Tutoring & School Follow-up', 'الدروس الخصوصية والمتابعة الدراسية')},
            {'icon': 'fa-palette', 'link': '/women-courses',
             'title': t("Women's Professional Courses", 'الدورات المهنية للسيدات')},
            {'icon': 'fa-list', 'link': '/courses',
             'title': t('All courses', 'جميع الدورات')},
        ],
        'others_same': t('Other branches in {city}', 'فروع أخرى في {city}'),
        'others_any': t('Other branches', 'فروع أخرى'),
        'details': t('Details', 'التفاصيل'),
        'cta_title': t('Ready to start?', 'هل أنت جاهز للبدء؟'),
        'cta_text': t('Visit us at the branch or contact us for more information.',
                      'تفضّل بزيارتنا في الفرع أو تواصل معنا لمزيد من المعلومات.'),
        'cta_contact': t('Contact us', 'تواصل معنا'),
        'wa_message': t('Hello, I would like to ask about Al Omran {branch}.',
                        'مرحباً، أود الاستفسار عن {branch} في مركز العمران.'),
        'page_title': t('{branch} | Al Omran Training Center', '{branch} | مركز العمران للتدريب والتطوير'),
        'page_description': t('Al Omran Training and Development Center — {branch}: {location}. '
                              'Phone {phone}. {hours}. English, IELTS, private tutoring and professional courses.',
                              'مركز العمران للتدريب والتطوير — {branch}: {location}. هاتف {phone}. {hours}. '
                              'دورات اللغة الإنجليزية وIELTS والدروس الخصوصية والدورات المهنية.'),
    }