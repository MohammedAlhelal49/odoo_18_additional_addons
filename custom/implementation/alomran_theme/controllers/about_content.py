# -*- coding: utf-8 -*-
"""
محتوى صفحة "من نحن" (/about) — عربي وإنجليزي بمكان واحد.
النصوص العربية نفسها اللي كانت بـ ar.po (مع تصحيح أخطاء إملائية بسيطة).
الأرقام من home_content / site_facts منشان تضل نفسها بكل الموقع.
"""
from .site_facts import BRANCHES
from . import home_content


def get_content(is_en):
    def t(en, ar):
        return en if is_en else ar

    years = home_content.years_of_experience()

    return {
        'page_title': t('About Al Omran Training and Development Center | Since 2010',
                        'من نحن | مركز العمران للتدريب والتطوير منذ 2010'),
        'page_description': t(
            'Al Omran Training and Development Center: a leading accredited training center in the UAE since 2010, '
            f'with {BRANCHES} branches, certified trainers and programs in languages, technology and professional skills.',
            'مركز العمران للتدريب والتطوير: مركز تدريب معتمد ورائد في الإمارات منذ 2010، '
            f'بـ {BRANCHES} فرعًا ومدربين معتمدين وبرامج في اللغات والتقنية والمهارات المهنية.'),

        'hero': {
            'badge': t('Certified training center since 2010', 'مركز تدريب معتمد منذ 2010'),
            'eyebrow': t('About us', 'من نحن'),
            'title_1': t('Al Omran', 'مركز العمران'),
            'title_2': t('Training & Development Center', 'للتدريب والتطوير'),
            'lead': t("Shaping tomorrow's leaders through excellence in training",
                      'نصنع قادة الغد من خلال التميز في التدريب'),
        },

        'stats': [
            {'icon': 'fa-calendar-check', 'value': years, 'label': t('years of experience', 'سنة خبرة')},
            {'icon': 'fa-user-graduate', 'value': '50,000+', 'label': t('trainees', 'متدرب')},
            {'icon': 'fa-chalkboard-user', 'value': home_content.TRAINERS, 'label': t('certified trainers', 'مدرب معتمد')},
            {'icon': 'fa-building-columns', 'value': home_content.GOV_ENTITIES,
             'label': t('government entities', 'جهة حكومية')},
            {'icon': 'fa-location-dot', 'value': str(BRANCHES), 'label': t('branches in the UAE', 'فرعًا في الإمارات')},
        ],

        'story': {
            'eyebrow': t('Our story', 'قصتنا'),
            'title': t('Who we are', 'من نحن'),
            'subtitle': t("Leaders in shaping tomorrow's leaders", 'رواد في صناعة قادة الغد'),
            'p1': t('Al Omran Training and Development Center is one of the leading centers in the United Arab Emirates '
                    'in providing specialized and diverse training programs. The center aims to develop human '
                    'competencies through high-quality professional courses in management, technology, languages, '
                    'human development, and professional courses.',
                    'مركز العمران للتدريب والتطوير هو أحد المراكز الرائدة في دولة الإمارات العربية المتحدة في تقديم '
                    'برامج تدريبية متخصصة ومتنوعة. يهدف المركز إلى تطوير الكفاءات البشرية من خلال دورات مهنية عالية '
                    'الجودة في الإدارة والتقنية واللغات والتنمية البشرية والدورات المهنية.'),
            'p2': t('The center is distinguished by an experienced training team, locally and internationally recognized '
                    'programs, and a modern educational environment that supports practical and theoretical development, '
                    'making it an ideal choice for individuals, government entities, and companies seeking excellence '
                    'and sustainable growth.',
                    'يتميز المركز بفريق تدريبي ذي خبرة، وبرامج معترف بها محلياً ودولياً، وبيئة تعليمية حديثة تدعم '
                    'التطوير العملي والنظري، مما يجعله الخيار الأمثل للأفراد والجهات الحكومية والشركات التي تبحث عن '
                    'التميز والنمو المستدام.'),
            'points': [
                t('Experienced training team', 'فريق تدريبي ذو خبرة'),
                t('Locally and internationally recognized programs', 'برامج معترف بها محلياً ودولياً'),
                t('Modern learning environment', 'بيئة تعليمية حديثة'),
                t('For individuals, government entities and companies', 'للأفراد والجهات الحكومية والشركات'),
            ],
            'years_label': t('years of experience', 'سنة من الخبرة'),
            'image_alt': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
        },
        'years': years,

        'vm': {
            'eyebrow': t('Vision & mission', 'الرؤية والرسالة'),
            'title': t('Towards a better future', 'نحو مستقبل أفضل'),
            'subtitle': t('The foundation upon which we build our success', 'الأساس الذي نبني عليه نجاحنا'),
            'items': [
                {'key': 'vision', 'icon': 'fa-eye', 'tag': t('Vision', 'الرؤية'), 'title': t('Our vision', 'رؤيتنا'),
                 'text': t('At Al Omran Training and Development Center, we aspire to be a beacon of excellence in '
                           'developing human competencies in the UAE, through innovative and accredited training '
                           'programs that meet the needs of individuals and institutions, contributing to building a '
                           'knowledge-based society capable of meeting future challenges.',
                           'في مركز العمران للتدريب والتطوير، نطمح بأن نكون منارة للتميز في تطوير الكفاءات البشرية في '
                           'الإمارات، من خلال برامج تدريبية مبتكرة ومعتمدة تلبي احتياجات الأفراد والمؤسسات، وتساهم في '
                           'بناء مجتمع معرفي قادر على مواجهة التحديات المستقبلية.')},
                {'key': 'mission', 'icon': 'fa-bullseye', 'tag': t('Mission', 'الرسالة'), 'title': t('Our mission', 'رسالتنا'),
                 'text': t('At Al Omran Training and Development Center, we are committed to providing high-quality '
                           'training solutions that meet the aspirations of individuals, government and private '
                           'entities, through elite certified experts and trainers, using the latest educational methods '
                           "and techniques, enhancing trainees' competencies and helping achieve their professional "
                           'and developmental goals.',
                           'في مركز العمران للتدريب والتطوير، نلتزم بتقديم حلول تدريبية عالية الجودة تلبي تطلعات الأفراد '
                           'والجهات الحكومية والخاصة، من خلال نخبة من الخبراء والمدربين المعتمدين، باستخدام أحدث '
                           'الأساليب والتقنيات التعليمية، وتعزيز كفاءات المتدربين والمساعدة في تحقيق أهدافهم المهنية '
                           'والتنموية.')},
            ],
        },

        'goals': {
            'eyebrow': t('Our goal', 'هدفنا'),
            'title': t('Our strategic goals', 'أهدافنا الاستراتيجية'),
            'subtitle': t('The path to excellence and leadership', 'الطريق إلى التميز والقيادة'),
            'intro': t('Al Omran Training and Development Center aims to enable individuals and institutions to achieve '
                       'their full potential, through comprehensive training programs that contribute to skill '
                       'development, efficiency enhancement, and strengthening competitive ability in the local and '
                       'regional job market.',
                       'يهدف مركز العمران للتدريب والتطوير إلى تمكين الأفراد والمؤسسات من تحقيق أقصى إمكاناتهم، من '
                       'خلال برامج تدريبية شاملة تساهم في تطوير المهارات وتعزيز الكفاءة، وتقوية القدرة التنافسية في '
                       'سوق العمل المحلي والإقليمي.'),
            'items': [
                {'icon': 'fa-arrow-trend-up', 'title': t('Continuous development', 'التطوير المستمر'),
                 'text': t('Advanced programs meeting market requirements', 'برامج متقدمة تلبي متطلبات السوق')},
                {'icon': 'fa-medal', 'title': t('High quality', 'جودة عالية'),
                 'text': t('International training standards', 'معايير تدريب دولية')},
                {'icon': 'fa-user-tie', 'title': t('Professional empowerment', 'التمكين المهني'),
                 'text': t('Building competencies capable of competition', 'بناء كفاءات قادرة على المنافسة')},
                {'icon': 'fa-lightbulb', 'title': t('Innovation & development', 'الابتكار والتطوير'),
                 'text': t('Using the latest educational technologies', 'استخدام أحدث التقنيات التعليمية')},
            ],
        },

        'values': {
            'eyebrow': t('Our values', 'قيمنا'),
            'title': t('The values that guide our work', 'القيم التي توجه عملنا'),
            'subtitle': t('Principles we commit to at every step', 'المبادئ التي نلتزم بها في كل خطوة'),
            'items': [
                {'icon': 'fa-shield-halved', 'title': t('Quality & excellence', 'الجودة والتميز'),
                 'text': t('We are committed to the highest quality standards in all our training programs and services',
                           'نحن ملتزمون بأعلى معايير الجودة في جميع برامجنا التدريبية وخدماتنا')},
                {'icon': 'fa-seedling', 'title': t('Continuous development', 'التطوير المستمر'),
                 'text': t('We believe in continuous learning and development to achieve growth and innovation',
                           'نؤمن بالتعلم والتطوير المستمر لتحقيق النمو والابتكار')},
                {'icon': 'fa-users', 'title': t('Teamwork', 'العمل الجماعي'),
                 'text': t("We work as one team to achieve our shared goals and our trainees' success",
                           'نعمل كفريق واحد لتحقيق أهدافنا المشتركة ونجاح متدربينا')},
                {'icon': 'fa-handshake', 'title': t('Integrity & transparency', 'النزاهة والشفافية'),
                 'text': t('We operate with complete transparency and commit to the highest professional integrity standards',
                           'نعمل بشفافية كاملة ونلتزم بأعلى معايير النزاهة المهنية')},
            ],
        },

        'cta': {
            'title': t('Start your journey with us today', 'ابدأ رحلتك معنا اليوم'),
            'text': t('Join thousands of successful trainees who chose Al Omran Center to achieve their professional dreams',
                      'انضم إلى آلاف المتدربين الناجحين الذين اختاروا مركز العمران لتحقيق أحلامهم المهنية'),
            'courses': t('Explore courses', 'استكشف الدورات'),
            'contact': t('Contact us', 'تواصل معنا'),
        },
    }