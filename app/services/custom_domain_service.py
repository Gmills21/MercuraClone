"""
Custom Domain Service for Multi-Tenant SaaS
Handles domain validation, DNS verification, and SSL provisioning.
"""

import re
import uuid
import secrets
import socket
import dns.resolver
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.config import settings
from app.database_sqlite import (
    get_custom_domain, create_custom_domain, update_custom_domain_status,
    delete_custom_domain, check_domain_exists, get_organization_by_custom_domain
)
from app.security_utils import sanitize_string


class CustomDomainService:
    """
    Manages custom domains for organizations.
    
    Features:
    - Domain validation and sanitization
    - DNS record generation and verification
    - SSL certificate provisioning (via CDN/edge)
    - Domain uniqueness checks
    """
    
    # Domain validation regex
    DOMAIN_REGEX = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )
    
    # Reserved domains that cannot be used
    RESERVED_DOMAINS = {
        'www', 'mail', 'ftp', 'localhost', 'admin', 'api', 'app',
        'dashboard', 'portal', 'secure', 'cdn', 'static', 'assets',
        'openmercura.com', 'mercura.io', 'mercura.app',
    }
    
    def __init__(self):
        self.app_domain = self._extract_app_domain()
    
    def _extract_app_domain(self) -> str:
        """Extract the main app domain from app_url config."""
        from urllib.parse import urlparse
        parsed = urlparse(settings.app_url)
        return parsed.netloc or 'openmercura.com'
    
    def validate_domain(self, domain: str) -> tuple[bool, str]:
        """
        Validate a custom domain.
        
        Returns:
            (is_valid, error_message)
        """
        # Sanitize input
        domain = sanitize_string(domain, max_length=253).lower().strip()
        
        if not domain:
            return False, "Domain is required"
        
        # Remove protocol if present
        domain = re.sub(r'^https?://', '', domain)
        domain = domain.rstrip('/')
        
        # Check length
        if len(domain) > 253:
            return False, "Domain too long (max 253 characters)"
        
        # Check format
        if not self.DOMAIN_REGEX.match(domain):
            return False, "Invalid domain format"
        
        # Check if it's an IP address
        try:
            socket.inet_aton(domain)
            return False, "IP addresses are not allowed"
        except socket.error:
            pass
        
        # Check reserved domains
        domain_root = domain.split('.')[0]
        if domain_root in self.RESERVED_DOMAINS:
            return False, f"'{domain_root}' is a reserved subdomain"
        
        # Check if it's the app domain itself
        if domain == self.app_domain or domain.endswith(f'.{self.app_domain}'):
            return False, f"Cannot use {self.app_domain} subdomain"
        
        # Check for wildcards
        if '*' in domain:
            return False, "Wildcard domains are not allowed"
        
        return True, ""
    
    def check_domain_available(self, domain: str) -> tuple[bool, str]:
        """
        Check if a domain is available (not already registered).
        
        Returns:
            (is_available, error_message)
        """
        # First validate
        is_valid, error = self.validate_domain(domain)
        if not is_valid:
            return False, error
        
        # Check if already registered
        domain = domain.lower().strip()
        if check_domain_exists(domain):
            return False, "Domain is already registered"
        
        return True, ""
    
    def generate_dns_records(self, domain: str) -> List[Dict[str, str]]:
        """
        Generate required DNS records for custom domain.
        
        For Render.com deployment:
        - CNAME record pointing to yourapp.onrender.com
        
        For other platforms, adjust accordingly.
        """
        # Extract the target from your app URL
        target = self.app_domain
        
        # If apex domain (e.g., example.com), use A/ALIAS record
        # If subdomain (e.g., crm.example.com), use CNAME
        is_apex = domain.count('.') == 1  # e.g., arkatos.com
        
        records = []
        
        if is_apex:
            # Apex domain - typically needs A record or ALIAS/ANAME
            # For Render, you'd use their apex domain instructions
            records.append({
                'type': 'ALIAS',
                'name': '@',
                'value': target,
                'ttl': '3600',
                'notes': 'If your DNS supports ALIAS/ANAME, use this. Otherwise use A record with Render\'s IP'
            })
            # Also add www redirect
            records.append({
                'type': 'CNAME',
                'name': 'www',
                'value': domain,
                'ttl': '3600',
                'notes': 'Redirect www to apex'
            })
        else:
            # Subdomain - use CNAME
            records.append({
                'type': 'CNAME',
                'name': domain.split('.')[0],  # e.g., "crm" from "crm.example.com"
                'value': target,
                'ttl': '3600',
                'notes': f'Point {domain} to {target}'
            })
        
        # Verification record (TXT)
        verification_token = self.generate_verification_token()
        records.append({
            'type': 'TXT',
            'name': '_mercura',
            'value': f'mercura-verify={verification_token}',
            'ttl': '3600',
            'notes': 'Verification record - required for domain ownership confirmation'
        })
        
        return records, verification_token
    
    def generate_verification_token(self) -> str:
        """Generate a unique verification token."""
        return secrets.token_urlsafe(32)
    
    def verify_domain_dns(self, domain: str, expected_token: str) -> tuple[bool, str]:
        """
        Verify domain DNS records are correctly configured.
        
        Returns:
            (is_verified, message)
        """
        try:
            # Check TXT record for verification
            try:
                answers = dns.resolver.resolve(f'_mercura.{domain}', 'TXT')
                for rdata in answers:
                    for txt_string in rdata.strings:
                        if f'mercura-verify={expected_token}'.encode() in txt_string:
                            return True, "Domain verified successfully"
            except dns.resolver.NXDOMAIN:
                return False, "Verification TXT record not found. Please add the DNS record and wait for propagation (can take up to 24 hours)."
            except dns.resolver.NoAnswer:
                return False, "Verification TXT record not found. Please add the DNS record and wait for propagation."
            
            return False, "Verification token mismatch. Please check your TXT record."
            
        except Exception as e:
            return False, f"DNS verification failed: {str(e)}"
    
    def register_domain(self, organization_id: str, domain: str) -> Dict[str, Any]:
        """
        Register a custom domain for an organization.
        
        Returns:
            Dict with success status and DNS records to configure
        """
        # Validate and check availability
        is_available, error = self.check_domain_available(domain)
        if not is_available:
            return {
                'success': False,
                'error': error
            }
        
        # Check if org already has a custom domain
        existing = get_custom_domain(organization_id)
        if existing:
            return {
                'success': False,
                'error': 'Organization already has a custom domain. Remove it first.'
            }
        
        # Generate DNS records and token
        domain = domain.lower().strip()
        dns_records, verification_token = self.generate_dns_records(domain)
        
        # Create domain record
        domain_data = {
            'id': str(uuid.uuid4()),
            'organization_id': organization_id,
            'domain': domain,
            'status': 'pending',
            'verification_token': verification_token,
            'dns_records': dns_records,
            'ssl_status': 'pending',
            'metadata': {
                'requested_at': datetime.utcnow().isoformat(),
                'app_domain': self.app_domain
            }
        }
        
        result = create_custom_domain(domain_data)
        if result:
            return {
                'success': True,
                'domain': result,
                'dns_records': dns_records,
                'instructions': self._get_setup_instructions(domain, dns_records)
            }
        else:
            return {
                'success': False,
                'error': 'Failed to register domain. Please try again.'
            }
    
    def verify_domain(self, organization_id: str) -> Dict[str, Any]:
        """
        Verify a domain's DNS configuration.
        
        Returns:
            Dict with verification status
        """
        domain_data = get_custom_domain(organization_id)
        if not domain_data:
            return {
                'success': False,
                'error': 'No custom domain found for this organization'
            }
        
        is_verified, message = self.verify_domain_dns(
            domain_data['domain'],
            domain_data['verification_token']
        )
        
        if is_verified:
            update_custom_domain_status(
                organization_id,
                'verified',
                ssl_status='pending'  # SSL will be provisioned by CDN
            )
            return {
                'success': True,
                'status': 'verified',
                'message': message,
                'next_step': 'SSL certificate will be provisioned automatically. Domain will be active within 10 minutes.'
            }
        else:
            return {
                'success': False,
                'status': 'pending',
                'message': message
            }
    
    def activate_domain(self, organization_id: str) -> bool:
        """Mark domain as active (called after SSL is ready)."""
        return update_custom_domain_status(organization_id, 'active', ssl_status='active')
    
    def remove_domain(self, organization_id: str) -> Dict[str, Any]:
        """Remove a custom domain from an organization."""
        domain_data = get_custom_domain(organization_id)
        if not domain_data:
            return {
                'success': False,
                'error': 'No custom domain found'
            }
        
        if delete_custom_domain(organization_id):
            return {
                'success': True,
                'message': f"Domain {domain_data['domain']} has been removed",
                'note': 'Remember to remove the DNS records from your DNS provider'
            }
        else:
            return {
                'success': False,
                'error': 'Failed to remove domain'
            }
    
    def get_domain_status(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an organization's custom domain."""
        domain_data = get_custom_domain(organization_id)
        if not domain_data:
            return None
        
        return {
            'domain': domain_data['domain'],
            'status': domain_data['status'],
            'ssl_status': domain_data['ssl_status'],
            'dns_records': domain_data['dns_records'],
            'created_at': domain_data['created_at'],
            'verified_at': domain_data.get('verified_at'),
            'is_active': domain_data['status'] == 'active'
        }
    
    def resolve_organization_by_domain(self, host: str) -> Optional[Dict[str, Any]]:
        """
        Resolve an organization by custom domain (for middleware).
        
        Args:
            host: The Host header from the request
            
        Returns:
            Organization dict or None
        """
        # Skip if it's the app domain
        if host == self.app_domain or host.endswith(f'.{self.app_domain}'):
            return None
        
        # Remove port if present
        host = host.split(':')[0]
        
        return get_organization_by_custom_domain(host)
    
    def _get_setup_instructions(self, domain: str, records: List[Dict]) -> str:
        """Generate human-readable setup instructions."""
        instructions = f"""
Custom Domain Setup for {domain}
================================

1. Add these DNS records to your DNS provider (Cloudflare, GoDaddy, etc.):

"""
        for record in records:
            instructions += f"""
   Type: {record['type']}
   Name: {record['name']}
   Value: {record['value']}
   TTL: {record['ttl']}
   Notes: {record['notes']}
"""
        
        instructions += f"""
2. Wait for DNS propagation (usually 5-30 minutes, can take up to 24 hours)

3. Click "Verify Domain" in the dashboard

4. SSL certificate will be provisioned automatically

For help, contact support@openmercura.com
"""
        return instructions


# Global instance
custom_domain_service = CustomDomainService()
