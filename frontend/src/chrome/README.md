# Mercura Chrome Extension

**Phase 4: The Kill Shot** - Lightweight overlay for Gmail/Outlook

## Overview

This Chrome extension provides a "Quick Quote" button that appears in Gmail and Outlook email views, allowing sales reps to extract quote data directly from emails without leaving their workflow.

## Key Features

- **3-Minute Setup**: No IT permission required vs. Mercura's 3-day enterprise integration
- **Lightweight Overlay**: Works where sales reps already work (Gmail/Outlook)
- **One-Click Extraction**: Extract quote data from email body with a single click
- **Margin Optimization**: Automatically suggests high-margin alternatives

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `frontend/src/chrome` directory
5. The extension will be installed and active

## Usage

1. Open any email in Gmail or Outlook
2. Look for the "Quick Quote" button in the email action bar
3. Click the button to extract quote data
4. The system will process the email and create a draft quote
5. Open the quote in the dashboard to review and optimize margins

## Development

### Files

- `manifest.json`: Extension configuration and permissions
- `content.js`: Main content script that injects the Quick Quote button
- `content.css`: Styles for the injected button
- `popup.html`: Extension popup window (shown when clicking extension icon)

### API Integration

The extension sends email content to the backend `/webhooks/upload` endpoint, which:
1. Extracts line items using Gemini AI
2. Matches items to catalog SKUs
3. Suggests high-margin alternatives
4. Creates a draft quote

## Strategy

**vs. Mercura:**
- Mercura: Requires 3-day SAP integration, IT approval, enterprise setup
- Mercura Clone: 3-minute email forwarding, no IT permission, lightweight overlay

This extension is the "Kill Shot" because it eliminates the need for complex integrations by working directly in the email client where sales reps already spend their time.
