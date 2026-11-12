# -*- coding: utf-8 -*-
"""
محتوى الصفحة الرئيسية (/)
=========================
نفس فكرة ملفات محتوى صفحات الهبوط: كل النصوص بالعربي والإنجليزي هون،
والـ template (views/pages/home.xml) بنيوي بس — بدون terms بـ ar.po.

ملاحظة: الملف ما بيستورد أي ملف محتوى تاني (منعاً للـ circular import).
"""
from datetime import date

from .site_facts import BRANCHES

FOUNDED_YEAR = 2010

# ------------------------------------------------------------------
# أرقام المركز — عدّلها من هون بس
# ------------------------------------------------------------------
TRAINEES = '50K+'
TRAINERS = '250+'
PROGRAMS = '1750+'
GOV_ENTITIES = '25'

WHATSAPP_NUMBER = '971505829697'
PHONE_NUMBER = '+971505829697'
PHONE_DISPLAY = '+971 50 582 9697'

# صور اختيارية (أول ملف موجود بينعرض) — بدونها التصميم بيضل كامل
IMAGE_FILES = {
    # صورة المركز (خلفية الهيرو بالرئيسية والفروع): webp أخف، وإلا jpg
    'hero': ('alomran_theme/static/src/img/hero-bg.webp',
             'alomran_theme/static/src/img/hero-bg.jpg'),
    'logo': ('alomran_theme/static/src/img/Logo_Mockup_3.png',),
}


def years_count():
    return max(date.today().year - FOUNDED_YEAR, 1)


def years_of_experience():
    return f'{years_count()}+'


