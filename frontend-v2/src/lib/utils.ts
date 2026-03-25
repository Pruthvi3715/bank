export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
  }).format(amount);
};

export const formatTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString();
};

export const getRiskColor = (score: number): string => {
  if (score >= 8) return 'text-red-600 dark:text-red-400';
  if (score >= 6) return 'text-orange-600 dark:text-orange-400';
  return 'text-yellow-600 dark:text-yellow-400';
};

export const getRiskBgColor = (score: number): string => {
  if (score >= 8) return 'bg-red-100 dark:bg-red-900';
  if (score >= 6) return 'bg-orange-100 dark:bg-orange-900';
  return 'bg-yellow-100 dark:bg-yellow-900';
};

export const capitalizeFirstLetter = (string: string): string => {
  return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
};

export const truncateString = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
};