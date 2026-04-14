/**
 * Build a print-friendly "Travel Wallet" HTML page and open it in a new
 * window so the user can save it as a PDF (or print to paper) using the
 * browser's native print dialog.
 *
 * Going through the browser print dialog avoids pulling in a heavy PDF
 * library like jsPDF for what is, ultimately, "render some HTML and turn it
 * into a PDF".
 */
import type { Deal } from '@/services/dealsService';
import { formatDiscount, daysUntilExpiry } from '@/services/dealsService';

const escapeHtml = (s: string): string =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

/**
 * Public, no-auth QR rendering service. The QR encodes only the coupon code
 * + partner name (no PII), so this is safe to delegate to a third-party.
 */
const qrSrc = (data: string, size = 160): string =>
  `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`;

const renderCouponCard = (deal: Deal): string => {
  const expiry = deal.validUntil
    ? new Date(deal.validUntil).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'No expiry';
  const days = daysUntilExpiry(deal.validUntil);
  const expiryNote =
    days === null
      ? ''
      : days < 0
      ? '<span style="color:#b91c1c;font-weight:600;"> · Expired</span>'
      : days <= 7
      ? `<span style="color:#b45309;font-weight:600;"> · ${days} day${days === 1 ? '' : 's'} left</span>`
      : '';
  return `
    <div class="coupon">
      <div class="left">
        <div class="discount">${escapeHtml(formatDiscount(deal))}</div>
        <div class="category">${escapeHtml(deal.partnerCategory)}</div>
      </div>
      <div class="middle">
        <div class="title">${escapeHtml(deal.title)}</div>
        <div class="partner">${escapeHtml(deal.partnerName)}${
          deal.partnerDestination
            ? ` &middot; ${escapeHtml(deal.partnerDestination)}`
            : ''
        }</div>
        ${
          deal.description
            ? `<div class="desc">${escapeHtml(deal.description)}</div>`
            : ''
        }
        <div class="meta">
          ${
            deal.minSpend
              ? `<span>Min. spend $${deal.minSpend.toFixed(0)}</span>`
              : ''
          }
          <span>Expires: ${expiry}${expiryNote}</span>
        </div>
        ${
          deal.terms
            ? `<div class="terms">${escapeHtml(deal.terms)}</div>`
            : ''
        }
        <div class="code-row">
          <div class="code">${escapeHtml(deal.code)}</div>
        </div>
      </div>
      <div class="right">
        <img src="${qrSrc(deal.qrData)}" alt="QR for ${escapeHtml(deal.code)}" width="120" height="120" />
        <div class="scan">SCAN TO REDEEM</div>
      </div>
    </div>
  `;
};

export interface PrintWalletOptions {
  /** Header subtitle, usually the destination(s) the wallet covers. */
  subtitle?: string;
  /** Optional traveller name to print at the top. */
  travelerName?: string;
}

/**
 * Open a new window with a print-ready Travel Wallet page and trigger the
 * browser print dialog. The user can then choose "Save as PDF".
 *
 * Returns ``true`` on success, ``false`` if the popup was blocked.
 */
export const printDealsAsWallet = (
  deals: Deal[],
  options: PrintWalletOptions = {},
): boolean => {
  const win = window.open('', '_blank', 'width=900,height=1100');
  if (!win) return false;

  const today = new Date().toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const couponsHtml = deals.map(renderCouponCard).join('');
  const subtitle = options.subtitle
    ? `<div class="subtitle">${escapeHtml(options.subtitle)}</div>`
    : '';
  const traveler = options.travelerName
    ? `<div class="traveler">For ${escapeHtml(options.travelerName)}</div>`
    : '';

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Travel Wallet — ${escapeHtml(options.subtitle || 'Your Deals')}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         color: #111827; margin: 0; padding: 32px; background: #fafaf9; }
  .header { text-align: center; padding-bottom: 16px; border-bottom: 2px solid #0d9488; margin-bottom: 24px; }
  h1 { color: #0d9488; margin: 0; font-size: 28px; }
  .subtitle { color: #4b5563; margin-top: 4px; font-size: 14px; }
  .traveler { color: #6b7280; margin-top: 4px; font-size: 13px; }
  .meta-line { color: #9ca3af; margin-top: 6px; font-size: 12px; }
  .coupon { display: flex; gap: 20px; align-items: stretch;
            background: #fff; border: 1px solid #e5e7eb; border-radius: 14px;
            padding: 18px 22px; margin-bottom: 14px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            page-break-inside: avoid; }
  .left { width: 130px; flex-shrink: 0; text-align: center;
          border-right: 2px dashed #e5e7eb; padding-right: 16px;
          display: flex; flex-direction: column; justify-content: center; }
  .discount { font-size: 22px; font-weight: 800; color: #0d9488; line-height: 1.1; }
  .category { text-transform: uppercase; font-size: 10px; color: #6b7280;
              margin-top: 6px; letter-spacing: 1px; }
  .middle { flex: 1; min-width: 0; }
  .title { font-size: 16px; font-weight: 700; color: #111827; }
  .partner { font-size: 12px; color: #6b7280; margin-top: 2px; }
  .desc { font-size: 13px; color: #374151; margin-top: 8px; line-height: 1.4; }
  .meta { font-size: 11px; color: #6b7280; margin-top: 8px; display: flex; gap: 12px; flex-wrap: wrap; }
  .terms { font-size: 10px; color: #9ca3af; margin-top: 6px; font-style: italic; line-height: 1.3; }
  .code-row { margin-top: 10px; }
  .code { display: inline-block; font-family: "SF Mono", Menlo, Consolas, monospace;
          font-weight: 700; letter-spacing: 1.5px; font-size: 14px;
          background: #ecfdf5; color: #065f46; padding: 6px 14px; border-radius: 6px;
          border: 1px dashed #10b981; }
  .right { width: 140px; flex-shrink: 0; text-align: center;
           display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .scan { font-size: 9px; color: #9ca3af; margin-top: 6px; letter-spacing: 1px; }
  .footer { text-align: center; color: #9ca3af; font-size: 11px; margin-top: 24px;
            padding-top: 12px; border-top: 1px solid #e5e7eb; }
  @media print {
    body { padding: 16px; background: #fff; }
    .no-print { display: none !important; }
  }
</style>
</head>
<body>
  <div class="header">
    <h1>🎟️ Travel Wallet</h1>
    ${subtitle}
    ${traveler}
    <div class="meta-line">Generated ${escapeHtml(today)} · ${deals.length} deal${deals.length === 1 ? '' : 's'}</div>
  </div>
  ${couponsHtml || '<div style="text-align:center;color:#9ca3af;padding:48px;">No deals to print.</div>'}
  <div class="footer">
    AI Smart Trip Planner · Show this code or QR at checkout to redeem.
  </div>
  <script>
    // Auto-trigger print after images (QR codes) load so the dialog
    // doesn't appear before everything is on the page.
    window.addEventListener('load', function () {
      setTimeout(function () { window.print(); }, 400);
    });
  </script>
</body>
</html>`;

  win.document.open();
  win.document.write(html);
  win.document.close();
  return true;
};
