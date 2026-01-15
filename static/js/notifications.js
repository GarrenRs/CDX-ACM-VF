/**
 * Real-time Notifications System
 * Polls for new notifications and updates the UI without page refresh
 */

(function() {
    'use strict';
    
    let notificationInterval = null;
    let lastNotificationCount = 0;
    let lastNotificationIds = [];
    const POLL_INTERVAL = 5000; // 5 seconds for faster updates
    
    /**
     * Fetch and display latest notifications
     */
    function fetchNotifications() {
        fetch('/dashboard/notifications/latest', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(notifications => {
            updateNotificationUI(notifications);
        })
        .catch(error => {
            console.log('Notification fetch error (will retry):', error.message);
        });
    }
    
    /**
     * Update notification UI with latest data
     */
    function updateNotificationUI(notifications) {
        const notificationList = document.getElementById('notificationList');
        const notificationBadge = document.getElementById('notificationBadge') || document.querySelector('.notification-badge');
        const notificationBell = document.getElementById('notificationBell');
        const bellIcon = document.getElementById('bellIcon');
        
        if (!notificationList) return;
        
        const count = notifications.length;
        
        // Check for new notifications by comparing IDs
        const currentIds = notifications.map(n => n.id);
        const newNotifications = currentIds.filter(id => !lastNotificationIds.includes(id));
        const hasNewNotifications = newNotifications.length > 0 && lastNotificationIds.length > 0;
        
        // Update badge count with animation
        if (notificationBadge) {
            if (count > 0) {
                notificationBadge.textContent = count > 99 ? '99+' : count;
                notificationBadge.classList.remove('d-none');
                
                // Add pulse animation for new notifications
                if (hasNewNotifications) {
                    notificationBadge.classList.add('badge-pulse');
                    setTimeout(() => notificationBadge.classList.remove('badge-pulse'), 2000);
                }
            } else {
                notificationBadge.classList.add('d-none');
            }
        }
        
        // Play sound and animate bell for new notifications
        if (hasNewNotifications) {
            playNotificationSound();
            
            // Animate bell icon
            if (bellIcon) {
                bellIcon.classList.add('bell-shake');
                setTimeout(() => bellIcon.classList.remove('bell-shake'), 1000);
            }
            
            // Show browser notification if permitted
            showBrowserNotification(notifications[0]);
        }
        
        // Store current state
        lastNotificationCount = count;
        lastNotificationIds = currentIds;
        
        // Update notification list
        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="p-4 text-center text-muted">
                    <i class="fas fa-check-circle fa-2x mb-2 text-success opacity-50"></i>
                    <p class="small mb-0">All caught up! No new messages.</p>
                </div>
            `;
        } else {
            notificationList.innerHTML = notifications.map(notif => {
                const categoryIcon = getCategoryIcon(notif.category);
                const categoryColor = getCategoryColor(notif.category);
                const viewUrl = getNotificationUrl(notif);
                
                return `
                    <a href="${viewUrl}" class="notification-item d-flex align-items-start p-3 border-bottom border-secondary text-decoration-none">
                        <div class="flex-shrink-0 me-3">
                            <div class="notification-icon-wrapper" style="width: 40px; height: 40px; border-radius: 50%; background: ${categoryColor}20; display: flex; align-items: center; justify-content: center;">
                                <i class="${categoryIcon}" style="color: ${categoryColor};"></i>
                            </div>
                        </div>
                        <div class="flex-grow-1 min-width-0">
                            <div class="d-flex justify-content-between align-items-start mb-1">
                                <h6 class="mb-0 fw-semibold text-white small text-truncate">${escapeHtml(notif.name)}</h6>
                                <span class="badge bg-dark text-muted small ms-2" style="font-size: 0.65rem;">${notif.time}</span>
                            </div>
                            <p class="mb-1 small text-muted text-truncate" style="max-width: 250px;">${escapeHtml(notif.message)}</p>
                            <span class="badge" style="font-size: 0.6rem; background-color: ${categoryColor}30; color: ${categoryColor};">
                                ${notif.category || 'message'}
                            </span>
                        </div>
                    </a>
                `;
            }).join('');
        }
    }
    
    /**
     * Show browser notification (if permitted)
     */
    function showBrowserNotification(notif) {
        if (!('Notification' in window)) return;
        
        if (Notification.permission === 'granted') {
            new Notification('New Message', {
                body: `${notif.name}: ${notif.message}`,
                icon: '/static/logo/logo.png',
                tag: 'codexx-notification'
            });
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission();
        }
    }
    
    /**
     * Get icon for notification category
     */
    function getCategoryIcon(category) {
        const icons = {
            'portfolio': 'fas fa-briefcase',
            'internal': 'fas fa-comments',
            'platform': 'fas fa-bell',
            'system': 'fas fa-cog'
        };
        return icons[category] || 'fas fa-envelope';
    }
    
    /**
     * Get color for notification category
     */
    function getCategoryColor(category) {
        const colors = {
            'portfolio': '#D4AF37',
            'internal': '#17a2b8',
            'platform': '#6c757d',
            'system': '#ffc107'
        };
        return colors[category] || '#6c757d';
    }
    
    /**
     * Get URL for notification based on category
     * Internal messages go to internal_view, inbox messages go to view_message
     */
    function getNotificationUrl(notif) {
        if (notif.category === 'internal') {
            // Internal messages - go to internal thread view
            return `/dashboard/messages/internal/view/${notif.id}`;
        } else if (notif.category === 'portfolio' || notif.category === 'platform') {
            // Inbox messages - go to message view
            return `/dashboard/messages/view/${notif.id}`;
        } else {
            // Fallback to inbox
            return `/dashboard/messages/view/${notif.id}`;
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Play notification sound
     */
    function playNotificationSound() {
        try {
            // Create a simple beep sound using Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (error) {
            console.log('Could not play notification sound:', error);
        }
    }
    
    /**
     * Start polling for notifications
     */
    function startNotificationPolling() {
        // Clear any existing interval
        if (notificationInterval) {
            clearInterval(notificationInterval);
        }
        
        // Fetch immediately
        fetchNotifications();
        
        // Then poll at the defined interval (5 seconds)
        notificationInterval = setInterval(fetchNotifications, POLL_INTERVAL);
        console.log('Notification polling started (every ' + (POLL_INTERVAL/1000) + 's)');
    }
    
    /**
     * Stop polling for notifications
     */
    function stopNotificationPolling() {
        if (notificationInterval) {
            clearInterval(notificationInterval);
            notificationInterval = null;
            console.log('Notification polling stopped');
        }
    }
    
    /**
     * Initialize notification system
     */
    function initNotifications() {
        // Start polling when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startNotificationPolling);
        } else {
            startNotificationPolling();
        }
        
        // Stop polling when page is hidden (battery saving)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopNotificationPolling();
            } else {
                // Resume polling and fetch immediately
                startNotificationPolling();
            }
        });
        
        // Refresh notifications when dropdown is opened
        const notificationDropdown = document.getElementById('notificationDropdown');
        if (notificationDropdown) {
            notificationDropdown.addEventListener('show.bs.dropdown', function() {
                fetchNotifications();
            });
        }
        
        // Also listen for clicks on the bell button
        const notificationBell = document.getElementById('notificationBell');
        if (notificationBell) {
            notificationBell.addEventListener('click', function() {
                fetchNotifications();
            });
        }
    }
    
    // Initialize
    initNotifications();
    
    // Expose to global scope for manual refresh
    window.refreshNotifications = fetchNotifications;
    window.startNotificationPolling = startNotificationPolling;
    window.stopNotificationPolling = stopNotificationPolling;
})();
