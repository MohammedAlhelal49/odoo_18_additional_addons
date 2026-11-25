# -*- coding: utf-8 -*-
"""
كل نصوص الموقع (إنجليزي + عربي) بمكان واحد.

كل نص مكتوب بالشكل t('English', 'عربي')، فتعديل أي جملة بالموقع بيصير من هون
بدون ما نلمس القوالب. معلومات التواصل بـ COMPANY.
"""

IMG = '/alomran_engineering_website/static/src/img/'

COMPANY = {
    'logo_white': IMG + 'logo-white.png',
    'logo_color': IMG + 'logo-color.jpg',
    'phone': '+971 54 444 1047',
    'phone_href': 'tel:+971544441047',
    'whatsapp': 'https://wa.me/971544441047',
    'email': 'info@alomran-int.ae',
    'instagram': 'https://www.instagram.com/alomran.ae/',
    'map_embed': 'https://www.google.com/maps?q=Al+Dar+Street,+Central+District,+Al+Ain,+UAE&output=embed',
    'map_link': 'https://www.google.com/maps/search/?api=1&query=Al+Dar+Street+Central+District+Al+Ain',
}

# الخدمات — المفتاح (slug) بيستخدم كـ anchor بصفحة الخدمات وبفورم التواصل
SERVICE_KEYS = [
    'architecture', 'structural', 'mep', 'approvals', 'supervision',
    'interior', 'landscape', 'sustainability', 'extensions',
]


def translator(is_en):
    def t(en, ar):
        return en if is_en else ar
    return t


def common(is_en):
    """نصوص مشتركة: الهيدر، الفوتر، الأزرار، بيانات الشركة."""
    t = translator(is_en)
    return {
        'brand': t('Al Omran', 'العمران'),
        'brand_sub': t('International Engineering Consultants', 'الدولية للاستشارات الهندسية'),
        'nav': [
            ('home', '/', t('Home', 'الرئيسية')),
            ('about', '/about', t('About', 'من نحن')),
            ('services', '/services', t('Services', 'خدماتنا')),
            ('projects', '/projects', t('Projects', 'مشاريعنا')),
            ('contact', '/contact', t('Contact', 'تواصل معنا')),
        ],
        'cta': t('Book a consultation', 'احجز استشارة'),
        'call': t('Call us', 'اتصل بنا'),
        'whatsapp_label': t('Chat on WhatsApp', 'تواصل عبر واتساب'),
        'lang_switch': t('العربية', 'English'),
        'address': t('Al Dar Street 14/1, Central District, Al Ain, UAE',
                     'شارع الدار 14/1، المنطقة الوسطى، العين، الإمارات'),
        'address_short': t('Al Ain, Abu Dhabi — UAE', 'العين، أبوظبي — الإمارات'),
        'hours_title': t('Working hours', 'ساعات العمل'),
        'hours': [
            t('Saturday – Thursday', 'السبت – الخميس'),
            t('10:00 AM – 2:00 PM', '10:00 صباحًا – 2:00 ظهرًا'),
            t('4:00 PM – 8:00 PM', '4:00 عصرًا – 8:00 مساءً'),
        ],
        'footer_about': t(
            'A UAE engineering consultancy delivering architecture, engineering, interiors and '
            'landscape — from the first sketch to the completion certificate.',
            'مكتب استشارات هندسية في الإمارات يقدّم التصميم المعماري والهندسي والداخلي وتنسيق المواقع '
            '— من أول فكرة وحتى شهادة الإنجاز.'),
        'footer_links': t('Explore', 'روابط'),
        'footer_services': t('Services', 'الخدمات'),
        'footer_contact': t('Get in touch', 'تواصل معنا'),
        'rights': t('All rights reserved.', 'جميع الحقوق محفوظة.'),
        'company_full': t('Al Omran International Engineering Consultants',
                          'العمران الدولية للاستشارات الهندسية'),
        'read_more': t('Learn more', 'اعرف المزيد'),
        'view_all': t('View all projects', 'عرض جميع المشاريع'),
        'view_project': t('View project', 'تفاصيل المشروع'),
        'menu': t('Menu', 'القائمة'),
        'close': t('Close', 'إغلاق'),
        'back_top': t('Back to top', 'للأعلى'),
    }


