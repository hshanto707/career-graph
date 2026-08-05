export const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
] as const;

const CURRENT_YEAR = new Date().getFullYear();
const EXPERIENCE_MIN_YEAR = CURRENT_YEAR - 60;

/** Descending so the most recent years appear first in the picker. */
export const EXPERIENCE_YEAR_OPTIONS = Array.from(
  { length: CURRENT_YEAR + 1 - EXPERIENCE_MIN_YEAR },
  (_, i) => CURRENT_YEAR + 1 - i
);

export function formatMonthYear(month: number, year: number): string {
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

export function formatExperienceDateRange(exp: {
  start_month: number;
  start_year: number;
  end_month: number | null;
  end_year: number | null;
  is_current: boolean;
}): string {
  const start = formatMonthYear(exp.start_month, exp.start_year);
  if (exp.is_current) return `${start} - Present`;
  if (exp.end_month == null || exp.end_year == null) return start;
  return `${start} - ${formatMonthYear(exp.end_month, exp.end_year)}`;
}
