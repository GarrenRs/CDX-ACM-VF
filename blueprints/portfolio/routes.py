"""
Portfolio Routes - Public portfolio views
Handles: Portfolio display, project details, CV, contact forms
"""

import io
from datetime import datetime
from flask import render_template, session, redirect, url_for, request, flash, jsonify, send_file, current_app
from utils.data import load_data, save_data
from utils.helpers import track_visitor
from utils.decorators import disable_in_demo
from utils.security import check_rate_limit
from utils.notifications import send_telegram_notification
from . import portfolio_bp


@portfolio_bp.route('/portfolio/<username>')
def user_portfolio(username):
    """Public view of user portfolio"""
    user_data = load_data(username=username)
    all_data = load_data()
    users = all_data.get('users', [])
    
    user_entry = next((u for u in users if u['username'] == username), None)
    if not user_entry and username != 'admin':
        return render_template('404.html'), 404
    
    if user_entry:
        user_data['is_verified'] = user_entry.get('is_verified', False)
        user_data['username'] = username
    
    # Redirect admin users to home
    is_admin_user = (user_entry and user_entry.get('role') == 'admin') or username == 'admin'
    if is_admin_user:
        return redirect(url_for('pages.index'))
    
    track_visitor(username=username)
    current_theme = user_data.get('settings', {}).get('theme', 'luxury-gold')
    
    return render_template('index.html',
                           data=user_data,
                           is_public=True,
                           current_theme=current_theme)


@portfolio_bp.route('/portfolio/<username>/project/<project_id>')
def project_detail(username, project_id):
    """Project detail page"""
    user_data = load_data(username=username)
    if not user_data:
        return render_template('404.html'), 404

    # Convert project_id to int if possible for matching
    try:
        project_id_int = int(project_id)
    except (ValueError, TypeError):
        project_id_int = None
    
    # Find project by ID (match both int and string)
    project = next(
        (p for p in user_data.get('projects', []) 
         if p.get('id') == project_id_int or str(p.get('id')) == str(project_id)),
        None)

    if not project:
        return render_template('404.html'), 404

    # Get current theme
    current_theme = user_data.get('settings', {}).get('theme', 'luxury-gold')

    return render_template('project_detail.html',
                           project=project,
                           data=user_data,
                           current_theme=current_theme)


@portfolio_bp.route('/cv-preview')
@disable_in_demo
def cv_preview():
    """CV preview page with PDF generation capability hints"""
    username = session.get('username', 'admin')
    data = load_data(username=username)

    pdf_methods = {
        'weasy_available': False,
        'weasy_error': None,
        'wkhtml_available': False,
        'wkhtml_path': None
    }

    # Check WeasyPrint availability
    try:
        import weasyprint  # noqa: F401
        pdf_methods['weasy_available'] = True
    except ImportError as ie:
        pdf_methods['weasy_error'] = str(ie)
    except OSError as oe:
        # Runtime dependency missing (e.g., GTK on Windows)
        pdf_methods['weasy_error'] = str(oe)

    # Check wkhtmltopdf availability (for pdfkit fallback)
    try:
        import pdfkit  # noqa: F401
        import shutil
        wk = shutil.which('wkhtmltopdf')
        if wk:
            pdf_methods['wkhtml_available'] = True
            pdf_methods['wkhtml_path'] = wk
    except Exception:
        pass

    current_theme = data.get('settings', {}).get('theme', 'luxury-gold')
    services = [s for s in data.get('services', []) if s.get('is_active', True)]
    return render_template('cv_preview.html', data=data, pdf_methods=pdf_methods, current_theme=current_theme, services=services)


