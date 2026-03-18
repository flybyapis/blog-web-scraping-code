function fetchAndSendDeals() {
  // Returns the cell value, or "" if blank / "(leave blank to skip)"
  function getOptional(sheet, cell) {
    if (!sheet) return "";
    var v = sheet.getRange(cell).getValue().toString().trim();
    return (v === "" || v.charAt(0) === "(") ? "" : v;
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Find or create history sheet
  var history = ss.getSheetByName("Sent Deals");
  if (!history) {
    history = ss.insertSheet("Sent Deals");
    history.appendRow(["deal_id", "title", "price", "discount", "sent_at"]);
  }

  // Find settings sheet — first sheet that isn't "Sent Deals"
  var settings = ss.getSheetByName("Settings") || ss.getSheetByName("Sheet1");
  if (!settings) {
    var sheets = ss.getSheets();
    for (var i = 0; i < sheets.length; i++) {
      if (sheets[i].getName() !== "Sent Deals") { settings = sheets[i]; break; }
    }
  }
  if (!settings) throw new Error("Settings sheet not found. Sheets available: " + ss.getSheets().map(function(s){ return s.getName(); }).join(", "));

  // Read settings
  var apiKey        = settings.getRange("B1").getValue();
  var telegramToken = settings.getRange("B2").getValue();
  var chatId        = settings.getRange("B3").getValue().toString();
  var marketplace   = settings.getRange("B4").getValue();
  var language      = settings.getRange("B5").getValue();
  var pageSize      = settings.getRange("B6").getValue();
  var minDiscount   = settings.getRange("B7").getValue();
  var minPrice      = getOptional(settings, "B8");
  var maxPrice      = getOptional(settings, "B9");
  var category      = getOptional(settings, "B10");
  var minRating     = getOptional(settings, "B11");
  var isPrime       = getOptional(settings, "B12");

  // Load sent deal IDs
  var sentData = history.getDataRange().getValues();
  var sentIds = sentData.slice(1).map(function(row) { return row[0]; });

  // Fetch deals from FlyByAPIs Amazon API
  var url = "https://real-time-amazon-data-the-most-complete.p.rapidapi.com/deals"
    + "?marketplace=" + marketplace
    + "&language=" + language
    + "&page_size=" + pageSize
    + "&min_discount=" + minDiscount
    + (isPrime ? "&is_prime=" + isPrime : "")
    + (minPrice ? "&min_price=" + minPrice : "")
    + (maxPrice ? "&max_price=" + maxPrice : "")
    + (category ? "&category=" + category : "")
    + (minRating ? "&min_rating=" + minRating : "");

  var response = UrlFetchApp.fetch(url, {
    headers: {
      "X-RapidAPI-Key": apiKey,
      "X-RapidAPI-Host": "real-time-amazon-data-the-most-complete.p.rapidapi.com"
    }
  });

  var deals = JSON.parse(response.getContentText()).data.deals;
  var newCount = 0;

  for (var i = 0; i < deals.length; i++) {
    var deal = deals[i];
    var dealId = deal.deal_id || deal.asin;

    if (sentIds.indexOf(dealId) !== -1) continue;

    // Send to Telegram with photo
    var caption = "🔥 *" + deal.title + "*\n\n"
      + "💰 Was " + (deal.original_price || "N/A") + " → "
      + "Now *" + deal.price_symbol + deal.price + "* (" + deal.discount_percentage + "% off)\n\n"
      + "🔗 [See deal on Amazon](" + deal.product_url + ")";

    var telegramUrl = "https://api.telegram.org/bot" + telegramToken + "/sendPhoto";

    // Fetch image from Amazon and send as binary — CDN blocks Telegram's servers
    var imgBlob = UrlFetchApp.fetch(deal.image || "").getBlob().setName("deal.jpg");
    UrlFetchApp.fetch(telegramUrl, {
      method: "post",
      payload: {
        chat_id: chatId,
        photo: imgBlob,
        caption: caption,
        parse_mode: "Markdown"
      }
    });

    // Log to Sent Deals sheet
    history.appendRow([
      dealId,
      deal.title,
      deal.price,
      deal.discount_percentage + "%",
      new Date()
    ]);

    newCount++;
  }

  console.log("Sent " + newCount + " new deals.");
}