def services(is_en):
    t = translator(is_en)
    data = {
        'architecture': {
            'image': IMG + 'architecture.jpg',
            'icon': 'fa-building-o',
            'title': t('Architectural Design', 'التصميم المعماري'),
            'short': t('Villas, residential buildings and commercial projects designed around the way '
                       'UAE families and businesses actually live and work.',
                       'فلل ومبانٍ سكنية ومشاريع تجارية مصممة حول طريقة حياة وعمل الأسر والشركات في الإمارات.'),
            'points': [
                t('Concept design, 3D visualization and walkthroughs', 'التصميم المبدئي والتصور ثلاثي الأبعاد'),
                t('Modern, contemporary-Arabic and classic villa styles', 'فلل بطابع حديث أو عربي معاصر أو كلاسيكي'),
                t('Majlis, privacy and family-zoning focused planning', 'تخطيط يراعي المجلس والخصوصية وتوزيع العائلة'),
                t('Full permit & construction drawing sets', 'مخططات الترخيص والتنفيذ الكاملة'),
            ],
        },
        'structural': {
            'image': IMG + 'structural.jpg',
            'icon': 'fa-cubes',
            'title': t('Structural Engineering', 'التصميم الإنشائي'),
            'short': t('Safe, economical structures engineered to UAE codes and local soil and climate conditions.',
                       'هياكل آمنة واقتصادية مصممة وفق الكودات الإماراتية وظروف التربة والمناخ المحلية.'),
            'points': [
                t('Structural analysis and design (RC & steel)', 'التحليل والتصميم الإنشائي (خرسانة وحديد)'),
                t('Foundation design based on soil investigation', 'تصميم الأساسات بناءً على تقرير التربة'),
                t('Value engineering to optimise construction cost', 'هندسة القيمة لتقليل تكلفة التنفيذ'),
                t('Structural assessment of existing buildings', 'تقييم إنشائي للمباني القائمة'),
            ],
        },
        'mep': {
            'image': IMG + 'mep.jpg',
            'icon': 'fa-bolt',
            'title': t('MEP Engineering', 'الأعمال الكهروميكانيكية (MEP)'),
            'short': t('Mechanical, electrical and plumbing systems designed for comfort and efficiency in the Gulf heat.',
                       'أنظمة تكييف وكهرباء وصحي مصممة للراحة وكفاءة الطاقة في أجواء الخليج الحارة.'),
            'points': [
                t('HVAC load calculation and system design', 'حساب الأحمال وتصميم أنظمة التكييف'),
                t('Electrical, lighting and low-current systems', 'الكهرباء والإنارة والتيار الخفيف'),
                t('Plumbing, drainage and water supply', 'التمديدات الصحية والصرف وتغذية المياه'),
                t('Fire fighting & fire alarm design to Civil Defence requirements',
                  'أنظمة مكافحة وإنذار الحريق وفق اشتراطات الدفاع المدني'),
            ],
        },
        'approvals': {
            'image': IMG + 'floor-plan.jpg',
            'icon': 'fa-check-square-o',
            'title': t('Permits & Authority Approvals', 'التراخيص واعتمادات الجهات'),
            'short': t('We handle the paperwork and follow-up with municipality, Civil Defence and service providers.',
                       'نتولى المعاملات والمتابعة مع البلدية والدفاع المدني ومزودي الخدمات نيابةً عنك.'),
            'points': [
                t('Building permit applications and follow-up', 'استخراج رخص البناء ومتابعتها'),
                t('Civil Defence drawings and approvals', 'مخططات واعتمادات الدفاع المدني'),
                t('Utility NOCs (electricity, water, telecom)', 'شهادات عدم الممانعة من الكهرباء والماء والاتصالات'),
                t('Completion certificates and as-built drawings', 'شهادات الإنجاز ومخططات الواقع الفعلي'),
            ],
        },
        'supervision': {
            'image': IMG + 'project-management.jpg',
            'icon': 'fa-binoculars',
            'title': t('Project Management & Supervision', 'إدارة المشاريع والإشراف'),
            'short': t('Independent site supervision that protects your budget, schedule and quality.',
                       'إشراف هندسي مستقل يحمي ميزانيتك وجدولك الزمني وجودة التنفيذ.'),
            'points': [
                t('Tender documents, BOQ and contractor selection', 'وثائق المناقصة وجداول الكميات واختيار المقاول'),
                t('Regular site visits, inspections and reports', 'زيارات موقع دورية وتقارير فحص'),
                t('Payment certification and variation control', 'اعتماد الدفعات وضبط الأوامر التغييرية'),
                t('Snagging and handover management', 'متابعة الملاحظات النهائية والتسليم'),
            ],
        },
        'interior': {
            'image': IMG + 'model-interior.jpg',
            'icon': 'fa-paint-brush',
            'title': t('Interior Design & Fit-Out', 'التصميم الداخلي والتشطيبات'),
            'short': t('Elegant residential and commercial interiors, delivered turnkey.',
                       'تصاميم داخلية أنيقة للمساكن والمشاريع التجارية مع التنفيذ المتكامل.'),
            'points': [
                t('Residential and commercial interior design', 'تصميم داخلي سكني وتجاري'),
                t('Custom joinery, furniture and material selection', 'نجارة وأثاث مخصص واختيار المواد'),
                t('Smart-home and automation solutions', 'حلول المنزل الذكي والأتمتة'),
                t('Turnkey fit-out and renovation', 'تشطيب وتجديد متكامل تسليم مفتاح'),
            ],
        },
        'landscape': {
            'image': IMG + 'landscape.jpg',
            'icon': 'fa-tree',
            'title': t('Landscape & Urban Design', 'تنسيق المواقع والتخطيط العمراني'),
            'short': t('Outdoor spaces, gardens and master plans that work with the desert climate.',
                       'مساحات خارجية وحدائق ومخططات عامة تتناغم مع المناخ الصحراوي.'),
            'points': [
                t('Master planning and zoning', 'المخططات العامة وتقسيم الأراضي'),
                t('Villa gardens, pools and outdoor majlis', 'حدائق الفلل والمسابح والمجالس الخارجية'),
                t('Public spaces and green areas', 'الساحات العامة والمسطحات الخضراء'),
                t('Water-efficient planting and irrigation', 'زراعة وري موفران للمياه'),
            ],
        },
        'sustainability': {
            'image': IMG + 'green-building.jpg',
            'icon': 'fa-leaf',
            'title': t('Sustainable & Green Buildings', 'المباني المستدامة والخضراء'),
            'short': t('Design that meets Estidama Pearl and Al Sa\'fat requirements and lowers running costs.',
                       'تصاميم تحقق متطلبات استدامة (نظام اللؤلؤ) والسعفات وتخفض تكاليف التشغيل.'),
            'points': [
                t('Estidama Pearl Rating (Abu Dhabi) compliance', 'الامتثال لنظام تقييم اللؤلؤ – استدامة (أبوظبي)'),
                t('Al Sa\'fat green building (Dubai) compliance', 'الامتثال لنظام السعفات للمباني الخضراء (دبي)'),
                t('Thermal insulation and energy-efficiency studies', 'دراسات العزل الحراري وكفاءة الطاقة'),
                t('Solar and water-saving solutions', 'حلول الطاقة الشمسية وترشيد المياه'),
            ],
        },
        'extensions': {
            'image': IMG + 'site-photo.jpg',
            'icon': 'fa-plus-square-o',
            'title': t('Villa Extensions & Renovation', 'إضافات وتوسعات وترميم الفلل'),
            'short': t('Add a majlis, extra rooms or a new floor — designed, approved and supervised end-to-end.',
                       'إضافة مجلس أو غرف أو طابق جديد — تصميم واعتماد وإشراف متكامل.'),
            'points': [
                t('Majlis, annex and room extensions', 'المجالس والملاحق وإضافة الغرف'),
                t('Facade upgrades and modernisation', 'تحديث وتجديد الواجهات'),
                t('Structural checks before adding floors', 'فحص إنشائي قبل إضافة الطوابق'),
                t('Modification permits and approvals', 'تراخيص واعتمادات التعديل والإضافة'),
            ],
        },
    }
    return [dict(data[key], key=key) for key in SERVICE_KEYS]