@portfolio_bp.route('/download-cv')
@disable_in_demo
def download_cv():
    """Download CV as PDF with graceful fallbacks and clear error messages."""
    username = session.get('username', 'admin')
    data = load_data(username=username)
    html_content = render_template('cv_preview.html', data=data, pdf_mode=True)

    # Try WeasyPrint first (recommended), but handle platform-specific dependency errors gracefully.
    try:
        import weasyprint
        pdf_buffer = io.BytesIO()
        html = weasyprint.HTML(string=html_content, base_url=request.url_root)
        html.write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        filename = data.get("name", "CV").replace(' ', '_')
        return send_file(pdf_buffer,
                         mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'{filename}_CV.pdf')

    except ImportError as ie:
        # weasyprint not installed - try fallback to wkhtmltopdf/pdfkit
        current_app.logger.warning('WeasyPrint not installed: %s', str(ie))
    except OSError as ose:
        # Often on Windows a missing libgobject or other GTK runtime raises OSError from ctypes
        msg = str(ose)
        current_app.logger.error('WeasyPrint runtime error: %s', msg)
        if 'libgobject-2.0-0' in msg or 'libgobject' in msg:
            # Provide actionable guidance for Windows users
            flash('PDF generation failed: missing GTK runtime (libgobject). On Windows install the MSYS2 GTK runtime (see https://weasyprint.readthedocs.io/en/latest/install.html#windows) or install wkhtmltopdf and python-pdfkit as an alternative (https://wkhtmltopdf.org/downloads.html).', 'error')
            return redirect(url_for('portfolio.cv_preview'))
        # Otherwise, continue to fallback
    except Exception as e:
        current_app.logger.error('WeasyPrint unexpected error: %s', str(e))
        # continue to fallback

    # Fallback: try pdfkit (wkhtmltopdf) if available
    try:
        import pdfkit
        import shutil
        wkhtml_path = shutil.which('wkhtmltopdf')
        config = None
        if wkhtml_path:
            config = pdfkit.configuration(wkhtml=wkhtml_path)
        # Generate PDF bytes
        pdf_bytes = pdfkit.from_string(html_content, False, configuration=config)
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)

        filename = data.get("name", "CV").replace(' ', '_')
        return send_file(pdf_buffer,
                         mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'{filename}_CV.pdf')

    except ImportError:
        current_app.logger.warning('pdfkit not installed; no fallback available')
        flash('PDF generation library not available. Please install WeasyPrint (and its GTK runtime on Windows) or install wkhtmltopdf and python-pdfkit as an alternative.', 'error')
        return redirect(url_for('portfolio.cv_preview'))
    except OSError as ose:
        current_app.logger.error('wkhtmltopdf not found or failed: %s', str(ose))
        flash('wkhtmltopdf not found. Install wkhtmltopdf and ensure it is on the PATH, or install WeasyPrint with GTK runtime on Windows.', 'error')
        return redirect(url_for('portfolio.cv_preview'))
    except Exception as e:
        current_app.logger.error('PDF fallback error: %s', str(e))
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('portfolio.cv_preview'))


@portfolio_bp.route('/contact', methods=['POST'])
def contact():
    """Portfolio contact form processing - saves directly to database"""
    try:
        from models import Message, Workspace
        from extensions import db
        
        # Honeypot spam protection
        if request.form.get('website'):
            return jsonify({'success': True})

        if not check_rate_limit('portfolio_contact'):
            flash('Too many requests.', 'danger')
            return redirect(request.referrer or url_for('pages.index'))

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message_content = request.form.get('message', '').strip()
        portfolio_owner = request.form.get('portfolio_owner', '').strip()
        
        # Additional portfolio form fields
        request_type = request.form.get('request_type', '').strip()
        interest_area = request.form.get('interest_area', '').strip()
        seriousness = request.form.get('seriousness', '').strip()
        contact_pref = request.form.get('contact_pref', '').strip()
        company = request.form.get('company', '').strip()
        
        if not all([name, email, message_content, portfolio_owner]):
            flash('Required fields missing.', 'danger')
            return redirect(request.referrer or url_for('pages.index'))

        # Get portfolio owner's workspace
        workspace = Workspace.query.filter_by(slug=portfolio_owner).first()
        if not workspace:
            current_app.logger.error(f"Workspace not found for user: {portfolio_owner}")
            flash('Error sending message. Please try again.', 'danger')
            return redirect(request.referrer or url_for('pages.index'))

        # Create message in database with all form fields
        new_message = Message(
            workspace_id=workspace.id,
            name=name,
            email=email,
            message=message_content[:5000],
            is_read=False,
            category='portfolio',
            sender_role='visitor',
            request_type=request_type or None,
            interest_area=interest_area or None,
            seriousness=seriousness or None,
            contact_pref=contact_pref or None,
            company=company or None
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        current_app.logger.info(f"Portfolio message saved to DB for {portfolio_owner}, message_id: {new_message.id}")

        # Send notification to portfolio owner via Telegram
        send_telegram_notification(
            f"📧 <b>New Portfolio Message</b>\n\n"
            f"👤 <b>From:</b> {name}\n"
            f"📧 <b>Email:</b> {email}\n"
            f"💬 <b>Message:</b>\n{message_content[:200]}{'...' if len(message_content) > 200 else ''}",
            username=portfolio_owner)

        flash('Message sent successfully! We will get back to you soon.', 'success')
        return redirect(request.referrer or url_for('pages.index'))

    except Exception as e:
        current_app.logger.error(f"Contact form error: {str(e)}")
        db.session.rollback()
        flash('Error sending message. Please try again.', 'danger')
        return redirect(request.referrer or url_for('pages.index'))
