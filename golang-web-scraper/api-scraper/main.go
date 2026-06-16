// Package main shows the other half of the story: when a target fights back
// with JavaScript rendering, CAPTCHAs or IP bans, you stop maintaining a
// scraper and call a managed API instead.
//
// This hits the FlyByAPIs Google Search API and prints the organic results.
// Same idea works for Amazon, Google Maps, jobs and more.
//
//	export RAPIDAPI_KEY=your_key_here   # free at https://rapidapi.com/flybyapi1/api/google-serp-search-api
//	go run ./api-scraper -q "golang web scraper"
//
// API landing page: https://flybyapis.com/apis/google-search/
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"time"
)

const apiHost = "google-serp-search-api.p.rapidapi.com"

// searchResponse mirrors the shape the API returns. We only model the fields
// we care about; encoding/json ignores the rest.
type searchResponse struct {
	Data struct {
		OrganicResults []struct {
			Title       string `json:"title"`
			Link        string `json:"link"`
			Description string `json:"description"`
			Position    int    `json:"position"`
			Domain      string `json:"domain"`
		} `json:"organic_results"`
	} `json:"data"`
}

func main() {
	q := flag.String("q", "web scraping golang", "search query")
	gl := flag.String("gl", "us", "country code")
	num := flag.Int("num", 10, "number of results (1-100)")
	flag.Parse()

	key := os.Getenv("RAPIDAPI_KEY")
	if key == "" {
		log.Fatal("set RAPIDAPI_KEY (get one free at https://rapidapi.com/flybyapi1/api/google-serp-search-api)")
	}

	results, err := searchGoogle(*q, *gl, *num, key)
	if err != nil {
		log.Fatalf("search: %v", err)
	}

	fmt.Printf("Top %d results for %q:\n\n", len(results.Data.OrganicResults), *q)
	for _, r := range results.Data.OrganicResults {
		fmt.Printf("%2d. %s\n    %s\n\n", r.Position, r.Title, r.Link)
	}
}

func searchGoogle(query, gl string, num int, key string) (*searchResponse, error) {
	endpoint := fmt.Sprintf("https://%s/search", apiHost)
	req, err := http.NewRequest(http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, err
	}

	params := url.Values{}
	params.Set("q", query)
	params.Set("gl", gl)
	params.Set("num", fmt.Sprintf("%d", num))
	req.URL.RawQuery = params.Encode()

	req.Header.Set("X-RapidAPI-Key", key)
	req.Header.Set("X-RapidAPI-Host", apiHost)

	client := &http.Client{Timeout: 20 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("status %d: %s", resp.StatusCode, body)
	}

	var out searchResponse
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, err
	}
	return &out, nil
}
