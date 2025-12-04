/**
 * AUBS AI Assistant v3.9.0
 * Now fetches FULL email bodies via backend API
 */

(function() {
    'use strict';

    let config = {
        endpoint: 'http://host.docker.internal:11434',
        model: 'gpt-oss:120b-cloud',
        domains: 'brinker.com,chilis.com,hotshedules.co'
    };

    // Load config from backend
    function loadConfig() {
        return rl.pluginRemoteRequest((result) => {
            if (result && result.Result) {
                config = result.Result;
                console.log('[AUBS] Config loaded:', config);
            }
        }, 'AubsGetConfig', {});
    }

    // Get work emails from message list (metadata only)
    function getWorkEmailMeta() {
        const messages = rl.app.messageList();
        if (!messages || !messages.length) {
            console.log('[AUBS] No messages found');
            return [];
        }

        const domains = config.domains.toLowerCase().split(',').map(d => d.trim());
        const workEmails = [];

        messages.forEach(msg => {
            // Get actual email address
            let emailAddr = '';
            if (typeof msg.senderClearEmailsString === 'function') {
                emailAddr = msg.senderClearEmailsString();
            } else if (msg.senderClearEmailsString) {
                emailAddr = msg.senderClearEmailsString;
            }

            const emailLower = emailAddr.toLowerCase();
            const isWork = domains.some(d => emailLower.includes(d));

            if (isWork) {
                // Get UID for fetching full body later
                let uid = typeof msg.uid === 'function' ? msg.uid() : msg.uid;
                let folder = typeof msg.folder === 'function' ? msg.folder() : msg.folder;
                let fromName = typeof msg.senderEmailsString === 'function' ? msg.senderEmailsString() : msg.senderEmailsString || '';
                let subject = typeof msg.subject === 'function' ? msg.subject() : msg.subject || '';
                let date = typeof msg.dateTimestamp === 'function' ? msg.dateTimestamp() : msg.dateTimestamp || 0;

                workEmails.push({
                    uid: uid,
                    folder: folder || 'INBOX',
                    from: fromName,
                    email: emailAddr,
                    subject: subject,
                    date: new Date(date * 1000).toLocaleString()
                });
            }
        });

        console.log(`[AUBS] Found ${workEmails.length} work emails (metadata)`);
        return workEmails;
    }

    // Fetch full message bodies from backend
    function fetchFullBodies(emails, callback) {
        if (!emails || emails.length === 0) {
            callback([]);
            return;
        }

        // Group by folder
        const byFolder = {};
        emails.forEach(e => {
            const folder = e.folder || 'INBOX';
            if (!byFolder[folder]) byFolder[folder] = [];
            byFolder[folder].push(e);
        });

        const allMessages = [];
        const folders = Object.keys(byFolder);
        let completed = 0;

        folders.forEach(folder => {
            const uids = byFolder[folder].map(e => e.uid);
            
            rl.pluginRemoteRequest((result) => {
                console.log(`[AUBS] Fetch result for ${folder}:`, result);
                
                if (result && result.Result && result.Result.messages) {
                    // Merge full body data with metadata
                    result.Result.messages.forEach(msg => {
                        const meta = byFolder[folder].find(e => e.uid == msg.uid);
                        if (meta) {
                            allMessages.push({
                                ...meta,
                                body: msg.body || '(No body)',
                                hasFullBody: msg.hasBody
                            });
                        }
                    });
                }
                
                completed++;
                if (completed === folders.length) {
                    console.log(`[AUBS] Fetched ${allMessages.length} full messages`);
                    callback(allMessages);
                }
            }, 'AubsFetchMessages', { uids: uids, folder: folder });
        });
    }

    // Run daily digest with FULL email bodies
    function runDigest() {
        const workMeta = getWorkEmailMeta();
        
        if (workMeta.length === 0) {
            showModal('📭 No Work Emails', 'No emails from work domains found in current view.');
            return;
        }

        showModal(`🌶️ AUBS Digest`, 
            `<div style="text-align:center;padding:40px;">
                <div style="font-size:32px;margin-bottom:15px;">📨</div>
                <div>Fetching ${workMeta.length} work emails...</div>
                <div style="font-size:12px;color:#888;margin-top:10px;">Getting full message bodies</div>
            </div>`
        );

        // Fetch full bodies
        fetchFullBodies(workMeta, (fullEmails) => {
            if (fullEmails.length === 0) {
                showModal('❌ Fetch Failed', 'Could not retrieve email bodies. Check console for errors.');
                return;
            }

            showModal(`🌶️ AUBS Digest (${fullEmails.length} work emails)`, 
                `<div style="text-align:center;padding:40px;">
                    <div style="font-size:32px;margin-bottom:15px;">⏳</div>
                    <div>Analyzing with ${config.model}...</div>
                    <div style="font-size:12px;color:#888;margin-top:10px;">This may take 30-60 seconds</div>
                </div>`
            );

            // Build email summary for AI - now with FULL BODIES
            let emailText = `DAILY EMAIL DIGEST - ${new Date().toLocaleDateString()}\n`;
            emailText += `Restaurant: Chili's #605 Auburn Hills\n`;
            emailText += `Total work emails: ${fullEmails.length}\n\n`;
            emailText += `---\n\n`;

            fullEmails.forEach((email, i) => {
                emailText += `EMAIL ${i + 1}:\n`;
                emailText += `From: ${email.from} <${email.email}>\n`;
                emailText += `Subject: ${email.subject}\n`;
                emailText += `Date: ${email.date}\n`;
                emailText += `\n--- FULL EMAIL BODY ---\n`;
                emailText += `${email.body}\n`;
                emailText += `--- END EMAIL ${i + 1} ---\n\n`;
            });

            emailText += `\nPlease analyze these emails and provide your daily operations brief.`;

            console.log('[AUBS] Sending to AI (first 2000 chars):', emailText.substring(0, 2000));

            rl.pluginRemoteRequest((result) => {
                console.log('[AUBS] AI Response:', result);
                
                if (result && result.Result) {
                    const r = result.Result;
                    if (r.success && r.response) {
                        showModal(`🌶️ AUBS Digest (${fullEmails.length} work emails)`, formatResponse(r.response));
                    } else if (r.response) {
                        showModal(`❌ AI Error`, `<div style="color:#c00;white-space:pre-wrap;">${r.response}</div>`);
                    } else if (r.error) {
                        showModal(`❌ Error`, r.error);
                    }
                } else {
                    showModal(`❌ Request Failed`, 'No response from plugin.');
                }
            }, 'AubsAnalyze', { email: emailText, action: 'analyze' });
        });
    }

    // Format AI response
    function formatResponse(text) {
        if (!text) return '<em>No response</em>';
        
        let html = text
            .replace(/^### (.+)$/gm, '<h4 style="color:#c41230;margin:15px 0 8px;">$1</h4>')
            .replace(/^## (.+)$/gm, '<h3 style="color:#c41230;margin:18px 0 10px;">$1</h3>')
            .replace(/^# (.+)$/gm, '<h2 style="color:#c41230;margin:20px 0 12px;">$1</h2>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/^- (.+)$/gm, '<li style="margin:4px 0;">$1</li>')
            .replace(/^• (.+)$/gm, '<li style="margin:4px 0;">$1</li>')
            .replace(/^\* (.+)$/gm, '<li style="margin:4px 0;">$1</li>')
            .replace(/^\d+\. (.+)$/gm, '<li style="margin:4px 0;">$1</li>')
            .replace(/\n\n/g, '</p><p style="margin:10px 0;">')
            .replace(/\n/g, '<br>');

        html = '<p style="margin:10px 0;">' + html + '</p>';
        html = html.replace(/(<li[^>]*>.*?<\/li>)+/g, '<ul style="margin:8px 0;padding-left:20px;">$&</ul>');

        return html;
    }

    // Show modal
    function showModal(title, content) {
        const existing = document.getElementById('aubs-modal');
        if (existing) existing.remove();

        const modal = document.createElement('div');
        modal.id = 'aubs-modal';
        modal.innerHTML = `
            <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:99998;"></div>
            <div style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:white;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.3);z-index:99999;min-width:400px;max-width:850px;max-height:85vh;display:flex;flex-direction:column;">
                <div style="background:linear-gradient(135deg,#c41230,#8b0000);color:white;padding:15px 20px;border-radius:12px 12px 0 0;display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-weight:600;font-size:16px;">${title}</span>
                    <button id="aubs-close" style="background:none;border:none;color:white;font-size:24px;cursor:pointer;padding:0 5px;">&times;</button>
                </div>
                <div style="padding:20px;overflow-y:auto;flex:1;font-size:14px;line-height:1.6;">${content}</div>
            </div>
        `;

        document.body.appendChild(modal);
        document.getElementById('aubs-close').onclick = () => modal.remove();
        modal.querySelector('div').onclick = (e) => { if (e.target === modal.querySelector('div')) modal.remove(); };
    }

    // Show menu
    function showMenu() {
        const existing = document.getElementById('aubs-menu');
        if (existing) { existing.remove(); return; }

        const menu = document.createElement('div');
        menu.id = 'aubs-menu';
        menu.innerHTML = `
            <div style="position:fixed;bottom:90px;right:20px;background:white;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.25);z-index:99997;padding:10px;min-width:220px;">
                <div style="padding:8px 12px;font-weight:600;color:#c41230;border-bottom:1px solid #eee;margin-bottom:8px;">🌶️ AUBS AI Assistant</div>
                <button id="aubs-digest" style="display:block;width:100%;padding:12px 15px;border:none;background:#f8f8f8;border-radius:8px;cursor:pointer;text-align:left;margin-bottom:6px;font-size:14px;">📊 Daily Digest (Full Bodies)</button>
                <button id="aubs-test" style="display:block;width:100%;padding:12px 15px;border:none;background:#f8f8f8;border-radius:8px;cursor:pointer;text-align:left;margin-bottom:6px;font-size:14px;">🔌 Test Connection</button>
                <button id="aubs-debug" style="display:block;width:100%;padding:12px 15px;border:none;background:#f8f8f8;border-radius:8px;cursor:pointer;text-align:left;font-size:14px;">🔍 Debug Info</button>
                <div style="padding:10px 12px;font-size:11px;color:#888;border-top:1px solid #eee;margin-top:8px;">
                    <div>Model: ${config.model}</div>
                    <div>Domains: ${config.domains}</div>
                </div>
            </div>
        `;

        document.body.appendChild(menu);

        document.getElementById('aubs-digest').onclick = () => { menu.remove(); runDigest(); };
        document.getElementById('aubs-test').onclick = () => { menu.remove(); testConnection(); };
        document.getElementById('aubs-debug').onclick = () => { menu.remove(); debugEmails(); };

        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target) && e.target.id !== 'aubs-button') {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 100);
    }

    // Test connection
    function testConnection() {
        showModal('🔌 Testing...', 'Checking Ollama endpoint...');
        
        rl.pluginRemoteRequest((result) => {
            if (result && result.Result) {
                const r = result.Result;
                if (r.success) {
                    showModal('✅ Connection OK', 
                        `<b>Endpoint:</b> ${r.endpoint}<br><b>Models:</b> ${r.modelCount}`
                    );
                } else {
                    showModal('❌ Failed', `<b>Error:</b> ${r.error}`);
                }
            }
        }, 'AubsTestConnection', {});
    }

    // Debug
    function debugEmails() {
        const workMeta = getWorkEmailMeta();
        
        let html = `<div style="font-family:monospace;font-size:12px;">`;
        html += `<b>Work emails found:</b> ${workMeta.length}<br>`;
        html += `<b>Domains:</b> ${config.domains}<br><br>`;
        
        if (workMeta.length > 0) {
            html += `<b>First 5:</b><br>`;
            workMeta.slice(0, 5).forEach((e, i) => {
                html += `<div style="background:#f5f5f5;padding:8px;margin:5px 0;border-radius:4px;">`;
                html += `${i+1}. <b>${e.subject}</b><br>`;
                html += `From: ${e.email}<br>`;
                html += `UID: ${e.uid} | Folder: ${e.folder}`;
                html += `</div>`;
            });
        }
        
        html += `</div>`;
        showModal('🔍 Debug Info', html);
    }

    // Create button
    function createButton() {
        if (document.getElementById('aubs-button')) return;

        const btn = document.createElement('button');
        btn.id = 'aubs-button';
        btn.innerHTML = '🌶️';
        btn.title = 'AUBS AI Assistant';
        btn.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #c41230, #8b0000);
            color: white;
            font-size: 28px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(196, 18, 48, 0.4);
            z-index: 99996;
        `;
        
        btn.onclick = showMenu;
        document.body.appendChild(btn);
        console.log('[AUBS] Button created v3.9.0 (full body fetch)');
    }

    // Init
    function init() {
        console.log('[AUBS] Initializing v3.9.0...');
        loadConfig();
        
        if (document.readyState === 'complete') {
            createButton();
        } else {
            window.addEventListener('load', createButton);
        }
        setTimeout(createButton, 2000);
    }

    init();
})();
