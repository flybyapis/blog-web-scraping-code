// Package main is a complete, production-minded Colly web scraper.
//
// It crawls every page of https://books.toscrape.com (a sandbox built for
// scraping practice), extracts each book's title, price, rating and stock
// status, follows pagination to the end, scrapes pages concurrently, and
// writes the results to books.csv.
//
// It also bundles the production hardening you actually need in the real
// world: a rate limit with random delay, a request timeout, automatic
// retries with backoff, a rotating User-Agent, and optional proxy support.
//
// Run it:
//
//	go run ./colly-scraper
//	go run ./colly-scraper -out=mybooks.csv -parallel=4
//
// Full tutorial: https://flybyapis.com/blog/golang-web-scraper/
package main

import (
	"encoding/csv"
	"flag"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/gocolly/colly/v2"
	"github.com/gocolly/colly/v2/debug"
	"github.com/gocolly/colly/v2/extensions"
)

// Book is one row of scraped data.
type Book struct {
	Title        string
	Price        string
	Rating       string
	Availability string
	URL          string
}

const startURL = "https://books.toscrape.com/"

func main() {
	out := flag.String("out", "books.csv", "output CSV file")
	parallel := flag.Int("parallel", 2, "number of concurrent requests")
	maxRetries := flag.Int("retries", 3, "max retries per failed request")
	verbose := flag.Bool("v", false, "verbose colly debug logging")
	flag.Parse()

	// books holds everything we scrape. Colly calls our callbacks from
	// multiple goroutines when Async is on, so guard the slice with a mutex.
	var (
		books []Book
		mu    sync.Mutex
	)

	// retries tracks how many times we've retried each URL so we don't loop
	// forever on a page that is genuinely dead.
	retries := map[string]int{}
	var retryMu sync.Mutex

	opts := []colly.CollectorOption{
		colly.AllowedDomains("books.toscrape.com"),
		colly.Async(true),
		colly.MaxDepth(0), // 0 = no limit; pagination controls the crawl
	}
	if *verbose {
		opts = append(opts, colly.Debugger(&debug.LogDebugger{}))
	}
	c := colly.NewCollector(opts...)

	// Rotate the User-Agent on every request. A bare Go default UA is the
	// fastest way to get blocked.
	extensions.RandomUserAgent(c)

	// Be a good citizen and stay under the radar: cap concurrency and add a
	// random delay between requests to the same host.
	c.SetRequestTimeout(30 * time.Second)
	if err := c.Limit(&colly.LimitRule{
		DomainGlob:  "*toscrape.com*",
		Parallelism: *parallel,
		RandomDelay: 2 * time.Second,
	}); err != nil {
		log.Fatalf("limit rule: %v", err)
	}

	// Optional proxy support. Set PROXIES to a comma-separated list and every
	// request rotates through them. Leave it unset to scrape direct.
	if raw := os.Getenv("PROXIES"); raw != "" {
		list := strings.Split(raw, ",")
		rp, err := proxySwitcher(list)
		if err != nil {
			log.Fatalf("proxy setup: %v", err)
		}
		c.SetProxyFunc(rp)
		log.Printf("routing through %d proxies", len(list))
	}

	// 1. Extract one book per product card.
	c.OnHTML("article.product_pod", func(e *colly.HTMLElement) {
		book := Book{
			// The visible h3 text is truncated; the full title lives in the
			// anchor's title attribute.
			Title:        e.ChildAttr("h3 a", "title"),
			Price:        strings.TrimSpace(e.ChildText("p.price_color")),
			Rating:       ratingFromClass(e.ChildAttr("p.star-rating", "class")),
			Availability: strings.TrimSpace(e.ChildText("p.instock.availability")),
			URL:          e.Request.AbsoluteURL(e.ChildAttr("h3 a", "href")),
		}
		mu.Lock()
		books = append(books, book)
		mu.Unlock()
	})

	// 2. Follow the "next" link until there are no more pages.
	c.OnHTML("li.next a", func(e *colly.HTMLElement) {
		next := e.Request.AbsoluteURL(e.Attr("href"))
		if err := c.Visit(next); err != nil && err != colly.ErrAlreadyVisited {
			log.Printf("queue next page %s: %v", next, err)
		}
	})

	c.OnRequest(func(r *colly.Request) {
		log.Printf("visiting %s", r.URL)
	})

	// 3. Retry transient failures with a small backoff before giving up.
	c.OnError(func(r *colly.Response, err error) {
		url := r.Request.URL.String()
		retryMu.Lock()
		retries[url]++
		n := retries[url]
		retryMu.Unlock()

		if n > *maxRetries {
			log.Printf("giving up on %s after %d tries: %v", url, n-1, err)
			return
		}
		backoff := time.Duration(n) * time.Second
		log.Printf("error on %s (%v) — retry %d/%d in %s", url, err, n, *maxRetries, backoff)
		time.Sleep(backoff)
		_ = r.Request.Retry()
	})

	if err := c.Visit(startURL); err != nil {
		log.Fatalf("initial visit: %v", err)
	}

	// Async means Visit returns immediately. Block until the crawl drains.
	c.Wait()

	if err := writeCSV(*out, books); err != nil {
		log.Fatalf("write csv: %v", err)
	}
	log.Printf("done: scraped %d books into %s", len(books), *out)
}

// ratingFromClass turns "star-rating Three" into "Three".
func ratingFromClass(class string) string {
	parts := strings.Fields(class)
	if len(parts) == 2 {
		return parts[1]
	}
	return ""
}

func writeCSV(path string, books []Book) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	defer w.Flush()

	if err := w.Write([]string{"title", "price", "rating", "availability", "url"}); err != nil {
		return err
	}
	for _, b := range books {
		row := []string{b.Title, b.Price, b.Rating, b.Availability, b.URL}
		if err := w.Write(row); err != nil {
			return err
		}
	}
	return w.Error()
}
