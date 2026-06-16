package main

import (
	"github.com/gocolly/colly/v2"
	"github.com/gocolly/colly/v2/proxy"
)

// proxySwitcher returns a colly.ProxyFunc that rotates round-robin through the
// given proxy URLs. Each URL must include the scheme, e.g.
// "http://user:pass@host:port" or "socks5://host:port".
func proxySwitcher(urls []string) (colly.ProxyFunc, error) {
	return proxy.RoundRobinProxySwitcher(urls...)
}
