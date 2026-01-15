"""
Badges Module - Project badge system
Handles badge types, labels, icons, and colors
"""

BADGE_TYPES = {
    'completed': {
        'label': 'Completed Project',
        'icon': 'fa-check-circle',
        'color': 'success',
        'bg_color': 'rgba(16, 185, 129, 0.1)',
        'text_color': '#10b981',
        'border_color': 'rgba(16, 185, 129, 0.3)'
    },
    'request': {
        'label': 'Project Request',
        'icon': 'fa-hand-holding-usd',
        'color': 'info',
        'bg_color': 'rgba(59, 130, 246, 0.1)',
        'text_color': '#3b82f6',
        'border_color': 'rgba(59, 130, 246, 0.3)'
    },
    'training': {
        'label': 'Training / Skill Demo',
        'icon': 'fa-graduation-cap',
        'color': 'warning',
        'bg_color': 'rgba(245, 158, 11, 0.1)',
        'text_color': '#f59e0b',
        'border_color': 'rgba(245, 158, 11, 0.3)'
    },
    'service_result': {
        'label': 'Service Showcase',
        'icon': 'fa-star',
        'color': 'gold',
        'bg_color': 'rgba(212, 175, 55, 0.1)',
        'text_color': '#d4af37',
        'border_color': 'rgba(212, 175, 55, 0.3)'
    }
}

PROJECT_TYPES = {
    'portfolio': {
        'label': 'Portfolio / Case Study',
        'badge': 'completed',
        'description': 'Showcase completed projects and case studies'
    },
    'request': {
        'label': 'Project Request',
        'badge': 'request',
        'description': 'Looking for someone to execute this project'
    },
    'service_showcase': {
        'label': 'Service Results Showcase',
        'badge': 'service_result',
        'description': 'Results from services provided'
    },
    'training': {
        'label': 'Training / Skill Demonstration',
        'badge': 'training',
        'description': 'Training projects or skill demonstrations'
    }
}


def determine_badge(project_type):
    """
    Determine badge based on project type
    
    Args:
        project_type (str): Project type (portfolio, request, service_showcase, training)
        
    Returns:
        str: Badge type
    """
    return PROJECT_TYPES.get(project_type, {}).get('badge', 'completed')


def get_badge_info(badge_type):
    """
    Get badge information
    
    Args:
        badge_type (str): Badge type
        
    Returns:
        dict: Badge information or default
    """
    return BADGE_TYPES.get(badge_type, BADGE_TYPES['completed'])


def get_project_type_info(project_type):
    """
    Get project type information
    
    Args:
        project_type (str): Project type
        
    Returns:
        dict: Project type information or default
    """
    return PROJECT_TYPES.get(project_type, PROJECT_TYPES['portfolio'])


__all__ = [
    'BADGE_TYPES',
    'PROJECT_TYPES',
    'determine_badge',
    'get_badge_info',
    'get_project_type_info'
]
