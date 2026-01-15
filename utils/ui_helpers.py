"""
UI Helper Functions for Blueprint-Specific Styling
===================================================

هذا الملف يوفر دوال مساعدة لإدارة الأصول (CSS/JS) الخاصة بكل Blueprint.

الفكرة:
- كل Blueprint يمكنه الحصول على CSS/JS خاص به
- يتم تحميل الأصول ديناميكيًا حسب Blueprint النشط
- سهولة الصيانة والتوسع

الاستخدام:
1. إضافة ملفات CSS/JS في المجلدات المناسبة
2. تحديث القواميس أدناه
3. الأصول تُحمَّل تلقائيًا في القوالب
"""

from flask import request, url_for
from typing import List, Dict, Optional


def get_blueprint_styles(blueprint_name: Optional[str]) -> List[str]:
    """
    الحصول على ملفات CSS الخاصة بـ Blueprint معين
    
    Args:
        blueprint_name: اسم الـ Blueprint (مثل: 'dashboard', 'auth', 'pages', 'portfolio')
        
    Returns:
        list: قائمة بمسارات ملفات CSS
        
    Example:
        >>> get_blueprint_styles('dashboard')
        ['css/pages/dashboard.css']
    """
    if not blueprint_name:
        return []
    
    # خريطة Blueprints وملفات CSS الخاصة بها
    blueprint_css_map = {
        'dashboard': [
            'css/pages/dashboard.css',
        ],
        'auth': [
            'css/pages/auth.css',
        ],
        'pages': [
            'css/pages/public.css',
        ],
        'portfolio': [
            # portfolio.css موجود بالفعل ويُحمَّل دائمًا
            # يمكن إضافة ملفات إضافية هنا
        ],
    }
    
    return blueprint_css_map.get(blueprint_name, [])


def get_blueprint_scripts(blueprint_name: Optional[str]) -> List[str]:
    """
    الحصول على ملفات JavaScript الخاصة بـ Blueprint معين
    
    Args:
        blueprint_name: اسم الـ Blueprint
        
    Returns:
        list: قائمة بمسارات ملفات JavaScript
        
    Example:
        >>> get_blueprint_scripts('dashboard')
        ['js/dashboard.js']
    """
    if not blueprint_name:
        return []
    
    # خريطة Blueprints وملفات JS الخاصة بها
    blueprint_js_map = {
        'dashboard': [
            'js/dashboard.js',
        ],
        'auth': [
            # يمكن إضافة ملفات JS للـ auth إذا لزم الأمر
        ],
        'pages': [
            # يمكن إضافة ملفات JS للصفحات العامة
        ],
        'portfolio': [
            # يمكن إضافة ملفات JS للبورتفوليو
        ],
    }
    
    return blueprint_js_map.get(blueprint_name, [])


def inject_blueprint_assets() -> Dict[str, List[str]]:
    """
    Context processor لإدراج الأصول الخاصة بـ Blueprint في القوالب
    
    يتم استدعاء هذه الدالة تلقائيًا من Flask context processor
    
    Returns:
        dict: قاموس يحتوي على:
            - blueprint_styles: قائمة ملفات CSS
            - blueprint_scripts: قائمة ملفات JS
            - current_blueprint: اسم الـ Blueprint الحالي
            
    Example في القالب:
        {% for style_file in blueprint_styles %}
        <link rel="stylesheet" href="{{ url_for('static', filename=style_file) }}">
        {% endfor %}
    """
    # الحصول على Blueprint الحالي من Flask request
    blueprint_name = request.blueprint if request.blueprint else None
    
    return {
        'blueprint_styles': get_blueprint_styles(blueprint_name),
        'blueprint_scripts': get_blueprint_scripts(blueprint_name),
        'current_blueprint': blueprint_name,
    }


def get_page_specific_class(blueprint_name: Optional[str], route_name: Optional[str] = None) -> str:
    """
    الحصول على CSS class خاص بصفحة معينة
    يُستخدم لإضافة فئات CSS ديناميكية على body أو container
    
    Args:
        blueprint_name: اسم الـ Blueprint
        route_name: اسم الـ route (اختياري)
        
    Returns:
        str: CSS class للصفحة
        
    Example:
        >>> get_page_specific_class('dashboard', 'settings')
        'page-dashboard page-dashboard-settings'
    """
    if not blueprint_name:
        return 'page-default'
    
    classes = [f'page-{blueprint_name}']
    
    if route_name:
        classes.append(f'page-{blueprint_name}-{route_name}')
    
    return ' '.join(classes)


def get_ui_config() -> Dict[str, any]:
    """
    الحصول على إعدادات UI العامة
    
    Returns:
        dict: إعدادات UI مثل:
            - enable_animations: تفعيل/تعطيل الرسوم المتحركة
            - sidebar_collapsed: حالة الـ sidebar
            - etc.
    """
    # يمكن توسيع هذه الدالة لاحقًا لتحميل الإعدادات من database أو session
    return {
        'enable_animations': True,
        'sidebar_collapsed': False,
        'theme_mode': 'dark',  # 'light' or 'dark'
    }


# ========== UTILITY FUNCTIONS ========== #

def add_blueprint_css(blueprint_name: str, css_file: str) -> None:
    """
    إضافة ملف CSS جديد لـ Blueprint (للاستخدام البرمجي)
    
    Args:
        blueprint_name: اسم الـ Blueprint
        css_file: مسار ملف CSS
        
    Note:
        هذه الدالة للتوسع المستقبلي - حاليًا استخدم القواميس مباشرة
    """
    # Future implementation: dynamic CSS registration
    pass


def add_blueprint_js(blueprint_name: str, js_file: str) -> None:
    """
    إضافة ملف JavaScript جديد لـ Blueprint (للاستخدام البرمجي)
    
    Args:
        blueprint_name: اسم الـ Blueprint
        js_file: مسار ملف JavaScript
        
    Note:
        هذه الدالة للتوسع المستقبلي - حاليًا استخدم القواميس مباشرة
    """
    # Future implementation: dynamic JS registration
    pass


# ========== DOCUMENTATION ========== #

"""
كيفية إضافة Blueprint جديد:

1. إنشاء ملف CSS للـ Blueprint:
   static/css/pages/my-blueprint.css

2. تحديث القاموس في get_blueprint_styles():
   'my-blueprint': [
       'css/pages/my-blueprint.css',
   ]

3. (اختياري) إضافة ملف JS:
   static/js/my-blueprint.js
   
4. تحديث القاموس في get_blueprint_scripts()

5. استخدام في القالب:
   <!-- يتم تحميل الأصول تلقائيًا -->
   
مثال كامل:
-----------
Blueprint: 'settings'
CSS: static/css/pages/settings.css
JS: static/js/settings.js

في get_blueprint_styles():
'settings': ['css/pages/settings.css']

في get_blueprint_scripts():
'settings': ['js/settings.js']

انتهى! الأصول ستُحمَّل تلقائيًا عند زيارة أي صفحة من Blueprint 'settings'
"""
