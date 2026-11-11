// Prices charged for the both-programs plan (first month), by currency. Files in api/_lib are shared code, not routes.
// The server decides the amount: the browser never sends one.
// Keep in step with PRICES in assets/js/parents-site.js (the numbers shown on the page).
// USD and EUR are placeholders until Rohith confirms them.
export const BOTH_PRICES = { INR: 4999, USD: 165, EUR: 149 };

// Same rule as currencyFor() in parents-site.js: India INR, euro countries EUR, everywhere else USD.
const EURO = 'AT BE BG HR CY EE FI FR DE GR IE IT LV LT LU MT NL PT SK SI ES'.split(' ');
export function currencyForCountry(country) {
  const c = String(country || '').toUpperCase();
  if (!/^[A-Z]{2}$/.test(c)) return '';
  return c === 'IN' ? 'INR' : (EURO.includes(c) ? 'EUR' : 'USD');
}

// Razorpay takes amounts in the smallest unit (paise, cents). All three currencies have two decimals.
export const toMinor = (amount) => Math.round(amount * 100);
