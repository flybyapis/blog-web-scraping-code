<?php
/**
 * api-scraper.php — the same "scrape search results" job, but through the
 * FlyByAPIs Google Search API instead of a homemade Google scraper.
 *
 * From the FlyByAPIs tutorial:
 *   https://flybyapis.com/blog/php-web-scraping-tutorial/
 *
 * The moment your PHP crawler points at Google you hit CAPTCHAs, layout changes,
 * and IP bans. A managed API absorbs the blocking and hands you clean JSON. Notice
 * it is the same Guzzle client you already learned.
 *
 * Usage:
 *   composer install
 *   export RAPIDAPI_KEY=your_key_here          # free key at the URL below
 *   php api-scraper.php "php web scraping"
 *   php api-scraper.php "best php libraries" --num=20 --gl=us --hl=en
 *
 * Get a free key (200 requests/month, no card):
 *   https://rapidapi.com/flybyapi1/api/google-serp-search-api
 */

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use GuzzleHttp\Client;

$key = getenv('RAPIDAPI_KEY');
if (!$key) {
    fwrite(STDERR, "Set RAPIDAPI_KEY first. Get a free key at:\n");
    fwrite(STDERR, "  https://rapidapi.com/flybyapi1/api/google-serp-search-api\n");
    exit(1);
}

$query = $argv[1] ?? 'php web scraping';
$opts  = getopt('', ['num::', 'gl::', 'hl::']);

$client = new Client();

$response = $client->get('https://google-serp-search-api.p.rapidapi.com/search', [
    'query' => [
        'q'   => $query,
        'num' => (int) ($opts['num'] ?? 10),
        'gl'  => $opts['gl'] ?? 'us',
        'hl'  => $opts['hl'] ?? 'en',
    ],
    'headers' => [
        'X-RapidAPI-Key'  => $key,
        'X-RapidAPI-Host' => 'google-serp-search-api.p.rapidapi.com',
    ],
]);

$data = json_decode((string) $response->getBody(), true)['data'] ?? [];

printf("Results for: %s\n\n", $query);

foreach ($data['organic'] ?? [] as $result) {
    printf("%2d. %s\n", $result['position'] ?? 0, $result['title'] ?? '');
    printf("    %s\n",  $result['link'] ?? '');
}
