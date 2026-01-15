/**
 * Portfolio Admin Dashboard JavaScript
 * © 2025 All rights reserved
 * Optimized for production use
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {

    // ==========================================
    // PORTFOLIO DARK MODE ONLY (Theme Toggle Disabled)
    // ==========================================
    // Portfolio pages now use dark mode exclusively
    // Theme toggle functionality has been removed for consistency

    // ==========================================
    // NAVBAR SCROLL EFFECT
    // ==========================================

    const navbar = document.getElementById('mainNav');

    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // ==========================================
    // SMOOTH SCROLLING FOR NAVIGATION LINKS
    // ==========================================

    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            if (href.startsWith('#')) {
                e.preventDefault();
                const targetId = href.substring(1);
                const targetSection = document.getElementById(targetId);

                if (targetSection) {
                    const offsetTop = targetSection.offsetTop - 80;

                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });

                    // Close mobile menu if open
                    const navbarCollapse = document.querySelector('.navbar-collapse');
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                        toggle: false
                    });
                    bsCollapse.hide();
                }
            }
        });
    });

    // ==========================================
    // ACTIVE NAVIGATION HIGHLIGHTING
    // ==========================================

    const sections = document.querySelectorAll('section[id]');

    function highlightActiveNav() {
        const scrollPosition = window.scrollY + 100;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            const navLink = document.querySelector(`.navbar-nav .nav-link[href="#${sectionId}"]`);

            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                navLinks.forEach(link => link.classList.remove('active'));
                if (navLink) {
                    navLink.classList.add('active');
                }
            }
        });
    }

    window.addEventListener('scroll', highlightActiveNav);

    // ==========================================
    // SKILLS PROGRESS ANIMATION
    // ==========================================

    const skillsSection = document.getElementById('skills');
    const progressBars = document.querySelectorAll('.progress-bar');
    let skillsAnimated = false;

    function animateSkills() {
        if (!skillsAnimated) {
            progressBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';

                setTimeout(() => {
                    bar.style.width = width;
                }, 200);
            });
            skillsAnimated = true;
        }
    }

    // Intersection Observer for skills animation
    const skillsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateSkills();
            }
        });
    }, { threshold: 0.5 });

    if (skillsSection) {
        skillsObserver.observe(skillsSection);
    }

    // ==========================================
    // SCROLL ANIMATIONS
    // ==========================================

    const animateElements = document.querySelectorAll('.project-card, .skill-item, .contact-item');

    const scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    animateElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        scrollObserver.observe(element);
    });

    // ==========================================
    // CONTACT FORM HANDLING
    // ==========================================

    const contactForm = document.querySelector('#contact form');

    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;

            // Show loading state
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
            submitBtn.disabled = true;

            // Note: Form will be handled by Formspree
            // Reset button after a delay if not redirected
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 3000);
        });
    }

    // ==========================================
    // TYPING ANIMATION FOR HERO SECTION
    // ==========================================

    const heroTitle = document.querySelector('.hero-title');

    if (heroTitle) {
        const originalText = heroTitle.textContent;
        heroTitle.textContent = '';

        let i = 0;
        function typeWriter() {
            if (i < originalText.length) {
                heroTitle.textContent += originalText.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            }
        }

        // Start typing animation after page load
        setTimeout(typeWriter, 1000);
    }

    // ==========================================
    // PARTICLE BACKGROUND EFFECT
    // ==========================================

    function createParticles() {
        const heroSection = document.querySelector('.hero-section');
        if (!heroSection) return;

        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.cssText = `
                position: absolute;
                width: 2px;
                height: 2px;
                background: var(--primary-color);
                opacity: 0.3;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation: float ${3 + Math.random() * 4}s ease-in-out infinite;
            `;
            heroSection.appendChild(particle);
        }
    }

    // Create particles on load
    createParticles();

    // ==========================================
    // SCROLL TO TOP BUTTON
    // ==========================================

    const scrollTopBtn = document.createElement('button');
    scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    scrollTopBtn.className = 'scroll-top-btn';
    scrollTopBtn.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: var(--primary-color);
        color: white;
        border: none;
        box-shadow: var(--shadow);
        display: none;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 1000;
    `;

    document.body.appendChild(scrollTopBtn);

    // Show/hide scroll to top button
    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            scrollTopBtn.style.display = 'flex';
        } else {
            scrollTopBtn.style.display = 'none';
        }
    });

    // Scroll to top functionality
    scrollTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // ==========================================
    // PRELOADER
    // ==========================================

    const preloader = document.createElement('div');
    preloader.innerHTML = `
        <div class="preloader-content">
            <div class="spinner"></div>
            <p>Loading...</p>
        </div>
    `;
    preloader.className = 'preloader';
    preloader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: var(--bg-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        transition: opacity 0.5s ease;
    `;

    const style = document.createElement('style');
    style.textContent = `
        .preloader-content {
            text-align: center;
            color: var(--text-primary);
        }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--border-color);
            border-top: 4px solid var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;

    document.head.appendChild(style);
    document.body.prepend(preloader);

    // Hide preloader when page is loaded
    window.addEventListener('load', function() {
        setTimeout(() => {
            preloader.style.opacity = '0';
            setTimeout(() => {
                preloader.remove();
            }, 500);
        }, 1000);
    });

    // ==========================================
    // PERFORMANCE OPTIMIZATIONS
    // ==========================================

    // Lazy loading for images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Throttle scroll events
    let ticking = false;

    function updateOnScroll() {
        highlightActiveNav();
        ticking = false;
    }

    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateOnScroll);
            ticking = true;
        }
    });

    console.log('Portfolio Template Loaded Successfully! 🚀');
});
// ==========================================
// PORTFOLIO OWNER EXTRACTION FOR CONTACT FORM
// ==========================================

// Set portfolio owner hidden field based on current URL
const ownerInput = document.getElementById('portfolio_owner');
if (ownerInput) {
    // Extract username from current URL if it's a portfolio page
    const pathMatch = window.location.pathname.match(/\/portfolio\/([a-zA-Z0-9_-]+)/);
    if (pathMatch) {
        ownerInput.value = pathMatch[1];
    }
    // Otherwise leave empty - backend will use referrer as fallback
}
