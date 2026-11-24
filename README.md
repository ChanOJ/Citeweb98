# Citeweb98

**Citeweb (1998 redesign).** Citeweb was a free web host for French-language personal sites, run by volunteers from 1996 until it was sold in 1999. This archive keeps its 1998 framed interface ("CITEWEB - votre espace d'expression sur internet"): sign-up and hosting rules, contact page and the help pages (FTP, e-mail, newsgroups, IRC services, FAQ). The full 1997 site is [Citeweb97](https://citeweb97.sauthier.family).

Archive of an old static website, served as-is from bunny.net at the hostname
of [`site.json`](site.json). Kept online for history, no longer developed.

Full list of the sites: https://chanoj.github.io/

## Layout

| Path | Content |
| --- | --- |
| `site/` | The website files, exactly as served (generated, committed) |
| `site.json` | The only site-specific settings: repository, storage zone, pull zone, hostname, 404 page |
| `scripts/build.py` | Generates `site/` from the raw store (`$CITEWEB_RAW`, default `~/Code/Citeweb/raw`), then runs `seo.py` |
| `scripts/seo.py` | `robots.txt`, `sitemap.xml`, and the `frame-restore.js` tag in every page |
| `scripts/frame-restore.js` | A page opened on its own reopens inside the nested framesets (no loop) |
| `scripts/check_excludes.py` | Fails if engine code, backups, forms or server markup reach `site/` |
| `infra/` | OpenTofu: storage zone, pull zone, hostname (state encrypted, committed) |
| `infra/secrets.env` | Proton Pass **references** to the secrets (vault `OldSites`), no secret values |
| `scripts/deploy.py` | Sync `site/` to the storage zone, purge the CDN |
| `scripts/smoke_test.py` | Check that the public site serves the files of `site/` |

DNS is not managed here: the hostname is a CNAME to `<pull zone>.b-cdn.net` at Infomaniak.

## What is left out

Pages that needed the server (member area, forums, member directory, search, counters, forms), engine code, and the history/administrator pages. Links that needed the server become plain text; other external links are kept and open in a new window. Personal e-mail addresses are masked as `local@????`; role addresses (`tech@`, `irc@`...) and the sample addresses of the help pages are kept. Visitor data in the samples (IP, host) is replaced by `????`. The frame fragments and empty directory pages are `noindex` and out of the sitemap.

## Deploying

- **Website**: push a change under `site/` to `main` → workflow *Website: deploy* uploads the changed files, deletes the removed ones, purges the CDN and runs the smoke test.
- **Infra**: pull requests touching `infra/` show the plan; apply is a manual run of *Infra: bunny.net*.

GitHub secrets: `BUNNY_API_KEY` and `TF_VAR_STATE_PASSPHRASE`, both from Proton Pass vault `OldSites`.
