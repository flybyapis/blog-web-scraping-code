<?php
/**
 * php-web-scraping — a complete, runnable web crawler in PHP.
 *
 * From the FlyByAPIs tutorial:
 *   https://flybyapis.com/blog/php-web-scraping-tutorial/
 *
 * It crawls books.toscrape.com (a sandbox built for scraping practice) and shows
 * every piece a real crawler needs, not just a pagination loop:
 *
 *   - a link frontier (queue) with URL deduplication and a depth limit
 *   - concurrent fetching via Guzzle's Pool (breadth-first, level by level)
 *   - retries with exponential backoff
 *   - HTML parsing with Symfony DomCrawler (CSS selectors, not regex)
 *   - per-record validation to catch selector drift early
 *   - storage in SQLite (dedup + resume), with optional CSV export
 *
 * Usage:
 *   composer install
 *   php crawler.php
 *   php crawler.php --seed=https://books.toscrape.com/ --concurrency=5 --max-pages=200
 *   php crawler.php --export=books.csv
 */

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\HandlerStack;
use GuzzleHttp\Middleware;
use GuzzleHttp\Pool;
use GuzzleHttp\Psr7\Request;
use GuzzleHttp\Exception\ConnectException;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Symfony\Component\DomCrawler\Crawler;

final class BookCrawler
{
    private Client $client;
    private PDO $db;

    /** @var array<string,bool> URLs we have already queued, for deduplication. */
    private array $seen = [];

    private int $pagesCrawled = 0;
    private int $booksSaved = 0;

