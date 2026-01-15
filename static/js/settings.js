// Settings page JavaScript
(function() {
    'use strict';

    // Update theme preview
    function updateThemePreview(themeId) {
        const themeInfo = {
            'luxury-gold': {
                name: 'Luxury Gold',
                icon: 'fas fa-crown',
                color: '#D4AF37',
                secondary: '#8B7355',
                desc: 'Premium & Classic design.'
            },
            'modern-dark': {
                name: 'Modern Dark',
                icon: 'fas fa-zap',
                color: '#00FF88',
                secondary: '#333',
                desc: 'Tech & Trendy design.'
            },
            'clean-light': {
                name: 'Clean Light',
                icon: 'fas fa-sun',
                color: '#4A90E2',
                secondary: '#F5F5F5',
                desc: 'Minimal & Fresh design.'
            },
            'terracotta-red': {
                name: 'Terracotta Red',
                icon: 'fas fa-fire',
                color: '#E07A5F',
                secondary: '#F4A261',
                desc: 'Warm & Modern design.'
            },
            'vibrant-green': {
                name: 'Vibrant Green',
                icon: 'fas fa-leaf',
                color: '#06FFA5',
                secondary: '#2D5A3D',
                desc: 'Natural & Fresh design.'
            },
            'silver-grey': {
                name: 'Silver Grey',
                icon: 'fas fa-gem',
                color: '#C0C0C0',
                secondary: '#808080',
                desc: 'Sophisticated & Modern design.'
            }
        };

        const info = themeInfo[themeId];
        if (!info) return;

        const previewCard = document.querySelector('.theme-preview-card');
        if (previewCard) {
            previewCard.style.background = `linear-gradient(135deg, ${info.color} 0%, ${info.secondary} 100%)`;
            previewCard.style.color = '#fff';
            previewCard.innerHTML = `
                <div class="text-center p-4">
                    <i class="${info.icon} fa-3x mb-3"></i>
                    <h4>${info.name}</h4>
                    <p class="mb-0">${info.desc}</p>
                </div>
            `;
        }
    }

    // Initialize theme preview on page load
    document.addEventListener('DOMContentLoaded', function() {
        const currentThemeRadio = document.querySelector('input[name="theme"]:checked');
        if (currentThemeRadio) {
            updateThemePreview(currentThemeRadio.value);
        }
        loadBackups();
    });

    // Make functions global
    window.updateThemePreview = updateThemePreview;
    window.testEmailConnection = testEmailConnection;
    window.testTelegramConnection = testTelegramConnection;

    // Load backups function
    async function loadBackups() {
        try {
            const response = await fetch('/api/backups');
            const backups = await response.json();
            const tbody = document.getElementById('backupsList');
            const isDemoMode = document.querySelector('.container-fluid').dataset.demoMode === 'true';

            if (backups.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No backups available yet</td></tr>';
                return;
            }

            tbody.innerHTML = backups.map((backup, index) => {
                return '<tr>' +
                    '<td>' +
                        '<small>' + new Date(backup.timestamp).toLocaleString() + '</small>' +
                    '</td>' +
                    '<td>' +
                        '<span class="badge ' + (backup.type === 'manual' ? 'bg-success' : 'bg-info') + '">' +
                            (backup.type === 'manual' ? '📌 Manual' : '⚙️ Auto') +
                        '</span>' +
                    '</td>' +
                    '<td>' + backup.size_kb + '</td>' +
                    '<td>' +
                        '<div class="dropdown d-inline-block">' +
                            '<button class="btn btn-sm btn-outline-light dropdown-toggle" type="button" ' +
                                    'id="backupDropdown' + index + '" data-bs-toggle="dropdown" aria-expanded="false">' +
                                '<i class="fas fa-ellipsis-v"></i>' +
                            '</button>' +
                            '<ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end" aria-labelledby="backupDropdown' + index + '">' +
                                (isDemoMode ?
                                '<li>' +
                                    '<button type="button" class="dropdown-item disabled" disabled title="Demo mode: Restore disabled">' +
                                        '<i class="fas fa-lock me-2 icon-gray"></i><span class="icon-muted">Restore (Demo Disabled)</span>' +
                                    '</button>' +
                                '</li>'
                                :
                                '<li>' +
                                    '<form method="POST" action="/backup/restore/' + backup.filename + '" class="d-inline" ' +
                                          'onsubmit="return confirm(\'Restore this backup? Current data will be backed up first.\')">' +
                                        '<button type="submit" class="dropdown-item btn-reset">' +
                                            '<i class="fas fa-undo me-2 icon-info"></i>Restore' +
                                        '</button>' +
                                    '</form>' +
                                '</li>') +
                                '<li>' +
                                    '<a class="dropdown-item" href="/backup/download/' + backup.filename + '">' +
                                        '<i class="fas fa-download me-2 icon-primary"></i>Download' +
                                    '</a>' +
                                '</li>' +
                                '<li><hr class="dropdown-divider"></li>' +
                                (isDemoMode ?
                                '<li>' +
                                    '<button type="button" class="dropdown-item text-danger disabled" disabled title="Demo mode: Delete disabled">' +
                                        '<i class="fas fa-lock me-2"></i><span class="icon-muted">Delete (Demo Disabled)</span>' +
                                    '</button>' +
                                '</li>'
                                :
                                '<li>' +
                                    '<form method="POST" action="/backup/delete/' + backup.filename + '" class="d-inline" ' +
                                          'onsubmit="return confirm(\'Delete this backup permanently?\')">' +
                                        '<button type="submit" class="dropdown-item text-danger btn-reset">' +
                                            '<i class="fas fa-trash me-2"></i>Delete' +
                                        '</button>' +
                                    '</form>' +
                                '</li>') +
                            '</ul>' +
                        '</div>' +
                    '</td>' +
                '</tr>';
            }).join('');
        } catch (error) {
            console.error('Error loading backups:', error);
        }
    }

    // Test email connection
    async function testEmailConnection() {
        const btn = document.getElementById('testEmailBtn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
        
        try {
            const response = await fetch('/dashboard/email-test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            const data = await response.json();
            
            if (data.success) {
                alert('✅ Test email sent successfully! Check your inbox.');
            } else {
                alert('❌ Failed to send test email: ' + data.error);
            }
        } catch (error) {
            alert('❌ Error: ' + error.message);
        }
        
        btn.disabled = false;
        btn.innerHTML = originalText;
    }

    // Test telegram connection
    async function testTelegramConnection() {
        const btn = document.getElementById('testConnectionBtn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Testing...';
        
        try {
            const response = await fetch('/dashboard/telegram-test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            });
            const data = await response.json();
            
            if (data.success) {
                alert('✅ Connection successful! Check your Telegram for a test message.');
            } else {
                alert('❌ Connection failed: ' + data.error);
            }
        } catch (error) {
            alert('❌ Error: ' + error.message);
        }
        
        btn.disabled = false;
        btn.innerHTML = originalText;
    }

    // Test admin notifications
    window.testAdminNotifications = function() {
        const btn = document.getElementById('testAdminNotificationsBtn');
        const original = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Testing...';

        fetch('/dashboard/admin/test-notifications', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(resp => resp.json())
        .then(data => {
            if (data.success) {
                alert('✅ Test notification sent successfully! Check your Telegram and email for the test message.');
            } else {
                alert('❌ Test failed: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(err => {
            console.error('Test error:', err);
            alert('❌ Connection error. Check console for details.');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = original;
        });
    };

})();