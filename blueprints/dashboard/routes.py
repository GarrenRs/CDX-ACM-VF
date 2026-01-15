"""
Dashboard Routes - User dashboard management
Handles: All dashboard routes for managing portfolio, projects, clients, messages, etc.
"""

import os
import json
import shutil
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, session, redirect, url_for, request, flash, current_app, jsonify, send_file
from utils.data import load_data, save_data
from utils.decorators import login_required, admin_required, disable_in_demo
from utils.helpers import allowed_file, get_clients_stats, create_backup, get_backups_list
from utils.security import get_admin_credentials, log_audit_event
from utils.notifications import send_telegram_notification, get_telegram_credentials, load_smtp_config, send_event_notification_async, send_email
from utils.badges import determine_badge
from models import User, db, Message
from . import dashboard_bp


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    from models import Workspace, Project, Skill, Client, VisitorLog
    from datetime import datetime, timedelta
    
    username = session.get('username')
    user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    data = load_data(username=username)

    if is_admin:
        # Admin statistics from database
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_workspaces = Workspace.query.count()
        total_messages = Message.query.count()
        unread_messages = Message.query.filter_by(is_read=False).count()
        total_projects = Project.query.count()
        total_clients = Client.query.count()
        
        # Visitors in last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_visitors = VisitorLog.query.filter(
            VisitorLog.created_at >= thirty_days_ago
        ).count()
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'total_workspaces': total_workspaces,
            'total_messages': total_messages,
            'unread_messages': unread_messages,
            'total_projects': total_projects,
            'total_clients': total_clients,
            'recent_visitors': recent_visitors,
            'demo_users': User.query.filter_by(is_demo=True).count(),
            'verified_users': User.query.filter_by(is_verified=True).count()
        }
    else:
        # User statistics from database
        user = User.query.filter_by(username=username).first()
        if user:
            workspace_id = user.workspace_id
            
            # Count user's data
            user_projects = Project.query.filter_by(workspace_id=workspace_id).count()
            user_skills = Skill.query.filter_by(workspace_id=workspace_id).count()
            user_clients = Client.query.filter_by(workspace_id=workspace_id).count()
            user_messages = Message.query.filter_by(workspace_id=workspace_id).count()
            user_unread = Message.query.filter_by(
                workspace_id=workspace_id,
                is_read=False
            ).count()
            
            # Visitors
            today = datetime.now().date()
            today_visitors = VisitorLog.query.filter(
                VisitorLog.workspace_id == workspace_id,
                db.func.date(VisitorLog.created_at) == today
            ).count()
            
            total_visitors = VisitorLog.query.filter_by(workspace_id=workspace_id).count()
            
            stats = {
                'projects': user_projects,
                'skills': user_skills,
                'clients': user_clients,
                'messages': user_messages,
                'unread_messages': user_unread,
                'visitors': total_visitors,
                'today_visitors': today_visitors,
                'is_verified': user.is_verified,
                'is_demo': user.is_demo
            }
        else:
            # Fallback to data.json
            user_data = data.get('portfolios', {}).get(username, {})
            stats = {
                'projects': len(user_data.get('projects', [])),
                'skills': len(user_data.get('skills', [])),
                'messages': len(user_data.get('messages', [])),
                'unread_messages': len([
                    m for m in user_data.get('messages', [])
                    if not m.get('read', False)
                ]),
                'visitors': user_data.get('visitors', {}).get('total', 0),
                'today_visitors': len(user_data.get('visitors', {}).get('today', []))
            }
    
    return render_template('dashboard/index.html', data=data, stats=stats, is_admin=is_admin)