def process(is_en):
    t = translator(is_en)
    return [
        {'title': t('Consultation', 'الاستشارة'),
         'text': t('We meet you, visit the plot and understand your needs, budget and timeline.',
                   'نلتقي بك ونزور الموقع ونفهم احتياجاتك وميزانيتك وجدولك الزمني.')},
        {'title': t('Concept & 3D', 'الفكرة والتصور ثلاثي الأبعاد'),
         'text': t('Concept layouts and 3D views — refined with you until it feels right.',
                   'مخططات مبدئية ومناظير ثلاثية الأبعاد نطورها معك حتى تصل للتصميم المثالي.')},
        {'title': t('Design & Approvals', 'التصميم والاعتمادات'),
         'text': t('Full architectural, structural and MEP drawings, submitted and followed up with authorities.',
                   'مخططات معمارية وإنشائية وكهروميكانيكية كاملة، نقدّمها ونتابعها مع الجهات المختصة.')},
        {'title': t('Tender & Construction', 'المناقصة والتنفيذ'),
         'text': t('We help you choose the right contractor and supervise the work on site.',
                   'نساعدك في اختيار المقاول المناسب ونشرف على التنفيذ في الموقع.')},
        {'title': t('Handover', 'التسليم'),
         'text': t('Snagging, completion certificate and handover of a building you can be proud of.',
                   'معالجة الملاحظات وشهادة الإنجاز وتسليم مبنى تفخر به.')},
    ]


