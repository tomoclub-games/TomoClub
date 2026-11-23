// All settings come from environment variables. Secrets never reach the browser.
import path from 'node:path';

const int = (v, d) => (Number.isFinite(Number(v)) && v !== '' && v != null ? Number(v) : d);

export const config = {
  port: int(process.env.PORT, 3000),
  dataDir: process.env.DATA_DIR || path.resolve('data'),

  // AI
  anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
  anthropicApiUrl: (process.env.ANTHROPIC_API_URL || 'https://api.anthropic.com').replace(/\/$/, ''),
  answerModel: process.env.ANTHROPIC_MODEL || 'claude-sonnet-5-5',
  searchModel: process.env.ANTHROPIC_FAST_MODEL || 'claude-haiku-5-5',

  // Crawl limits (keep costs and load on district sites low)
  maxPages: int(process.env.MAX_PAGES, 40),
  maxPdfs: int(process.env.MAX_PDFS, 15),
  maxDepth: int(process.env.MAX_DEPTH, 3),
  crawlTimeLimitMs: int(process.env.CRAWL_TIME_LIMIT_SEC, 240) * 1000,
  requestTimeoutMs: int(process.env.REQUEST_TIMEOUT_SEC, 20) * 1000,
  delayBetweenRequestsMs: int(process.env.CRAWL_DELAY_MS, 400),
  maxHtmlBytes: 4 * 1024 * 1024,
  maxPdfBytes: int(process.env.MAX_PDF_MB, 25) * 1024 * 1024,
  reuseDays: int(process.env.REUSE_DAYS, 7),
  userAgent:
    process.env.CRAWLER_USER_AGENT ||
    'TomoClubDistrictAssistant/0.1 (+https://tomoclub.org; reads public pages only)',

  // Only for local tests: lets the crawler reach 127.0.0.1 fixture sites.
  allowPrivateHosts: process.env.ALLOW_PRIVATE_HOSTS === 'true',

  // Leads
  adminUser: process.env.ADMIN_USER || 'tomoclub',
  adminPassword: process.env.ADMIN_PASSWORD || '',
  leadWebhookUrl: process.env.LEAD_WEBHOOK_URL || '',
  ipHashSalt: process.env.IP_HASH_SALT || 'change-me',
  minFormSeconds: int(process.env.MIN_FORM_SECONDS, 3),

  // Rate limits per IP per hour
  limits: {
    crawl: int(process.env.LIMIT_CRAWLS_PER_HOUR, 6),
    ask: int(process.env.LIMIT_QUESTIONS_PER_HOUR, 60),
    lead: int(process.env.LIMIT_LEADS_PER_HOUR, 5),
    upload: int(process.env.LIMIT_UPLOADS_PER_HOUR, 20),
  },
  // Whole-site daily caps (all visitors together) so a public demo cannot run up costs
  daily: {
    ask: int(process.env.DAILY_QUESTION_LIMIT, 400),
    crawl: int(process.env.DAILY_CRAWL_LIMIT, 40),
  },
  trustProxy: process.env.TRUST_PROXY === 'true',
};

export const aiConfigured = () => Boolean(config.anthropicApiKey);