@dashboard_bp.route('/general', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def general():
    """Edit general information"""
    username = session.get('username')
    data = load_data(username=username)

    if request.method == 'POST':
        data['name'] = request.form.get('name', '')
        data['title'] = request.form.get('title', '')
        data['description'] = request.form.get('description', '')

        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"profile_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                data['photo'] = f"static/assets/uploads/{filename}"

        save_data(data, username=username)
        flash('General information saved successfully', 'success')
        return redirect(url_for('dashboard.general'))

    return render_template('dashboard/general.html', data=data)


@dashboard_bp.route('/about', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def about():
    """Edit about section"""
    username = session.get('username')
    data = load_data(username=username)

    if request.method == 'POST':
        data['about'] = request.form.get('about', '')
        save_data(data, username=username)
        flash('About section saved successfully', 'success')
        return redirect(url_for('dashboard.about'))

    return render_template('dashboard/about.html', data=data)


@dashboard_bp.route('/skills', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def skills():
    """Edit skills section"""
    username = session.get('username')
    data = load_data(username=username)

    if request.method == 'POST':
        skills = []
        skill_names = request.form.getlist('skill_name[]')
        skill_levels = request.form.getlist('skill_level[]')

        for name, level in zip(skill_names, skill_levels):
            name_clean = name.strip()
            if name_clean:
                try:
                    level_int = int(level)
                    if not (0 <= level_int <= 100):
                        level_int = 0
                except (ValueError, TypeError):
                    level_int = 0
                    
                skills.append({
                    'name': name_clean,
                    'level': level_int
                })

        data['skills'] = skills
        save_data(data, username=username)
        flash('Skills saved successfully', 'success')
        return redirect(url_for('dashboard.skills'))

    return render_template('dashboard/skills.html', data=data)


@dashboard_bp.route('/projects')
@login_required
@disable_in_demo
def projects():
    """List all projects"""
    username = session.get('username')
    data = load_data(username=username)
    return render_template('dashboard/projects.html', data=data)


@dashboard_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def add_project():
    """Add new project"""
    username = session.get('username')
    if request.method == 'POST':
        data = load_data(username=username)

        project_ids = [p.get('id', 0) for p in data.get('projects', [])]
        new_id = max(project_ids) + 1 if project_ids else 1

        image_path = "static/assets/project-placeholder.svg"
        gallery_images = []
        
        # Handle main image
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"project_{username}_{new_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                image_path = f"static/assets/uploads/{filename}"
        
        # Handle gallery images (up to 8)
        if 'gallery_images[]' in request.files:
            files = request.files.getlist('gallery_images[]')
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/assets/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            for idx, file in enumerate(files[:8]):  # Limit to 8 images
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"project_{username}_{new_id}_gallery_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file.save(os.path.join(upload_folder, filename))
                    gallery_images.append(f"static/assets/uploads/{filename}")

        technologies = [
            tech.strip()[:50] for tech in request.form.getlist('technologies[]')
            if tech.strip()
        ]
        short_desc = request.form.get('short_description', '').strip()
        full_content = request.form.get('content', '').strip()
        
        # Get project type and determine badge
        project_type = request.form.get('project_type', 'portfolio')
        badge = determine_badge(project_type)

        new_project = {
            'id': new_id,
            'title': request.form.get('title', '').strip()[:200],
            'short_description': short_desc[:500],
            'content': full_content,
            'description': short_desc[:500],
            'image': image_path,
            'gallery': gallery_images,  # Gallery images array
            'demo_url': request.form.get('demo_url', '').strip()[:500] or '#',
            'github_url': request.form.get('github_url', '').strip()[:500] or '#',
            'technologies': technologies,
            'project_type': project_type,
            'badge': badge
        }
        
        # Add type-specific fields
        if project_type == 'request':
            request_budget_min = request.form.get('request_budget_min', '').strip()
            request_budget_max = request.form.get('request_budget_max', '').strip()
            request_deadline = request.form.get('request_deadline', '').strip()
            if request_budget_min:
                new_project['request_budget_min'] = float(request_budget_min) if request_budget_min.replace('.', '').isdigit() else None
            if request_budget_max:
                new_project['request_budget_max'] = float(request_budget_max) if request_budget_max.replace('.', '').isdigit() else None
            if request_deadline:
                new_project['request_deadline'] = request_deadline
            new_project['request_status'] = 'open'
        
        elif project_type == 'service_showcase':
            service_id = request.form.get('service_id', '').strip()
            if service_id:
                new_project['service_id'] = int(service_id) if service_id.isdigit() else None
        
        elif project_type == 'training':
            skill_related = [
                s.strip() for s in request.form.getlist('skill_related[]')
                if s.strip()
            ]
            new_project['skill_related'] = skill_related

        if 'projects' not in data:
            data['projects'] = []
        data['projects'].append(new_project)

        save_data(data, username=username)
        flash('Project added successfully', 'success')
        return redirect(url_for('dashboard.projects'))

    # Load user's services and skills for the form
    data = load_data(username=username)
    user_services = data.get('services', [])
    user_skills = data.get('skills', [])
    return render_template('dashboard/add_project.html', data=data, user_services=user_services, user_skills=user_skills)


@dashboard_bp.route('/projects/edit/<project_id>', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def edit_project(project_id):
    """Edit existing project"""
    username = session.get('username')
    data = load_data(username=username)
    project = next(
        (p for p in data.get('projects', []) if p.get('id') == project_id),
        None)

    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('dashboard.projects'))

    if request.method == 'POST':
        short_desc = request.form.get('short_description', '').strip()
        full_content = request.form.get('content', '').strip()
        
        # Get project type and determine badge
        project_type = request.form.get('project_type', project.get('project_type', 'portfolio'))
        badge = determine_badge(project_type)

        project['title'] = request.form.get('title', '').strip()[:200]
        project['short_description'] = short_desc[:500]
        project['content'] = full_content
        project['description'] = short_desc[:500]
        project['demo_url'] = request.form.get('demo_url', '').strip()[:500] or '#'
        project['github_url'] = request.form.get('github_url', '').strip()[:500] or '#'
        project['project_type'] = project_type
        project['badge'] = badge

        # Handle main image
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"project_{username}_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                project['image'] = f"static/assets/uploads/{filename}"
        
        # Handle gallery images (up to 8)
        if 'gallery_images[]' in request.files:
            files = request.files.getlist('gallery_images[]')
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/assets/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Initialize gallery if not exists
            if 'gallery' not in project:
                project['gallery'] = []
            
            # Add new gallery images (limit to 8 total)
            existing_count = len(project.get('gallery', []))
            remaining_slots = 8 - existing_count
            
            for idx, file in enumerate(files[:remaining_slots]):
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"project_{username}_{project_id}_gallery_{existing_count + idx + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file.save(os.path.join(upload_folder, filename))
                    project['gallery'].append(f"static/assets/uploads/{filename}")

        project['technologies'] = [
            tech.strip()[:50] for tech in request.form.getlist('technologies[]')
            if tech.strip()
        ]
        
        # Update type-specific fields
        if project_type == 'request':
            request_budget_min = request.form.get('request_budget_min', '').strip()
            request_budget_max = request.form.get('request_budget_max', '').strip()
            request_deadline = request.form.get('request_deadline', '').strip()
            if request_budget_min:
                project['request_budget_min'] = float(request_budget_min) if request_budget_min.replace('.', '').isdigit() else None
            if request_budget_max:
                project['request_budget_max'] = float(request_budget_max) if request_budget_max.replace('.', '').isdigit() else None
            if request_deadline:
                project['request_deadline'] = request_deadline
            if 'request_status' not in project:
                project['request_status'] = 'open'
        
        elif project_type == 'service_showcase':
            service_id = request.form.get('service_id', '').strip()
            if service_id:
                project['service_id'] = int(service_id) if service_id.isdigit() else None
            # Remove request fields if switching from request
            project.pop('request_budget_min', None)
            project.pop('request_budget_max', None)
            project.pop('request_deadline', None)
            project.pop('request_status', None)
        
        elif project_type == 'training':
            skill_related = [
                s.strip() for s in request.form.getlist('skill_related[]')
                if s.strip()
            ]
            project['skill_related'] = skill_related
            # Remove other type fields
            project.pop('request_budget_min', None)
            project.pop('request_budget_max', None)
            project.pop('request_deadline', None)
            project.pop('request_status', None)
            project.pop('service_id', None)
        
        else:  # portfolio
            # Remove all type-specific fields
            project.pop('request_budget_min', None)
            project.pop('request_budget_max', None)
            project.pop('request_deadline', None)
            project.pop('request_status', None)
            project.pop('service_id', None)
            project.pop('skill_related', None)

        save_data(data, username=username)
        flash('Project updated successfully', 'success')
        return redirect(url_for('dashboard.projects'))

    # Load user's services and skills for the form
    user_services = data.get('services', [])
    user_skills = data.get('skills', [])
    return render_template('dashboard/edit_project.html', project=project, data=data, user_services=user_services, user_skills=user_skills)


@dashboard_bp.route('/projects/delete/<project_id>', methods=['POST'])
@login_required
@disable_in_demo
def delete_project(project_id):
    """Delete project"""
    username = session.get('username')
    data = load_data(username=username)
    data['projects'] = [
        p for p in data.get('projects', []) if p.get('id') != project_id
    ]
    save_data(data, username=username)
    flash('Project deleted successfully', 'success')
    return redirect(url_for('dashboard.projects'))


@dashboard_bp.route('/contact', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def contact():
    """Edit contact information"""
    username = session.get('username')
    data = load_data(username=username)

    if request.method == 'POST':
        if 'contact' not in data:
            data['contact'] = {}

        data['contact']['email'] = request.form.get('email', '')[:100]
        data['contact']['phone'] = request.form.get('phone', '')[:20]
        data['contact']['location'] = request.form.get('location', '')[:200]

        save_data(data, username=username)
        flash('Contact information saved successfully', 'success')
        return redirect(url_for('dashboard.contact'))

    return render_template('dashboard/contact.html', data=data)


@dashboard_bp.route('/social', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def social():
    """Edit social media links"""
    username = session.get('username')
    data = load_data(username=username)

    if request.method == 'POST':
        if 'social' not in data:
            data['social'] = {}

        data['social']['linkedin'] = request.form.get('linkedin', '').strip()[:200]
        data['social']['github'] = request.form.get('github', '').strip()[:200]
        data['social']['twitter'] = request.form.get('twitter', '').strip()[:200]
        data['social']['instagram'] = request.form.get('instagram', '').strip()[:200]
        data['social']['facebook'] = request.form.get('facebook', '').strip()[:200]
        data['social']['youtube'] = request.form.get('youtube', '').strip()[:200]
        data['social']['behance'] = request.form.get('behance', '').strip()[:200]
        data['social']['dribbble'] = request.form.get('dribbble', '').strip()[:200]

        # Clean empty values (convert empty strings to None) to avoid stale entries
        for k, v in list(data['social'].items()):
            if v == '':
                data['social'].pop(k)

        save_data(data, username=username)
        flash('Social links saved successfully', 'success')
        return redirect(url_for('dashboard.social'))

    return render_template('dashboard/social.html', data=data, social=data.get('social', {}))


@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def settings():
    """Dashboard settings page"""
    username = session.get('username')
    data = load_data(username=username)
    is_demo_mode = session.get('is_demo_mode', False)
    is_admin = session.get('is_admin', False)

    if request.method == 'POST':
        if 'settings' not in data:
            data['settings'] = {}

        selected_theme = request.form.get('theme', 'luxury-gold')
        valid_themes = [
            'luxury-gold', 'modern-dark', 'clean-light', 'terracotta-red',
            'vibrant-green', 'silver-grey'
        ]
        if selected_theme in valid_themes:
            data['settings']['theme'] = selected_theme
            save_data(data, username=username)
            flash(f'Theme changed to {selected_theme.replace("-", " ").title()} successfully', 'success')
        else:
            flash('Invalid theme selected', 'error')

        return redirect(url_for('dashboard.settings'))

    themes = [
        {'id': 'luxury-gold', 'name': 'Luxury Gold', 'icon': 'fas fa-crown', 'description': 'Premium & Classic'},
        {'id': 'modern-dark', 'name': 'Modern Dark', 'icon': 'fas fa-zap', 'description': 'Tech & Trendy'},
        {'id': 'clean-light', 'name': 'Clean Light', 'icon': 'fas fa-sun', 'description': 'Minimal & Fresh'},
        {'id': 'terracotta-red', 'name': 'Terracotta Red', 'icon': 'fas fa-fire', 'description': 'Warm & Modern'},
        {'id': 'vibrant-green', 'name': 'Vibrant Green', 'icon': 'fas fa-leaf', 'description': 'Natural & Fresh'},
        {'id': 'silver-grey', 'name': 'Silver Grey', 'icon': 'fas fa-gem', 'description': 'Sophisticated & Modern'}
    ]

    current_theme = data.get('settings', {}).get('theme', 'luxury-gold')
    bot_token, chat_id = get_telegram_credentials(username=username)
    telegram_status = bool(bot_token and chat_id)
    telegram_bot_token_display = (bot_token[:10] + '...' + bot_token[-5:]) if bot_token and len(bot_token) > 15 else ''
    smtp_cfg = load_smtp_config(username=username)
    smtp_host = smtp_cfg.get('host', '')
    smtp_port = smtp_cfg.get('port', '')
    smtp_email = smtp_cfg.get('email', '')
    smtp_status = bool(all([smtp_host, smtp_port, smtp_email, smtp_cfg.get('password')]))

    return render_template(
        'dashboard/settings.html',
        themes=themes,
        current_theme=current_theme,
        data=data,
        telegram_bot_token=telegram_bot_token_display,
        telegram_chat_id=chat_id,
        telegram_status=telegram_status,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_email=smtp_email,
        smtp_status=smtp_status,
        is_demo_mode=is_demo_mode,
        is_admin=is_admin,
    )


@dashboard_bp.route('/telegram', methods=['POST'])
@login_required
@disable_in_demo
def telegram_settings():
    """Update Telegram settings - per-user configuration"""
    username = session.get('username')
    bot_token = request.form.get('bot_token', '').strip()
    chat_id = request.form.get('chat_id', '').strip()

    if not bot_token or not chat_id:
        flash('Please provide both Bot Token and Chat ID', 'error')
        return redirect(url_for('dashboard.settings'))

    try:
        # Test connection to Telegram API
        test_url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(test_url, timeout=5)

        if response.status_code != 200:
            flash('Invalid Telegram Bot Token. Please check and try again.', 'error')
            return redirect(url_for('dashboard.settings'))

        # Send test message
        test_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        test_payload = {
            'chat_id': chat_id,
            'text': '✅ Telegram notifications configured successfully for your Codexx Portfolio!',
            'parse_mode': 'HTML'
        }
        test_response = requests.post(test_message_url, json=test_payload, timeout=5)

        if test_response.status_code != 200:
            flash('Invalid Telegram Chat ID or permission denied. Please check and try again.', 'error')
            return redirect(url_for('dashboard.settings'))

        # Save to user data (per-user configuration)
        data = load_data(username=username)
        if 'notifications' not in data:
            data['notifications'] = {}

        data['notifications']['telegram'] = {
            'bot_token': bot_token,
            'chat_id': chat_id,
            'configured_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data(data, username=username)

        flash('✅ Telegram notifications configured successfully for your portfolio! Check your Telegram for a test message.', 'success')

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Telegram configuration error: {str(e)}")
        flash('Connection error. Please check your internet connection and try again.', 'error')
    except Exception as e:
        current_app.logger.error(f"Telegram error: {str(e)}")
        flash('An error occurred. Please try again.', 'error')

    return redirect(url_for('dashboard.settings'))


@dashboard_bp.route('/telegram-test', methods=['POST'])
@login_required
@disable_in_demo
def telegram_test_connection():
    """Test Telegram connection"""
    username = session.get('username')
    bot_token, chat_id = get_telegram_credentials(username=username)

    if not bot_token or not chat_id:
        return jsonify({'success': False, 'error': 'Telegram not configured'})

    try:
        # Send test message
        test_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        test_payload = {
            'chat_id': chat_id,
            'text': '🧪 <b>Connection Test Successful!</b>\n✅ Your Portfolio Bot is working perfectly!',
            'parse_mode': 'HTML'
        }
        test_response = requests.post(test_url, json=test_payload, timeout=5)

        if test_response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Test message sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to send message: {test_response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Telegram test error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Connection error. Please check your internet connection.'
        })
    except Exception as e:
        current_app.logger.error(f"Telegram test error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred. Please try again.'
        })


@dashboard_bp.route('/smtp', methods=['POST'])
@login_required
@disable_in_demo
def smtp_settings():
    """Update SMTP settings - per-user configuration"""
    username = session.get('username')
    smtp_host = request.form.get('smtp_host', '').strip()
    smtp_port = request.form.get('smtp_port', '').strip()
    smtp_email = request.form.get('smtp_email', '').strip()
    smtp_password = request.form.get('smtp_password', '').strip()

    if not all([smtp_host, smtp_port, smtp_email, smtp_password]):
        flash('Please provide all SMTP settings', 'error')
        return redirect(url_for('dashboard.settings'))

    try:
        # Save to user data (per-user configuration)
        data = load_data(username=username)
        if 'notifications' not in data:
            data['notifications'] = {}

        data['notifications']['smtp'] = {
            'host': smtp_host,
            'port': smtp_port,
            'email': smtp_email,
            'password': smtp_password,
            'configured_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_data(data, username=username)

        flash('✅ SMTP settings saved successfully for your portfolio!', 'success')
    except Exception as e:
        current_app.logger.error(f"SMTP configuration error: {str(e)}")
        flash('An error occurred. Please try again.', 'error')

    return redirect(url_for('dashboard.settings'))


@dashboard_bp.route('/email-test', methods=['POST'])
@login_required
@disable_in_demo
def email_test_connection():
    """Test SMTP connection"""
    username = session.get('username')
    smtp_config = load_smtp_config(username=username)

    if not all([
        smtp_config.get('host'),
        smtp_config.get('email'),
        smtp_config.get('password')
    ]):
        return jsonify({'success': False, 'error': 'SMTP not configured'})

    try:
        user_data = load_data(username=username)
        user_email = smtp_config.get('email') or user_data.get('contact', {}).get('email')
        
        if not user_email:
            return jsonify({'success': False, 'error': 'No recipient email found'})

        # Send test email
        success = send_email(
            recipient=user_email,
            subject='🧪 SMTP Connection Test',
            body='This is a test email from your Codexx Portfolio. Your SMTP configuration is working correctly!',
            html=False,
            username=username
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send test email'
            })
    except Exception as e:
        current_app.logger.error(f"SMTP test error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })


# Clients Routes
@dashboard_bp.route('/clients')
@login_required
@disable_in_demo
def clients():
    """List all clients"""
    username = session.get('username')
    data = load_data(username=username)
    if 'clients' not in data:
        data['clients'] = []
        save_data(data, username=username)

    clients_list = sorted(data.get('clients', []),
                         key=lambda x: x.get('created_at', ''),
                         reverse=True)

    stats = get_clients_stats(username)
    return render_template('dashboard/clients.html',
                           clients=clients_list,
                           stats=stats)


@dashboard_bp.route('/clients/add', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def add_client():
    """Add new client"""
    username = session.get('username')
    prefill = None
    
    prefill_msg_id = request.args.get('prefill_msg_id')
    if prefill_msg_id:
        data = load_data(username=username)
        message = next((m for m in data.get('messages', [])
                        if str(m.get('id')) == str(prefill_msg_id)), None)
        if message:
            prefill = message

    if request.method == 'POST':
        data = load_data(username=username)

        if 'clients' not in data:
            data['clients'] = []

        client_ids = [c.get('id', 0) for c in data.get('clients', [])]
        new_id = max(client_ids) + 1 if client_ids else 1

        new_client = {
            'id': new_id,
            'name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'company': request.form.get('company', '').strip(),
            'project_title': request.form.get('project_title', '').strip(),
            'project_description': request.form.get('project_description', '').strip(),
            'status': request.form.get('status', 'lead'),
            'price': request.form.get('price', '').strip(),
            'deadline': request.form.get('deadline', '').strip(),
            'start_date': request.form.get('start_date', '').strip() or datetime.now().strftime('%Y-%m-%d'),
            'notes': request.form.get('notes', '').strip(),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status_updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        data['clients'].append(new_client)
        save_data(data, username=username)

        send_telegram_notification(
            f"📊 <b>New Lead Added</b>\n\n"
            f"👤 {new_client['name']}\n"
            f"📧 {new_client['email']}\n"
            f"📋 {new_client['project_title']}\n"
            f"💰 ${new_client['price'] if new_client['price'] else 'TBD'}",
            username=username)

        flash('Client added successfully', 'success')
        return redirect(url_for('dashboard.clients'))

    return render_template('dashboard/add_client.html', prefill=prefill)


@dashboard_bp.route('/clients/edit/<client_id>', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def edit_client(client_id):
    """Edit existing client"""
    username = session.get('username')
    data = load_data(username=username)
    client = next(
        (c for c in data.get('clients', []) if c.get('id') == client_id), None)

    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('dashboard.clients'))

    if request.method == 'POST':
        old_status = client.get('status', 'lead')
        new_status = request.form.get('status', 'lead')

        client['name'] = request.form.get('name', '').strip()
        client['email'] = request.form.get('email', '').strip()
        client['phone'] = request.form.get('phone', '').strip()
        client['company'] = request.form.get('company', '').strip()
        client['project_title'] = request.form.get('project_title', '').strip()
        client['project_description'] = request.form.get('project_description', '').strip()
        client['status'] = new_status
        client['price'] = request.form.get('price', '').strip()
        client['deadline'] = request.form.get('deadline', '').strip()
        client['start_date'] = request.form.get('start_date', '').strip()
        client['notes'] = request.form.get('notes', '').strip()

        if old_status != new_status:
            client['status_updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status_emoji = {
                'lead': '🎯',
                'negotiation': '💬',
                'in-progress': '⚙️',
                'delivered': '✅'
            }
            send_telegram_notification(
                f"{status_emoji.get(new_status, '📊')} <b>Client Status Updated</b>\n\n"
                f"👤 {client['name']}\n"
                f"📋 {client['project_title']}\n"
                f"📍 {old_status.title()} → {new_status.replace('-', ' ').title()}\n"
                f"💰 ${client['price'] if client['price'] else 'TBD'}",
                username=username)

        save_data(data, username=username)
        flash('Client updated successfully', 'success')
        return redirect(url_for('dashboard.clients'))

    return render_template('dashboard/edit_client.html', client=client)


@dashboard_bp.route('/clients/view/<client_id>')
@login_required
def view_client(client_id):
    """View client details"""
    username = session.get('username')
    data = load_data(username=username)
    client = next(
        (c for c in data.get('clients', []) if c.get('id') == client_id), None)

    if not client:
        flash('Client not found', 'error')
        return redirect(url_for('dashboard.clients'))

    return render_template('dashboard/view_client.html', client=client)


@dashboard_bp.route('/clients/delete/<client_id>')
@login_required
@disable_in_demo
def delete_client(client_id):
    """Delete client"""
    username = session.get('username')
    data = load_data(username=username)
    data['clients'] = [
        c for c in data.get('clients', []) if c.get('id') != client_id
    ]
    save_data(data, username=username)
    flash('Client deleted successfully', 'success')
    return redirect(url_for('dashboard.clients'))


# Messages Routes
@dashboard_bp.route('/messages')
@login_required
@disable_in_demo
def messages():
    """List INBOX messages (portfolio & platform) - EXCLUDES internal messages"""
    username = session.get('username')
    is_admin = session.get('is_admin', False)
    category = request.args.get('category', 'all')
    
    try:
        from models import Workspace
        
        if is_admin:
            # Admin inbox: platform messages only (NOT internal)
            query = Message.query.filter(
                Message.category != 'internal',  # Exclude internal
                db.or_(
                    Message.workspace_id.is_(None),  # Platform messages
                    Message.category == 'platform'
                )
            )
        else:
            # User inbox: portfolio messages only (NOT internal)
            user = User.query.filter_by(username=username).first()
            if user:
                query = Message.query.filter(
                    Message.workspace_id == user.workspace_id,
                    Message.category != 'internal'  # Exclude internal
                )
            else:
                query = Message.query.filter(Message.id.is_(None))  # Empty query
        
        # Filter by category (only portfolio or platform allowed)
        if category != 'all' and category != 'internal':
            query = query.filter(Message.category == category)
        
        # Exclude replies (only show main messages)
        query = query.filter(Message.parent_id.is_(None))
        
        # Order by date descending
        db_messages = query.order_by(Message.created_at.desc()).all()
        
        # Convert to dict format for template compatibility
        all_messages = []
        for msg in db_messages:
            all_messages.append({
                'id': msg.id,
                'name': msg.name,
                'email': msg.email,
                'message': msg.message,
                'read': msg.is_read,
                'category': msg.category or 'portfolio',
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id,
                'sender_role': msg.sender_role,
                'date': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else '',
                'parent_id': msg.parent_id
            })
        
        current_app.logger.info(f"Loaded {len(all_messages)} inbox messages from DB for {username}")
        
    except Exception as e:
        current_app.logger.error(f"Error loading inbox messages from DB: {str(e)}")
        # Fallback to JSON
        data = load_data(username=username)
        all_messages = [m for m in data.get('messages', []) if m.get('category') != 'internal']
        if category != 'all' and category != 'internal':
            all_messages = [m for m in all_messages if m.get('category') == category]
        all_messages.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template('dashboard/messages.html', messages=all_messages, current_category=category, is_admin=is_admin)


@dashboard_bp.route('/messages/internal')
@login_required
@disable_in_demo
def internal_messages():
    """List internal conversations - shows conversation threads"""
    username = session.get('username')
    user_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    
    try:
        if is_admin:
            # Admin sees internal conversations (main messages only, not replies)
            db_messages = Message.query.filter(
                Message.category == 'internal',
                Message.parent_id.is_(None),  # Only main messages
                db.or_(
                    Message.receiver_id == 'admin',
                    Message.sender_role == 'admin'
                )
            ).order_by(Message.created_at.desc()).all()
        else:
            # User sees their internal conversations
            user = User.query.filter_by(username=username).first()
            if user:
                db_messages = Message.query.filter(
                    Message.category == 'internal',
                    Message.parent_id.is_(None),  # Only main messages
                    db.or_(
                        Message.sender_id == str(user.id),
                        Message.receiver_id == str(user.id),
                        Message.name == username
                    )
                ).order_by(Message.created_at.desc()).all()
            else:
                db_messages = []
        
        # Convert to dict format with reply count
        all_messages = []
        for msg in db_messages:
            # Count replies for this conversation
            reply_count = Message.query.filter_by(parent_id=msg.id).count()
            # Count unread replies
            unread_replies = Message.query.filter(
                Message.parent_id == msg.id,
                Message.is_read == False
            ).count()
            
            # Determine conversation partner name
            if is_admin:
                partner_name = msg.name  # The user who sent the message
            else:
                partner_name = 'Admin' if msg.receiver_id == 'admin' or msg.sender_role == 'admin' else msg.name
            
            all_messages.append({
                'id': msg.id,
                'name': msg.name,
                'email': msg.email,
                'message': msg.message,
                'read': msg.is_read,
                'category': msg.category,
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id,
                'sender_role': msg.sender_role,
                'date': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else '',
                'display_name': partner_name,
                'display_email': msg.email or '',
                'reply_count': reply_count,
                'unread_count': unread_replies + (0 if msg.is_read else 1)
            })
        
        current_app.logger.info(f"Loaded {len(all_messages)} internal conversations from DB")
        
    except Exception as e:
        current_app.logger.error(f"Error loading internal messages: {str(e)}")
        # Fallback to JSON
        data = load_data(username=username)
        all_messages = [m for m in data.get('messages', []) if m.get('category') == 'internal' and not m.get('parent_id')]
        all_messages.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template('dashboard/internal_messages.html', messages=all_messages, is_admin=is_admin)


@dashboard_bp.route('/messages/internal/compose')
@dashboard_bp.route('/messages/internal/compose/<receiver_id>')
@login_required
@disable_in_demo
def internal_compose(receiver_id=None):
    """View for composing a new internal message"""
    receiver = None
    if receiver_id and receiver_id != 'admin':
        try:
            receiver = User.query.get(receiver_id)
        except:
            pass
    return render_template('dashboard/internal_compose.html', receiver=receiver)


@dashboard_bp.route('/messages/internal/send', methods=['POST'])
@login_required
@disable_in_demo
def internal_send():
    """Process sending a new internal message - saves to database"""
    username = session.get('username')
    sender_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    receiver_id = request.form.get('receiver_id')
    message_content = request.form.get('message')
    
    if not message_content:
        flash('Message content cannot be empty.', 'danger')
        return redirect(url_for('dashboard.internal_compose', receiver_id=receiver_id))
    
    try:
        from utils.notifications import send_admin_notification, send_user_notification
        from models import Workspace
        
        sender_role = 'admin' if is_admin else 'user'
        
        # Get sender's workspace
        sender_user = User.query.filter_by(username=username).first()
        sender_workspace_id = sender_user.workspace_id if sender_user else None
        
        # Create message in database
        new_message = Message(
            workspace_id=sender_workspace_id,
            name=username,
            email=session.get('email', ''),
            message=message_content[:5000],
            is_read=False,
            category='internal',
            sender_id=str(sender_id) if sender_id else username,
            receiver_id=receiver_id,
            sender_role=sender_role
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        current_app.logger.info(f"Internal message saved to DB, message_id: {new_message.id}")
        
        # Send notifications
        if receiver_id == 'admin':
            send_admin_notification(
                subject="New Internal Message",
                message_text=f"From: {username}\n\nMessage: {message_content[:200]}"
            )
        else:
            # Get receiver user info
            receiver_user = User.query.get(receiver_id)
            if receiver_user:
                send_user_notification(
                    username=receiver_user.username,
                    subject="New Internal Message",
                    message_text=f"From: {username}\n\nMessage: {message_content[:200]}"
                )
        
        flash('Message sent successfully.', 'success')
        return redirect(url_for('dashboard.internal_messages'))
    except Exception as e:
        current_app.logger.error(f"Error sending internal message: {str(e)}")
        db.session.rollback()
        flash('System error. Please try again.', 'danger')
        return redirect(url_for('dashboard.internal_messages'))


@dashboard_bp.route('/messages/internal/view/<message_id>')
@login_required
@disable_in_demo
def internal_view(message_id):
    """View an internal thread - loads from database"""
    username = session.get('username')
    is_admin = session.get('is_admin', False)
    
    try:
        # Load message from database
        db_message = Message.query.get(message_id)
        
        if not db_message:
            flash('Message not found.', 'danger')
            return redirect(url_for('dashboard.internal_messages'))
        
        # Mark as read
        if not db_message.is_read:
            db_message.is_read = True
            db.session.commit()
        
        # Convert to dict
        message = {
            'id': db_message.id,
            'name': db_message.name,
            'email': db_message.email,
            'message': db_message.message,
            'read': db_message.is_read,
            'category': db_message.category,
            'sender_id': db_message.sender_id,
            'receiver_id': db_message.receiver_id,
            'sender_role': db_message.sender_role,
            'date': db_message.created_at.strftime('%Y-%m-%d %H:%M:%S') if db_message.created_at else '',
            'display_name': db_message.name or 'Unknown'
        }
        
        # Get replies from database
        db_replies = Message.query.filter_by(parent_id=message_id).order_by(Message.created_at.asc()).all()
        replies = []
        for r in db_replies:
            replies.append({
                'id': r.id,
                'name': r.name,
                'email': r.email,
                'message': r.message,
                'sender_role': r.sender_role,
                'date': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })
        
        current_app.logger.info(f"Loaded internal message {message_id} with {len(replies)} replies")
        
    except Exception as e:
        current_app.logger.error(f"Error loading internal message: {str(e)}")
        flash('Error loading message.', 'danger')
        return redirect(url_for('dashboard.internal_messages'))
    
    return render_template('dashboard/internal_view.html', 
                          message=message, 
                          replies=replies,
                          is_admin=is_admin)


@dashboard_bp.route('/messages/reply/<message_id>', methods=['POST'])
@login_required
@disable_in_demo
def reply_message(message_id):
    """Reply to a message - saves directly to database"""
    username = session.get('username')
    sender_id = session.get('user_id')
    is_admin = session.get('is_admin', False)
    
    # Support both 'reply' and 'reply_content' field names
    reply_content = request.form.get('reply_content', '').strip() or request.form.get('reply', '').strip()
    
    if not reply_content:
        flash('Reply content cannot be empty.', 'danger')
        return redirect(url_for('dashboard.view_message', message_id=message_id))
    
    try:
        from utils.notifications import send_admin_notification, send_user_notification
        
        # Get parent message from database
        parent_message = Message.query.get(message_id)
        
        if not parent_message:
            flash('Original message not found.', 'danger')
            return redirect(url_for('dashboard.messages'))
        
        sender_role = 'admin' if is_admin else 'user'
        
        # Determine receiver
        original_sender_id = parent_message.sender_id
        original_receiver_id = parent_message.receiver_id
        
        # If I'm the sender of the original message, reply goes to the receiver
        # If I'm the receiver, reply goes to the sender
        if str(sender_id) == str(original_sender_id) or username == parent_message.name:
            receiver_id = original_receiver_id
        else:
            receiver_id = original_sender_id
        
        # Get sender's workspace
        sender_user = User.query.filter_by(username=username).first()
        sender_workspace_id = sender_user.workspace_id if sender_user else parent_message.workspace_id
        
        # Create reply in database
        reply = Message(
            workspace_id=sender_workspace_id,
            parent_id=message_id,
            name=username,
            email=session.get('email', ''),
            message=reply_content[:5000],
            is_read=False,
            category=parent_message.category or 'portfolio',
            sender_id=str(sender_id) if sender_id else username,
            receiver_id=receiver_id,
            sender_role=sender_role
        )
        
        db.session.add(reply)
        db.session.commit()
        
        current_app.logger.info(f"Reply saved to DB, reply_id: {reply.id}, parent: {message_id}")
        
        # Send notifications
        if receiver_id == 'admin':
            send_admin_notification(
                subject="New Reply to Message",
                message_text=f"From: {username}\n\nReply: {reply_content[:200]}"
            )
        elif receiver_id:
            # Get receiver user
            receiver_user = User.query.get(receiver_id)
            if not receiver_user:
                receiver_user = User.query.filter_by(username=receiver_id).first()
            
            if receiver_user and receiver_user.username != username:
                send_user_notification(
                    username=receiver_user.username,
                    subject="New Reply to Your Message",
                    message_text=f"From: {username}\n\nReply: {reply_content[:200]}"
                )
        
        flash('Reply sent successfully.', 'success')
        
        # Redirect based on category
        if parent_message.category == 'internal':
            return redirect(url_for('dashboard.internal_view', message_id=message_id))
        else:
            return redirect(url_for('dashboard.view_message', message_id=message_id))
            
    except Exception as e:
        current_app.logger.error(f"Error sending reply: {str(e)}")
        db.session.rollback()
        flash('Error sending reply. Please try again.', 'danger')
        return redirect(url_for('dashboard.messages'))


@dashboard_bp.route('/messages/view/<message_id>')
@login_required
@disable_in_demo
def view_message(message_id):
    """View specific message - loads from database"""
    username = session.get('username')
    is_admin = session.get('is_admin', False)
    
    try:
        # Load message from database
        db_message = Message.query.get(message_id)
        
        if not db_message:
            flash('Message not found', 'error')
            return redirect(url_for('dashboard.messages'))
        
        # Verify access (admin can see all, user can see their workspace messages)
        if not is_admin:
            user = User.query.filter_by(username=username).first()
            if user and db_message.workspace_id != user.workspace_id:
                flash('Message not found', 'error')
                return redirect(url_for('dashboard.messages'))
        
        # Mark as read
        if not db_message.is_read:
            db_message.is_read = True
            db.session.commit()
        
        # Convert to dict for template
        message = {
            'id': db_message.id,
            'name': db_message.name,
            'email': db_message.email,
            'message': db_message.message,
            'read': db_message.is_read,
            'category': db_message.category or 'portfolio',
            'sender_id': db_message.sender_id,
            'receiver_id': db_message.receiver_id,
            'sender_role': db_message.sender_role,
            'date': db_message.created_at.strftime('%Y-%m-%d %H:%M:%S') if db_message.created_at else '',
            'parent_id': db_message.parent_id,
            # Portfolio form fields
            'request_type': db_message.request_type,
            'interest_area': db_message.interest_area,
            'seriousness': db_message.seriousness,
            'contact_pref': db_message.contact_pref,
            'company': db_message.company
        }
        
        # Get replies from database
        db_replies = Message.query.filter_by(parent_id=message_id).order_by(Message.created_at.asc()).all()
        replies = []
        for r in db_replies:
            replies.append({
                'id': r.id,
                'name': r.name,
                'email': r.email,
                'message': r.message,
                'read': r.is_read,
                'category': r.category,
                'sender_role': r.sender_role,
                'date': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
            })
        
        current_app.logger.info(f"Loaded message {message_id} from DB with {len(replies)} replies")
        
    except Exception as e:
        current_app.logger.error(f"Error loading message from DB: {str(e)}")
        # Fallback to JSON
        data = load_data(username=username)
        message = next((m for m in data.get('messages', [])
                        if str(m.get('id')) == str(message_id)), None)
        if not message:
            flash('Message not found', 'error')
            return redirect(url_for('dashboard.messages'))
        replies = [m for m in data.get('messages', []) if str(m.get('parent_id')) == str(message_id)]
    
    # Check if this is an internal system message
    is_internal_system = message.get('category') == 'internal' or message.get('sender_role') in ['admin', 'member']
    
    return render_template('dashboard/view_message.html', 
                          message=message, 
                          replies=replies, 
                          is_internal_system=is_internal_system,
                          is_admin=is_admin)


@dashboard_bp.route('/messages/delete/<message_id>')
@login_required
@disable_in_demo
def delete_message(message_id):
    """Delete message from database"""
    username = session.get('username')
    is_admin = session.get('is_admin', False)
    
    try:
        db_message = Message.query.get(message_id)
        
        if not db_message:
            flash('Message not found', 'error')
            return redirect(url_for('dashboard.messages'))
        
        # Verify access
        if not is_admin:
            user = User.query.filter_by(username=username).first()
            if user and db_message.workspace_id != user.workspace_id:
                flash('Message not found', 'error')
                return redirect(url_for('dashboard.messages'))
        
        # Delete replies first
        Message.query.filter_by(parent_id=message_id).delete()
        
        # Delete message
        db.session.delete(db_message)
        db.session.commit()
        
        current_app.logger.info(f"Deleted message {message_id} from DB")
        flash('Message deleted successfully', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error deleting message from DB: {str(e)}")
        db.session.rollback()
        flash('Error deleting message', 'error')
    
    return redirect(url_for('dashboard.messages'))


# Admin Routes (Users Management)
@dashboard_bp.route('/users')
@login_required
@admin_required
@disable_in_demo
def users():
    """Manage users and permissions (Admin only)"""
    data = load_data()
    users_list = data.get('users', [])
    # Ensure legacy users have the must_change_password flag (default False)
    updated = False
    for u in users_list:
        if 'must_change_password' not in u:
            u['must_change_password'] = False
            updated = True
    if updated:
        save_data(data)
    return render_template('dashboard/users.html', users=users_list)


@dashboard_bp.route('/user/<user_id>')
@login_required
@admin_required
@disable_in_demo
def view_user(user_id):
    """View detailed information about a specific user"""
    data = load_data()
    users_list = data.get('users', [])
    target_user = next((u for u in users_list if u.get('id') == user_id), None)

    if not target_user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard.users'))

    username = target_user['username']
    user_portfolio_data = load_data(username=username)

    stats = {
        'projects_count': len(user_portfolio_data.get('projects', [])),
        'skills_count': len(user_portfolio_data.get('skills', [])),
        'clients_count': len(user_portfolio_data.get('clients', [])),
        'messages_count': len(user_portfolio_data.get('messages', [])),
        'visitors_total': user_portfolio_data.get('visitors', {}).get('total', 0)
    }

    return render_template('dashboard/view_user.html',
                           target_user=target_user,
                           stats=stats,
                           is_verified=target_user.get('is_verified', False))


@dashboard_bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
@disable_in_demo
def add_user():
    """Create a new user account from the Admin Panel"""
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    role = request.form.get('role', 'user')
    is_demo = request.form.get('is_demo') == 'on'

    if not username or not password or not email:
        flash('All fields are required', 'error')
        return redirect(url_for('dashboard.users'))

    # Check for existing user in data.json
    data = load_data()
    if 'users' not in data:
        data['users'] = []

    if any(u['username'] == username for u in data['users']):
        flash('Username already exists', 'error')
        return redirect(url_for('dashboard.users'))

    # Hash password and create user object for data.json
    user_ids = [u.get('id', 0) for u in data['users']]
    new_id = max(user_ids) + 1 if user_ids else 1
    
    new_user = {
        'id': new_id,
        'username': username,
        'password_hash': generate_password_hash(password),
        'email': email,
        'role': role,
        'is_demo': is_demo,
        'must_change_password': True,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    data['users'].append(new_user)

    # Initialize portfolio for the new user
    if 'portfolios' not in data:
        data['portfolios'] = {}
    data['portfolios'][username] = {
        'username': username,
        'name': '',
        'title': '',
        'description': '',
        'about': '',
        'photo': '',
        'skills': [],
        'projects': [],
        'messages': [],
        'clients': [],
        'contact': {
            'email': '',
            'phone': '',
            'location': ''
        },
        'social': {
            'linkedin': '',
            'github': '',
            'twitter': ''
        },
        'settings': {
            'theme': 'luxury-gold'
        },
        'visitors': {
            'total': 0,
            'today': [],
            'unique_ips': []
        }
    }

    save_data(data)

    # Audit: record provisioning event and that this user must change password on first login
    try:
        log_audit_event('user_provisioned', username=username, details='must_change_password=True')
    except Exception:
        pass

    # Sync with PostgreSQL
    try:
        from models import Workspace
        ws = Workspace.query.first()
        if not ws:
            ws = Workspace(name='Default', slug='default')
            db.session.add(ws)
            db.session.commit()

        # Check if user already exists in DB
        existing_db_user = User.query.filter_by(username=username).first()
        if existing_db_user:
            existing_db_user.password_hash = new_user['password_hash']
            existing_db_user.email = email
            existing_db_user.role = role
            existing_db_user.is_demo = is_demo
            existing_db_user.must_change_password = True
        else:
            db_user = User(username=username,
                           password_hash=new_user['password_hash'],
                           email=email,
                           role=role,
                           is_demo=is_demo,
                           must_change_password=True,
                           workspace_id=ws.id)
            db.session.add(db_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error syncing user to DB: {str(e)}")
        flash(f'Error syncing with database: {str(e)}', 'warning')

    flash(f'User {username} created successfully', 'success')
    return redirect(url_for('dashboard.users'))


@dashboard_bp.route('/user/<user_id>/toggle-demo', methods=['POST'])
@login_required
@admin_required
@disable_in_demo
def toggle_user_demo(user_id):
    """Toggle demo mode for a specific user"""
    from utils.notifications import send_user_notification
    
    # Update in database
    user = User.query.get(user_id)
    if not user:
        # Try by username as fallback
        user = User.query.filter_by(username=user_id).first()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard.users'))
    
    # Toggle demo status
    user.is_demo = not user.is_demo
    db.session.commit()
    
    flash(f'User {user.username} access updated to {"Demo Mode" if user.is_demo else "Full Access"}.', 'success')
    
    # Send notification to user about access level change
    access_type = "Full Access" if not user.is_demo else "Demo Mode"
    advice = "You now have full platform capabilities. Explore the advanced features in your dashboard." if not user.is_demo else "Your account is currently in demo mode. Complete your profile to request full access."
    send_user_notification(
        user.username,
        "Access Level Changed",
        f"Your account access level has been updated to: <b>{access_type}</b>.\n\n<i>Advice: {advice}</i>"
    )
    
    return redirect(url_for('dashboard.view_user', user_id=user_id))


@dashboard_bp.route('/user/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
@disable_in_demo
def delete_user(user_id):
    """Delete a user and their portfolio data"""
    data = load_data()
    users_list = data.get('users', [])

    target_user = next((u for u in users_list if u.get('id') == user_id), None)
    if not target_user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard.users'))

    if target_user['username'] == 'admin':
        flash('Cannot delete admin user.', 'error')
        return redirect(url_for('dashboard.users'))

    # Remove from users list
    data['users'] = [u for u in users_list if u.get('id') != user_id]

    # Remove their portfolio data
    if 'portfolios' in data and target_user['username'] in data['portfolios']:
        del data['portfolios'][target_user['username']]

    save_data(data)
    flash(f'User {target_user["username"]} has been deleted.', 'success')
    return redirect(url_for('dashboard.users'))


@dashboard_bp.route('/users/toggle-verification/<user_id>', methods=['POST'])
@login_required
@admin_required
@disable_in_demo
def toggle_user_verification(user_id):
    """Toggle user's verified status with criteria check"""
    from utils.notifications import send_user_notification
    
    try:
        data = load_data()
        users_list = data.get('users', [])
        target_user = None
        for u in users_list:
            if str(u.get('id')) == str(user_id):
                target_user = u
                break
        
        if not target_user:
            flash('User not found.', 'error')
            return redirect(url_for('dashboard.users'))

        # Check criteria only when enabling
        if not target_user.get('is_verified', False):
            # Conditions: Full Access (is_demo is False) AND at least 3 projects
            user_portfolio_data = load_data(username=target_user['username'])
            projects_count = len(user_portfolio_data.get('projects', []))
            is_full_access = not target_user.get('is_demo', True)

            if not is_full_access or projects_count < 3:
                flash(f'Criteria not met: Full Access and 3 projects required. (Current: {"Full Access" if is_full_access else "Demo"}, {projects_count} projects)', 'warning')
                return redirect(url_for('dashboard.view_user', user_id=user_id))
            
            target_user['is_verified'] = True
            flash('Verification Badge enabled successfully! Portfolio now visible in the main gallery.', 'success')
            
            # Send notification to user
            send_user_notification(
                target_user['username'],
                "Portfolio Verified",
                "Congratulations! Your professional portfolio has been officially verified by the Academy. Your proof-of-work is now showcased in our elite gallery.\n\n<i>Advice: Keep your portfolio updated with your latest high-impact projects to maintain your elite standing.</i>"
            )
        else:
            target_user['is_verified'] = False
            flash('Verification Badge disabled.', 'info')
            
            # Send notification to user
            send_user_notification(
                target_user['username'],
                "Verification Status Updated",
                "Your verification status has been updated. Please review your dashboard for required standards.\n\n<i>Advice: Ensure you have at least 3 high-quality projects and complete profile information to regain verification.</i>"
            )

        save_data(data)
        
        # Sync with Database
        try:
            user_obj = User.query.get(str(user_id))
            if user_obj:
                user_obj.is_verified = target_user['is_verified']
                db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error syncing verification to DB: {str(e)}")
            
        return redirect(url_for('dashboard.view_user', user_id=user_id))
    except Exception as e:
        current_app.logger.error(f"Error toggling verification: {str(e)}")
        flash('An error occurred while updating verification status.', 'error')
        return redirect(url_for('dashboard.users'))


# Access Instructions and Password Change
@dashboard_bp.route('/access-instructions')
@login_required
def access_instructions():
    """Show terms of use and how to get Full Access/Verified Badge"""
    return render_template('dashboard/access_instructions.html')


@dashboard_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def change_password():
    """Change user password"""
    forced = session.get('force_change_password', False)
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        username = session.get('username')

        if not new_password:
            flash('New password is required', 'error')
        elif len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'error')
        elif new_password != confirm_password:
            flash('New password and confirmation do not match', 'error')
        else:
            data = load_data()
            user_found = False
            ADMIN_CREDENTIALS = get_admin_credentials()

            if 'users' in data:
                for user in data['users']:
                    if user.get('username') == username:
                        user_found = True
                        # If not forced, verify current password
                        if not forced:
                            if username == ADMIN_CREDENTIALS.get('username'):
                                if not check_password_hash(ADMIN_CREDENTIALS['password_hash'], current_password):
                                    flash('Current password is incorrect', 'error')
                                    return render_template('dashboard/change_password.html')
                            else:
                                if not check_password_hash(user.get('password_hash', ''), current_password):
                                    flash('Current password is incorrect', 'error')
                                    return render_template('dashboard/change_password.html')

                        user['password_hash'] = generate_password_hash(new_password)
                        # Clear force flag after successful change
                        user['must_change_password'] = False
                        save_data(data)

                        log_audit_event('password_changed', username=username, details='Password changed via change_password')
                        flash('Password changed successfully. Please login again.', 'success')
                        session.pop('force_change_password', None)
                        session.clear()
                        return redirect(url_for('auth.login'))

            if not user_found:
                flash('User not found', 'error')

    return render_template('dashboard/change_password.html')


@dashboard_bp.route('/backups')
@login_required
def view_backups():
    """View all available backups - redirect to settings"""
    return redirect(url_for('dashboard.settings') + '#backups')


@dashboard_bp.route('/backup/create', methods=['POST'])
@login_required
def create_manual_backup():
    """Create a manual backup"""
    try:
        backup_info = create_backup(manual=True)
        if backup_info:
            flash(f'✓ Backup created successfully: {backup_info["filename"]}', 'success')
            username = session.get('username')
            send_event_notification_async(
                'backup_created',
                f'Manual backup: {backup_info["filename"]} ({backup_info["size_kb"]} KB)',
                username=username)
        else:
            flash('Error creating backup', 'error')
    except Exception as e:
        current_app.logger.error(f"Error creating manual backup: {str(e)}")
        flash('Error creating backup', 'error')
    return redirect(url_for('dashboard.settings') + '#backups')


@dashboard_bp.route('/backup/restore/<filename>', methods=['POST'])
@login_required
@disable_in_demo
def restore_backup(filename):
    """Restore a backup"""
    try:
        filename = secure_filename(filename)
        backup_path = os.path.join('backups', filename)

        if not os.path.exists(backup_path):
            flash('Backup file not found', 'error')
            return redirect(url_for('dashboard.settings') + '#backups')

        if os.path.exists('data.json'):
            recovery_backup = f'backups/recovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            shutil.copy('data.json', recovery_backup)

        shutil.copy(backup_path, 'data.json')
        flash(f'✓ Portfolio restored from backup: {filename}', 'success')
        username = session.get('username')
        send_event_notification_async('backup_restored', f'Restored from: {filename}', username=username)
        return redirect(url_for('dashboard.settings') + '#backups')
    except Exception as e:
        current_app.logger.error(f"Error restoring backup: {str(e)}")
        flash('Error restoring backup', 'error')
        return redirect(url_for('dashboard.settings') + '#backups')


@dashboard_bp.route('/backup/download/<filename>')
@login_required
def download_backup(filename):
    """Download a backup file"""
    try:
        filename = secure_filename(filename)
        backup_path = os.path.join('backups', filename)

        if not os.path.exists(backup_path):
            flash('Backup file not found', 'error')
            return redirect(url_for('dashboard.settings') + '#backups')

        return send_file(backup_path, as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.error(f"Error downloading backup: {str(e)}")
        flash('Error downloading backup', 'error')
        return redirect(url_for('dashboard.settings') + '#backups')


@dashboard_bp.route('/backup/delete/<filename>', methods=['POST'])
@login_required
@disable_in_demo
def delete_backup(filename):
    """Delete a backup file"""
    try:
        filename = secure_filename(filename)
        backup_path = os.path.join('backups', filename)

        if not os.path.exists(backup_path):
            flash('Backup file not found', 'error')
            return redirect(url_for('dashboard.settings') + '#backups')

        os.remove(backup_path)

        backups = get_backups_list()
        updated_backups = [b for b in backups if b['filename'] != filename]
        with open('backups/backups.json', 'w', encoding='utf-8') as f:
            json.dump(updated_backups, f, ensure_ascii=False, indent=2)

        flash(f'✓ Backup deleted: {filename}', 'success')
    except Exception as e:
        current_app.logger.error(f"Error deleting backup: {str(e)}")
        flash('Error deleting backup', 'error')

    return redirect(url_for('dashboard.settings') + '#backups')


@dashboard_bp.route('/api/backups')
@login_required
def api_backups():
    """API endpoint to get backups list"""
    try:
        backups = get_backups_list()
        return jsonify(backups)
    except Exception as e:
        current_app.logger.error(f"Error fetching backups: {str(e)}")
        return jsonify([]), 500


@dashboard_bp.route('/chat', methods=['GET', 'POST'])
@dashboard_bp.route('/chat/<user_id>', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def chat(user_id=None):
    """Internal chat system between users and admin"""
    current_user_id = str(session.get('user_id'))
    username = session.get('username')
    is_admin = session.get('is_admin')

    # For admin, if no user_id is provided, show the user list
    if is_admin and not user_id:
        # Fetch all users except admin to start conversations
        users = User.query.filter(User.username != 'admin').all()
        return render_template('dashboard/chat_list.html', users=users)

    # If a user is accessing, their user_id is always their own, unless they're admin
    target_user_id = user_id if is_admin else current_user_id

    # Internal chat routes are deprecated. Redirecting to consolidated messages.
    return redirect(url_for('dashboard.messages'))


@dashboard_bp.route('/notifications/latest')
def get_latest_notifications():
    """Fetch latest unread notifications - includes inbox AND internal messages"""
    try:
        username = session.get('username')
        is_admin = session.get('is_admin', False)
        
        if not username:
            return jsonify([])
        
        if is_admin:
            # Admin sees: platform messages + internal messages to admin
            unread_messages = Message.query.filter(
                Message.is_read == False,
                Message.parent_id.is_(None),  # Only main messages, not replies
                db.or_(
                    Message.workspace_id.is_(None),  # Platform messages
                    Message.receiver_id == 'admin',  # Messages/internal to admin
                    Message.category == 'platform'
                )
            ).order_by(Message.created_at.desc()).limit(10).all()
        else:
            # User sees: portfolio messages + internal messages RECEIVED (not sent)
            user = User.query.filter_by(username=username).first()
            if not user:
                return jsonify([])
            
            unread_messages = Message.query.filter(
                Message.is_read == False,
                Message.parent_id.is_(None),  # Only main messages
                db.or_(
                    # Portfolio messages from visitors (sender_id is NULL or not user)
                    db.and_(
                        Message.workspace_id == user.workspace_id,
                        Message.category == 'portfolio',
                        db.or_(
                            Message.sender_id.is_(None),  # Visitor messages
                            Message.sender_id != str(user.id)  # Not from self
                        )
                    ),
                    # Internal messages FROM admin TO user
                    db.and_(
                        Message.category == 'internal',
                        Message.sender_role == 'admin',
                        Message.receiver_id == str(user.id)
                    )
                )
            ).order_by(Message.created_at.desc()).limit(10).all()
        
        notifications = []
        for msg in unread_messages:
            # For internal messages, the "thread ID" to link to is the parent_id (if it's a reply) or its own ID (if it's a parent)
            thread_id = msg.parent_id if msg.parent_id else msg.id
            
            notifications.append({
                'id': msg.id,
                'thread_id': thread_id,
                'name': msg.name or 'Unknown',
                'message': (msg.message[:50] + '...') if msg.message and len(msg.message) > 50 else (msg.message or ''),
                'category': msg.category or 'portfolio',
                'time': msg.created_at.strftime('%H:%M') if msg.created_at else ''
            })
        
        return jsonify(notifications)
    except Exception as e:
        current_app.logger.error(f"Error fetching notifications: {str(e)}")
        return jsonify([]), 500


@dashboard_bp.route('/admin/test-notifications', methods=['POST'])
@admin_required
def admin_test_notifications():
    """Test admin notifications (Telegram and SMTP)"""
    try:
        from utils.notifications import send_admin_notification
        
        send_admin_notification(
            'Admin Notification Test',
            'This is a test notification to verify that admin Telegram and SMTP settings are working correctly.'
        )
        
        return jsonify({'success': True, 'message': 'Test notification sent successfully'})
    except Exception as e:
        current_app.logger.error(f"Admin notification test error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
