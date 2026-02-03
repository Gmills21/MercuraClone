/**
 * Shared utilities for OpenMercura
 */

/**
 * Format currency value
 */
export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(value);
}

/**
 * Format date to locale string
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Calculate confidence score color
 */
export function getConfidenceColor(score: number): string {
  if (score >= 0.8) return '#22c55e'; // green
  if (score >= 0.6) return '#eab308'; // yellow
  return '#ef4444'; // red
}

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Debounce function calls
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Generate a random token
 */
export function generateToken(length = 32): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * Parse CSV text to array of objects
 */
export function parseCSV<T extends Record<string, any>>(
  csvText: string,
  delimiter = ','
): T[] {
  const lines = csvText.trim().split('\n');
  if (lines.length < 2) return [];
  
  const headers = lines[0].split(delimiter).map(h => h.trim().replace(/^"|"$/g, ''));
  const results: T[] = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(delimiter).map(v => v.trim().replace(/^"|"$/g, ''));
    const obj: Record<string, any> = {};
    headers.forEach((header, index) => {
      obj[header] = values[index];
    });
    results.push(obj as T);
  }
  
  return results;
}

/**
 * Convert array of objects to CSV
 */
export function toCSV<T extends Record<string, any>>(
  data: T[],
  delimiter = ','
): string {
  if (data.length === 0) return '';
  
  const headers = Object.keys(data[0]);
  const lines = [
    headers.join(delimiter),
    ...data.map(row => 
      headers.map(h => {
        const val = row[h];
        if (val === null || val === undefined) return '';
        const str = String(val);
        if (str.includes(delimiter) || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      }).join(delimiter)
    )
  ];
  
  return lines.join('\n');
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Calculate percentage change
 */
export function percentChange(oldVal: number, newVal: number): number {
  if (oldVal === 0) return newVal > 0 ? 100 : 0;
  return ((newVal - oldVal) / oldVal) * 100;
}