def home(is_en):
    t = translator(is_en)
    return {
        'title': t('Al Omran International Engineering Consultants | Al Ain, UAE',
                   'العمران الدولية للاستشارات الهندسية | العين، الإمارات'),
        'description': t(
            'Engineering consultancy in Al Ain, UAE: architectural design, structural & MEP engineering, '
            'authority approvals, supervision, interior design and landscape.',
            'مكتب استشارات هندسية في العين – الإمارات: تصميم معماري وإنشائي وكهروميكانيكي، '
            'استخراج التراخيص، الإشراف، التصميم الداخلي وتنسيق المواقع.'),
        'hero': {
            'image': IMG + 'hero-villa.jpg',
            'eyebrow': t('Engineering Consultancy · Al Ain, UAE', 'استشارات هندسية · العين، الإمارات'),
            'title_1': t('Designing the spaces', 'نصمم المساحات'),
            'title_2': t('where the UAE lives,', 'التي تعيش فيها الإمارات'),
            'title_3': t('works & grows.', 'وتعمل وتنمو.'),
            'lead': t(
                'Architecture, engineering, interiors and landscape under one roof — with permits, approvals and '
                'site supervision handled for you, from the first sketch to the completion certificate.',
                'تصميم معماري وهندسي وداخلي وتنسيق مواقع تحت سقف واحد — مع التراخيص والاعتمادات والإشراف '
                'على التنفيذ، من أول رسمة وحتى شهادة الإنجاز.'),
            'cta_primary': t('Book a free consultation', 'احجز استشارة مجانية'),
            'cta_secondary': t('Explore our projects', 'استكشف مشاريعنا'),
            'chips': [
                t('Authority approvals', 'اعتمادات الجهات'),
                t('Estidama-ready design', 'تصاميم متوافقة مع استدامة'),
                t('Site supervision', 'إشراف على التنفيذ'),
            ],
            'card_1_title': t('Permit drawings', 'مخططات الترخيص'),
            'card_1_text': t('Approved & submitted', 'مُعدة ومقدمة للاعتماد'),
            'card_2_title': t('3D visualization', 'تصور ثلاثي الأبعاد'),
            'card_2_text': t('See it before it\'s built', 'شاهده قبل أن يُبنى'),
        },
        'marquee': [
            t('Architecture', 'العمارة'), t('Structural', 'الإنشاءات'), t('MEP', 'الكهروميكانيك'),
            t('Approvals', 'الاعتمادات'), t('Supervision', 'الإشراف'), t('Interiors', 'التصميم الداخلي'),
            t('Landscape', 'تنسيق المواقع'), t('Sustainability', 'الاستدامة'),
        ],
        'intro': {
            'eyebrow': t('Who we are', 'من نحن'),
            'title': t('One consultant. Every discipline. Zero hassle.',
                       'استشاري واحد. كل التخصصات. بدون عناء.'),
            'text': t(
                'Al Omran International Engineering Consultants is an Al Ain-based firm bringing architects, '
                'engineers and interior designers together in one team. We turn your plot and your ideas into '
                'a building that is beautiful, buildable and fully approved — and we stay with you on site '
                'until the keys are in your hand.',
                'العمران الدولية للاستشارات الهندسية مكتب مقره مدينة العين، يجمع المعماريين والمهندسين '
                'ومصممي الديكور في فريق واحد. نحوّل أرضك وأفكارك إلى مبنى جميل وقابل للتنفيذ ومعتمد بالكامل '
                '— ونبقى معك في الموقع حتى تستلم المفتاح.'),
            'image': IMG + 'projects/villa-03.jpg',
            'pillars': [
                {'icon': 'fa-compass', 'title': t('Engineering Consultancy', 'الاستشارات الهندسية'),
                 'text': t('Architecture, structure, MEP, approvals and supervision.',
                           'معماري، إنشائي، كهروميكانيك، اعتمادات وإشراف.')},
                {'icon': 'fa-paint-brush', 'title': t('Interior Design & Fit-Out', 'التصميم الداخلي والتشطيبات'),
                 'text': t('Residential and commercial interiors, delivered turnkey.',
                           'تصاميم داخلية سكنية وتجارية مع تنفيذ متكامل.')},
                {'icon': 'fa-tree', 'title': t('Landscape & Urban Design', 'تنسيق المواقع والتخطيط'),
                 'text': t('Gardens, public spaces and master planning.',
                           'حدائق وساحات عامة ومخططات عمرانية.')},
            ],
        },
        'services': {
            'eyebrow': t('What we do', 'ماذا نقدم'),
            'title': t('Complete engineering services for every stage of your project',
                       'خدمات هندسية متكاملة لكل مرحلة من مراحل مشروعك'),
            'cta': t('All services', 'كل الخدمات'),
        },
        'process': {
            'eyebrow': t('How we work', 'كيف نعمل'),
            'title': t('A clear path from idea to handover', 'طريق واضح من الفكرة إلى التسليم'),
        },
        'projects': {
            'eyebrow': t('Selected work', 'من أعمالنا'),
            'title': t('Projects that speak for us', 'مشاريع تتحدث عنا'),
        },
        'why': {
            'eyebrow': t('Why Al Omran', 'لماذا العمران'),
            'title': t('Built on local know-how, delivered with care',
                       'خبرة محلية وعناية في كل تفصيل'),
            'items': [
                {'icon': 'fa-map-marker', 'title': t('Local expertise', 'خبرة محلية'),
                 'text': t('We know UAE building regulations, authorities and the realities of building here.',
                           'نعرف أنظمة البناء في الإمارات والجهات المختصة وواقع التنفيذ على الأرض.')},
                {'icon': 'fa-sitemap', 'title': t('All disciplines, one team', 'كل التخصصات بفريق واحد'),
                 'text': t('Architecture, structure, MEP and interiors coordinated in-house — fewer clashes, faster approvals.',
                           'تنسيق داخلي بين المعماري والإنشائي والكهروميكانيك والديكور — أخطاء أقل واعتماد أسرع.')},
                {'icon': 'fa-shield', 'title': t('Your interests on site', 'نحمي مصلحتك في الموقع'),
                 'text': t('Independent supervision that keeps contractors on spec, on time and on budget.',
                           'إشراف مستقل يُلزم المقاول بالمواصفات والجدول والميزانية.')},
                {'icon': 'fa-comments', 'title': t('Clear communication', 'تواصل واضح'),
                 'text': t('Arabic and English, regular updates, and an engineer who answers your calls.',
                           'بالعربي والإنجليزي، تحديثات منتظمة، ومهندس يرد على اتصالك.')},
            ],
        },
        'stats': [
            {'value': len(SERVICE_KEYS), 'suffix': '', 'label': t('Specialised services', 'خدمة متخصصة')},
            {'value': 3, 'suffix': '', 'label': t('Design disciplines', 'مجالات تصميم')},
            {'value': 6, 'suffix': '', 'label': t('Days a week for you', 'أيام عمل أسبوعيًا')},
            {'value': 2, 'suffix': '', 'label': t('Languages: Arabic & English', 'لغتان: العربية والإنجليزية')},
        ],
        'approvals': {
            'title': t('We take care of the approvals', 'نتولى عنك الاعتمادات'),
            'items': [
                t('Building permits', 'رخص البناء'),
                t('Civil Defence', 'الدفاع المدني'),
                t('Electricity & water NOCs', 'عدم ممانعة الكهرباء والماء'),
                t('Telecom NOCs', 'عدم ممانعة الاتصالات'),
                t('Completion certificates', 'شهادات الإنجاز'),
                t('Estidama / Al Sa\'fat', 'استدامة / السعفات'),
            ],
        },
    }


