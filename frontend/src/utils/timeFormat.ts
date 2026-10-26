/**
 * Time and date formatting utilities for Indian Standard Time (IST, UTC+05:30).
 * Displays full date day, month, year, and 12-hour/24-hour IST time.
 * Zero em dashes strictly enforced.
 */

export interface FormattedIST {
  dayName: string;
  dayOfMonth: string;
  monthName: string;
  year: string;
  fullDate: string; // e.g. "Monday, 26 October 2026"
  shortDate: string; // e.g. "26 Oct 2026"
  time12: string; // e.g. "01:35 PM"
  timeIST: string; // e.g. "01:35 PM IST"
  fullDateTimeIST: string; // e.g. "Monday, 26 October 2026 at 01:35 PM IST"
  shortDateTimeIST: string; // e.g. "26 Oct 2026, 01:35 PM IST"
}

/**
 * Format any ISO string, date string, or timestamp to Indian Standard Time (IST).
 */
export function formatToIST(input?: string | number | Date | null): FormattedIST {
  let date: Date;

  if (!input) {
    date = new Date();
  } else if (typeof input === 'string') {
    // If no timezone specified, treat ERA5-Land historical timestamps as UTC
    const normalized =
      input.includes('Z') || input.includes('+') || input.includes('GMT')
        ? input
        : input.replace(' ', 'T') + 'Z';
    date = new Date(normalized);
  } else if (typeof input === 'number') {
    date = new Date(input);
  } else {
    date = input;
  }

  if (isNaN(date.getTime())) {
    date = new Date();
  }

  const dayNameFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    weekday: 'long',
  });
  const dayName = dayNameFormatter.format(date);

  const dayOfMonthFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: 'numeric',
  });
  const dayOfMonth = dayOfMonthFormatter.format(date);

  const monthNameFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    month: 'long',
  });
  const monthName = monthNameFormatter.format(date);

  const shortMonthFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    month: 'short',
  });
  const shortMonth = shortMonthFormatter.format(date);

  const yearFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
  });
  const year = yearFormatter.format(date);

  const timeFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
  const time12 = timeFormatter.format(date).toUpperCase();

  const fullDate = `${dayName}, ${dayOfMonth} ${monthName} ${year}`;
  const shortDate = `${dayOfMonth} ${shortMonth} ${year}`;
  const timeIST = `${time12} IST`;
  const fullDateTimeIST = `${fullDate} at ${timeIST}`;
  const shortDateTimeIST = `${shortDate}, ${timeIST}`;

  return {
    dayName,
    dayOfMonth,
    monthName,
    year,
    fullDate,
    shortDate,
    time12,
    timeIST,
    fullDateTimeIST,
    shortDateTimeIST,
  };
}

/**
 * Returns current live IST timestamp with seconds.
 */
export function getCurrentISTClock(): { fullDate: string; timeString: string } {
  const now = new Date();
  const dayDateFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
  const timeFormatter = new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });

  return {
    fullDate: dayDateFormatter.format(now),
    timeString: `${timeFormatter.format(now).toUpperCase()} IST`,
  };
}
