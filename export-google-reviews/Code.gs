/**
 * Export Google reviews straight into Google Sheets. FlyByAPIs.
 *
 * Paste this into Extensions > Apps Script in any spreadsheet, set the three
 * values below, and click Run. The reviews land in the active sheet with real
 * dates you can sort and filter.
 *
 * Works for any public business on Google Maps — you do not need to own the
 * profile, so client and competitor reviews work the same way.
 *
 * Get a free key (100 requests/month):
 *   https://rapidapi.com/flybyapi1/api/google-maps-extractor2
 */

const RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"; // paste your key between the quotes
const BUSINESS = "Reading Terminal Market, Philadelphia"; // name + city
const MAX_REVIEWS = 100; // each page costs 1 request and returns 20 reviews

const API_HOST = "google-maps-extractor2.p.rapidapi.com";
const PAGE_SIZE = 20; // the API caps limit at 20, so we paginate

function exportGoogleReviews() {
  const sheet = SpreadsheetApp.getActiveSheet();

  const business = findBusiness(BUSINESS);
  if (!business) {
    throw new Error("No business found for: " + BUSINESS + " — try adding the city.");
  }

  const reviews = fetchReviews(business.google_id);
  if (!reviews.length) {
    throw new Error("Found " + business.name + " but got no reviews back.");
  }

  const rows = reviews.map(function (review) {
    return [
      business.name || "",
      toDate(review.timestamp),
      review.rating || "",
      (review.text || "").replace(/\n/g, " "),
      review.user_name || "",
      review.user_is_local_guide ? "yes" : "no",
      review.user_reviews_count || 0,
      toDate(review.owner_response_timestamp),
      (review.owner_response_text || "").replace(/\n/g, " "),
      review.url || "",
    ];
  });

  // Only clear once every page came back fine, so a mid-run failure never
  // leaves you with a half-empty sheet.
  sheet.clearContents();
  sheet.appendRow([
    "Business", "Date", "Rating", "Review", "Reviewer",
    "Local guide", "Reviewer total reviews", "Owner replied", "Owner response", "Link",
  ]);
  sheet.getRange(2, 1, rows.length, rows[0].length).setValues(rows);
  sheet.getRange(1, 1, 1, 10).setFontWeight("bold");
  sheet.setFrozenRows(1);

  SpreadsheetApp.getActiveSpreadsheet().toast(
    "Exported " + rows.length + " reviews for " + business.name
  );
}

/** Turn a business name into the google_id the reviews endpoint needs. */
function findBusiness(query) {
  const url = "https://" + API_HOST + "/locate_and_search" +
    "?query=" + encodeURIComponent(query) +
    "&country=us&language=en&limit=1";

  const data = callApi(url).data || [];
  return data.length ? data[0] : null;
}

/** Page through the review history 20 at a time until we hit MAX_REVIEWS. */
function fetchReviews(googleId) {
  let reviews = [];
  let token = "";

  while (reviews.length < MAX_REVIEWS) {
    let url = "https://" + API_HOST + "/business_reviews" +
      "?business_id=" + encodeURIComponent(googleId) +
      "&country=us&language=en&sort_by=mostRecent&limit=" + PAGE_SIZE;
    if (token) {
      url += "&next_page_token=" + encodeURIComponent(token);
    }

    const payload = callApi(url);
    const batch = payload.data || [];
    if (!batch.length) break;

    reviews = reviews.concat(batch);

    token = payload.next_token || "";
    if (!token) break; // no more pages
    Utilities.sleep(500); // stay inside the rate limit
  }

  return reviews.slice(0, MAX_REVIEWS);
}

function callApi(url) {
  const response = UrlFetchApp.fetch(url, {
    headers: {
      "x-rapidapi-host": API_HOST,
      "x-rapidapi-key": RAPIDAPI_KEY,
    },
    muteHttpExceptions: true,
  });

  const code = response.getResponseCode();
  if (code === 401) throw new Error("401 Unauthorized — check your RAPIDAPI_KEY.");
  if (code !== 200) throw new Error("API error " + code + ": " + response.getContentText());

  return JSON.parse(response.getContentText());
}

/**
 * Convert the Unix timestamp into a real date.
 *
 * This is the whole reason to do it this way. Every scraper and extension
 * gives you "3 months ago", which you cannot sort, filter by quarter, or chart.
 */
function toDate(timestamp) {
  return timestamp ? new Date(timestamp * 1000) : "";
}