def cta(is_en):
    t = translator(is_en)
    return {
        'title': t('Have a plot, a villa or an idea?', 'عندك أرض أو فيلا أو فكرة مشروع؟'),
        'text': t('Tell us about your project — an engineer will call you back within one working day.',
                  'أخبرنا عن مشروعك — وسيتواصل معك أحد مهندسينا خلال يوم عمل واحد.'),
        'button': t('Request a consultation', 'اطلب استشارة'),
    }


def form(is_en):
    t = translator(is_en)
    return {
        'name': t('Full name', 'الاسم الكامل'),
        'phone': t('Mobile number', 'رقم الجوال'),
        'email': t('Email (optional)', 'البريد الإلكتروني (اختياري)'),
        'service': t('Service needed', 'الخدمة المطلوبة'),
        'service_placeholder': t('Choose a service', 'اختر الخدمة'),
        'service_other': t('Other / not sure yet', 'أخرى / لم أحدد بعد'),
        'emirate': t('Emirate', 'الإمارة'),
        'message': t('Tell us about your project', 'حدثنا عن مشروعك'),
        'message_ph': t('Plot location, size, what you would like to build…',
                        'موقع الأرض، المساحة، ماذا تريد أن تبني…'),
        'submit': t('Send request', 'أرسل الطلب'),
        'privacy': t('We only use your details to contact you about your request.',
                     'نستخدم بياناتك فقط للتواصل معك بخصوص طلبك.'),
        'success_title': t('Thank you!', 'شكرًا لك!'),
        'success_text': t('Your request has been received. Our team will contact you shortly.',
                          'تم استلام طلبك، وسيتواصل معك فريقنا قريبًا.'),
        'error': t('Please enter your name and a valid mobile number.',
                   'يرجى إدخال الاسم ورقم جوال صحيح.'),
        'emirates': [
            ('al_ain', t('Al Ain', 'العين')),
            ('abu_dhabi', t('Abu Dhabi', 'أبوظبي')),
            ('dubai', t('Dubai', 'دبي')),
            ('sharjah', t('Sharjah', 'الشارقة')),
            ('ajman', t('Ajman', 'عجمان')),
            ('uaq', t('Umm Al Quwain', 'أم القيوين')),
            ('rak', t('Ras Al Khaimah', 'رأس الخيمة')),
            ('fujairah', t('Fujairah', 'الفجيرة')),
        ],
    }


