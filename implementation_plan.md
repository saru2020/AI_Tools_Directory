```text
AI Tools Directory - Implementation Plan (Frappe)

Goal: Launch a fully functional AI tools directory in 1 week with ALL core + growth + differentiation features live.
Approach: MVP-first, rapid iteration, parallelize tasks.

---

Day 1: Setup & Foundations
- [x] Environment Setup
  - [x] Install Frappe bench
  - [x] Create new site + new app
  - [x] Configure MariaDB, Redis
  - [x] Init repo + push to GitHub
- [x] CI/CD
  - [x] Setup GitHub Actions workflow for deploy
  - [x] Configure staging (local) + prod (VPS or Docker)
- [ ] Theme/UI
  - [ ] Pick Frappe theme
  - [ ] Add navbar (Home, Categories, Submit Tool, Blog)

- [x] Prerequisites
  - [x] Pin Python, Node/Yarn, Frappe/bench versions
  - [x] Install Redis and MariaDB locally
  - [x] Create .env and set up secrets management
- [x] Repo Hygiene
  - [x] Add .editorconfig, pre-commit with black/isort/ruff and eslint/prettier
  - [x] Add CONTRIBUTING.md with setup, branching, and PR rules
- [x] CI/CD Enhancements
  - [x] Cache bench/node/pip deps; run unit tests and build assets
  - [x] Add database migration step; deploy with rollback
  - [x] Keep environment parity between staging and prod
- [ ] Ops
  - [ ] Domain + TLS plan
  - [ ] Backups/restore strategy
  - [ ] Sentry/error reporting and basic logs/metrics

---

Day 2: Database Schema (Doctypes)
- [x] Tool
  - [x] Fields: Name, Slug, Description, Pricing (Free, Freemium, Paid), Website, Tags, Logo, Category Link
- [x] Category
  - [x] Fields: Name, Slug, Description
- [x] Stack
  - [x] Fields: Name, Description, Tool Links (multi)
- [x] Review
  - [x] Fields: User, Rating (1-5), Comment, Tool Link
- [x] Extend Frappe User
  - [x] Use Frappe auth; add custom profile fields (username, avatar)
- [x] Constraints and Indexes
  - [x] Unique indexes for Tool.slug and Category.slug
  - [x] Field length limits and URL validation
  - [x] Rating field constrained to 1-5
- [x] Tags and Relationships
  - [x] Use Frappe tagging or child table for many-to-many tags; add indexes
- [ ] Permissions and Roles
  - [ ] Roles: Admin, Moderator, Author, Authenticated, Guest
  - [ ] Permission matrix per doctype
  - [ ] Workflows for Tool and Review
- [ ] Derived Data
  - [ ] Tool.average_rating, review_count, click_count, upvote_count recomputed in background

---

Day 3: Core Features
- [ ] Directory Pages
  - [ ] Tool listing grid
  - [ ] Category filter
  - [ ] Search bar
- [ ] Tool Detail Page
  - [ ] Show description, pricing, tags
  - [ ] Show reviews
  - [ ] "Similar tools" (same category)
- [ ] Category Pages
  - [ ] Tools grouped by category
- [ ] Admin Dashboard
  - [ ] CRUD for tools, categories, stacks
  - [ ] Basic analytics (views/clicks logging)

- [ ] UX/SEO Enhancements
  - [ ] Pagination and sorting (Newest, Popular, Top Rated) on listings
  - [ ] SEO-friendly URLs: /tools/<slug>, /categories/<slug>, /collections/<slug>
  - [ ] JSON-LD structured data and canonical tags on detail pages
  - [ ] Image handling: logo upload, resizing, WebP, caching/CDN headers

---

Day 4: Content Seeding + Submissions
- [x] Scraper/ETL
  - [x] Build Python script to scrape 200+ tools (from public directories)
  - [x] Normalize fields into CSV
  - [ ] Import into Frappe with Data Import
- [ ] Submission Form
  - [ ] Public "Submit a Tool" page
  - [ ] Store as draft in Tool
  - [ ] Workflow: Draft -> Admin Review -> Published
- [ ] SEO Setup
  - [ ] Meta tags + OpenGraph per page
  - [ ] Auto sitemap.xml + robots.txt

- [ ] Scraping Quality & Compliance
  - [ ] Source list, deduplication by domain+name, rate limiting, respect robots.txt
  - [ ] Track source provenance and licensing
- [ ] ETL Idempotency
  - [ ] Stable IDs and upsert strategy
- [ ] Spam & Moderation
  - [ ] Human/bot verification (hCaptcha/Cloudflare Turnstile)
  - [ ] Email verification required for publishing
  - [ ] Moderation queue with email/Slack notifications

---

Day 5: Differentiation Features
- [ ] Tool Stacks
  - [ ] Create 5 curated stacks manually
  - [ ] Render stacks on site
- [ ] Comparison Engine
  - [ ] Multi-select tools -> Compare page
  - [ ] Show feature matrix (pricing, integrations, etc.)
- [ ] AI Search Assistant
  - [ ] Install RedisSearch
  - [ ] Generate embeddings for tool descriptions
  - [ ] Implement semantic search endpoint
  - [ ] Add chat-style UI: "Find me AI for X"

- [ ] Comparison Schema
  - [ ] Define feature schema (boolean/numeric/text) and groups; handle missing data gracefully
- [ ] AI Search Details
  - [ ] Choose embedding model and storage (Redis Stack or FAISS/SQLite)
  - [ ] Background jobs for embedding and re-embedding; incremental updates on changes
  - [ ] Privacy note and opt-out for tool owners

---

Day 6: Community Layer
- [ ] Reviews
  - [ ] Add review form on tool pages
  - [ ] Store rating + comment + user link
- [ ] Reviews Moderation & Rules
  - [ ] One review per user per tool; edit/delete window; flag/report abuse; moderator tools
- [ ] Voting
  - [ ] Add upvote button (per tool)
  - [ ] Show "Most Upvoted Tools"
- [ ] Voting Anti-abuse
  - [ ] One vote per user/tool; rate limiting; basic IP/device heuristics; cache hot lists
- [ ] Collections
  - [ ] Allow users to save tools into custom stacks
  - [ ] Publicly share collections (URLs)
- [ ] Collections Visibility
  - [ ] Private, unlisted, and public options with owner controls

---

Day 7: Monetization + Polish
- [ ] Monetization
  - [ ] Add Google AdSense script
  - [ ] Add "Featured Tool" field in Tool (for sponsor placement)
  - [ ] Affiliate link support (track clicks)
- [ ] Content Marketing
  - [ ] Add Blog module
  - [ ] Publish 3 SEO articles:
  - Best Free AI Tools in 2025
  - Top AI Tools for Students
  - AI Stack for Content Creators
- [ ] Final QA
  - [ ] Cross-browser check
  - [ ] Mobile responsive test
  - [ ] Fix dead links
  - [ ] Deploy production site

- [ ] Ads/Affiliate Compliance
  - [ ] Consent management (GDPR/CCPA), sponsorship disclosure
  - [ ] UTM tracking taxonomy; noindex on ad-only pages if needed
- [ ] Blog Enhancements
  - [ ] Categories/tags, RSS feed, draft review flow, author profiles

---

Cross-cutting

- [ ] Accessibility (WCAG AA), keyboard navigation, color contrast
- [ ] Performance budgets (TTFB, LCP), HTTP caching, Redis cache, image lazy-load
- [ ] Testing: unit tests and smoke E2E (list, detail, submit), link checker in CI
- [ ] Analytics: GA4/PostHog taxonomy (search, filter, detail view, outbound click, upvote, review submit)
- [ ] Internationalization (optional later)
- [ ] Risk register, rollback and hotfix playbook

---

Launch Deliverables (End of Week)
- Live website with:
  - [x] 200+ seeded AI tools
  - [x] Categories, search, tool detail pages
  - [x] Submission form & moderation
  - [x] Tool stacks & comparisons
  - [x] AI semantic search assistant
  - [x] Reviews, voting, collections
  - [x] Ads + featured listings enabled
  - [x] Blog with 3 starter SEO posts
- Deployed to production server
- CI/CD pipeline ready for updates

- Acceptance criteria:
  - Search returns relevant results within 500ms P95
  - 200+ tools deduplicated with logo, description, and category
  - Pages have valid structured data and pass basic SEO audits
  - Error rate < 1% and uptime > 99.9% during launch window
```

