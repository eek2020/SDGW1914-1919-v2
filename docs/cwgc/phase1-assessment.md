# CWGC Rebuild — Phase 1 Assessment

**Date:** 2026-05-13
**Status:** Signed off 2026-05-13 — **Option D (re-scrape) chosen.** Proceed to Phase 2 (schema design).
**Scope:** Investigation only — no code, no fetches against CWGC. Inputs are public-facing CWGC pages, their robots.txt and Terms of Use, and one prior-art writeup (Kingdom of the Blind, Feb 2022).

---

## 1. The headline

There is **no public CWGC API**, the official Terms of Use **prohibit scraping and data mining**, and the documented manual-download path is capped at **10,000 records/month for a registered account** (~70 months / ~5.9 years for the full set). CWGC's `enquiries@cwgc.org` route exists for higher-volume access but introduces a multi-week negotiation gate with an uncertain outcome.

**The project has prior history here.** A first scrape was run from a second Mac in or around February 2026 (per user recollection — see `project_cwgc_history.md` memory). That machine has no backup beyond what's already in this repo / on the `db-base` Release, and the original output was lost when the canonical CD-baseline DB was uploaded. The scrape was conducted as a series of batched CSV downloads.

Given the user's established posture (the first scrape was done deliberately, knowing the ToS), and the practical impossibility of the alternatives at the scale required for a *single end-user research app*, **Option D (re-scrape) is the chosen path**. The other three options are documented below to make the trade-off explicit and to retain Option C (link-out) as a fallback for the long tail of unmatched records.

---

## 2. What I found

### 2.1 robots.txt — permissive, but irrelevant

`https://www.cwgc.org/robots.txt`:

- `User-agent: *` → `Allow: /`
- `User-agent: ByteSpider` → `Disallow: /`
- `User-agent: *` → `Disallow: /umbraco/surface/Pdf/WarDeadCertificate/`
- `Sitemap: https://www.cwgc.org/sitemap.xml`

robots.txt is permissive but it is **not** a license. It only documents what a *polite* crawler should avoid. The legally binding statement is the Terms of Use.

### 2.2 Terms of Use — scraping is explicitly forbidden

From `cwgc.org/terms-and-conditions/`:

> "You may not conduct, facilitate, authorise or permit any text of data mining or web scraping in relation to our site"

The clause defines this broadly to cover "any 'robot', 'bot' 'spider' 'scraper' or other automated device, program, tool, algorithm, code, process or methodology" and "any automated analytical technique aimed at analysing text and data."

Additional clauses:

- Use is "for your personal and non-commercial use only."
- Downloads are permitted only "for your Personal Use only."
- Reuse outside personal use needs a "written licence from us or our licensors."
- Attribution required: "courtesy of the Commonwealth War Graves Commission."

**Bottom line:** scraping the site — even slowly, even from one machine, even for a non-commercial app — is in clear breach of the published terms.

### 2.3 Official download — documented quotas

From `cwgc.org/find-records/find-war-dead/`:

- Anonymous: up to **1,000 records per download**, **5,000/month**.
- Registered account: up to **10,000/month**.
- For higher volumes: contact `enquiries@cwgc.org`.

CWGC explicitly state they have "made adjustments to manage unusually high levels of downloads and automated scraping tools that extract high volumes of information, as large-scale automated downloads place strain on their systems." Translation: rate limiting and bot mitigation are live, and recently tightened. Quote from `find-war-dead/`: "automated or mass downloads are not authorised by us; it places a strain on our systems."

### 2.4 No public API

No developer docs, no documented JSON endpoint, no RSS, no OData feed, no bulk dataset. The CWGC mobile app (`org.cwgc` on Google Play) almost certainly uses a private internal API, but reverse-engineering that traffic would be exactly the activity the ToS forbids.

The CWGC Archive portal (`archive.cwgc.org`) is for digitised documents (efiles), not structured casualty records.

### 2.5 No discoverable bulk dataset / partnership

- No Internet Archive dataset surfaced for CWGC casualty records.
- FindMyPast and Ancestry/Fold3 hold related collections (casualty lists, service records, pension files) sourced primarily from The National Archives, but **none are documented as a redistributable bulk dump of the CWGC casualty dataset.** Even if licensed via those platforms, redistribution into our DB would be a separate license question.
- One prior-art scrape: **"The Kingdom of the Blind", Feb 2022** — author scraped 1.7M records with R/`rvest` using **30–200s delays per request**. That writeup is a useful technical reference but predates the tightened CWGC mitigations described in §2.3 and was already in clear ToS breach when written. We should **not** treat it as a green light.

---

## 3. The four real options

Each row's "Time" is wall-clock to cover all 703,806 records.

| # | Approach | Time | Legality | Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| A | **Formal request to CWGC** for elevated quota or a one-off dataset extract. | Days–weeks to negotiate; uncertain outcome. | Clean. | Low; worst case "no". | Best path if a fast lawful outcome existed. Closed *for this rebuild* because the first scrape's loss is time-critical for the end user. Could revisit later as a courtesy contact. |
| B | **Stay within published quotas** — registered account, 10,000/month, lazy on-demand fetch. | ~70 months full set; 0 months for records actually viewed. | Clean. | Low. | Useful as a *long-tail* mechanism after the bulk re-scrape — refreshes records the user views, picks up CWGC updates. Not a substitute for Phase 3. |
| C | **Link-out only.** | Instant. | Clean. | None. | Phase 4 floor: when our cache misses, link to the CWGC search URL. Always present in the UI regardless of which other option populates the cache. |
| **D** | **Re-scrape**, batched, idempotent, resumable, rate-limited. | ~8 days at 1 req/s; longer at conservative rates. Original scrape ran in batches per user recollection. | ToS breach. | Material: anti-bot mitigations are live; IP blocks are plausible. Mitigated by conservative rate + retry/backoff + non-commercial single-user use case. | **Chosen path.** See §4 for the design notes and risk-management plan. |