def about(is_en):
    t = translator(is_en)
    return {
        'title': t('About Us | Al Omran International Engineering Consultants',
                   'من نحن | العمران الدولية للاستشارات الهندسية'),
        'description': t('Meet Al Omran International Engineering Consultants — an Al Ain engineering, '
                         'interior and landscape design firm serving clients across the UAE.',
                         'تعرّف على العمران الدولية للاستشارات الهندسية — مكتب تصميم هندسي وداخلي '
                         'وتنسيق مواقع في العين يخدم العملاء في مختلف إمارات الدولة.'),
        'hero_image': IMG + 'site-photo.jpg',
        'hero_eyebrow': t('About us', 'من نحن'),
        'hero_title': t('Engineering excellence, interior elegance.', 'تميّز هندسي، وأناقة في التفاصيل.'),
        'hero_lead': t('Shaping the future of architecture in the UAE with inspiring designs and complete consulting solutions.',
                       'نساهم في صناعة مستقبل العمارة في الإمارات بتصاميم ملهمة وحلول استشارية متكاملة.'),
        'story_image': IMG + 'engineers.jpg',
        'story_eyebrow': t('Our story', 'قصتنا'),
        'story_title': t('A consultancy built around the client', 'مكتب استشاري يضع العميل أولًا'),
        'story': [
            t('Al Omran International Engineering Consultants was founded in Al Ain with a simple idea: building '
              'your home or business should be exciting, not exhausting. That means one trusted team that designs, '
              'engineers, gets the approvals and watches over the construction for you.',
              'تأسست العمران الدولية للاستشارات الهندسية في مدينة العين بفكرة بسيطة: بناء منزلك أو مشروعك يجب أن '
              'يكون تجربة ممتعة لا مُرهقة. وهذا يعني فريقًا واحدًا موثوقًا يصمم ويهندس ويستخرج الاعتمادات ويشرف على '
              'التنفيذ بالنيابة عنك.'),
            t('Today our architects, engineers and interior designers work on villas, residential buildings, '
              'commercial spaces and landscapes — combining modern design with the culture, climate and '
              'regulations of the UAE.',
              'واليوم يعمل معماريونا ومهندسونا ومصممونا على الفلل والمباني السكنية والمساحات التجارية وتنسيق '
              'المواقع — جامعين بين التصميم العصري وثقافة الإمارات ومناخها وأنظمتها.'),
        ],
        'mission_title': t('Our mission', 'رسالتنا'),
        'mission': t('To deliver inspiring, buildable and sustainable designs, and to guide every client '
                     'confidently from idea to handover.',
                     'تقديم تصاميم ملهمة وقابلة للتنفيذ ومستدامة، ومرافقة كل عميل بثقة من الفكرة حتى التسليم.'),
        'vision_title': t('Our vision', 'رؤيتنا'),
        'vision': t('To be the most trusted engineering consultant for families and businesses in the UAE.',
                    'أن نكون الاستشاري الهندسي الأكثر ثقة لدى الأسر والشركات في الإمارات.'),
        'values_title': t('What we stand for', 'قيمنا'),
        'values': [
            {'icon': 'fa-diamond', 'title': t('Quality', 'الجودة'),
             'text': t('Precise drawings and careful detailing.', 'مخططات دقيقة وتفاصيل مدروسة.')},
            {'icon': 'fa-lightbulb-o', 'title': t('Innovation', 'الابتكار'),
             'text': t('Creative, functional design ideas.', 'أفكار تصميمية مبتكرة وعملية.')},
            {'icon': 'fa-handshake-o', 'title': t('Integrity', 'النزاهة'),
             'text': t('Honest advice and transparent fees.', 'نصيحة صادقة وأتعاب واضحة.')},
            {'icon': 'fa-leaf', 'title': t('Sustainability', 'الاستدامة'),
             'text': t('Efficient buildings that cost less to run.', 'مبانٍ كفؤة بتكاليف تشغيل أقل.')},
        ],
        'team_eyebrow': t('Our team', 'فريقنا'),
        'team_title': t('The people behind your project', 'الفريق وراء مشروعك'),
        'team_text': t('A group of passionate professionals dedicated to innovation, collaboration and excellence.',
                       'مجموعة من المهنيين الشغوفين بالابتكار والعمل الجماعي والتميّز.'),
        'team': [
            {'initials': t('O', 'ع'), 'photo': IMG + 'team/obada.jpg', 'name': t('Eng. Obada', 'م. عبادة'), 'role': t('Founder & Owner', 'المؤسس والمالك')},
            {'initials': t('G', 'غ'), 'photo': IMG + 'team/ghaith.jpg', 'name': t('Eng. Ghaith', 'م. غيث'), 'role': t('Engineer', 'مهندس')},
            {'initials': t('G', 'ج'), 'photo': IMG + 'team/giana.jpg', 'name': t('Eng. Giana', 'م. جيانا'), 'role': t('Engineer', 'مهندسة')},
            {'initials': t('H', 'ح'), 'photo': IMG + 'team/hussein.jpg', 'name': t('Eng. Hussein', 'م. حسين'), 'role': t('Engineer', 'مهندس')},
        ],
    }


