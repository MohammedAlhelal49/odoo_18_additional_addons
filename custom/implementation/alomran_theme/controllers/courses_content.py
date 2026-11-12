# -*- coding: utf-8 -*-
"""
محتوى صفحة الدورات (/courses) — عربي وإنجليزي بمكان واحد.
- FEATURED: صفحات الهبوط (بطاقات كبيرة فوق)
- COURSES: باقي المجالات. 'link' = صفحة خاصة، أو بدونه = زر "سجل الآن" بيفتح فورم التسجيل
- 'cat' لازم يكون من CATEGORIES (فلتر الصفحة)
الأسماء العربية/الإنجليزية نفس اللي كانت بالكونترولر و ar.po.
"""
from . import home_content


def get_content(is_en):
    def t(en, ar):
        return en if is_en else ar

    categories = [
        ('education', t('Education', 'تعليم وتدريب')),
        ('languages', t('Languages', 'لغات')),
        ('tech', t('Technology', 'تقنية')),
        ('business', t('Business', 'أعمال وإدارة')),
        ('creative', t('Creative & professional', 'مهني وإبداعي')),
    ]

    courses = [
        {'cat': 'education', 'icon': 'fa-graduation-cap', 'link': '/teachers',
         'title': t('Professional Teacher Training', 'تأهيل المعلمين المحترف'),
         'text': t('Specialized programs for developing educational competencies and modern pedagogical skills',
                   'برامج متخصصة لتطوير الكفاءات التعليمية والمهارات التربوية الحديثة')},
        {'cat': 'languages', 'icon': 'fa-earth-americas', 'link': '/languages',
         'title': t('Language Learning', 'تعلم اللغات'),
         'text': t('Courses in French, Spanish, Italian, Chinese, Turkish and more',
                   'دورات في الفرنسية والإسبانية والإيطالية والصينية والتركية وغيرها')},
        {'cat': 'tech', 'icon': 'fa-laptop-code', 'link': '/it-programs',
         'title': t('Information Technology', 'تقنية المعلومات'),
         'text': t('Programming, graphic design, cybersecurity, and data science',
                   'البرمجة والتصميم الجرافيكي والأمن السيبراني وعلوم البيانات')},
        {'cat': 'creative', 'icon': 'fa-scissors',
         'title': t('Fashion & Design', 'الأزياء والتصميم'),
         'text': t('Fashion design, abaya and dress design, with professional cutting and sewing courses',
                   'تعلم تصميم الأزياء وتصميم العبايات والفساتين، مع دورات قص وخياطة احترافية')},
        {'cat': 'creative', 'icon': 'fa-spa',
         'title': t('Skincare', 'العناية بالبشرة'),
         'text': t('Specialized courses in skincare and natural beauty',
                   'دورات متخصصة في العناية بالبشرة والجمال الطبيعي')},
        {'cat': 'business', 'icon': 'fa-scale-balanced',
         'title': t('Law', 'القانون'),
         'text': t('Qualifying courses in law and legal procedures',
                   'دورات تأهيلية في القانون والإجراءات القانونية')},
        {'cat': 'business', 'icon': 'fa-file-lines',
         'title': t('Secretarial', 'السكرتارية'),
         'text': t('Office management, executive secretarial, and communication skills',
                   'إدارة المكاتب والسكرتارية التنفيذية ومهارات التواصل')},
        {'cat': 'business', 'icon': 'fa-calculator',
         'title': t('Accounting', 'المحاسبة'),
         'text': t('Financial accounting, management accounting, and banking sciences',
                   'المحاسبة المالية والإدارية والعلوم المصرفية')},
        {'cat': 'business', 'icon': 'fa-bullhorn',
         'title': t('Marketing', 'التسويق'),
         'text': t('Digital marketing, brand management, and social media',
                   'التسويق الرقمي وإدارة العلامات التجارية ووسائل التواصل الاجتماعي')},
        {'cat': 'business', 'icon': 'fa-users-gear',
         'title': t('Human Resources', 'الموارد البشرية'),
         'text': t('HR management, recruitment, and career development',
                   'إدارة الموارد البشرية والتوظيف والتطوير المهني')},
        {'cat': 'creative', 'icon': 'fa-video',
         'title': t('Media & Editing', 'الإعلام والمونتاج'),
         'text': t('Content production, video editing, and filmmaking',
                   'إنتاج المحتوى وتحرير الفيديو وصناعة الأفلام')},
        {'cat': 'business', 'icon': 'fa-briefcase',
         'title': t('Business Administration', 'إدارة الأعمال'),
         'text': t('Leadership skills, project management, and decision making',
                   'مهارات القيادة وإدارة المشاريع واتخاذ القرارات')},
    ]
    cat_labels = dict(categories)
    for c in courses:
        c['cat_label'] = cat_labels[c['cat']]
    counts = {}
    for c in courses:
        counts[c['cat']] = counts.get(c['cat'], 0) + 1

    return {
        'page_title': t('Training Courses in the UAE: English, IELTS, IT & Business | Al Omran',
                        'الدورات التدريبية في الإمارات: إنجليزي، IELTS، تقنية معلومات وإدارة | مركز العمران'),
        'page_description': t(
            'Browse Al Omran training courses: English and IELTS/TOEFL preparation, private tutoring, women\'s '
            'courses, teacher training, IT, accounting, marketing, HR and more across the UAE.',
            'تصفح دورات مركز العمران: اللغة الإنجليزية وتحضير IELTS وTOEFL، الدروس الخصوصية، دورات السيدات، '
            'تأهيل المعلمين، تقنية المعلومات، المحاسبة، التسويق، الموارد البشرية وغيرها في الإمارات.'),

        'hero': {
            'badge': t(f'{home_content.PROGRAMS} training programs available',
                       f'{home_content.PROGRAMS} برنامج تدريبي متاح'),
            'title_1': t('Training', 'الدورات'),
            'title_2': t('Courses', 'التدريبية'),
            'lead': t('Develop your skills with our accredited training programs and certified trainers',
                      'طوّر مهاراتك مع برامجنا التدريبية المعتمدة ومدربينا المعتمدين'),
            'trust': [
                {'icon': 'fa-certificate', 'text': t('Accredited certificates', 'شهادات معتمدة')},
                {'icon': 'fa-chalkboard-user', 'text': t(f'{home_content.TRAINERS} expert trainers',
                                                         f'{home_content.TRAINERS} مدرب خبير')},
                {'icon': 'fa-user-graduate', 'text': t('50,000+ graduates', '50,000+ خريج')},
            ],
        },

        'featured': {
            'eyebrow': t('Featured programs', 'برامج مميزة'),
            'title': t('Start with our most requested programs', 'ابدأ مع برامجنا الأكثر طلبًا'),
            'items': home_content.get_content(is_en)['programs']['items'],
        },

        'list': {
            'eyebrow': t('All courses', 'جميع الدورات'),
            'title': t('Choose your training field', 'اختر مجالك التدريبي'),
            'subtitle': t('Comprehensive training programs with accredited certificates',
                          'برامج تدريبية شاملة مع شهادات معتمدة'),
            'search_ph': t('Search for a course…', 'ابحث عن دورة…'),
            'all': t('All', 'الكل'),
            'more': t('View details', 'عرض التفاصيل'),
            'register': t('Register now', 'سجّل الآن'),
            'empty': t('No course matches your search.', 'لا توجد دورة تطابق بحثك.'),
        },
        'categories': [{'key': k, 'label': v, 'count': counts.get(k, 0)} for k, v in categories],
        'courses': courses,

        'features': {
            'eyebrow': t('Course features', 'مميزات دوراتنا'),
            'title': t('Why choose our courses?', 'لماذا تختار دوراتنا؟'),
            'items': [
                {'icon': 'fa-chalkboard-user', 'title': t('Professional trainers', 'مدربون محترفون'),
                 'text': t('Internationally certified experts', 'خبراء معتمدون دولياً')},
                {'icon': 'fa-certificate', 'title': t('Accredited certificates', 'شهادات معتمدة'),
                 'text': t('Recognized locally and internationally', 'معترف بها محلياً ودولياً')},
                {'icon': 'fa-laptop', 'title': t('Practical application', 'تطبيق عملي'),
                 'text': t('Training on real cases', 'تدريب على حالات حقيقية')},
                {'icon': 'fa-headset', 'title': t('Continuous support', 'دعم مستمر'),
                 'text': t('Follow-up after graduation', 'متابعة بعد التخرج')},
            ],
        },

        'cta': {
            'title': t("Didn't find what you're looking for?", 'لم تجد الدورة التي تبحث عنها؟'),
            'text': t('Contact us and our team will help you find the right program.',
                      'تواصل معنا وسيساعدك فريقنا في إيجاد البرنامج المناسب.'),
            'contact': t('Contact us', 'تواصل معنا'),
            'whatsapp': t('WhatsApp', 'واتساب'),
        },
        'wa_message': t('Hello, I would like to ask about the training courses at Al Omran.',
                        'مرحباً، أود الاستفسار عن الدورات التدريبية في مركز العمران.'),

        'modal': {
            'title': t('Course registration', 'تسجيل الدورة'),
            'note': t('For pricing and schedule details, our team will contact you',
                      'للحصول على تفاصيل الأسعار والمواعيد، سيتواصل معك فريقنا'),
            'name': t('Full name', 'الاسم الكامل'),
            'name_ph': t('Enter your full name', 'أدخل اسمك الكامل'),
            'phone': t('Phone number', 'رقم الهاتف'),
            'email': t('Email (optional)', 'البريد الإلكتروني (اختياري)'),
            'submit': t('Submit request', 'أرسل الطلب'),
            'sending': t('Sending…', 'جاري الإرسال…'),
            'success_title': t('Your request was submitted successfully!', 'تم إرسال طلبك بنجاح!'),
            'success_text': t('Thank you! Our team will contact you within 24 hours to provide all details.',
                              'شكراً لك! سيتواصل معك فريقنا خلال 24 ساعة لتزويدك بكل التفاصيل.'),
            'close': t('Close', 'إغلاق'),
            'err_required': t('Please fill in all required fields.', 'الرجاء تعبئة جميع الحقول المطلوبة.'),
            'err_branch': t('Please select a branch', 'الرجاء اختيار الفرع'),
            'err_network': t('A connection error occurred. Please try again.', 'حدث خطأ في الاتصال، حاول مرة أخرى.'),
        },
    }