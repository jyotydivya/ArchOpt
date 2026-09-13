export const formatPercent = (val: number | undefined | null): string => {
  if (val === undefined || val === null || isNaN(val)) return '0%';
  const num = val > 1 ? val : val * 100;
  return `${Math.round(num * 10) / 10}%`;
};

export const formatScore = (val: number | undefined | null): string => {
  if (val === undefined || val === null || isNaN(val)) return '0.00';
  return Number(val).toFixed(2);
};

export const getMetricColor = (metric: string, val: number): string => {
  if (metric === 'constraintScore') {
    return val >= 1.0 ? 'var(--accent-emerald)' : 'var(--accent-rose)';
  }
  if (val >= 0.8) return 'var(--accent-emerald)';
  if (val >= 0.6) return 'var(--accent-cyan)';
  if (val >= 0.4) return 'var(--accent-amber)';
  return 'var(--accent-rose)';
};
