// utils/formatters.ts
import { format, formatDistanceToNow, parseISO } from 'date-fns';

/**
 * Format currency in Indian Rupees
 */
export const formatCurrency = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined) return 'N/A';
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format currency in crores
 */
export const formatCrores = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined) return 'N/A';
  
  return `₹${amount.toFixed(2)} Cr`;
};

/**
 * Format percentage
 */
export const formatPercentage = (value: number | null | undefined, decimals: number = 2): string => {
  if (value === null || value === undefined) return 'N/A';
  
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format subscription times (e.g., 2.5x)
 */
export const formatSubscription = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'N/A';
  
  return `${value.toFixed(2)}x`;
};

/**
 * Format date
 */
export const formatDate = (dateString: string | null | undefined, formatStr: string = 'dd MMM yyyy'): string => {
  if (!dateString) return 'N/A';
  
  try {
    return format(parseISO(dateString), formatStr);
  } catch (error) {
    return 'Invalid Date';
  }
};

/**
 * Format relative time (e.g., "2 days ago")
 */
export const formatRelativeTime = (dateString: string | null | undefined): string => {
  if (!dateString) return 'N/A';
  
  try {
    return formatDistanceToNow(parseISO(dateString), { addSuffix: true });
  } catch (error) {
    return 'Invalid Date';
  }
};

/**
 * Format number with commas
 */
export const formatNumber = (num: number | null | undefined): string => {
  if (num === null || num === undefined) return 'N/A';
  
  return new Intl.NumberFormat('en-IN').format(num);
};

/**
 * Get status badge color
 */
export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    upcoming: 'bg-blue-100 text-blue-800',
    open: 'bg-green-100 text-green-800',
    closed: 'bg-gray-100 text-gray-800',
    listed: 'bg-purple-100 text-purple-800',
    withdrawn: 'bg-red-100 text-red-800',
  };
  
  return colors[status.toLowerCase()] || 'bg-gray-100 text-gray-800';
};

/**
 * Get risk category color
 */
export const getRiskColor = (category: string | null): string => {
  if (!category) return 'bg-gray-100 text-gray-800';
  
  const colors: Record<string, string> = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };
  
  return colors[category.toLowerCase()] || 'bg-gray-100 text-gray-800';
};

/**
 * Calculate days until or since date
 */
export const getDaysUntil = (dateString: string | null | undefined): number | null => {
  if (!dateString) return null;
  
  try {
    const date = parseISO(dateString);
    const today = new Date();
    const diffTime = date.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  } catch (error) {
    return null;
  }
};

/**
 * Truncate text
 */
export const truncateText = (text: string | null | undefined, maxLength: number = 100): string => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};
