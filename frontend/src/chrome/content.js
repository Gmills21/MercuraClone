/**
 * Phase 4: Chrome Overlay Content Script
 * Injects "Quick Quote" button into Gmail/Outlook email views
 * 
 * Strategy: Lightweight overlay that lives where sales reps already work
 * vs. Mercura's heavy enterprise integration requiring IT permission
 */

(function() {
    'use strict';

    const API_BASE = 'http://localhost:8000';
    const TEST_USER_ID = '3d4df718-47c3-4903-b09e-711090412204';

    // Detect email provider
    const isGmail = window.location.hostname.includes('mail.google.com');
    const isOutlook = window.location.hostname.includes('outlook.');

    if (!isGmail && !isOutlook) {
        return; // Not an email provider we support
    }

    // Create Extract RFQ button
    function createExtractRFQButton() {
        const button = document.createElement('button');
        button.id = 'mercura-extract-rfq-btn';
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
            </svg>
            <span>Extract RFQ</span>
        `;
        button.className = 'mercura-extract-rfq-button';
        button.title = 'Extract RFQ from this email and send to Gemini service';

        button.addEventListener('click', handleExtractRFQ);

        return button;
    }

    // Extract email body text
    function extractEmailBody() {
        if (isGmail) {
            // Gmail structure
            const emailBody = document.querySelector('[role="main"] [data-message-id] .a3s, [role="main"] .ii.gt');
            return emailBody ? emailBody.innerText : '';
        } else if (isOutlook) {
            // Outlook structure
            const emailBody = document.querySelector('[role="main"] ._rp_1, [role="main"] ._rp_1b');
            return emailBody ? emailBody.innerText : '';
        }
        return '';
    }

    // Extract email metadata
    function extractEmailMetadata() {
        let subject = '';
        let sender = '';
        
        if (isGmail) {
            const subjectEl = document.querySelector('[role="main"] h2[data-thread-perm-id]');
            const senderEl = document.querySelector('[role="main"] [email]');
            subject = subjectEl ? subjectEl.textContent : '';
            sender = senderEl ? senderEl.getAttribute('email') : '';
        } else if (isOutlook) {
            const subjectEl = document.querySelector('[role="main"] [aria-label*="Subject"]');
            const senderEl = document.querySelector('[role="main"] [aria-label*="From"]');
            subject = subjectEl ? subjectEl.textContent : '';
            sender = senderEl ? senderEl.textContent : '';
        }
        
        return { subject, sender };
    }

    // Handle Quick Quote button click
    async function handleQuickQuote() {
        const button = document.getElementById('mercura-quick-quote-btn');
        if (!button) return;

        // Show loading state
        button.disabled = true;
        button.innerHTML = '<span>Processing...</span>';

        try {
            const emailBody = extractEmailBody();
            const metadata = extractEmailMetadata();

            if (!emailBody || emailBody.trim().length < 10) {
                alert('Could not extract email content. Please ensure you are viewing an email.');
                button.disabled = false;
                button.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        <path d="M13 8H7M17 12H7"/>
                    </svg>
                    <span>Quick Quote</span>
                `;
                return;
            }

            // Send to Gemini service for extraction
            const response = await fetch(`${API_BASE}/gemini/extract-rfq`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': TEST_USER_ID,
                },
                body: JSON.stringify({
                    email_body: emailBody,
                    metadata: metadata
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            // Show success message and open popup with summary
            if (result.extracted_data) {
                // Store extracted data for popup
                chrome.storage.local.set({
                    'extracted_rfq': result.extracted_data,
                    'extraction_timestamp': Date.now()
                });

                // Open popup with summary
                chrome.action.openPopup();
            } else {
                alert('RFQ extraction failed. Please try again.');
            }

        } catch (error) {
            console.error('Quick Quote error:', error);
            alert('Failed to extract quote. Please try again or use the web interface.');
        } finally {
            button.disabled = false;
            button.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    <path d="M13 8H7M17 12H7"/>
                </svg>
                <span>Quick Quote</span>
            `;
        }
    }

    // Inject button into email view
    function injectButton() {
        // Remove existing button if present
        const existing = document.getElementById('mercura-quick-quote-btn');
        if (existing) {
            existing.remove();
        }

        let targetContainer = null;

        if (isGmail) {
            // Gmail: Find the email action bar
            targetContainer = document.querySelector('[role="main"] .T-I.J-J5-Ji.nu.T-I-ax7.L3');
            if (!targetContainer) {
                // Fallback to toolbar area
                targetContainer = document.querySelector('[role="main"] .bAp.b8.UC');
            }
        } else if (isOutlook) {
            // Outlook: Find the email action bar
            targetContainer = document.querySelector('[role="main"] .ms-CommandBar');
            if (!targetContainer) {
                targetContainer = document.querySelector('[role="main"] ._rp_1');
            }
        }

        if (targetContainer) {
            const button = createExtractRFQButton();
            
            // Insert button
            if (isGmail) {
                targetContainer.parentElement?.insertBefore(button, targetContainer.nextSibling);
            } else {
                targetContainer.insertBefore(button, targetContainer.firstChild);
            }
        }
    }

    // Observe DOM changes to inject button when email view loads
    const observer = new MutationObserver(() => {
        // Check if we're viewing an email (not inbox)
        const isEmailView = isGmail 
            ? document.querySelector('[role="main"] [data-message-id]') !== null
            : document.querySelector('[role="main"] ._rp_1') !== null;

        if (isEmailView && !document.getElementById('mercura-extract-rfq-btn')) {
            // Small delay to ensure DOM is ready
            setTimeout(injectButton, 500);
        }
    });

    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Initial injection attempt
    setTimeout(injectButton, 1000);
})();
