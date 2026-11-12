# -*- coding: utf-8 -*-
"""
محتوى صفحة الدروس الخصوصية والمتابعة المدرسية والدعم الجامعي (/private-tutoring)
==============================================================================
نفس فكرة english_landing_content.py: كل النصوص بالعربي والإنجليزي هون،
والـ template بنيوي بس. أي تعديل على النصوص بيصير هون بدون ما نلمس الـ XML أو ar.po.

القيم الثابتة (keys) هي اللي بتنبعت من الفورم وبتنفحص بالسيرفر — لا تغيرها
بدون ما تعدل الـ Selection fields على crm.lead.
"""
from . import english_landing_content as _shared

# نفس أرقام المركز ونفس رقم التواصل بصفحة الإنجليزي / تواصل معنا
TRAINEES = _shared.TRAINEES
BRANCHES = _shared.BRANCHES
PHONE_NUMBER = _shared.PHONE_NUMBER
PHONE_DISPLAY = _shared.PHONE_DISPLAY
ORG_ID = _shared.ORG_ID

# رقم الواتساب الافتراضي (ممكن يتغير من System Parameter: alomran.tutoring_whatsapp)
WHATSAPP_NUMBER = _shared.WHATSAPP_NUMBER

# ------------------------------------------------------------------
# الخدمات — key: اسم الخدمة بالـ CRM (x_course_interest) منشان التقارير
# ------------------------------------------------------------------
SERVICE_CRM_NAMES = {
    'private': 'Private Tutoring',
    'school': 'School Follow-up',
    'university': 'University Academic Support',
    'unsure': 'Needs Consultation',
}
SERVICE_KEYS = tuple(SERVICE_CRM_NAMES)
# الخدمات اللي إلها بطاقة (كل شي ما عدا "لا أعرف")
CARD_SERVICE_KEYS = ('private', 'school', 'university')

# لازم تتطابق مع x_study_stage على crm.lead
STAGE_KEYS = ('primary', 'middle', 'secondary', 'university')
MODE_KEYS = ('branch', 'online', 'home')

# ------------------------------------------------------------------
# صور الصفحة (مش بالهيرو — الهيرو للفيديو).
# حط الصورة بالمسار وبتظهر لحالها؛ إذا مش موجودة بيطلع بديل (لون + أيقونة).
# أول ملف موجود من كل قائمة هو اللي بينعرض. المقاس المقترح:
#   الخدمات: 800×520 (webp)      صورة الفورم: 900×1100 (webp، طولية)
# ------------------------------------------------------------------
_IMG = 'alomran_theme/static/src/img/tutoring/'
IMAGE_FILES = {
    'private': (_IMG + 'private.webp', _IMG + 'private.jpg'),
    'school': (_IMG + 'school.webp', _IMG + 'school.jpg'),
    'university': (_IMG + 'university.webp', _IMG + 'university.jpg'),
    'form': (_IMG + 'form.webp', _IMG + 'form.jpg'),
}


