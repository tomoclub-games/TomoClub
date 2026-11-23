// Information categories, detected from what was actually collected
// (page addresses, titles and text). Also used to rank which links to read first.

export const CATEGORIES = [
  { key: 'handbook', label: 'Student handbook & code of conduct', words: ['handbook', 'code of conduct', 'student conduct', 'discipline', 'dress code', 'behavior'] },
  { key: 'attendance', label: 'Attendance', words: ['attendance', 'absence', 'absent', 'tardy', 'truancy', 'excused'] },
  { key: 'enrollment', label: 'Enrollment & registration', words: ['enroll', 'enrollment', 'registration', 'register', 'kindergarten registration', 'new student', 'residency', 'proof of address'] },
  { key: 'transportation', label: 'Transportation', words: ['transportation', 'bus', 'buses', 'bus route', 'bus stop', 'routing'] },
  { key: 'calendar', label: 'Calendars & schedules', words: ['calendar', 'school year', 'holiday', 'break', 'bell schedule', 'early release', 'first day', 'last day', 'no school'] },
  { key: 'policies', label: 'Board policies', words: ['board policy', 'policies', 'policy', 'regulation', 'board of education', 'school board'] },
  { key: 'nutrition', label: 'Meals & nutrition', words: ['nutrition', 'meal', 'lunch', 'breakfast', 'cafeteria', 'free and reduced', 'menu'] },
  { key: 'health', label: 'Health & immunizations', words: ['health', 'immunization', 'vaccination', 'nurse', 'medication', 'illness'] },
  { key: 'special_ed', label: 'Special education & student support', words: ['special education', 'iep', '504', 'student services', 'counseling', 'english learner', 'multilingual', 'esl'] },
  { key: 'closings', label: 'Weather & closings', words: ['closing', 'closure', 'delay', 'inclement weather', 'snow day', 'emergency'] },
  { key: 'technology', label: 'Technology & devices', words: ['technology', 'chromebook', 'device', 'acceptable use', 'internet safety', 'cell phone', 'artificial intelligence'] },
  { key: 'faq', label: 'FAQs & contacts', words: ['faq', 'frequently asked', 'contact us', 'directory'] },
];

const escape = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const patterns = CATEGORIES.map((c) => ({
  ...c,
  re: new RegExp(`\\b(${c.words.map(escape).join('|')})`, 'gi'),
}));

/** Score a link by how likely it is to hold parent and staff information. */
export function linkScore(url, text = '') {
  const hay = `${decodeURIComponentSafe(url)} ${text}`.toLowerCase().replace(/[-_/+.]+/g, ' ');
  let score = 0;
  for (const c of patterns) {
    c.re.lastIndex = 0;
    if (c.re.test(hay)) score += 3;
  }
  if (/\.pdf(\?|$)/i.test(url)) score += 1;
  if (/(parent|famil|student|guide|resources)/.test(hay)) score += 1;
  if (/(news|article|post|blog|athletic|sports|staff directory|employment|careers|jobs|bid|rfp|minutes|agenda|login|signin|portal|translate|lang=)/.test(hay)) score -= 3;
  return score;
}

/** Categories present in a district's collected documents. */
export function detectCategories(docs) {
  // docs: [{ title, url, text }]
  return patterns
    .map((c) => {
      let count = 0;
      for (const d of docs) {
        const head = `${d.title || ''} ${decodeURIComponentSafe(d.url || '')}`.toLowerCase().replace(/[-_/+.]+/g, ' ');
        c.re.lastIndex = 0;
        const inHead = c.re.test(head);
        c.re.lastIndex = 0;
        const hits = (String(d.text || '').slice(0, 200000).match(c.re) || []).length;
        if (inHead || hits >= 3) count++;
      }
      return { key: c.key, label: c.label, count };
    })
    .filter((c) => c.count > 0)
    .sort((a, b) => b.count - a.count);
}

export function decodeURIComponentSafe(s) {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}
