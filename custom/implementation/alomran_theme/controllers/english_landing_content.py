# -*- coding: utf-8 -*-
"""
محتوى صفحة اللغة الإنجليزية والاختبارات القياسية (صفحة هبوط إعلانات غوغل)
=========================================================================
كل نصوص الصفحة بالعربي والإنجليزي بمكان واحد، والـ template بنيوي بس.
أي تعديل على النصوص بيصير هون بدون ما نلمس الـ XML أو ar.po.

القيم الثابتة (keys) هي اللي بتنبعت من الفورم وبتنفحص بالسيرفر — لا تغيرها
بدون ما تعدل الـ Selection fields على crm.lead.
"""

# ------------------------------------------------------------------
# أرقام المركز — لازم تتطابق مع باقي صفحات الموقع
# ------------------------------------------------------------------
from .site_facts import BRANCHES  # noqa: F401  (عدد الفروع من مكان واحد)

TRAINEES = '+20,000'

# رقم الواتساب الافتراضي (ممكن يتغير من System Parameter: alomran.english_whatsapp)
WHATSAPP_NUMBER = '971505829697'

# رقم الاتصال — نفس رقم صفحة تواصل معنا
PHONE_NUMBER = '+971505829697'
PHONE_DISPLAY = '+971 50 582 9697'

# رابط "شاهد المزيد من تجارب المتدربين"
MORE_TESTIMONIALS_URL = 'https://www.instagram.com/alomran.td/'

ORG_ID = 'https://alomrantd.com/#organization'

# ------------------------------------------------------------------
# البرامج — key: (اسم البرنامج بالـ CRM، أيقونة)
# أسماء الـ CRM نفس الأسماء القديمة من صفحة اللغات منشان التقارير
# ------------------------------------------------------------------
PROGRAM_CRM_NAMES = {
    'english': 'General English',
    'ielts': 'IELTS Preparation',
    'toefl': 'TOEFL Preparation',
    'sat': 'SAT Preparation',
    'alcpt': 'ALCPT Preparation',
    'unsure': 'Needs Consultation',
}
PROGRAM_KEYS = tuple(PROGRAM_CRM_NAMES)
# البرامج اللي إلها بطاقة (كل شي ما عدا "لا أعرف")
CARD_PROGRAM_KEYS = ('english', 'ielts', 'toefl', 'sat', 'alcpt')

EMIRATE_KEYS = ('abu_dhabi', 'al_ain', 'dubai', 'sharjah', 'ajman',
                'umm_al_quwain', 'ras_al_khaimah', 'fujairah')
MODE_KEYS = ('branch', 'online', 'home')

# ------------------------------------------------------------------
# صور المعرض والشهادات — بتنعبى لما يبعتهم العميل.
# إذا القائمة فاضية، القسم ما بيظهر بالصفحة.
#
# GALLERY = [
#     {'src': '/alomran_theme/static/src/img/english/class-1.webp',
#      'alt_ar': 'فصل تدريبي في مركز العمران', 'alt_en': 'Training class at Al Omran'},
# ]
# TESTIMONIALS = [
#     {'name': 'اسم المتدرب', 'name_en': 'Trainee name',
#      'program': 'ielts', 'text_ar': '...', 'text_en': '...',
#      'photo': '/alomran_theme/static/src/img/english/t1.webp'},
# ]
#
# فيديوهات يوتيوب من System Parameters:
#   alomran.english_hero_video           ID الفيديو الرئيسي (11 محرف)
#   alomran.english_testimonial_videos   IDs مفصولة بفاصلة (حتى 3)
# ------------------------------------------------------------------
GALLERY = []
TESTIMONIALS = []


