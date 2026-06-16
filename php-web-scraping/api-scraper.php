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

$opts  = getopt('', ['num::', 'gl::', 'hl::']);
$query = firstNonFlagArg($argv) ?? 'php web scraping';

// http_errors => false so a non-200 is a normal response we inspect, not an
// exception that dumps a stack trace. Real tools surface a clean message.
$client = new Client(['http_errors' => false, 'timeout' => 20]);

try {
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
} catch (\GuzzleHttp\Exception\GuzzleException $e) {
    // Connection refused, DNS failure, timeout: a network problem, not an HTTP status.
    fwrite(STDERR, "Could not reach the API: {$e->getMessage()}\n");
    exit(1);
}

$status = $response->getStatusCode();
$body   = (string) $response->getBody();

if ($status !== 200) {
    fwrite(STDERR, "API returned HTTP {$status}.\n");
    fwrite(STDERR, trim($body) . "\n");
    if ($status === 403) {
        fwrite(STDERR, "Check that your key is subscribed at https://rapidapi.com/flybyapi1/api/google-serp-search-api\n");
    } elseif ($status >= 500) {
        fwrite(STDERR, "That is an API-side error. Wait a moment and retry.\n");
    }
    exit(1);
}

$data = json_decode($body, true)['data'] ?? [];

printf("Results for: %s\n\n", $query);

$results = $data['organic_results'] ?? [];

if ($results === []) {
    echo "No organic results returned.\n";
    exit(0);
}

foreach ($results as $result) {
    printf("%2d. %s\n", $result['position'] ?? 0, $result['title'] ?? '');
    printf("    %s\n",  $result['link'] ?? '');
}

/** First CLI argument that is not a --flag (so the query can go anywhere). */
function firstNonFlagArg(array $argv): ?string
{
    foreach (array_slice($argv, 1) as $arg) {
        if (!str_starts_with($arg, '--')) {
            return $arg;
        }
    }
    return null;
}