    public function __construct(
        private string $seed,
        private int $concurrency = 5,
        private int $maxPages = 0,               // 0 = no limit
        private int $maxDepth = 6,
        string $dbPath = __DIR__ . '/crawl.db',
    ) {
        // One handler stack with a retry middleware, so EVERY request retries
        // transient failures (5xx, dropped connections) with exponential backoff.
        $stack = HandlerStack::create();
        $stack->push(Middleware::retry($this->retryDecider(), $this->retryDelay()));

        $this->client = new Client([
            'handler'         => $stack,
            'timeout'         => 15,
            'connect_timeout' => 10,
            'http_errors'     => false,           // we inspect status codes ourselves
            'headers'         => [
                'User-Agent' => 'FlyByAPIs-TutorialCrawler/1.0 (+https://flybyapis.com/blog/php-web-scraping-tutorial/)',
            ],
        ]);

        $this->db = new PDO('sqlite:' . $dbPath);
        $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $this->db->exec('
            CREATE TABLE IF NOT EXISTS books (
                url        TEXT PRIMARY KEY,
                title      TEXT NOT NULL,
                price      REAL,
                stock      TEXT,
                scraped_at TEXT NOT NULL
            )
        ');
    }

    /**
     * Crawl breadth-first. Each "level" of URLs is fetched concurrently with a
     * Guzzle Pool; links discovered on that level form the next level. The pool's
     * concurrency cap is the throttle, so we do not add a per-request sleep here.
     */
    public function crawl(): void
    {
        $host  = parse_url($this->seed, PHP_URL_HOST);
        $level = [$this->seed];
        $this->seen[$this->seed] = true;

        for ($depth = 0; $level !== [] && $depth <= $this->maxDepth; $depth++) {
            $nextLevel = [];

            $requests = function (array $urls) {
                foreach ($urls as $url) {
                    yield $url => new Request('GET', $url);
                }
            };

            $pool = new Pool($this->client, $requests($level), [
                'concurrency' => $this->concurrency,
                'fulfilled'   => function (ResponseInterface $response, string $url) use (&$nextLevel, $host) {
                    if ($response->getStatusCode() !== 200) {
                        fwrite(STDERR, "Skip {$url}: HTTP {$response->getStatusCode()}\n");
                        return;
                    }

                    $this->pagesCrawled++;
                    $crawler = new Crawler((string) $response->getBody(), $url);

                    $this->saveBooks($crawler, $url);
                    $this->discover($crawler, $host, $nextLevel);
                },
                'rejected' => function ($reason, string $url) {
                    $message = $reason instanceof \Throwable ? $reason->getMessage() : (string) $reason;
                    fwrite(STDERR, "Failed {$url}: {$message}\n");
                },
            ]);

            $pool->promise()->wait();

            if ($this->maxPages > 0 && $this->pagesCrawled >= $this->maxPages) {
                break;
            }

            $level = $nextLevel;
        }

        printf(
            "Done. Crawled %d pages, saved %d books to SQLite.\n",
            $this->pagesCrawled,
            $this->booksSaved,
        );
    }

    /** Extract every book on a listing page and upsert it into SQLite. */
    private function saveBooks(Crawler $crawler, string $pageUrl): void
    {
        $stmt = $this->db->prepare('
            INSERT OR REPLACE INTO books (url, title, price, stock, scraped_at)
            VALUES (:url, :title, :price, :stock, :scraped_at)
        ');

        foreach ($crawler->filter('article.product_pod') as $node) {
            $book = new Crawler($node);

            $title = $book->filter('h3 a')->count() ? $book->filter('h3 a')->attr('title') : null;
            $price = $book->filter('.price_color')->count() ? $book->filter('.price_color')->text() : '';

            // Validation: if the shape is wrong, the markup changed (selector drift).
            // Shout about it instead of writing garbage.
            if ($title === null || trim($title) === '') {
                fwrite(STDERR, "WARN: title selector returned nothing on {$pageUrl} — markup may have changed\n");
                continue;
            }

            $href = $book->filter('h3 a')->attr('href') ?? $pageUrl;

            $stmt->execute([
                ':url'        => $this->resolve($pageUrl, $href),
                ':title'      => trim(preg_replace('/\s+/', ' ', $title)),
                ':price'      => (float) preg_replace('/[^0-9.]/', '', $price),
                ':stock'      => str_contains($book->filter('.availability')->count() ? $book->filter('.availability')->text() : '', 'In stock')
                    ? 'in_stock' : 'unknown',
                ':scraped_at' => date('c'),
            ]);

            $this->booksSaved++;
        }
    }

    /** Find same-host links on the page and add the unseen ones to the next level. */
    private function discover(Crawler $crawler, ?string $host, array &$nextLevel): void
    {
        foreach ($crawler->filter('a')->links() as $link) {
            $url = strtok($link->getUri(), '#');          // drop fragments

            if ($url === false || parse_url($url, PHP_URL_HOST) !== $host) {
                continue;                                  // stay on the same host
            }
            if (!isset($this->seen[$url])) {
                $this->seen[$url] = true;
                $nextLevel[] = $url;
            }
        }
    }

    /** Decide whether a failed request is worth retrying. */
    private function retryDecider(): callable
    {
        return function (
            int $retries,
            RequestInterface $request,
            ?ResponseInterface $response = null,
            ?\Throwable $exception = null,
        ): bool {
            if ($retries >= 3) {
                return false;                              // give up after 3 tries
            }
            if ($exception instanceof ConnectException) {
                return true;                               // network error, retry
            }
            if ($response && $response->getStatusCode() >= 500) {
                return true;                               // server error, retry
            }
            return false;                                  // 4xx will never become 200
        };
    }

    /** Exponential backoff in milliseconds: 1s, 2s, 4s. */
    private function retryDelay(): callable
    {
        return fn (int $retries): int => 1000 * (2 ** $retries);
    }

    /** Resolve a possibly-relative href against the page it was found on. */
    private function resolve(string $base, string $href): string
    {
        if (str_starts_with($href, 'http://') || str_starts_with($href, 'https://')) {
            return $href;
        }
        $baseDir = preg_replace('#/[^/]*$#', '/', $base);
        return $baseDir . ltrim($href, './');
    }

    /** Dump the SQLite table to a CSV file. */
    public function exportCsv(string $path): void
    {
        $rows = $this->db->query('SELECT url, title, price, stock, scraped_at FROM books ORDER BY title');
        $rows->setFetchMode(PDO::FETCH_NUM);          // numeric rows only, no duplicate columns
        $fh = fopen($path, 'w');
        fputcsv($fh, ['url', 'title', 'price', 'stock', 'scraped_at'], ',', '"', '');
        $count = 0;
        foreach ($rows as $row) {
            fputcsv($fh, $row, ',', '"', '');
            $count++;
        }
        fclose($fh);
        printf("Exported %d books to %s\n", $count, $path);
    }
}

// ---------------------------------------------------------------------------
// CLI entry point
// ---------------------------------------------------------------------------

$opts = getopt('', ['seed::', 'concurrency::', 'max-pages::', 'max-depth::', 'export::']);

$crawler = new BookCrawler(
    seed:        $opts['seed']        ?? 'https://books.toscrape.com/',
    concurrency: (int) ($opts['concurrency'] ?? 5),
    maxPages:    (int) ($opts['max-pages']   ?? 0),
    maxDepth:    (int) ($opts['max-depth']   ?? 6),
);

$crawler->crawl();

if (isset($opts['export'])) {
    $crawler->exportCsv($opts['export'] !== false ? $opts['export'] : 'books.csv');
}
