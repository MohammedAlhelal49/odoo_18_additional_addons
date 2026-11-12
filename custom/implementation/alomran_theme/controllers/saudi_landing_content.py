# -*- coding: utf-8 -*-
"""
محتوى صفحة التعلم أونلاين لطلاب السعودية (/saudi-online)
========================================================
نفس فكرة باقي صفحات الهبوط: كل النصوص بالعربي والإنجليزي هون، والـ template بنيوي بس.
الخدمة أونلاين بالكامل، فما في قائمة فروع بالفورم — الطلبات بتروح لشركة السعودية
(alomran.saudi_company_id / saudi_team_id / saudi_user_id — شوف main.py).

ملاحظة: الملف ما بيستورد أي ملف محتوى تاني (منعاً للـ circular import).
"""

PHONE_NUMBER = '+971505829697'
PHONE_DISPLAY = '+971 50 582 9697'
ORG_ID = 'https://alomrantd.com/#organization'

# رقم الواتساب الافتراضي (ممكن يتغير من System Parameter: alomran.saudi_whatsapp)
WHATSAPP_NUMBER = '971505829697'

# ------------------------------------------------------------------
# الخدمات — key: اسم الخدمة بالـ CRM (x_course_interest) منشان التقارير
# ------------------------------------------------------------------
SERVICE_CRM_NAMES = {
    'curriculum': 'Saudi Curriculum Tutoring (Online)',
    'qiyas': 'Tahsili & Qudurat Prep (Online)',
    'english': 'English Language (Online)',
    'tests': 'IELTS / TOEFL / SAT / STEP Prep (Online)',
    'unsure': 'Needs Consultation (Saudi Online)',
}
SERVICE_KEYS = tuple(SERVICE_CRM_NAMES)
CARD_SERVICE_KEYS = ('curriculum', 'qiyas', 'english', 'tests')

# المرحلة: القيم اللي إلها مقابل بـ x_study_stage بتنحفظ فيه، والباقي بالوصف بس
STAGE_KEYS = ('primary', 'intermediate', 'secondary', 'university', 'adult')
STAGE_TO_CRM = {'primary': 'primary', 'intermediate': 'middle', 'secondary': 'secondary',
                'university': 'university'}

# الإنجليزي بس فيه خيار مجموعة
FORMAT_KEYS = ('individual', 'group')

# صور اختيارية للبطاقات (أول ملف موجود) — بدونها بيطلع بديل (لون + أيقونة)
_IMG = 'alomran_theme/static/src/img/saudi/'
IMAGE_FILES = {
    key: (f'{_IMG}{key}.webp', f'{_IMG}{key}.jpg')
    for key in CARD_SERVICE_KEYS
}


