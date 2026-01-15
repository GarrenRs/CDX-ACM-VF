"""
Services Routes - Service offerings management
Handles: Adding, editing, deleting, and displaying services
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, session, redirect, url_for, request, flash, current_app
from utils.data import load_data, save_data
from utils.decorators import login_required, disable_in_demo
from utils.helpers import allowed_file
from . import services_bp


@services_bp.route('/dashboard/services')
@login_required
@disable_in_demo
def list_services():
    """List all services in dashboard"""
    username = session.get('username')
    data = load_data(username=username)
    services = data.get('services', [])
    return render_template('dashboard/services.html', data=data, services=services)


@services_bp.route('/dashboard/services/add', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def add_service():
    """Add new service"""
    username = session.get('username')
    data = load_data(username=username)
    
    if request.method == 'POST':
        # Get service IDs to generate new ID
        services = data.get('services', [])
        service_ids = [s.get('id', 0) for s in services if isinstance(s.get('id'), int)]
        new_id = max(service_ids) + 1 if service_ids else 1
        
        # Handle main image upload
        image_path = "static/assets/project-placeholder.svg"
        gallery_images = []
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"service_{username}_{new_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/assets/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                image_path = f"static/assets/uploads/{filename}"
        
        # Handle gallery images (up to 8)
        if 'gallery_images[]' in request.files:
            files = request.files.getlist('gallery_images[]')
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/assets/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            for idx, file in enumerate(files[:8]):  # Limit to 8 images
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"service_{username}_{new_id}_gallery_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file.save(os.path.join(upload_folder, filename))
                    gallery_images.append(f"static/assets/uploads/{filename}")
        
        # Get deliverables (dynamic list)
        deliverables = [
            d.strip() for d in request.form.getlist('deliverables[]')
            if d.strip()
        ]
        
        # Get related skills
        skills_related = [
            s.strip() for s in request.form.getlist('skills_related[]')
            if s.strip()
        ]
        
        # Create new service
        new_service = {
            'id': new_id,
            'title': request.form.get('title', '').strip()[:200],
            'description': request.form.get('description', '').strip(),
            'short_description': request.form.get('short_description', '').strip()[:500],
            'category': request.form.get('category', 'other').strip(),
            'pricing_type': request.form.get('pricing_type', 'custom'),
            'price_min': request.form.get('price_min', '') or None,
            'price_max': request.form.get('price_max', '') or None,
            'currency': request.form.get('currency', 'USD'),
            'deliverables': deliverables,
            'duration': request.form.get('duration', '').strip()[:50],
            'skills_required': skills_related,
            'image': image_path,
            'gallery': gallery_images,  # Gallery images array
            'is_active': True,
            'is_featured': request.form.get('is_featured') == 'on',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Initialize services list if not exists
        if 'services' not in data:
            data['services'] = []
        data['services'].append(new_service)
        
        save_data(data, username=username)
        flash('Service added successfully', 'success')
        return redirect(url_for('services.list_services'))
    
    # Load user's skills for the form
    user_skills = data.get('skills', [])
    return render_template('dashboard/add_service.html', data=data, user_skills=user_skills)


@services_bp.route('/dashboard/services/edit/<service_id>', methods=['GET', 'POST'])
@login_required
@disable_in_demo
def edit_service(service_id):
    """Edit existing service"""
    username = session.get('username')
    data = load_data(username=username)
    services = data.get('services', [])
    
    service = next((s for s in services if s.get('id') == service_id), None)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('services.list_services'))
    
    if request.method == 'POST':
        # Update service fields
        service['title'] = request.form.get('title', '').strip()[:200]
        service['description'] = request.form.get('description', '').strip()
        service['short_description'] = request.form.get('short_description', '').strip()[:500]
        service['category'] = request.form.get('category', 'other').strip()
        service['pricing_type'] = request.form.get('pricing_type', 'custom')
        service['price_min'] = request.form.get('price_min', '') or None
        service['price_max'] = request.form.get('price_max', '') or None
        service['currency'] = request.form.get('currency', 'USD')
        service['duration'] = request.form.get('duration', '').strip()[:50]
        service['is_featured'] = request.form.get('is_featured') == 'on'
        service['updated_at'] = datetime.now().isoformat()
        
        # Update deliverables
        deliverables = [
            d.strip() for d in request.form.getlist('deliverables[]')
            if d.strip()
        ]
        service['deliverables'] = deliverables
        
        # Update related skills
        skills_related = [
            s.strip() for s in request.form.getlist('skills_related[]')
            if s.strip()
        ]
        service['skills_required'] = skills_related
        
        # Handle main image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"service_{username}_{service_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/assets/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                service['image'] = f"static/assets/uploads/{filename}"
        
        # Handle gallery images (up to 8)
        if 'gallery_images[]' in request.files:
            files = request.files.getlist('gallery_images[]')
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/assets/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Initialize gallery if not exists
            if 'gallery' not in service:
                service['gallery'] = []
            
            # Add new gallery images (limit to 8 total)
            existing_count = len(service.get('gallery', []))
            remaining_slots = 8 - existing_count
            
            for idx, file in enumerate(files[:remaining_slots]):
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"service_{username}_{service_id}_gallery_{existing_count + idx + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                    file.save(os.path.join(upload_folder, filename))
                    service['gallery'].append(f"static/assets/uploads/{filename}")
        
        save_data(data, username=username)
        flash('Service updated successfully', 'success')
        return redirect(url_for('services.list_services'))
    
    # Load user's skills for the form
    user_skills = data.get('skills', [])
    return render_template('dashboard/edit_service.html', data=data, service=service, user_skills=user_skills)


@services_bp.route('/dashboard/services/delete/<service_id>', methods=['POST'])
@login_required
@disable_in_demo
def delete_service(service_id):
    """Delete service"""
    username = session.get('username')
    data = load_data(username=username)
    services = data.get('services', [])
    
    service = next((s for s in services if s.get('id') == service_id), None)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('services.list_services'))
    
    # Remove service
    data['services'] = [s for s in services if s.get('id') != service_id]
    save_data(data, username=username)
    flash('Service deleted successfully', 'success')
    return redirect(url_for('services.list_services'))


@services_bp.route('/dashboard/services/toggle/<service_id>', methods=['POST'])
@login_required
@disable_in_demo
def toggle_service_status(service_id):
    """Toggle service active status"""
    username = session.get('username')
    data = load_data(username=username)
    services = data.get('services', [])
    
    service = next((s for s in services if s.get('id') == service_id), None)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('services.list_services'))
    
    service['is_active'] = not service.get('is_active', True)
    service['updated_at'] = datetime.now().isoformat()
    save_data(data, username=username)
    
    status = 'activated' if service['is_active'] else 'deactivated'
    flash(f'Service {status} successfully', 'success')
    return redirect(url_for('services.list_services'))


@services_bp.route('/<username>')
def user_services(username):
    """Display user's services (public view)"""
    user_data = load_data(username=username)
    if not user_data:
        return render_template('404.html'), 404
    
    services = [s for s in user_data.get('services', []) if s.get('is_active', True)]
    current_theme = user_data.get('settings', {}).get('theme', 'luxury-gold')
    return render_template('services/list.html', data=user_data, services=services, username=username, current_theme=current_theme)


@services_bp.route('/<username>/<service_id>')
def service_detail(username, service_id):
    """Service detail page (public view)"""
    user_data = load_data(username=username)
    if not user_data:
        return render_template('404.html'), 404
    
    # Convert service_id to int if possible
    try:
        service_id_int = int(service_id)
    except (ValueError, TypeError):
        service_id_int = None
    
    services = user_data.get('services', [])
    # Match by either int or string ID
    service = next((s for s in services if s.get('id') == service_id_int or str(s.get('id')) == str(service_id)), None)
    
    if not service or not service.get('is_active', True):
        return render_template('404.html'), 404
    
    current_theme = user_data.get('settings', {}).get('theme', 'luxury-gold')
    return render_template('services/detail.html', data=user_data, service=service, username=username, current_theme=current_theme)
