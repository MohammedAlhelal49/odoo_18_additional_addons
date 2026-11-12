# -*- coding: utf-8 -*-
"""
محتوى صفحة الدورات المهنية والإبداعية للسيدات (/women-courses)
=============================================================
نفس فكرة صفحة الدروس الخصوصية: كل النصوص بالعربي والإنجليزي هون،
والـ template بنيوي بس. النصوص العربية بصيغة المؤنث (الصفحة موجهة للسيدات).

القيم الثابتة (keys) هي اللي بتنبعت من الفورم وبتنفحص بالسيرفر — لا تغيرها
بدون ما تعدل الـ Selection fields على crm.lead.

ملاحظة: الملف ما بيستورد أي ملف محتوى تاني (منعاً للـ circular import).
"""

# نفس أرقام التواصل بصفحة تواصل معنا وباقي صفحات الهبوط
PHONE_NUMBER = '+971505829697'
PHONE_DISPLAY = '+971 50 582 9697'
ORG_ID = 'https://alomrantd.com/#organization'

# رقم الواتساب الافتراضي (ممكن يتغير من System Parameter: alomran.women_whatsapp)
WHATSAPP_NUMBER = '971505829697'

# ------------------------------------------------------------------
# الدورات — key: اسم الدورة بالـ CRM (x_course_interest) منشان التقارير
# ------------------------------------------------------------------
COURSE_CRM_NAMES = {
    'fashion': 'Fashion Design',
    'makeup': 'Makeup',
    'jewelry': 'Jewelry Design',
    'crochet': 'Crochet',
    'drawing': 'Drawing',
    'unsure': 'Needs Consultation',
}
COURSE_KEYS = tuple(COURSE_CRM_NAMES)
# الدورات اللي إلها بطاقة (كل شي ما عدا "لا أعرف")
CARD_COURSE_KEYS = ('fashion', 'makeup', 'jewelry', 'crochet', 'drawing')

MODE_KEYS = ('branch', 'online', 'home')

# ------------------------------------------------------------------
# صور الصفحة — static/src/img/women/
# الموديول فيه رسومات SVG جاهزة لكل صورة. إذا حطيت صورة حقيقية بنفس الاسم
# (webp أو jpg) بتاخد الأولوية لحالها بدون أي تعديل بالكود.
#   الدورات: 800×520     الهيرو: 900×700     الفورم: 700×800
# الهيرو: إذا في فيديو (alomran.women_hero_video_url أو video/women_hero.mp4)
# بيظهر الفيديو، وإلا الصورة.
# ------------------------------------------------------------------
_IMG = 'alomran_theme/static/src/img/women/'
IMAGE_FILES = {
    key: (f'{_IMG}{key}.webp', f'{_IMG}{key}.jpg', f'{_IMG}{key}.svg')
    for key in CARD_COURSE_KEYS + ('hero', 'form', 'quote')
}

# ------------------------------------------------------------------
# آراء الطالبات — بتنعبى لما يبعتهم العميل (آراء حقيقية بس).
# إذا القائمة فاضية، القسم ما بيظهر بالصفحة.
#
# TESTIMONIALS = [
#     {'name': 'نورة', 'name_en': 'Noura', 'course': 'crochet',
#      'text_ar': '...', 'text_en': '...',
#      'photo': '/alomran_theme/static/src/img/women/t1.webp'},   # photo اختياري
# ]
# ------------------------------------------------------------------
TESTIMONIALS = []


