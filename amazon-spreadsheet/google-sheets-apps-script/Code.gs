const RAPIDAPI_KEY = 'PASTE_YOUR_KEY_HERE';
const API_HOST = 'real-time-amazon-data-the-most-complete.p.rapidapi.com';

// Run once: builds the template (tabs, headers, sample queries)
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const config = ss.getSheetByName('Config') || ss.insertSheet('Config');
  config.getRange('A1:B1').setValues([['Search term or ASIN', 'Marketplace']])
    .setFontWeight('bold').setBackground('#1E3A5F').setFontColor('#ffffff');
  config.getRange('A2:B4').setValues([
    ['wireless earbuds', 'com'],
    ['yoga mat', 'com'],
    ['B09B8V1LZ3', 'com'],
  ]);
  const out = ss.getSheetByName('Products') || ss.insertSheet('Products');
  out.clear();
  out.getRange(1, 1, 1, 10).setValues([[
    'Date', 'Query', 'ASIN', 'Title', 'Price', 'Original price',
    'Rating', 'Reviews', 'Best Seller', 'URL',
  ]]).setFontWeight('bold').setBackground('#1E3A5F').setFontColor('#ffffff');
  out.setFrozenRows(1);
}

// Run on a schedule: fetches live Amazon data for every Config row
function refreshData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const rows = ss.getSheetByName('Config').getDataRange().getValues().slice(1);
  const out = ss.getSheetByName('Products');
  const stamp = new Date();
  rows.forEach(([term, marketplace]) => {
    if (!term) return;
    const isAsin = /^B0[A-Z0-9]{8}$/i.test(String(term).trim());
    const path = isAsin
      ? '/product-details?asin=' + encodeURIComponent(term)
      : '/search?query=' + encodeURIComponent(term);
    const url = 'https://' + API_HOST + path + '&marketplace=' + (marketplace || 'com');
    const resp = UrlFetchApp.fetch(url, {
      headers: { 'x-rapidapi-key': RAPIDAPI_KEY, 'x-rapidapi-host': API_HOST },
      muteHttpExceptions: true,
    });
    const json = JSON.parse(resp.getContentText());
    if (!json.data) return;
    // Keeps the top 10 per search so the sheet stays readable.
    // Delete ".slice(0, 10)" to log every result (up to 48 per search).
    const products = isAsin
      ? [{ ...json.data, best_seller: json.data.is_best_seller,
           url: 'https://www.amazon.' + (marketplace || 'com') + '/dp/' + json.data.asin }]
      : (json.data.products || []).slice(0, 10);
    products.forEach(p => out.appendRow([
      stamp, term, p.asin, p.title, p.price, p.original_price || '',
      p.rating, p.reviews_count, p.best_seller ? 'Yes' : '', p.url,
    ]));
  });
}