def get_content(is_en):
    """كل نصوص الصفحة باللغة الحالية."""
    def t(en, ar):
        return en if is_en else ar

    trainees_num = TRAINEES.lstrip('+')

    programs = [
        {
            'key': 'english',
            'icon': 'fa-language',
            'heading': t('English Language', 'اللغة الإنجليزية'),
            'headline': t('Develop your English skills', 'طوّر مهاراتك في اللغة الإنجليزية'),
            'intro': t('A program that helps you develop your skills in:',
                       'برنامج يساعدك على تطوير مهارات:'),
            'skills': [t('Speaking', 'المحادثة'), t('Listening', 'الاستماع'), t('Reading', 'القراءة'),
                       t('Writing', 'الكتابة'), t('Grammar', 'القواعد'), t('Vocabulary', 'المفردات')],
            'note': t('Suitable for students, employees and anyone who wants to improve their English level.',
                      'مناسب للطلاب والموظفين وكل من يرغب في تطوير مستواه في اللغة الإنجليزية.'),
        },
        {
            'key': 'ielts',
            'icon': 'fa-bullseye',
            'heading': 'IELTS',
            'headline': t('Prepare for the IELTS test with confidence', 'استعد لاختبار IELTS بثقة'),
            'intro': t('Training on the core skills of the test:',
                       'تدريب على المهارات الأساسية للاختبار:'),
            'skills': ['Listening', 'Reading', 'Writing', 'Speaking'],
            'note': t('With a focus on understanding the test format, practice and time management.',
                      'مع التركيز على فهم طبيعة الاختبار والتدريب والممارسة وإدارة الوقت.'),
        },
        {
            'key': 'toefl',
            'icon': 'fa-graduation-cap',
            'heading': 'TOEFL',
            'headline': t('TOEFL test preparation', 'التحضير لاختبار TOEFL'),
            'intro': t('A training program focused on the core skills required in the test:',
                       'برنامج تدريبي يركز على المهارات الأساسية المطلوبة في الاختبار:'),
            'skills': ['Reading', 'Listening', 'Speaking', 'Writing'],
            'note': '',
        },
        {
            'key': 'sat',
            'icon': 'fa-book',
            'heading': 'SAT',
            'headline': t('Prepare for the SAT', 'استعد لاختبار SAT'),
            'intro': t('A preparation program focused on:', 'برنامج تحضيري يركز على:'),
            'skills': ['Math', 'Reading & Writing'],
            'note': t('With practice on question types and strategies to handle them.',
                      'مع التدريب على طبيعة الأسئلة واستراتيجيات التعامل معها.'),
        },
        {
            'key': 'alcpt',
            'icon': 'fa-shield-halved',
            'heading': 'ALCPT',
            'headline': t('ALCPT test preparation', 'التحضير لاختبار ALCPT'),
            'intro': t('A training program that helps you prepare for the ALCPT through skills training, '
                       'question types and practice tests.',
                       'برنامج تدريبي يساعدك على الاستعداد لاختبار ALCPT من خلال التدريب على المهارات '
                       'وطبيعة الأسئلة ونماذج الاختبار.'),
            'skills': [],
            'note': '',
        },
    ]

    modes_short = [
        {'key': 'branch', 'icon': 'fa-location-dot', 'label': t('At one of our branches', 'في أحد فروعنا')},
        {'key': 'online', 'icon': 'fa-laptop', 'label': t('Online', 'أونلاين')},
        {'key': 'home', 'icon': 'fa-house', 'label': t("At the student's home", 'في منزل الطالب')},
    ]

    return {
        'org_name': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
        'page_title': t('English Courses & IELTS, TOEFL, SAT, ALCPT Prep in the UAE | Al Omran',
                        'دورات اللغة الإنجليزية وتحضير IELTS وTOEFL وSAT وALCPT في الإمارات | مركز العمران'),
        'page_description': t(
            f'Improve your English and prepare for IELTS, TOEFL, SAT and ALCPT with Al Omran Training Center. '
            f'Train at one of our {BRANCHES} UAE branches, online or at home. Book your free consultation.',
            f'طوّر لغتك الإنجليزية واستعد لاختبارات IELTS وTOEFL وSAT وALCPT مع مركز العمران. '
            f'تدريب في {BRANCHES} فرعًا بالإمارات أو أونلاين أو في منزلك. احجز استشارتك الآن.'),

        'hero': {
            'h1': t('Improve your English… and prepare for your test with confidence',
                    'طوّر لغتك الإنجليزية… واستعد لاختبارك بثقة'),
            'subtitle': t('Specialized English language and standardized test preparation programs '
                          'at Al Omran Training and Development Center',
                          'برامج متخصصة في اللغة الإنجليزية والتحضير للاختبارات القياسية '
                          'في مركز العمران للتدريب والتطوير'),
            'intro': t('From developing your English skills to preparing for IELTS, TOEFL, SAT and ALCPT, '
                       'we offer training programs designed around your level, your goal and the way you '
                       'like to learn.',
                       'من تطوير مهارات اللغة الإنجليزية إلى الاستعداد لاختبارات IELTS وTOEFL وSAT وALCPT، '
                       'نقدم برامج تدريبية مصممة لتناسب مستواك وهدفك وطريقة التعلم التي تناسبك.'),
            'modes_title': t('Learn the way that suits you', 'تعلّم بالطريقة التي تناسبك'),
            'stats': [t(f'{TRAINEES} trainees', f'{TRAINEES} متدرب'),
                      t(f'{BRANCHES} branches in the UAE', f'{BRANCHES} فرعًا في الإمارات')],
            'cta_whatsapp': t('Talk to an education advisor now', 'تحدث مع مستشار تعليمي الآن'),
            'cta_call': t('Call us', 'اتصل بنا'),
        },
        'modes_short': modes_short,

        'video': {
            'title': t('Discover Al Omran Center', 'تعرّف على مركز العمران'),
            'subtitle': t('See the training atmosphere and learning experience at Al Omran',
                          'شاهد أجواء التدريب وتجربة التعلم في مركز العمران'),
            'play': t('Play video', 'تشغيل الفيديو'),
            'unmute': t('Turn sound on', 'تشغيل الصوت'),
            'mute': t('Mute', 'كتم الصوت'),
        },

        'why': {
            'title': t('Why Al Omran?', 'لماذا مركز العمران؟'),
            'items': [
                {'icon': 'fa-user-graduate', 'title': t(f'{TRAINEES} trainees', f'{TRAINEES} متدرب'),
                 'text': t(f'More than {trainees_num} trainees have benefited from Al Omran training programs.',
                           f'أكثر من {trainees_num} متدرب استفادوا من برامج مركز العمران التدريبية.'),
                 'extra': ''},
                {'icon': 'fa-building', 'title': t(f'{BRANCHES} branches in the UAE', f'{BRANCHES} فرعًا في الإمارات'),
                 'text': t('Choose the branch nearest to you and benefit from in-person training.',
                           'اختر الفرع الأقرب إليك واستفد من التدريب الحضوري.'),
                 'extra': ''},
                {'icon': 'fa-shuffle', 'title': t('3 ways to train', '3 طرق للتدريب'),
                 'text': t('Choose the option that fits your time and needs:',
                           'اختر الطريقة التي تناسب وقتك واحتياجاتك:'),
                 'extra': t("At the branch | Online | At the student's home",
                            'في الفرع | أونلاين | في منزل الطالب')},
                {'icon': 'fa-layer-group', 'title': t('Diverse programs', 'برامج متنوعة'),
                 'text': t('Programs for the English language and preparation for the most important '
                           'standardized tests.',
                           'برامج للغة الإنجليزية والتحضير لأهم الاختبارات القياسية.'),
                 'extra': ''},
                {'icon': 'fa-bullseye', 'title': t('Training focused on your goal', 'تدريب يركز على هدفك'),
                 'text': t('We help you choose the right program based on your level, goal and needs.',
                           'نساعدك على اختيار البرنامج المناسب بناءً على مستواك وهدفك واحتياجاتك.'),
                 'extra': ''},
            ],
        },

        'programs': {
            'title': t('Choose your program', 'اختر برنامجك'),
            'items': programs,
            'more': t('Learn more', 'اعرف المزيد'),
            'whatsapp': t('Ask on WhatsApp', 'اسأل عبر واتساب'),
        },

        'match': {
            'title': t('Which program suits you?', 'أي برنامج يناسبك؟'),
            'question': t("Don't know where to start?", 'لا تعرف من أين تبدأ؟'),
            'answer': t('No problem.', 'لا مشكلة.'),
            'text': t('The Al Omran team helps you choose the right program based on:',
                      'يساعدك فريق مركز العمران في اختيار البرنامج المناسب بناءً على:'),
            'factors': [t('Your current level', 'مستواك الحالي'), t('Your goal', 'هدفك'),
                        t('Your needs', 'احتياجاتك'), t('Preferred training method', 'طريقة التدريب المفضلة')],
            'tell': t('Tell us about your goal', 'أخبرنا عن هدفك'),
            'cta': t('Talk to an education advisor on WhatsApp', 'تحدث مع مستشار تعليمي عبر واتساب'),
        },

        'modes': {
            'title': t('Choose the learning method that suits you', 'اختر طريقة التعلم المناسبة لك'),
            'items': [
                {'key': 'branch', 'icon': 'fa-location-dot', 'title': t('Training at our branches', 'التدريب في الفروع'),
                 'text': t(f'Benefit from in-person training at one of Al Omran\'s {BRANCHES} branches in the UAE.',
                           f'استفد من التدريب الحضوري في أحد فروع مركز العمران الـ {BRANCHES} في دولة الإمارات.'),
                 'cta': t('View branches', 'شاهد الفروع'), 'href': '/branches'},
                {'key': 'online', 'icon': 'fa-laptop', 'title': t('Online training', 'التدريب أونلاين'),
                 'text': t('Learn from anywhere with online programs that suit students, employees and '
                           'anyone looking for flexibility.',
                           'تعلم من أي مكان مع برامج تدريبية أونلاين تناسب الطلاب والموظفين ومن يبحثون عن المرونة.'),
                 'cta': t('Request online training', 'اطلب التدريب أونلاين'), 'href': ''},
                {'key': 'home', 'icon': 'fa-house', 'title': t("Training at the student's home", 'التدريب في منزل الطالب'),
                 'text': t('For those who prefer privacy and comfort, we offer training at the student\'s home.',
                           'لمن يفضل الخصوصية والراحة، نوفر خيار التدريب في منزل الطالب.'),
                 'cta': t('Request home training', 'اطلب التدريب المنزلي'), 'href': ''},
            ],
        },

        'testimonials': {
            'title': t('Experiences of Al Omran trainees', 'تجارب متدربي مركز العمران'),
            'subtitle': t(f'More than {trainees_num} trainees… and here are some of their experiences',
                          f'أكثر من {trainees_num} متدرب… وهذه بعض تجاربهم'),
            'reviews_title': t('Trainee reviews', 'آراء المتدربين'),
            'more': t('See more trainee experiences', 'شاهد المزيد من تجارب المتدربين'),
        },

        'gallery': {
            'title': t('Life inside Al Omran', 'الحياة داخل مركز العمران'),
        },

        'faq': {
            'title': t('Frequently asked questions', 'أسئلة شائعة'),
            'items': [
                {'q': t('Which program is right for me?', 'أي برنامج يناسبني؟'),
                 'a': t('Our education advisor helps you choose based on your current level, your goal, your needs '
                        'and your preferred training method. Fill in the consultation form or message us on WhatsApp.',
                        'يساعدك مستشارنا التعليمي في الاختيار بناءً على مستواك الحالي وهدفك واحتياجاتك وطريقة '
                        'التدريب المفضلة لديك. املأ نموذج الاستشارة أو راسلنا عبر واتساب.')},
                {'q': t('What training methods are available?', 'ما طرق التدريب المتاحة؟'),
                 'a': t("You can train at one of our branches, online, or at the student's home.",
                        'يمكنك التدريب في أحد فروعنا، أو أونلاين، أو في منزل الطالب.')},
                {'q': t('Where are your branches?', 'أين تقع فروعكم؟'),
                 'a': t(f'We have {BRANCHES} branches across the UAE. You can see all locations on the branches page.',
                        f'لدينا {BRANCHES} فرعًا في دولة الإمارات، ويمكنك الاطلاع على جميع المواقع في صفحة الفروع.')},
                {'q': t('Can I train online from anywhere?', 'هل يمكنني التدريب أونلاين من أي مكان؟'),
                 'a': t('Yes, our online programs let you learn from anywhere with flexible options.',
                        'نعم، برامجنا الأونلاين تتيح لك التعلم من أي مكان بمرونة.')},
                {'q': t('How do I get schedule and fee details?', 'كيف أعرف المواعيد والرسوم؟'),
                 'a': t('Send your request and our team will contact you with all the details.',
                        'أرسل طلبك وسيتواصل معك فريقنا لتزويدك بكل التفاصيل.')},
            ],
        },

        'ready': {
            'title': t('Ready to start?', 'هل أنت مستعد للبدء؟'),
            'subtitle': t('Choose the program that fits your goal and start your journey with Al Omran',
                          'اختر البرنامج المناسب لهدفك وابدأ رحلتك مع مركز العمران'),
            'goal_intro': t('Whether your goal is:', 'سواء كان هدفك:'),
            'goals': [t('Improving your English', 'تطوير اللغة الإنجليزية'), 'IELTS', 'TOEFL', 'SAT', 'ALCPT'],
            'team': t('Our team is ready to help you.', 'فريقنا جاهز لمساعدتك.'),
            'cta': t('Talk to an education advisor on WhatsApp', 'تحدث مع مستشار تعليمي عبر واتساب'),
        },

        'form': {
            'title': t('Get an education consultation', 'احصل على استشارة تعليمية'),
            'subtitle': t("Tell us what you need and we'll contact you", 'أخبرنا عن احتياجك وسنتواصل معك'),
            'name': t('Name', 'الاسم'),
            'name_ph': t('Your full name', 'اسمك الكامل'),
            'phone': t('Phone / WhatsApp number', 'رقم الهاتف / واتساب'),
            'phone_ph': '05XXXXXXXX',
            'branch': t('Branch', 'الفرع'),
            'program_q': t('Which program are you looking for?', 'ما البرنامج الذي تبحث عنه؟'),
            'mode_q': t('Preferred training method:', 'طريقة التدريب المفضلة:'),
            'submit': t('Send request', 'أرسل الطلب'),
            'sending': t('Sending…', 'جاري الإرسال…'),
            'consent': t('By sending this request, you agree that our team may contact you by phone or WhatsApp '
                         'about your request.',
                         'بإرسال الطلب، توافق على تواصل فريقنا معك عبر الهاتف أو واتساب بخصوص طلبك.'),
            'success_title': t('Your request has been sent successfully!', 'تم إرسال طلبك بنجاح!'),
            'success_text': t('Thank you. An education advisor will contact you soon.',
                              'شكرًا لك، سيتواصل معك مستشار تعليمي قريبًا.'),
            'success_wa': t('Or talk to us now on WhatsApp', 'أو تحدث معنا الآن عبر واتساب'),
            'err_name': t('Please enter your name', 'الرجاء إدخال اسمك'),
            'err_phone': t('Please enter a valid phone number', 'الرجاء إدخال رقم هاتف صحيح'),
            'err_branch': t('Please select a branch', 'الرجاء اختيار الفرع'),
            'err_program': t('Please choose a program', 'الرجاء اختيار البرنامج'),
            'err_mode': t('Please choose a training method', 'الرجاء اختيار طريقة التدريب'),
            'err_network': t('Connection error, please try again or message us on WhatsApp',
                             'حدث خطأ في الاتصال، حاول مرة أخرى أو راسلنا عبر واتساب'),
            'selected': t('Selected program:', 'البرنامج المختار:'),
        },
        'program_options': [
            ('english', t('English Language', 'اللغة الإنجليزية')),
            ('ielts', 'IELTS'),
            ('toefl', 'TOEFL'),
            ('sat', 'SAT'),
            ('alcpt', 'ALCPT'),
            ('unsure', t("I don't know and need a consultation", 'لا أعرف وأحتاج إلى استشارة')),
        ],
        'mode_options': [
            ('branch', t('At the branch', 'في الفرع')),
            ('online', t('Online', 'أونلاين')),
            ('home', t("At the student's home", 'في منزل الطالب')),
        ],

        'direct': {
            'title': t('Or contact us directly', 'أو تواصل معنا مباشرة'),
            'text': t('Talk to an education advisor on WhatsApp', 'تحدث مع مستشار تعليمي عبر واتساب'),
            'cta': t('Talk to us now', 'تحدث معنا الآن'),
        },

        'closing': {
            'name': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
            'stats': t(f'{TRAINEES} trainees | {BRANCHES} branches in the UAE',
                       f'{TRAINEES} متدرب | {BRANCHES} فرعًا في الإمارات'),
            'programs_line': 'English Language | IELTS | TOEFL | SAT | ALCPT',
            'modes_line': t("At the branch | Online | At the student's home",
                            'في الفرع | أونلاين | في منزل الطالب'),
            'cta': t('Start your journey now', 'ابدأ رحلتك الآن'),
        },

        'sticky': {
            'whatsapp': t('WhatsApp', 'واتساب'),
            'form': t('Free consultation', 'استشارة مجانية'),
        },

        # رسائل واتساب الجاهزة
        'wa_general': t('Hello, I would like to ask about English and test preparation programs at Al Omran.',
                        'مرحباً، أود الاستفسار عن برامج اللغة الإنجليزية والاختبارات القياسية في مركز العمران.'),
        'wa_program': t('Hello, I would like to ask about the {program} program at Al Omran.',
                        'مرحباً، أود الاستفسار عن برنامج {program} في مركز العمران.'),

        # تسميات وصف الـ lead
        'lead_labels': {
            'program': t('Program', 'البرنامج'),
            'branch': t('Branch', 'الفرع'),
            'mode': t('Training method', 'طريقة التدريب'),
            'source': t('Source', 'المصدر'),
            'source_value': t('English & Tests landing page', 'صفحة اللغة الإنجليزية والاختبارات'),
            'campaign': t('Campaign', 'الحملة'),
            'click_id': t('Ad click ID', 'معرف النقرة الإعلانية'),
        },
    }