def get_content(is_en):
    """كل نصوص الصفحة باللغة الحالية."""
    def t(en, ar):
        return en if is_en else ar

    courses = [
        {
            'key': 'fashion',
            'color': 'rose',
            'short': t('Learn the basics of fashion design and create your own designs.', 'تعلّمي أساسيات تصميم الأزياء وابتكري تصاميمكِ الخاصة.'),
            'icon': 'fa-shirt',
            'title': t('Fashion design course', 'دورة تصميم الأزياء'),
            'lead': t('Turn your passion for fashion into a creative skill.',
                      'حوّلي شغفكِ بالأزياء إلى مهارة إبداعية.'),
            'points': [t('Basics of clothing design', 'أساسيات تصميم الملابس'),
                       t('Color coordination', 'تنسيق الألوان'),
                       t('Sketching ideas', 'رسم الأفكار'),
                       t('Turning ideas into distinctive designs', 'تحويل الأفكار إلى تصاميم مميزة')],
            'alt': t('Fashion design course at Al Omran', 'دورة تصميم الأزياء في مركز العمران'),
        },
        {
            'key': 'makeup',
            'color': 'blush',
            'short': t('Learn makeup techniques and how to highlight beauty professionally.', 'تعلّمي تقنيات المكياج وإبراز الجمال بأساليب احترافية.'),
            'icon': 'fa-wand-magic-sparkles',
            'title': t('Makeup course', 'دورة المكياج'),
            'lead': t('Highlight the beauty of features with professional techniques.',
                      'أبرزي جمال الملامح بأساليب احترافية.'),
            'points': [t('Makeup basics and application techniques', 'أساسيات المكياج وتقنيات تطبيقه'),
                       t('Choosing the right tools', 'التعرف على الأدوات المناسبة'),
                       t('Color coordination', 'تنسيق الألوان'),
                       t('Highlighting facial features', 'إبراز جمال الملامح')],
            'alt': t('Makeup course at Al Omran', 'دورة المكياج في مركز العمران'),
        },
        {
            'key': 'jewelry',
            'color': 'gold',
            'short': t('Discover the world of designing jewelry and accessories.', 'اكتشفي عالم تصميم المجوهرات والإكسسوارات.'),
            'icon': 'fa-gem',
            'title': t('Jewelry design course', 'دورة تصميم المجوهرات'),
            'lead': t('Discover the world of jewelry and accessory design.',
                      'اكتشفي عالم تصميم المجوهرات والإكسسوارات.'),
            'points': [t('Developing creative ideas', 'تطوير الأفكار الإبداعية'),
                       t('Sketching designs', 'رسم التصاميم'),
                       t('Principles of harmony and shapes', 'مبادئ التناسق والأشكال')],
            'alt': t('Jewelry design course at Al Omran', 'دورة تصميم المجوهرات في مركز العمران'),
        },
        {
            'key': 'crochet',
            'color': 'sage',
            'short': t('Turn yarn into beautiful handmade pieces.', 'حوّلي الخيوط إلى قطع يدوية جميلة.'),
            'icon': 'fa-mitten',
            'title': t('Crochet art course', 'دورة فن الكروشيه'),
            'lead': t('From the basics to making beautiful handmade pieces.',
                      'من الأساسيات إلى تنفيذ قطع يدوية جميلة.'),
            'points': [t('Stitches and techniques', 'الغرز والتقنيات'),
                       t('Making handmade pieces', 'تنفيذ قطع يدوية'),
                       t('Creating your own designs', 'ابتكار تصاميمكِ الخاصة')],
            'alt': t('Crochet course at Al Omran', 'دورة الكروشيه في مركز العمران'),
        },
        {
            'key': 'drawing',
            'color': 'lilac',
            'short': t('Develop your drawing and coloring skills and your own style.', 'طوّري مهارات الرسم والتلوين وأسلوبكِ الفني.'),
            'icon': 'fa-palette',
            'title': t('Drawing course', 'دورة الرسم'),
            'lead': t('Unleash your creativity and develop your own artistic style.',
                      'أطلقي العنان لإبداعكِ وطوّري أسلوبكِ الفني.'),
            'points': [t('Drawing and coloring skills', 'مهارات الرسم والتلوين'),
                       t('Artistic expression', 'التعبير الفني'),
                       t('Techniques and tools', 'التقنيات والأدوات')],
            'alt': t('Drawing course at Al Omran', 'دورة الرسم في مركز العمران'),
        },
    ]

    return {
        'org_name': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
        'page_title': t("Professional & Creative Courses for Women in the UAE | Al Omran",
                        'دورات مهنية وإبداعية للسيدات في الإمارات | مركز العمران'),
        'page_description': t(
            'Fashion design, makeup, jewelry design, crochet and drawing courses for women at '
            'Al Omran Training Center in the UAE. Contact us on WhatsApp.',
            'دورات تصميم الأزياء والمكياج وتصميم المجوهرات والكروشيه والرسم للسيدات في مركز العمران '
            'للتدريب والتطوير بالإمارات. تواصلي معنا عبر واتساب.'),

        'hero': {
            'kicker': t('Professional & creative courses for women', 'دورات مهنية وإبداعية للسيدات'),
            'h1': t('Discover your talent, and build your future', 'اكتشفي موهبتكِ، وابني مستقبلكِ'),
            'subtitle': t('Professional and creative courses for women from Al Omran Training and Development Center',
                          'دورات مهنية وإبداعية للسيدات من مركز العمران للتدريب والتطوير'),
            'question': t('Would you like to learn a new skill, develop your talent, or gain creative skills '
                          'that open new horizons for you?',
                          'هل ترغبين في تعلم مهارة جديدة، أو تطوير موهبتكِ، أو اكتساب مهارات إبداعية تفتح '
                          'أمامكِ آفاقاً جديدة؟'),
            'intro': t('Al Omran Training and Development Center offers a variety of professional and creative '
                       'courses for women in fashion, beauty, arts and handicrafts, within a learning experience '
                       'that helps you discover your abilities and develop your skills.',
                       'يقدم مركز العمران للتدريب والتطوير مجموعة متنوعة من الدورات المهنية والإبداعية للسيدات، '
                       'في مجالات الأزياء والجمال والفنون والحرف اليدوية، ضمن تجربة تعليمية تساعدكِ على '
                       'اكتشاف قدراتكِ وتطوير مهاراتكِ.'),
            'start': t('Start your journey today, and choose the course that suits your passion.',
                       'ابدئي رحلتكِ اليوم، واختاري الدورة التي تناسب شغفكِ.'),
            'cta_whatsapp': t('Contact us on WhatsApp', 'تواصلي معنا عبر واتساب'),
            'cta_call': t('Call us', 'اتصلي بنا'),
            'image_alt': t('Woman designing fashion sketches', 'سيدة ترسم تصاميم أزياء'),
            'modes': [
                {'icon': 'fa-location-dot', 'title': t('At our branches', 'في فروعنا'),
                 'text': t('across the UAE', 'في الإمارات')},
                {'icon': 'fa-laptop', 'title': t('Online', 'أونلاين'),
                 'text': t('remote learning', 'عن بُعد')},
                {'icon': 'fa-layer-group', 'title': t('Diverse courses', 'دورات متنوعة'),
                 'text': t('fashion, beauty & arts', 'أزياء وجمال وفنون')},
            ],
        },

        'video': {
            'unmute': t('Turn sound on', 'تشغيل الصوت'),
            'mute': t('Mute', 'كتم الصوت'),
        },

        'courses': {
            'title': t('Discover our professional courses', 'اكتشفي دوراتنا المهنية'),
            'subtitle': t('Fashion, beauty, arts and handicrafts', 'الأزياء والجمال والفنون والحرف اليدوية'),
            'items': courses,
            'more': t('Ask about the course', 'استفسري عن الدورة'),
            'whatsapp': t('Ask on WhatsApp', 'اسألي عبر واتساب'),
            'details': t('Course details', 'تفاصيل الدورة'),
            'quote': t('Because you deserve to invest in yourself', 'لأنكِ تستحقين الاستثمار في ذاتكِ'),
        },

        'testimonials': {
            'title': t('What our students say', 'ماذا تقول طالباتنا؟'),
        },

        'why': {
            'title': t('Why choose Al Omran courses?', 'لماذا تختارين دورات العمران؟'),
            'items': [
                {'icon': 'fa-layer-group', 'title': t('Diverse courses', 'دورات متنوعة'),
                 'text': t('Diverse courses in creative and professional fields.',
                           'دورات متنوعة في مجالات إبداعية ومهنية.')},
                {'icon': 'fa-lightbulb', 'title': t('Discover your talent', 'اكتشاف المواهب'),
                 'text': t('An opportunity to discover talents and develop skills.',
                           'فرصة لاكتشاف المواهب وتطوير المهارات.')},
                {'icon': 'fa-paintbrush', 'title': t('Creative environment', 'بيئة مشجعة'),
                 'text': t('A learning environment that encourages creativity and practice.',
                           'بيئة تعليمية مشجعة على الإبداع والتطبيق.')},
                {'icon': 'fa-calendar-check', 'title': t('Clear details', 'تفاصيل واضحة'),
                 'text': t('You can ask about schedules, fees and the training method.',
                           'إمكانية الاستفسار عن المواعيد والرسوم وطريقة التدريب.')},
                {'icon': 'fa-handshake-angle', 'title': t('A team that helps you', 'فريق يساعدكِ'),
                 'text': t('A team that helps you choose the course that suits your interests.',
                           'فريق يساعدكِ على اختيار الدورة المناسبة لاهتماماتكِ.')},
            ],
        },

        'steps': {
            'title': t('Your journey starts in four steps', 'رحلتكِ تبدأ بأربع خطوات'),
            'items': [
                {'icon': 'fa-hand-pointer', 'title': t('Choose', 'اختاري'),
                 'text': t('Choose the course that interests you.', 'اختاري الدورة التي تثير اهتمامكِ.')},
                {'icon': 'fa-comment-dots', 'title': t('Contact us', 'تواصلي معنا'),
                 'text': t('Contact us to learn the details.', 'تواصلي معنا لمعرفة التفاصيل.')},
                {'icon': 'fa-calendar-days', 'title': t('Learn the details', 'تعرّفي على التفاصيل'),
                 'text': t('Learn about the schedules, fees and requirements.',
                           'تعرّفي على المواعيد والرسوم والمتطلبات.')},
                {'icon': 'fa-star', 'title': t('Start', 'ابدئي'),
                 'text': t('Start your journey of learning and creativity.',
                           'ابدئي رحلتكِ في التعلم والإبداع.')},
            ],
        },

        'form': {
            'title': t('Which course suits your passion?', 'أي دورة تناسب شغفكِ؟'),
            'subtitle': t('Fill in your details or contact us on WhatsApp, and the Al Omran team will help you '
                          'learn about the available courses.',
                          'املئي بياناتكِ أو تواصلي معنا عبر واتساب، وسيساعدكِ فريق مركز العمران في التعرف '
                          'على الدورات المتاحة.'),
            'card_title': t('Register your interest', 'سجّلي اهتمامكِ بالدورات'),
            'image_note': t('Your future starts here', 'مستقبلكِ يبدأ من هنا'),
            'image_alt': t('Coffee mug on a stack of books', 'كوب قهوة على مجموعة كتب'),
            'name': t('Full name', 'الاسم الكامل'),
            'name_ph': t('Your full name', 'اسمكِ الكامل'),
            'phone': t('Phone / WhatsApp number', 'رقم الهاتف أو واتساب'),
            'phone_ph': '05XXXXXXXX',
            'branch': t('Nearest branch', 'الفرع الأقرب'),
            'course_q': t('Course you would like to join', 'الدورة التي ترغبين في الالتحاق بها'),
            'course_ph': t('Select the course', 'اختاري الدورة'),
            'mode_q': t('Preferred training method', 'طريقة التدريب المفضلة'),
            'mode_ph': t('Select the method', 'اختاري الطريقة'),
            'notes': t('Any additional questions', 'أي استفسارات إضافية'),
            'notes_ph': t('Write your question here (optional)', 'اكتبي استفساركِ هنا (اختياري)'),
            'submit': t('Send request', 'أرسلي الطلب'),
            'sending': t('Sending…', 'جاري الإرسال…'),
            'or': t('or', 'أو'),
            'wa_cta': t('Ask about the courses on WhatsApp', 'استفسري عن الدورات عبر واتساب'),
            'consent': t('By sending this request, you agree that our team may contact you by phone or WhatsApp '
                         'about your request.',
                         'بإرسال الطلب، توافقين على تواصل فريقنا معكِ عبر الهاتف أو واتساب بخصوص طلبكِ.'),
            'success_title': t('Your request has been sent successfully!', 'تم إرسال طلبكِ بنجاح!'),
            'success_text': t('Thank you. The Al Omran team will contact you soon.',
                              'شكرًا لكِ، سيتواصل معكِ فريق مركز العمران قريبًا.'),
            'success_wa': t('Or talk to us now on WhatsApp', 'أو تحدثي معنا الآن عبر واتساب'),
            'err_name': t('Please enter your name', 'الرجاء إدخال اسمكِ'),
            'err_phone': t('Please enter a valid phone number', 'الرجاء إدخال رقم هاتف صحيح'),
            'err_branch': t('Please select a branch', 'الرجاء اختيار الفرع'),
            'err_course': t('Please choose a course', 'الرجاء اختيار الدورة'),
            'err_mode': t('Please choose a training method', 'الرجاء اختيار طريقة التدريب'),
            'err_network': t('Connection error, please try again or message us on WhatsApp',
                             'حدث خطأ في الاتصال، حاولي مرة أخرى أو راسلينا عبر واتساب'),
        },
        'course_options': [
            ('fashion', t('Fashion design', 'تصميم الأزياء')),
            ('makeup', t('Makeup', 'المكياج')),
            ('jewelry', t('Jewelry design', 'تصميم المجوهرات')),
            ('crochet', t('Crochet', 'الكروشيه')),
            ('drawing', t('Drawing', 'الرسم')),
            ('unsure', t("I'm not sure and need a consultation", 'لست متأكدة وأحتاج إلى استشارة')),
        ],
        'mode_options': [
            ('branch', t('At the branch', 'في الفرع')),
            ('online', t('Online', 'أونلاين')),
            ('home', t('At home (subject to availability)', 'في المنزل (حسب التوفر)')),
        ],

        'ready': {
            'title': t('Start today — every new skill is a new opportunity',
                       'ابدئي اليوم، فكل مهارة جديدة هي فرصة جديدة'),
            'text': t('Whether your passion is fashion, makeup, jewelry, crochet or drawing, the first step '
                      'starts with choosing the skill you love.',
                      'سواء كان شغفكِ بالأزياء أو المكياج أو المجوهرات أو الكروشيه أو الرسم، فإن الخطوة '
                      'الأولى تبدأ باختيار المهارة التي تحبينها.'),
            'name': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
            'slogan': t('Together toward a better future.', 'معاً نحو مستقبل أفضل.'),
            'cta': t('Contact us now', 'تواصلي معنا الآن'),
        },

        'sticky': {
            'whatsapp': t('WhatsApp', 'واتساب'),
            'form': t('Ask about courses', 'استفسري الآن'),
        },

        # رسائل واتساب الجاهزة
        'wa_general': t('Hello, I would like to ask about the women\'s professional and creative courses at Al Omran.',
                        'مرحباً، أود الاستفسار عن الدورات المهنية والإبداعية للسيدات في مركز العمران.'),
        'wa_course': t('Hello, I would like to ask about the "{course}" course at Al Omran.',
                       'مرحباً، أود الاستفسار عن دورة "{course}" في مركز العمران.'),
        # رسالة "استفسري عن الدورات" — نفس البيانات المطلوبة جاهزة للتعبئة
        'wa_details': t('Hello, I would like to ask about the women\'s courses at Al Omran.\n'
                        'Full name: \n'
                        'Emirate and area: \n'
                        'Course: \n'
                        'Preferred training method: \n'
                        'Questions: ',
                        'مرحباً، أود الاستفسار عن دورات السيدات في مركز العمران.\n'
                        'الاسم الكامل: \n'
                        'الإمارة والمنطقة: \n'
                        'الدورة: \n'
                        'طريقة التدريب المفضلة: \n'
                        'الاستفسار: '),

        # تسميات وصف الـ lead
        'lead_labels': {
            'course': t('Course', 'الدورة'),
            'branch': t('Branch', 'الفرع'),
            'mode': t('Training method', 'طريقة التدريب'),
            'notes': t('Questions', 'الاستفسار'),
            'source': t('Source', 'المصدر'),
            'source_value': t("Women's courses landing page", 'صفحة دورات السيدات'),
            'campaign': t('Campaign', 'الحملة'),
            'click_id': t('Ad click ID', 'معرف النقرة الإعلانية'),
        },
    }
