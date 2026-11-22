# Launch Checklist - Aether AI Intelligence

All launch gate items required prior to public production deployment:

- [ ] Custom domain connected, DNS records verified, HTTPS active, www and apex both resolve, one redirects to the other (manual: owner).
  - DNS Record 1 (Apex): A record pointing `@` to hosting server IPv4 address.
  - DNS Record 2 (WWW): CNAME record pointing `www` to apex domain or hosting provider target.
  - TLS: Automated Let's Encrypt / Caddy certificate issuance.
- [x] Favicon added: favicon.svg, favicon.ico (32x32), apple-touch-icon.png (180x180), plus site.webmanifest. The mark is flat, no gradient, legible at 16px, and matches the logo.
- [x] "Made with AI" tag, generator meta tag, and any builder watermark removed from HTML, footer, meta tags, and comments.
- [ ] /privacy page live, linked from the footer, every TODO(owner) resolved by me.
- [ ] /terms page live, linked from the footer, every TODO(owner) resolved by me.
- [ ] Legal text reviewed by a qualified person (manual: owner).
- [x] Open Graph and Twitter card tags set with accurate title and meta description.
- [x] robots.txt and sitemap.xml present.
- [x] No third-party requests that are not disclosed in the privacy policy (self-hosted fonts, zero external font CDNs or analytics scripts).
- [x] All audit checks in Section 12 pass (verified via scripts/audit.sh).
- [x] Lighthouse and axe results attached in final report.
- [x] Every number on screen traced to a real source (verified with data-source attributes and SQLite queries).

