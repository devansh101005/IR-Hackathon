// Print docs/report/report.html to PDF with headless Chromium (needs Node + Playwright).
// Usage: node scripts/print_pdf.js
// Without Node: open docs/report/report.html in Chrome -> Print -> Save as PDF (A4, margins: default).
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const html = path.resolve(__dirname, "..", "docs", "report", "report.html");
  const pdf = path.resolve(__dirname, "..", "docs", "report", "LipiSetu_report.pdf");
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + html, { waitUntil: "networkidle" });
  await page.pdf({ path: pdf, format: "A4", printBackground: true, preferCSSPageSize: true });
  await browser.close();
  console.log("saved " + pdf);
})();