def services_page(is_en):
    t = translator(is_en)
    return {
        'title': t('Engineering Services in the UAE | Al Omran Engineering Consultants',
                   'خدمات هندسية في الإمارات | العمران للاستشارات الهندسية'),
        'description': t('Architectural design, structural and MEP engineering, building permits, supervision, '
                         'interior design, landscape and villa extensions across the UAE.',
                         'تصميم معماري وإنشائي وكهروميكانيكي، رخص البناء، الإشراف، التصميم الداخلي، '
                         'تنسيق المواقع وإضافات الفلل في الإمارات.'),
        'hero_image': IMG + 'structural.jpg',
        'hero_eyebrow': t('Our services', 'خدماتنا'),
        'hero_title': t('Everything your project needs, under one roof', 'كل ما يحتاجه مشروعك تحت سقف واحد'),
        'hero_lead': t('From feasibility and design to approvals and supervision — choose a single service or let us handle it all.',
                       'من الدراسة والتصميم إلى الاعتمادات والإشراف — اختر خدمة واحدة أو دعنا نتولى كل شيء.'),
        'faq_title': t('Frequently asked questions', 'أسئلة شائعة'),
        'faq': [
            {'q': t('Do you work outside Al Ain?', 'هل تعملون خارج مدينة العين؟'),
             'a': t('Yes. Our office is in Al Ain and we take on projects across the UAE. Contact us with your plot location.',
                    'نعم، مكتبنا في العين ونستقبل المشاريع في مختلف إمارات الدولة. تواصل معنا وأخبرنا بموقع أرضك.')},
            {'q': t('Can you handle the building permit for me?', 'هل يمكنكم استخراج رخصة البناء بالنيابة عني؟'),
             'a': t('Yes. We prepare the drawings, submit them to the relevant authorities and follow up on comments until approval.',
                    'نعم، نُعد المخططات ونقدمها للجهات المختصة ونتابع الملاحظات حتى الاعتماد.')},
            {'q': t('How long does villa design take?', 'كم يستغرق تصميم الفيلا؟'),
             'a': t('It depends on the size and how quickly decisions are made. We agree a clear schedule with you at the start.',
                    'يعتمد ذلك على حجم المشروع وسرعة اتخاذ القرارات، ونتفق معك على جدول زمني واضح منذ البداية.')},
            {'q': t('Can I hire you only for supervision?', 'هل يمكنني التعاقد معكم على الإشراف فقط؟'),
             'a': t('Yes. We provide independent supervision even when the design was done by another office, subject to a review of the drawings.',
                    'نعم، نقدم إشرافًا مستقلًا حتى لو كان التصميم من مكتب آخر، بعد مراجعة المخططات.')},
            {'q': t('How are your fees calculated?', 'كيف يتم احتساب الأتعاب؟'),
             'a': t('Fees depend on the scope and size of the project. After the first meeting we send you a clear written proposal.',
                    'تعتمد الأتعاب على نطاق العمل وحجم المشروع، وبعد الاجتماع الأول نرسل لك عرضًا مكتوبًا وواضحًا.')},
        ],
    }


