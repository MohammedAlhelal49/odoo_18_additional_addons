# -*- coding: utf-8 -*-
"""
أرقام المركز المشتركة بين كل صفحات الموقع — المصدر الوحيد لها.
الملف ما بيستورد شي (منعاً للـ circular import)، وكل ملفات المحتوى بتستورد منه.

ملاحظة: BRANCHES هو عدد الفروع الرسمي اللي بينكتب بالنصوص.
بطاقات صفحة الفروع بتنعرض من _get_branches_data بـ main.py، فأي فرع جديد
لازم ينضاف هناك كمان ليطلع إله بطاقة.
"""

BRANCHES = 13

# Public URL of the website used when Website > Settings > Domain is empty
# (the live value comes from website._alomran_site_url()).
DEFAULT_SITE_URL = 'https://alomrantd.com'