def get_content(is_en):
    """كل نصوص الصفحة الرئيسية باللغة الحالية."""
    def t(en, ar):
        return en if is_en else ar

    years = years_of_experience()
    years_num = years_count()

    return {
        'hero': {
            'badge': t(f'Certified training center since {FOUNDED_YEAR}',
                       f'مركز تدريب معتمد منذ عام {FOUNDED_YEAR}'),
            'title_1': t('Al Omran', 'مركز العمران'),
            'title_2': t('Training & Development Center', 'للتدريب والتطوير'),
            'lead': t(f'We shape tomorrow\'s leaders through advanced training programs, accredited certificates '
                      f'and more than {years_num} years of professional training experience across the UAE.',
                      f'نصنع قادة الغد من خلال برامج تدريبية متطورة وشهادات معتمدة وخبرة تدريبية تزيد عن '
                      f'{years_num} عامًا في دولة الإمارات.'),
            'cta_primary': t('Explore our programs', 'اكتشف برامجنا'),
            'cta_whatsapp': t('Talk to us on WhatsApp', 'تواصل معنا عبر واتساب'),
            'trust': [
                {'icon': 'fa-shield-halved', 'text': t('Accredited by official UAE authorities',
                                                       'معتمد من الجهات الرسمية في الدولة')},
                {'icon': 'fa-location-dot', 'text': t(f'{BRANCHES} branches across the UAE',
                                                      f'{BRANCHES} فرعًا في الإمارات')},
                {'icon': 'fa-laptop', 'text': t('At the branch, online or at home',
                                                'في الفرع أو أونلاين أو في المنزل')},
            ],
            'float_1': {'value': TRAINEES, 'label': t('successful trainees', 'متدرب ناجح')},
            'float_2': {'value': PROGRAMS, 'label': t('training programs', 'برنامج تدريبي')},
            'image_alt': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
        },
        'video': {
            'unmute': t('Turn sound on', 'تشغيل الصوت'),
            'mute': t('Mute', 'كتم الصوت'),
        },

        'stats': [
            {'icon': 'fa-calendar-check', 'value': years, 'label': t('years of experience', 'سنة خبرة')},
            {'icon': 'fa-user-graduate', 'value': TRAINEES, 'label': t('successful trainees', 'متدرب ناجح')},
            {'icon': 'fa-chalkboard-user', 'value': TRAINERS, 'label': t('certified trainers', 'مدرب معتمد')},
            {'icon': 'fa-building-columns', 'value': GOV_ENTITIES, 'label': t('government entities trained',
                                                                              'جهة حكومية دربناها')},
            {'icon': 'fa-location-dot', 'value': str(BRANCHES), 'label': t('branches in the UAE', 'فرعًا في الإمارات')},
        ],

        'programs': {
            'eyebrow': t('Most requested', 'الأكثر طلبًا'),
            'title': t('Our distinguished training programs', 'برامجنا التدريبية المتميزة'),
            'subtitle': t('Programs designed around your level, your goal and the way you like to learn',
                          'برامج مصممة لتناسب مستواك وهدفك وطريقة التعلم التي تفضّلها'),
            'items': [
                {
                    'key': 'english', 'icon': 'fa-language', 'link': '/english-ielts',
                    'badge': t('New', 'جديد'),
                    'title': t('English & Standardized Tests', 'اللغة الإنجليزية والاختبارات القياسية'),
                    'text': t('Improve your English and prepare for IELTS, TOEFL, SAT and ALCPT.',
                              'طوّر لغتك الإنجليزية واستعد لاختبارات IELTS وTOEFL وSAT وALCPT.'),
                    'tags': ['IELTS', 'TOEFL', 'SAT', 'ALCPT'],
                    'cta': t('Explore programs', 'اكتشف البرامج'),
                },
                {
                    'key': 'tutoring', 'icon': 'fa-chalkboard-user', 'link': '/private-tutoring',
                    'badge': t('Academic support', 'دعم أكاديمي'),
                    'title': t('Private Tutoring & School Follow-up', 'الدروس الخصوصية والمتابعة الدراسية'),
                    'text': t('Private lessons, school follow-up and university academic support across the UAE.',
                              'دروس خصوصية، متابعة مدرسية، ودعم أكاديمي جامعي في جميع الإمارات.'),
                    'tags': [t('School', 'مدرسي'), t('University', 'جامعي'), t('Online', 'أونلاين')],
                    'cta': t('Explore services', 'اكتشف الخدمات'),
                },
                {
                    'key': 'women', 'icon': 'fa-palette', 'link': '/women-courses',
                    'badge': t('For women', 'للسيدات'),
                    'title': t('Professional & Creative Courses for Women', 'الدورات المهنية والإبداعية للسيدات'),
                    'text': t('Fashion design, makeup, jewelry design, crochet and drawing.',
                              'تصميم الأزياء، المكياج، تصميم المجوهرات، الكروشيه والرسم.'),
                    'tags': [t('Fashion', 'أزياء'), t('Makeup', 'مكياج'), t('Arts', 'فنون')],
                    'cta': t('Explore courses', 'اكتشفي الدورات'),
                },
            ],
            'all': t(f'View all programs ({PROGRAMS} programs)', f'عرض جميع البرامج ({PROGRAMS} برنامج)'),
        },

        'why': {
            'eyebrow': t('Why Al Omran', 'لماذا العمران'),
            'title': t('Why choose Al Omran Center?', 'لماذا تختار مركز العمران؟'),
            'subtitle': t('At Al Omran Center, we offer you:', 'في مركز العمران نقدّم لك:'),
            'items': [
                {'icon': 'fa-user-tie', 'title': t('Specialized trainers', 'مدربون متخصصون'),
                 'text': t('Highly qualified specialized trainers.', 'مدربون متخصصون بكفاءة عالية.')},
                {'icon': 'fa-certificate', 'title': t('Accredited certificates', 'شهادات معتمدة'),
                 'text': t('Locally and internationally accredited certificates.', 'شهادات معتمدة محليًا ودوليًا.')},
                {'icon': 'fa-network-wired', 'title': t('Widest network', 'أوسع شبكة فروع'),
                 'text': t('One of the largest center networks in the country.', 'من أكبر شبكات المراكز في الدولة.')},
                {'icon': 'fa-language', 'title': t('Courses in all languages', 'دورات بكل اللغات'),
                 'text': t('We offer courses in world languages.', 'نقدّم دورات في لغات العالم.')},
                {'icon': 'fa-briefcase', 'title': t('Professional courses', 'دورات مهنية'),
                 'text': t('Specialized professional and creative courses.', 'دورات مهنية وإبداعية متخصصة.')},
                {'icon': 'fa-shuffle', 'title': t('Learn your way', 'تعلّم بطريقتك'),
                 'text': t('At the branch, online or at home.', 'في الفرع أو أونلاين أو في المنزل.')},
            ],
            'seal': t('Center accredited by official UAE authorities', 'مركز معتمد من الجهات الرسمية في دولة الإمارات'),
            'logo_alt': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير - مركز تعليمي في العين'),
        },

        'branches': {
            'eyebrow': t('Our branches', 'فروعنا'),
            'title': t('We are close to you across the UAE', 'قريبون منك في جميع أنحاء الإمارات'),
            'subtitle': t(f'{BRANCHES} branches equipped with the latest technologies',
                          f'{BRANCHES} فرعًا مجهزة بأحدث التقنيات'),
            # بطاقات الإمارات بالرئيسية — الاسم لازم يطابق 'city' بـ _get_branches_data
            'cities': [
                {'icon': 'fa-city', 'city': t('Dubai', 'دبي')},
                {'icon': 'fa-building-columns', 'city': t('Abu Dhabi', 'أبوظبي')},
                {'icon': 'fa-tree-city', 'city': t('Al Ain', 'العين')},
            ],
            'city_title': t('Our branches in {city}', 'فروعنا في {city}'),
            'city_cta': t('View {city} branches', 'عرض فروع {city}'),
            'all': t('View all branches & directions', 'عرض جميع الفروع والاتجاهات'),
        },

        'cta': {
            'title': t('Ready to start your training journey?', 'هل أنت جاهز لبدء رحلتك التدريبية؟'),
            'text': t('Join thousands of successful trainees and unleash your potential.',
                      'انضم إلى آلاف المتدربين الناجحين وأطلق إمكاناتك.'),
            'contact': t('Contact us', 'تواصل معنا'),
            'whatsapp': t('WhatsApp', 'واتساب'),
        },
        'wa_general': t('Hello, I would like to ask about the training programs at Al Omran.',
                        'مرحباً، أود الاستفسار عن البرامج التدريبية في مركز العمران.'),
    }