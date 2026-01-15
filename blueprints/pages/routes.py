"""
Pages Routes - Public static pages
"""

from datetime import datetime
from flask import render_template, session, redirect, url_for, request, flash, send_file, current_app
from utils.data import load_data
from . import pages_bp


@pages_bp.route('/')
def index():
    """Landing page - shows academy and portfolios"""
    is_logged_in = 'admin_logged_in' in session
    username = session.get('username')
    data = load_data()
    portfolios = data.get('portfolios', {})
    users = data.get('users', [])
    
    # Map verification status
    user_verify_map = {u['username']: u.get('is_verified', False) for u in users}
    for uname, port in portfolios.items():
        port['is_verified'] = user_verify_map.get(uname, False)
    
    return render_template('landing.html',
                           portfolios=portfolios,
                           is_logged_in=is_logged_in,
                           username=username,
                           is_admin=session.get('is_admin', False),
                           data=data)


@pages_bp.route('/landing')
def landing():
    """Alias for index"""
    return redirect(url_for('pages.index'))


@pages_bp.route('/verification')
def verification():
    """Professional Verification Standard page"""
    return render_template('pages/verification.html')


@pages_bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('pages/privacy.html')


@pages_bp.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('pages/terms.html')


@pages_bp.route('/about')
def about():
    """About Academy page"""
    return render_template('pages/about.html')


@pages_bp.route('/mastery')
def mastery():
    """Mastery Guide page"""
    return render_template('pages/mastery.html')


@pages_bp.route('/standards')
def standards():
    """Elite Standards page"""
    return render_template('pages/standards.html')


@pages_bp.route('/security-audit')
def security_audit():
    """Security Audit page"""
    return render_template('pages/security.html')


@pages_bp.route('/catalog')
def catalog():
    """Public portfolios directory"""
    data = load_data()
    portfolios = data.get('portfolios', {})
    users = data.get('users', [])
    
    # Map verification status
    user_status_map = {u['username']: u for u in users}
    classified_portfolios = {}
    
    for username, port in portfolios.items():
        if username == 'admin':
            continue
        
        user_info = user_status_map.get(username, {})
        is_verified = user_info.get('is_verified', False)
        
        # Only show verified in public catalog
        if is_verified or session.get('admin_logged_in'):
            classified_portfolios[username] = port
    
    return render_template('catalog.html', portfolios=classified_portfolios)


@pages_bp.route('/contact/academy', methods=['POST'])
def contact_academy():
    """Public contact form for the Academy - saves to database for admin"""
    from models import Message
    from extensions import db
    from utils.notifications import send_admin_notification
    
    name = request.form.get('name', 'Guest').strip()
    email = request.form.get('email', 'no-email@codexx.academy').strip()
    message_content = request.form.get('message', '').strip()
    
    if not message_content:
        flash('Please enter a message.', 'danger')
        return redirect(url_for('pages.index', _anchor='academy-contact'))
    
    try:
        # Create message in database for admin (no workspace_id means platform-level)
        new_message = Message(
            workspace_id=None,  # Platform-level message for admin
            name=name,
            email=email,
            message=message_content[:5000],
            is_read=False,
            category='platform',
            sender_role='visitor',
            receiver_id='admin'
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        current_app.logger.info(f"Platform message saved to DB, message_id: {new_message.id}")
        
        # Send notification to admin
        send_admin_notification(
            'New Platform Message',
            f"👤 From: {name}\n📧 Email: {email}\n💬 Message:\n{message_content[:300]}{'...' if len(message_content) > 300 else ''}"
        )
        
        flash('Thank you! Your message has been received.', 'success')
    except Exception as e:
        current_app.logger.error(f"Platform contact form error: {str(e)}")
        db.session.rollback()
        flash('Error sending message. Please try again.', 'danger')
    
    return redirect(url_for('pages.index', _anchor='academy-contact'))


@pages_bp.route('/sitemap.xml')
def sitemap():
    """Generate dynamic sitemap for SEO"""
    data = load_data()
    base_url = request.url_root.rstrip('/')

    sitemap_entries = []
    sitemap_entries.append({
        'loc': f'{base_url}/',
        'changefreq': 'weekly',
        'priority': '1.0',
        'lastmod': datetime.now().strftime('%Y-%m-%d')
    })

    for project in data.get('projects', []):
        sitemap_entries.append({
            'loc': f"{base_url}/project/{project['id']}",
            'changefreq': 'monthly',
            'priority': '0.8',
            'lastmod': project.get('created_at', datetime.now().strftime('%Y-%m-%d')).split()[0]
        })

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
    )

    for entry in sitemap_entries:
        sitemap_xml.append('<url>')
        sitemap_xml.append(f'<loc>{entry["loc"]}</loc>')
        sitemap_xml.append(f'<lastmod>{entry["lastmod"]}</lastmod>')
        sitemap_xml.append(f'<changefreq>{entry["changefreq"]}</changefreq>')
        sitemap_xml.append(f'<priority>{entry["priority"]}</priority>')
        sitemap_xml.append('</url>')

    sitemap_xml.append('</urlset>')

    response = current_app.make_response('\n'.join(sitemap_xml))
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response


@pages_bp.route('/robots.txt')
def robots():
    """Generate robots.txt for SEO"""
    robots_txt = """User-agent: *
Allow: /
Allow: /project/
Allow: /cv-preview
Allow: /sitemap.xml
Disallow: /dashboard/
Disallow: /static/
Disallow: /*.json$

Sitemap: """ + request.url_root.rstrip('/') + """/sitemap.xml
User-agent: GPTBot
Disallow: /

User-agent: CCBot
Disallow: /"""

    response = current_app.make_response(robots_txt)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response


@pages_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_file('static/favicon.ico', mimetype='image/x-icon')


@pages_bp.route('/guides/telegram-bot-token')
def guide_bot_token():
    """Guide for getting Telegram Bot Token"""
    return render_template('pages/guide_bot_token.html')


@pages_bp.route('/guides/telegram-chat-id')
def guide_chat_id():
    """Guide for getting Telegram Chat ID"""
    return render_template('pages/guide_chat_id.html')


@pages_bp.route('/documentation')
def documentation():
    """Serve documentation page"""
    import os
    doc_path = os.path.join('Documentation', 'English', 'documentation-english.html')
    if os.path.exists(doc_path):
        return send_file(doc_path)
    else:
        return render_template('404.html'), 404