def get_content(is_en):
    def t(en, ar):
        return en if is_en else ar

    individual = t('One-to-one', 'فردي')
    services = [
        {
            'key': 'curriculum',
            'icon': 'fa-book-open-reader',
            'format': individual,
            'title': t('Private lessons for all Saudi curricula', 'الدروس الخصوصية لجميع المناهج السعودية'),
            'lead': t('Live one-to-one online lessons that follow the Saudi curriculum for every stage.',
                      'حصص فردية مباشرة أونلاين وفق مناهج المملكة لجميع المراحل الدراسية.'),
            'points': [t('Explaining lessons and strengthening subjects', 'شرح الدروس وتقوية المواد'),
                       t('Solving exercises and homework support', 'حل التمارين والمساعدة في الواجبات'),
                       t('Reviewing before school exams', 'المراجعة قبل الاختبارات المدرسية'),
                       t('Primary, intermediate and secondary stages', 'المرحلة الابتدائية والمتوسطة والثانوية')],
            'alt': t('Online private lesson for a Saudi student', 'درس خصوصي أونلاين لطالب في المملكة'),
        },
        {
            'key': 'qiyas',
            'icon': 'fa-chart-line',
            'format': individual,
            'title': t('Tahsili & Qudurat preparation', 'التحضير لاختبارَي التحصيلي والقدرات'),
            'lead': t('One-to-one preparation for the national standardized tests (Qiyas).',
                      'تحضير فردي للاختبارات الوطنية المقننة (قياس).'),
            'points': [t('Understanding the test structure and question types', 'فهم هيكل الاختبار وأنواع الأسئلة'),
                       t('Quantitative and verbal sections (Qudurat)', 'القسم الكمي واللفظي (القدرات)'),
                       t('Science and math review (Tahsili)', 'مراجعة العلوم والرياضيات (التحصيلي)'),
                       t('Practice tests and time management', 'اختبارات تجريبية وإدارة الوقت')],
            'alt': t('Tahsili and Qudurat test preparation', 'التحضير لاختبار التحصيلي والقدرات'),
        },
        {
            'key': 'english',
            'icon': 'fa-language',
            'format': t('One-to-one or group', 'فردي أو ضمن مجموعة'),
            'title': t('English language learning', 'تعلّم اللغة الإنجليزية'),
            'lead': t('Develop your English online — one-to-one or in a group, as you prefer.',
                      'طوّر لغتك الإنجليزية أونلاين — بشكل فردي أو ضمن مجموعة حسب رغبتك.'),
            'points': [t('Speaking and listening', 'المحادثة والاستماع'),
                       t('Reading and writing', 'القراءة والكتابة'),
                       t('Grammar and vocabulary', 'القواعد والمفردات'),
                       t('For students and adults', 'للطلاب والكبار')],
            'alt': t('Online English lesson', 'درس لغة إنجليزية أونلاين'),
        },
        {
            'key': 'tests',
            'icon': 'fa-graduation-cap',
            'format': individual,
            'title': t('IELTS, TOEFL, SAT & STEP preparation', 'التحضير لاختبارات IELTS وTOEFL وSAT وSTEP'),
            'lead': t('One-to-one training for international tests needed for study and scholarships.',
                      'تدريب فردي على الاختبارات الدولية المطلوبة للدراسة والابتعاث.'),
            'points': ['IELTS: Listening · Reading · Writing · Speaking',
                       'TOEFL: Reading · Listening · Speaking · Writing',
                       'SAT: Math · Reading & Writing',
                       'STEP: Reading · Grammar · Listening · Writing',
                       t('Practice tests and strategies', 'اختبارات تجريبية واستراتيجيات الحل')],
            'alt': t('IELTS, TOEFL, SAT and STEP preparation', 'التحضير لاختبارات IELTS وTOEFL وSAT وSTEP'),
        },
    ]

    return {
        'org_name': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
        'page_title': t('Online Tutoring for Saudi Students: Curricula, Tahsili, Qudurat, IELTS | Al Omran',
                        'دروس خصوصية أونلاين لطلاب السعودية: المناهج والتحصيلي والقدرات وIELTS | مركز العمران'),
        'page_description': t(
            'Live online lessons for students in Saudi Arabia: private tutoring for all Saudi curricula, '
            'Tahsili & Qudurat prep, English (one-to-one or group) and IELTS, TOEFL, SAT & STEP preparation.',
            'حصص مباشرة أونلاين لطلاب المملكة: دروس خصوصية لجميع المناهج السعودية، تحضير التحصيلي والقدرات، '
            'اللغة الإنجليزية فردي أو مجموعات، والتحضير لاختبارات IELTS وTOEFL وSAT وSTEP.'),

        'hero': {
            'kicker': t('Online learning for students in Saudi Arabia', 'تعلّم أونلاين لطلاب المملكة العربية السعودية'),
            'h1': t('Learn online with Al Omran — from anywhere in the Kingdom',
                    'تعلّم أونلاين مع مركز العمران من أي مكان في المملكة'),
            'subtitle': t('Private tutoring for all Saudi curricula, Tahsili & Qudurat, English and IELTS, TOEFL, SAT & STEP.',
                          'دروس خصوصية لجميع المناهج السعودية، والتحصيلي والقدرات، واللغة الإنجليزية وIELTS وTOEFL وSAT وSTEP.'),
            'intro': t('Live online lessons with a plan built around the student\'s level and goal, at times that '
                       'suit you — all from home.',
                       'حصص مباشرة عبر الإنترنت بخطة مبنية على مستوى الطالب وهدفه، وبمواعيد تناسبك — وأنت في منزلك.'),
            'cta_whatsapp': t('Contact us on WhatsApp', 'تواصل معنا عبر واتساب'),
            'cta_form': t('Book a free consultation', 'احجز استشارة مجانية'),
        },
        'chips': [
            {'icon': 'fa-video', 'label': t('Live online lessons', 'حصص مباشرة أونلاين')},
            {'icon': 'fa-user', 'label': t('One-to-one lessons', 'حصص فردية')},
            {'icon': 'fa-users', 'label': t('Groups for English', 'مجموعات للإنجليزي')},
            {'icon': 'fa-calendar-check', 'label': t('Flexible schedules', 'مواعيد مرنة')},
        ],

        'video': {
            'unmute': t('Turn sound on', 'تشغيل الصوت'),
            'mute': t('Mute', 'كتم الصوت'),
        },

        'services': {
            'title': t('Our online services', 'خدماتنا أونلاين'),
            'subtitle': t('Four services designed for students in Saudi Arabia',
                          'أربع خدمات مصممة لطلاب المملكة'),
            'items': services,
            'more': t('Request this service', 'اطلب الخدمة'),
            'whatsapp': t('Ask on WhatsApp', 'اسأل عبر واتساب'),
            'format_label': t('Format', 'طريقة الحصص'),
        },

        'how': {
            'title': t('How do online lessons work?', 'كيف تتم الدراسة أونلاين؟'),
            'items': [
                {'icon': 'fa-comment-dots', 'title': t('Contact us', 'تواصل معنا'),
                 'text': t('Tell us the service, the stage and the subject you need.',
                           'أخبرنا بالخدمة والمرحلة والمادة المطلوبة.')},
                {'icon': 'fa-clipboard-check', 'title': t('Define the level and goal', 'تحديد المستوى والهدف'),
                 'text': t('We discuss the student\'s level and goal to set the right plan.',
                           'نناقش مستوى الطالب وهدفه لتحديد الخطة المناسبة.')},
                {'icon': 'fa-calendar-days', 'title': t('Choose your schedule', 'اختر مواعيدك'),
                 'text': t('We agree on the schedule and the number of lessons that suit you.',
                           'نتفق على الجدول وعدد الحصص بما يناسبك.')},
                {'icon': 'fa-laptop', 'title': t('Start learning online', 'ابدأ الدراسة أونلاين'),
                 'text': t('Live lessons over the internet from your device, wherever you are.',
                           'حصص مباشرة عبر الإنترنت من جهازك أينما كنت.')},
            ],
        },

        'why': {
            'title': t('Why learn with Al Omran?', 'لماذا تتعلم مع مركز العمران؟'),
            'items': [
                {'icon': 'fa-house-laptop', 'title': t('From home', 'من منزلك'),
                 'text': t('No commuting — learn from anywhere in the Kingdom.',
                           'بدون تنقل — تعلّم من أي مكان في المملكة.')},
                {'icon': 'fa-user-check', 'title': t('One-to-one focus', 'اهتمام فردي'),
                 'text': t('One-to-one lessons built around each student.',
                           'حصص فردية مبنية على احتياجات كل طالب.')},
                {'icon': 'fa-clock', 'title': t('Flexible times', 'مواعيد مرنة'),
                 'text': t('Schedules agreed to suit the student.', 'جدول يتم الاتفاق عليه بما يناسب الطالب.')},
                {'icon': 'fa-users', 'title': t('Your choice for English', 'اختيارك للإنجليزي'),
                 'text': t('English one-to-one or in a group, as you prefer.',
                           'الإنجليزي فردي أو ضمن مجموعة حسب رغبتك.')},
                {'icon': 'fa-award', 'title': t('Experience since 2010', 'خبرة منذ 2010'),
                 'text': t('An accredited training center in the UAE since 2010.',
                           'مركز تدريب معتمد في دولة الإمارات منذ عام 2010.')},
            ],
        },

        'form': {
            'title': t('Book a free consultation', 'احجز استشارة مجانية'),
            'subtitle': t('Tell us what you need and our team will contact you on WhatsApp or by phone.',
                          'أخبرنا باحتياجك وسيتواصل معك فريقنا عبر واتساب أو الهاتف.'),
            'image_note': t('Learn from home', 'تعلّم من منزلك'),
            'name': t('Name', 'الاسم'),
            'name_ph': t('Your full name', 'اسمك الكامل'),
            'phone': t('Mobile / WhatsApp number', 'رقم الجوال / واتساب'),
            'phone_ph': '05XXXXXXXX',
            'service_q': t('Service', 'الخدمة'),
            'service_ph': t('Select the service', 'اختر الخدمة'),
            'stage': t('Study stage', 'المرحلة الدراسية'),
            'stage_ph': t('Select the stage', 'اختر المرحلة'),
            'format_q': t('English lessons format', 'طريقة دروس الإنجليزي'),
            'format_ph': t('Select the format', 'اختر الطريقة'),
            'subjects': t('Subject(s) or test (optional)', 'المادة أو الاختبار (اختياري)'),
            'subjects_ph': t('e.g. Math, Qudurat, IELTS', 'مثال: الرياضيات، القدرات، IELTS'),
            'submit': t('Send request', 'أرسل الطلب'),
            'sending': t('Sending…', 'جاري الإرسال…'),
            'consent': t('By sending this request, you agree that our team may contact you by phone or WhatsApp '
                         'about your request.',
                         'بإرسال الطلب، توافق على تواصل فريقنا معك عبر الهاتف أو واتساب بخصوص طلبك.'),
            'success_title': t('Your request has been sent successfully!', 'تم إرسال طلبك بنجاح!'),
            'success_text': t('Thank you. The Al Omran team will contact you soon.',
                              'شكرًا لك، سيتواصل معك فريق مركز العمران قريبًا.'),
            'success_wa': t('Or talk to us now on WhatsApp', 'أو تحدث معنا الآن عبر واتساب'),
            'err_name': t('Please enter your name', 'الرجاء إدخال اسمك'),
            'err_phone': t('Please enter a valid mobile number', 'الرجاء إدخال رقم جوال صحيح'),
            'err_service': t('Please choose a service', 'الرجاء اختيار الخدمة'),
            'err_stage': t('Please select the study stage', 'الرجاء اختيار المرحلة الدراسية'),
            'err_format': t('Please choose one-to-one or group', 'الرجاء اختيار فردي أو مجموعة'),
            'err_network': t('Connection error, please try again or message us on WhatsApp',
                             'حدث خطأ في الاتصال، حاول مرة أخرى أو راسلنا عبر واتساب'),
        },
        'service_options': [
            ('curriculum', t('Private lessons (Saudi curricula)', 'دروس خصوصية (المناهج السعودية)')),
            ('qiyas', t('Tahsili & Qudurat', 'التحصيلي والقدرات')),
            ('english', t('English language', 'اللغة الإنجليزية')),
            ('tests', 'IELTS / TOEFL / SAT / STEP'),
            ('unsure', t("I'm not sure and need a consultation", 'لست متأكدًا وأحتاج إلى استشارة')),
        ],
        'stage_options': [
            ('primary', t('Primary', 'ابتدائي')),
            ('intermediate', t('Intermediate', 'متوسط')),
            ('secondary', t('Secondary', 'ثانوي')),
            ('university', t('University', 'جامعي')),
            ('adult', t('Adult / employee', 'خريج / موظف')),
        ],
        'format_options': [
            ('individual', t('One-to-one', 'فردي')),
            ('group', t('Group', 'ضمن مجموعة')),
        ],

        'faq': {
            'title': t('Frequently asked questions', 'أسئلة شائعة'),
            'items': [
                {'q': t('Are the lessons completely online?', 'هل الدروس أونلاين بالكامل؟'),
                 'a': t('Yes, all lessons are live over the internet, so you can study from anywhere in Saudi Arabia.',
                        'نعم، جميع الحصص مباشرة عبر الإنترنت، فتستطيع الدراسة من أي مكان في المملكة.')},
                {'q': t('Do you teach the Saudi curricula?', 'هل تدرّسون المناهج السعودية؟'),
                 'a': t('Yes, private lessons follow the Saudi curricula for all school stages.',
                        'نعم، الدروس الخصوصية وفق مناهج المملكة لجميع المراحل الدراسية.')},
                {'q': t('Are the lessons one-to-one or in groups?', 'هل الحصص فردية أم جماعية؟'),
                 'a': t('All services are one-to-one, except English which can be one-to-one or in a group as you prefer.',
                        'جميع الخدمات بشكل فردي، ما عدا اللغة الإنجليزية فيمكن أن تكون فردية أو ضمن مجموعة حسب رغبتك.')},
                {'q': t('How are the schedules set?', 'كيف يتم تحديد المواعيد؟'),
                 'a': t('Our team agrees with you on the schedule and the number of lessons that suit the student.',
                        'يتفق معك فريقنا على الجدول وعدد الحصص بما يناسب الطالب.')},
                {'q': t('How much do the lessons cost?', 'كم تبلغ رسوم الحصص؟'),
                 'a': t('Fees depend on the service and the number of lessons. Send your request and our team will '
                        'contact you with the details.',
                        'تختلف الرسوم حسب الخدمة وعدد الحصص. أرسل طلبك وسيتواصل معك فريقنا بالتفاصيل.')},
                {'q': t('What do I need to attend the lessons?', 'ماذا أحتاج لحضور الحصص؟'),
                 'a': t('A computer, tablet or phone with a stable internet connection.',
                        'جهاز كمبيوتر أو تابلت أو جوال مع اتصال إنترنت مستقر.')},
            ],
        },

        'band': {
            'title': t('Talk to us now on WhatsApp', 'تواصل معنا الآن عبر واتساب'),
            'text': t('Our team is ready to help you choose the right service', 'فريقنا جاهز لمساعدتك في اختيار الخدمة المناسبة'),
            'tagline': t('Learn from home with a plan made for you', 'تعلّم من منزلك بخطة مصممة لك'),
        },

        'sticky': {
            'whatsapp': t('WhatsApp', 'واتساب'),
            'form': t('Free consultation', 'استشارة مجانية'),
        },

        'wa_general': t('Hello, I am in Saudi Arabia and would like to ask about online lessons at Al Omran.',
                        'مرحباً، أنا من السعودية وأود الاستفسار عن الدروس أونلاين في مركز العمران.'),
        'wa_service': t('Hello, I am in Saudi Arabia and would like to ask about "{service}" online at Al Omran.',
                        'مرحباً، أنا من السعودية وأود الاستفسار عن "{service}" أونلاين في مركز العمران.'),

        'lead_labels': {
            'service': t('Service', 'الخدمة'),
            'stage': t('Study stage', 'المرحلة الدراسية'),
            'format': t('English format', 'طريقة الإنجليزي'),
            'subjects': t('Subjects / test', 'المادة / الاختبار'),
            'country': t('Country', 'الدولة'),
            'country_value': t('Saudi Arabia (online)', 'السعودية (أونلاين)'),
            'source': t('Source', 'المصدر'),
            'source_value': t('Saudi online learning landing page', 'صفحة التعلم أونلاين - السعودية'),
            'campaign': t('Campaign', 'الحملة'),
            'click_id': t('Ad click ID', 'معرف النقرة الإعلانية'),
        },
    }