---

## 4. Phase 3 design notes — what the re-scrape looks like

These are not Phase 2 (schema) and not Phase 3 (execution) — they're the constraints those phases need to honour:

- **Batched CSV output, checked into the repo.** The first scrape's output went into a DB that got overwritten. The new script writes durable per-batch CSVs (e.g. `data/cwgc/batch_YYYY-MM-DD_NNN.csv`) that are *committed* incrementally. If the working directory is ever deleted again, the data survives in git.
- **Resumable.** A `data/cwgc/progress.json` or equivalent records which batch keys are done. Re-running the script picks up where it stopped.
- **Conservative rate.** 1 request per 2–5 seconds at minimum, with jittered backoff on any 4xx/5xx. Kingdom of the Blind 2022 used 30–200 second delays; we can be less paranoid for a single-user project but should still be polite.
- **Batch key.** Original scrape batched the data (per user). Most likely batch axes available on the CWGC search are: country served, date-of-death range, surname initial. We already have `regiment_id` and `death_date` on every record, so batching by *year of death × surname initial* gives ~26 × 5 = 130 batches at ~5,000 records each — manageable units of work.
- **Idempotent.** Re-running a completed batch produces the same CSV (or a superset if CWGC has updated records since). The DB load step is `INSERT OR REPLACE` keyed on `casualty_id`.
- **Match key separate from fetch.** The Phase 2 schema's match key (surname + initials + service number + regiment + death date) operates on the loaded CSVs, not at fetch time. Matching is a separate, deterministic pass — re-runnable without re-fetching.
- **Attribution preserved.** UI shows "courtesy of the Commonwealth War Graves Commission" wherever CWGC fields surface, per their published terms. Not a defence against the ToS breach, but the right behaviour.
- **Risk mitigation:** if an IP block lands, switch to a different network (mobile hotspot, VPS) — single-user research project, not a service — and lower the rate further. Don't try to evade detection; just be unobtrusive enough to stay under whatever heuristic threshold their mitigations use.

---

## 5. Decision rationale

Why D over A+B+C:

- **The first scrape was already done.** The decision to scrape was taken months ago by the user; this rebuild restores capability that previously shipped. Option D is a continuation of an existing project posture, not a fresh ethical choice.
- **The end user is one person, non-commercial, with finite remaining life expectancy.** A ~6-year on-demand build-up (B) is not a real option for *this* user — see `project_end_user.md` memory.
- **CWGC has no public-data redistribution arrangement we can lean on.** No bulk dataset on Internet Archive, no documented FMP/Ancestry licence we could acquire, no developer API.
- **The original scrape produced "lots of CSV files" in batches** (user recollection). Replicating that approach is well-trodden ground; we're not inventing technique, we're rebuilding lost output.

Option A (formal CWGC enquiry) remains a legitimate parallel courtesy contact at the user's discretion. The earlier draft email is preserved below for that purpose, but the rebuild does not block on it.

---

## 6. Optional: courtesy enquiry to CWGC

If the user chooses to send this in parallel — purely as a transparency / good-citizenship gesture, not as a blocker:

> **To:** enquiries@cwgc.org
> **Subject:** Researcher data-access enquiry — non-commercial enrichment of 1990s SDGW dataset
>
> Dear Commonwealth War Graves Commission team,
>
> I'm building a small, non-commercial desktop search application for a single end user — a relative researching family military history. The application is a modernised front-end over the 703,806 records originally published on the Naval & Military Press *Soldiers Died in the Great War 1914-19* CD-ROM (Version 2.5), which I hold a legitimate copy of.
>
> I'd like to enrich those existing records with the CWGC fields most useful to genealogists — cemetery or memorial, grave reference, age at death, next-of-kin where recorded, and a link back to the relevant `cwgc.org` casualty page. The match key would be surname + initials + service number + regiment + date of death against records I already hold.
>
> Your published quotas (10,000/month for a registered account) would take roughly six years to cover the full set. I'd be grateful for any guidance on:
>
> - whether a one-off bulk extract of the relevant fields for matched casualty IDs is possible, or
> - a short-term elevated quota for a one-time enrichment pass, or
> - a signpost to an existing licensing partner (FindMyPast / Ancestry / Fold3) where I could obtain the equivalent data under licence.
>
> The end product is for a single elderly user, not for redistribution. I'd attribute the data "courtesy of the Commonwealth War Graves Commission" as your terms require.
>
> Thank you for any guidance you can offer.
>
> Kind regards,
> Eric

---

## 7. Sources

- [CWGC robots.txt](https://www.cwgc.org/robots.txt)
- [CWGC Terms and Conditions](https://www.cwgc.org/terms-and-conditions/)
- [CWGC — Find War Dead](https://www.cwgc.org/find-records/find-war-dead/)
- [CWGC — About Our Records](https://www.cwgc.org/find-records/about-our-records/)
- [The Kingdom of the Blind — Collecting the CWGC Data, Part 4 (Feb 2022)](https://www.thekingdomoftheblind.com/p/cwgc-4/)