def get_content(is_en):
    """كل نصوص الصفحة باللغة الحالية."""
    def t(en, ar):
        return en if is_en else ar

    services = [
        {
            'key': 'private',
            'icon': 'fa-chalkboard-user',
            'title': t('Private lessons', 'الدروس الخصوصية'),
            'lead': t('Clear, organized explanation of the curriculum with a focus on understanding.',
                      'شرح مبسط ومنظم للمناهج الدراسية مع التركيز على الفهم.'),
            'points': [t('Simplified explanation of the curriculum', 'شرح مبسط للمناهج الدراسية'),
                       t('Strengthening subjects', 'تقوية المواد'),
                       t('Solving exercises', 'حل التمارين'),
                       t('Reviewing lessons', 'مراجعة الدروس'),
                       t('Preparing for exams', 'الاستعداد للاختبارات')],
            'alt': t('Private lesson with a tutor at Al Omran', 'درس خصوصي مع مدرس في مركز العمران'),
            'text': t('Simplified explanation of the curriculum, strengthening subjects, solving exercises, '
                      'reviewing lessons and preparing for exams.',
                      'شرح مبسط للمناهج الدراسية، تقوية المواد، حل التمارين، ومراجعة الدروس والاستعداد للاختبارات.'),
        },
        {
            'key': 'school',
            'icon': 'fa-list-check',
            'title': t('School follow-up', 'المتابعة المدرسية'),
            'lead': t("Continuous follow-up that helps the student organize their studies and improve their level.",
                      'متابعة مستمرة تساعد الطالب على تنظيم دراسته وتطوير مستواه.'),
            'points': [t('Following up on homework', 'متابعة الواجبات'),
                       t('Organizing the study schedule', 'تنظيم جدول الدراسة'),
                       t('Reviewing lessons', 'مراجعة الدروس'),
                       t('Identifying weak points', 'تحديد نقاط الضعف'),
                       t("Improving the student's level", 'تطوير مستوى الطالب')],
            'alt': t('School follow-up for a student at Al Omran', 'متابعة مدرسية لطالبة في مركز العمران'),
            'text': t('Following up on homework, organizing the study schedule, reviewing lessons, and identifying '
                      "weak points to work on improving the student's level.",
                      'متابعة الواجبات، تنظيم جدول الدراسة، مراجعة الدروس، وتحديد نقاط الضعف والعمل على '
                      'تطوير مستوى الطالب.'),
        },
        {
            'key': 'university',
            'icon': 'fa-building-columns',
            'title': t('University academic support', 'الدعم الأكاديمي الجامعي'),
            'lead': t('Helping university students understand their courses and prepare for assessments.',
                      'مساعدة طلاب الجامعة على فهم المقررات والاستعداد للتقييمات.'),
            'points': [t('Explaining courses', 'شرح المقررات'),
                       t('Reviewing academic concepts', 'مراجعة المفاهيم الأكاديمية'),
                       t('Practicing problems', 'التدريب على المسائل'),
                       t('Preparing for university exams and assessments',
                         'الاستعداد للاختبارات والتقييمات الجامعية')],
            'alt': t('University student studying at Al Omran', 'طالب جامعي يدرس في مركز العمران'),
            'text': t('Explaining courses, reviewing academic concepts, practicing problems, and preparing for '
                      'university exams and assessments.',
                      'شرح المقررات، مراجعة المفاهيم الأكاديمية، التدريب على المسائل، والاستعداد للاختبارات '
                      'والتقييمات الجامعية.'),
        },
    ]

    modes_short = [
        {'key': 'branch', 'icon': 'fa-location-dot', 'label': t('At our branches in the UAE', 'في فروعنا في الإمارات')},
        {'key': 'online', 'icon': 'fa-laptop', 'label': t('Online', 'أونلاين')},
        {'key': 'home', 'icon': 'fa-house', 'label': t("At the student's home, subject to availability",
                                                       'في منزل الطالب، حسب التوفر')},
    ]

    return {
        'org_name': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
        'page_title': t('Private Tutoring, School Follow-up & University Support in the UAE | Al Omran',
                        'دروس خصوصية ومتابعة مدرسية ودعم أكاديمي جامعي في الإمارات | مركز العمران'),
        'page_description': t(
            'Private lessons, school follow-up and university academic support across the UAE with '
            'Al Omran Training Center — at our branches, online or at home. Contact us on WhatsApp.',
            'دروس خصوصية، متابعة مدرسية، ودعم أكاديمي جامعي في جميع الإمارات مع مركز العمران — '
            'في فروعنا أو أونلاين أو في منزل الطالب. تواصل معنا عبر واتساب.'),

        'hero': {
            'kicker': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
            'h1': t('With Al Omran, learn with confidence and move toward success',
                    'مع العمران، تعلّم بثقة وتقدّم نحو النجاح'),
            'subtitle': t('Private lessons, school follow-up and university academic support across all of the UAE.',
                          'دروس خصوصية، متابعة مدرسية، ودعم أكاديمي جامعي في جميع الإمارات.'),
            'intro': t('We help students understand their subjects, develop their skills and prepare for exams '
                       'through educational programs that suit their needs and academic level.',
                       'نساعد الطلاب على فهم المواد الدراسية، وتطوير مهاراتهم، والاستعداد للاختبارات من خلال '
                       'برامج تعليمية تناسب احتياجاتهم ومستواهم الدراسي.'),
            'cta_whatsapp': t('Contact us on WhatsApp', 'تواصل معنا عبر واتساب'),
            'cta_call': t('Call us', 'اتصل بنا'),
        },
        'modes_short': modes_short,

        'video': {
            'unmute': t('Turn sound on', 'تشغيل الصوت'),
            'mute': t('Mute', 'كتم الصوت'),
        },

        'services': {
            'title': t('Our educational services', 'خدماتنا التعليمية'),
            'subtitle': t('Three main services… one goal: your success', 'ثلاث خدمات رئيسية .. هدف واحد: نجاحك'),
            'items': services,
            'more': t('Request this service', 'اطلب الخدمة'),
            'whatsapp': t('Ask on WhatsApp', 'اسأل عبر واتساب'),
        },

        'why': {
            'title': t('Why choose Al Omran?', 'لماذا تختار العمران؟'),
            'items': [
                {'icon': 'fa-bullseye', 'title': t('A plan that fits the student', 'خطة تناسب الطالب'),
                 'text': t('Educational programs that suit the needs of every student.',
                           'برامج تعليمية تناسب احتياجات كل طالب.')},
                {'icon': 'fa-shuffle', 'title': t('Flexible learning', 'مرونة في التعلم'),
                 'text': t('Flexible options for in-person and remote learning.',
                           'خيارات مرنة للتعلم الحضوري وعن بُعد.')},
                {'icon': 'fa-user-graduate', 'title': t('Diverse study stages', 'مراحل تعليمية متنوعة'),
                 'text': t('Services for school and university stages.',
                           'خدمات لمراحل التعليم المدرسي والجامعي.')},
                {'icon': 'fa-map-location-dot', 'title': t('Coverage across the UAE', 'تغطية في جميع الإمارات'),
                 'text': t('Branches across the emirates of the UAE.',
                           'فروع في مختلف إمارات الدولة.')},
                {'icon': 'fa-comments', 'title': t('Free consultation', 'استشارة لتحديد الخدمة'),
                 'text': t('You can request a consultation to find the right service.',
                           'إمكانية طلب استشارة لتحديد الخدمة المناسبة.')},
            ],
        },

        'steps': {
            'title': t('How do you start?', 'كيف تبدأ؟'),
            'items': [
                {'icon': 'fa-comment-dots', 'title': t('Contact us', 'تواصل معنا'),
                 'text': t('Tell us the study stage and the subject you need.',
                           'أخبرنا بالمرحلة الدراسية والمادة المطلوبة.')},
                {'icon': 'fa-user-pen', 'title': t('Define your need', 'حدد احتياجك'),
                 'text': t('Discuss the available options with our team.',
                           'ناقش الخيارات المتاحة مع فريقنا.')},
                {'icon': 'fa-calendar-days', 'title': t('Choose how to learn', 'اختر طريقة التعلم'),
                 'text': t('At the branch, online or at home, subject to availability.',
                           'في الفرع أو أونلاين أو في المنزل حسب التوفر.')},
                {'icon': 'fa-circle-check', 'title': t('Start learning', 'ابدأ التعلم'),
                 'text': t('Agree with the team on the right schedule and plan.',
                           'اتفق مع الفريق على الجدول والخطة المناسبين.')},
            ],
        },

        'help': {
            'title': t('Let us help you choose the right service', 'دعنا نساعدك في اختيار الخدمة المناسبة'),
            'intro': t('Send us the following details on WhatsApp:', 'أرسل لنا عبر واتساب التفاصيل التالية:'),
            'details': [
                {'icon': 'fa-location-dot', 'text': t('Emirate and area.', 'الإمارة والمنطقة.')},
                {'icon': 'fa-layer-group', 'text': t('Study stage.', 'المرحلة الدراسية.')},
                {'icon': 'fa-book', 'text': t('Required subject or subjects.', 'المادة أو المواد المطلوبة.')},
                {'icon': 'fa-chalkboard', 'text': t('Preferred teaching method.', 'طريقة التدريس المفضلة.')},
            ],
            'note': t('The Al Omran team will contact you to discuss the available options, fees and schedules.',
                      'سيتواصل معك فريق مركز العمران لمناقشة الخيارات المتاحة والرسوم والمواعيد.'),
            'cta': t('Send the details on WhatsApp', 'أرسل التفاصيل عبر واتساب'),
            'band_title': t('Contact us now on WhatsApp', 'تواصل معنا الآن عبر واتساب'),
            'band_text': t('Our team is ready to help you', 'فريقنا جاهز لمساعدتك'),
            'band_tagline': t('Give your child the support they need to achieve their best',
                              'امنح ابنك الدعم الذي يحتاجه ليحقق الأفضل'),
        },

        'faq': {
            'title': t('Frequently asked questions', 'أسئلة شائعة'),
            'items': [
                {'q': t('Do you offer lessons for all study stages?', 'هل تقدمون دروساً لجميع المراحل الدراسية؟'),
                 'a': t('Our services cover school stages and university students. Tell us the stage and the '
                        'subject and our team will discuss the available options with you.',
                        'خدماتنا تشمل مراحل التعليم المدرسي وطلاب الجامعات. أخبرنا بالمرحلة والمادة '
                        'وسيناقش فريقنا الخيارات المتاحة معك.')},
                {'q': t('Can the student be followed up throughout the semester?',
                        'هل يمكن متابعة الطالب طوال الفصل الدراسي؟'),
                 'a': t('Yes, school follow-up includes following up on homework, organizing the study schedule '
                        'and reviewing lessons. The plan and schedule are agreed with the team.',
                        'نعم، المتابعة المدرسية تشمل متابعة الواجبات وتنظيم جدول الدراسة ومراجعة الدروس، '
                        'ويتم الاتفاق على الخطة والجدول مع الفريق.')},
                {'q': t('Can the lessons be at home?', 'هل يمكن أن تكون الدروس في المنزل؟'),
                 'a': t("Yes, lessons at the student's home are available subject to availability in your area.",
                        'نعم، تتوفر الدروس في منزل الطالب حسب التوفر في منطقتك.')},
                {'q': t('How much do private lessons cost?', 'كم تبلغ رسوم الدروس الخصوصية؟'),
                 'a': t('Fees depend on the stage, the subject and the teaching method. Send us your request and '
                        'our team will contact you with the fees and schedules.',
                        'تختلف الرسوم حسب المرحلة والمادة وطريقة التدريس. أرسل طلبك وسيتواصل معك فريقنا '
                        'لتوضيح الرسوم والمواعيد.')},
                {'q': t('Are lessons available online?', 'هل تتوفر الدروس أونلاين؟'),
                 'a': t('Yes, you can learn online from anywhere, in addition to our branches and home lessons.',
                        'نعم، يمكنك التعلم أونلاين من أي مكان، إلى جانب التعلم في فروعنا أو في المنزل.')},
                {'q': t('Where are your branches?', 'أين تقع فروعكم؟'),
                 'a': t(f'We have {BRANCHES} branches across the UAE. You can see all locations on the branches page.',
                        f'لدينا {BRANCHES} فرعًا في دولة الإمارات، ويمكنك الاطلاع على جميع المواقع في صفحة الفروع.')},
            ],
        },

        'form': {
            'title': t('Request a free educational consultation', 'اطلب استشارة تعليمية مجانية'),
            'subtitle': t('Tell us a few details to help you choose the right service',
                          'أخبرنا ببعض التفاصيل لنساعدك على اختيار الخدمة المناسبة'),
            'image_note': t('Your future starts here', 'مستقبلك يبدأ من هنا'),
            'image_alt': t('Student studying with confidence', 'طالبة تدرس بثقة'),
            'service_ph': t('Select the service type', 'اختر نوع الخدمة'),
            'mode_ph': t('Select the method', 'اختر الطريقة'),
            'name': t('Name', 'الاسم'),
            'name_ph': t('Your full name', 'اسمك الكامل'),
            'phone': t('Phone / WhatsApp number', 'رقم الهاتف / واتساب'),
            'phone_ph': '05XXXXXXXX',
            'branch': t('Nearest branch', 'الفرع الأقرب'),
            'service_q': t('Service type', 'نوع الخدمة'),
            'stage': t('Study stage', 'المرحلة الدراسية'),
            'stage_ph': t('Select the study stage', 'اختر المرحلة الدراسية'),
            'subjects': t('Subject(s) required', 'المادة أو المواد المطلوبة'),
            'subjects_ph': t('e.g. Math, Physics', 'مثال: الرياضيات، الفيزياء'),
            'mode_q': t('Preferred teaching method', 'طريقة الدراسة المفضلة'),
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
            'err_phone': t('Please enter a valid phone number', 'الرجاء إدخال رقم هاتف صحيح'),
            'err_branch': t('Please select a branch', 'الرجاء اختيار الفرع'),
            'err_service': t('Please choose a service', 'الرجاء اختيار الخدمة'),
            'err_stage': t('Please select the study stage', 'الرجاء اختيار المرحلة الدراسية'),
            'err_mode': t('Please choose a teaching method', 'الرجاء اختيار طريقة التدريس'),
            'err_network': t('Connection error, please try again or message us on WhatsApp',
                             'حدث خطأ في الاتصال، حاول مرة أخرى أو راسلنا عبر واتساب'),
        },
        'service_options': [
            ('private', t('Private lessons', 'الدروس الخصوصية')),
            ('school', t('School follow-up', 'المتابعة المدرسية')),
            ('university', t('University academic support', 'الدعم الأكاديمي الجامعي')),
            ('unsure', t("I'm not sure and need a consultation", 'لست متأكدًا وأحتاج إلى استشارة')),
        ],
        'stage_options': [
            ('primary', t('Primary school', 'المرحلة الابتدائية')),
            ('middle', t('Middle school', 'المرحلة الإعدادية')),
            ('secondary', t('Secondary school', 'المرحلة الثانوية')),
            ('university', t('University', 'المرحلة الجامعية')),
        ],
        'mode_options': [
            ('branch', t('At the branch', 'في الفرع')),
            ('online', t('Online', 'أونلاين')),
            ('home', t("At home (subject to availability)", 'في المنزل (حسب التوفر)')),
        ],

        'direct': {
            'title': t('Or contact us directly', 'أو تواصل معنا مباشرة'),
            'text': t('Talk to the Al Omran team on WhatsApp', 'تحدث مع فريق مركز العمران عبر واتساب'),
            'cta': t('Talk to us now', 'تحدث معنا الآن'),
        },

        'closing': {
            'name': t('Al Omran Training and Development Center', 'مركز العمران للتدريب والتطوير'),
            'slogan': t('Together toward a better future.', 'معاً نحو مستقبل أفضل.'),
            'stats': [
                {'icon': 'fa-user-graduate', 'value': TRAINEES, 'label': t('trainees', 'متدرب')},
                {'icon': 'fa-location-dot', 'value': str(BRANCHES), 'label': t('branches in the UAE', 'فرعًا في الإمارات')},
                {'icon': 'fa-users', 'value': '', 'label': t('All school and university stages',
                                                            'جميع المراحل المدرسية والجامعية')},
            ],
            'cta': t('Contact us on WhatsApp', 'تواصل معنا عبر واتساب'),
        },

        'sticky': {
            'whatsapp': t('WhatsApp', 'واتساب'),
            'form': t('Free consultation', 'استشارة مجانية'),
        },

        # رسائل واتساب الجاهزة
        'wa_general': t('Hello, I would like to ask about private tutoring and academic support services at Al Omran.',
                        'مرحباً، أود الاستفسار عن خدمات الدروس الخصوصية والدعم الأكاديمي في مركز العمران.'),
        'wa_service': t('Hello, I would like to ask about the "{service}" service at Al Omran.',
                        'مرحباً، أود الاستفسار عن خدمة "{service}" في مركز العمران.'),
        # رسالة قسم "دعنا نساعدك" — نفس التفاصيل المطلوبة جاهزة للتعبئة
        'wa_details': t('Hello, I would like to ask about private tutoring and academic support at Al Omran.\n'
                        'Emirate and area: \n'
                        'Study stage: \n'
                        'Subject(s): \n'
                        'Preferred teaching method: ',
                        'مرحباً، أود الاستفسار عن خدمات الدروس الخصوصية والدعم الأكاديمي في مركز العمران.\n'
                        'الإمارة والمنطقة: \n'
                        'المرحلة الدراسية: \n'
                        'المادة أو المواد: \n'
                        'طريقة التدريس المفضلة: '),

        # تسميات وصف الـ lead
        'lead_labels': {
            'service': t('Service', 'الخدمة'),
            'stage': t('Study stage', 'المرحلة الدراسية'),
            'subjects': t('Subjects', 'المواد'),
            'branch': t('Branch', 'الفرع'),
            'mode': t('Teaching method', 'طريقة التدريس'),
            'source': t('Source', 'المصدر'),
            'source_value': t('Private tutoring landing page', 'صفحة الدروس الخصوصية والدعم الأكاديمي'),
            'campaign': t('Campaign', 'الحملة'),
            'click_id': t('Ad click ID', 'معرف النقرة الإعلانية'),
        },
    }
