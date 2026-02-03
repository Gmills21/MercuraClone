/**
 * OpenMercura Gmail Add-in
 * Extracts quotes from emails and sends to OpenMercura
 */

(function() {
    'use strict';

    const API_BASE_URL = 'http://127.0.0.1:9000';
    
    // Inject button when Gmail loads
    function init() {
        console.log('[OpenMercura] Gmail add-in initialized');
        
        // Watch for email view changes
        const observer = new MutationObserver((mutations) => {
            if (isEmailOpen()) {
                addExtractButton();
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    function isEmailOpen() {
        // Check if we're viewing an email
        return document.querySelector('[role="main"]') !== null;
    }
    
    function addExtractButton() {
        // Check if button already exists
        if (document.getElementById('openmercura-extract-btn')) {
            return;
        }
        
        // Find toolbar
        const toolbar = document.querySelector('[gh="mtb"]');
        if (!toolbar) return;
        
        // Create button
        const btn = document.createElement('div');
        btn.id = 'openmercura-extract-btn';
        btn.className = 'openmercura-btn';
        btn.innerHTML = `
            <img src="${API_BASE_URL}/icon16.png" alt="OM" style="width:16px;height:16px;margin-right:4px;vertical-align:middle;">
            <span>Extract Quote</span>
        `;
        btn.onclick = extractQuoteFromEmail;
        
        // Add to toolbar
        toolbar.appendChild(btn);
    }
    
    function extractQuoteFromEmail() {
        // Get email content
        const emailBody = document.querySelector('[role="main"] .ii.gt');
        const subject = document.querySelector('[role="main"] h2.hP');
        const sender = document.querySelector('[role="main"] .gD');
        
        if (!emailBody) {
            alert('Could not find email content');
            return;
        }
        
        const emailData = {
            subject: subject ? subject.textContent : '',
            sender: sender ? sender.textContent : '',
            body: emailBody.innerText,
            html: emailBody.innerHTML
        };
        
        // Show loading
        const btn = document.getElementById('openmercura-extract-btn');
        btn.innerHTML = '<span>Extracting...</span>';
        
        // Send to OpenMercura API
        fetch(`${API_BASE_URL}/extractions/parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: emailData.body,
                source_type: 'gmail'
            })
        })
        .then(res => res.json())
        .then(data => {
            btn.innerHTML = '<span>✓ Extracted!</span>';
            setTimeout(() => {
                btn.innerHTML = `
                    <img src="${API_BASE_URL}/icon16.png" alt="OM" style="width:16px;height:16px;margin-right:4px;vertical-align:middle;">
                    <span>Extract Quote</span>
                `;
            }, 2000);
            
            // Show results popup
            showExtractionPopup(data);
        })
        .catch(err => {
            console.error('[OpenMercura] Extraction failed:', err);
            btn.innerHTML = '<span>✗ Failed</span>';
            setTimeout(() => {
                btn.innerHTML = `
                    <img src="${API_BASE_URL}/icon16.png" alt="OM" style="width:16px;height:16px;margin-right:4px;vertical-align:middle;">
                    <span>Extract Quote</span>
                `;
            }, 2000);
            alert('Extraction failed. Please try again.');
        });
    }
    
    function showExtractionPopup(data) {
        // Create popup to show extracted items
        const popup = document.createElement('div');
        popup.className = 'openmercura-popup';
        
        let itemsHtml = '';
        if (data.parsed_data && data.parsed_data.line_items) {
            itemsHtml = data.parsed_data.line_items.map(item => `
                <div class="om-item">
                    <strong>${item.item_name}</strong><br>
                    Qty: ${item.quantity} × $${item.unit_price} = $${item.total_price}
                </div>
            `).join('');
        }
        
        popup.innerHTML = `
            <div class="om-popup-header">
                <h3>Extracted Quote Items</h3>
                <button class="om-close">&times;</button>
            </div>
            <div class="om-popup-body">
                ${itemsHtml}
                <div class="om-total">
                    <strong>Total: $${data.parsed_data?.total_amount || 0}</strong>
                </div>
            </div>
            <div class="om-popup-footer">
                <a href="${API_BASE_URL}/extractions/${data.id}" target="_blank" class="om-btn om-btn-primary">View in OpenMercura</a>
                <button class="om-btn om-btn-secondary om-close">Close</button>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        // Close handlers
        popup.querySelectorAll('.om-close').forEach(el => {
            el.onclick = () => popup.remove();
        });
    }
    
    // Initialize when page loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