def projects_page(is_en):
    t = translator(is_en)
    return {
        'title': t('Our Projects | Al Omran Engineering Consultants', 'مشاريعنا | العمران للاستشارات الهندسية'),
        'description': t('Explore villas, residential, commercial, interior and landscape projects by Al Omran.',
                         'استكشف مشاريع العمران من فلل ومبانٍ سكنية وتجارية وتصاميم داخلية وتنسيق مواقع.'),
        'hero_image': IMG + 'hero-villa.jpg',
        'hero_eyebrow': t('Portfolio', 'معرض الأعمال'),
        'hero_title': t('Our latest projects', 'أحدث مشاريعنا'),
        'hero_lead': t('From luxurious villas to high-end commercial spaces — each project reflects our commitment '
                       'to quality, innovation and functionality.',
                       'من الفلل الفاخرة إلى المساحات التجارية الراقية — كل مشروع يعكس التزامنا بالجودة والابتكار والعملية.'),
        'all': t('All', 'الكل'),
        'empty': t('Projects will be published here soon.', 'سيتم نشر المشاريع هنا قريبًا.'),
        'location': t('Location', 'الموقع'),
        'year': t('Year', 'السنة'),
        'area': t('Built-up area', 'مساحة البناء'),
        'scope': t('Scope', 'نطاق العمل'),
        'category': t('Category', 'التصنيف'),
        'back': t('Back to projects', 'العودة إلى المشاريع'),
        'more': t('More projects', 'مشاريع أخرى'),
        'categories': {
            'villa': t('Villas', 'فلل'),
            'residential': t('Residential', 'سكني'),
            'commercial': t('Commercial', 'تجاري'),
            'interior': t('Interior', 'تصميم داخلي'),
            'landscape': t('Landscape', 'تنسيق مواقع'),
            'public': t('Public', 'مباني عامة'),
        },
    }


def contact_page(is_en):
    t = translator(is_en)
    return {
        'title': t('Contact Us | Al Omran Engineering Consultants', 'تواصل معنا | العمران للاستشارات الهندسية'),
        'description': t('Book a consultation with Al Omran International Engineering Consultants in Al Ain, UAE.',
                         'احجز استشارة مع العمران الدولية للاستشارات الهندسية في العين، الإمارات.'),
        'hero_image': IMG + 'engineers.jpg',
        'hero_eyebrow': t('Contact us', 'تواصل معنا'),
        'hero_title': t('Let\'s talk about your project', 'لنتحدث عن مشروعك'),
        'hero_lead': t('Visit our office in Al Ain, call us, message us on WhatsApp or send the form — '
                       'we reply within one working day.',
                       'زرنا في مكتبنا بالعين، أو اتصل بنا، أو راسلنا عبر واتساب، أو أرسل النموذج — '
                       'نرد خلال يوم عمل واحد.'),
        'visit': t('Visit us', 'زورونا'),
        'call': t('Call us', 'اتصل بنا'),
        'email': t('Email us', 'راسلنا'),
        'form_title': t('Request a consultation', 'اطلب استشارة'),
        'directions': t('Get directions', 'احصل على الاتجاهات'),
    }
