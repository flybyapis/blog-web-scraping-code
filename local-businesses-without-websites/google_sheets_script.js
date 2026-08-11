const RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"; // paste your key between the quotes
const QUERY = "barber shop in El Paso, TX, USA"; // your niche + city
const PAGES = 3; // each page checks 20 businesses

function findLeads() {
  const sheet = SpreadsheetApp.getActiveSheet();
  sheet.clearContents();

  const seen = {};
  const rows = [];

  for (let page = 0; page < PAGES; page++) {
    const url = "https://google-maps-extractor2.p.rapidapi.com/locate_and_search" +
      "?query=" + encodeURIComponent(QUERY) +
      "&country=us&language=en&limit=20&offset=" + (page * 20);

    const response = UrlFetchApp.fetch(url, {
      headers: {
        "x-rapidapi-host": "google-maps-extractor2.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY,
      },
      muteHttpExceptions: true,
    });

    if (response.getResponseCode() !== 200) {
      throw new Error("API error: " + response.getContentText());
    }

    const businesses = JSON.parse(response.getContentText()).data || [];
    businesses.forEach(function (biz) {
      if (biz.website_url) return; // has a website: skip it
      if (!biz.place_id || seen[biz.place_id]) return; // dedupe
      seen[biz.place_id] = true;
      rows.push([
        biz.name || "",
        biz.phone || biz.full_phone || "",
        biz.full_address || "",
        biz.main_category || "",
        biz.rating || "",
        biz.reviews_count || 0,
        "https://www.google.com/maps/place/?q=place_id:" + biz.place_id,
      ]);
    });
  }

  rows.sort(function (a, b) { return b[5] - a[5]; }); // most reviews first

  sheet.appendRow(["Name", "Phone", "Address", "Category", "Rating", "Reviews", "Maps link"]);
  rows.forEach(function (row) { sheet.appendRow(row); });
}
