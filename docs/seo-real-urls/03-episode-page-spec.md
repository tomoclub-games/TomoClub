# Episode page spec: `podcast-<id>/`

Status: **approved by Rohith, 2026-10-26.**

Phase F, step F2. Task spec: `00-context.md` §15.

---

## 1. Goal

Every episode of The Learning Shift podcast gets a real page at `https://www.tomoclub.org/podcast-<id>` with its own title, description and video. All 107 pages are generated from `podcasts_data.js`, so they never drift from the data again.

Today the 68 existing pages are empty shells (blank `<title>` and `<h1>`, speaker "TomoClub Guest", date "January 01, 1970", duration 0:00), and 39 episodes have no page.

---

## 2. Source data

`podcasts_data.js`, one entry per YouTube id (checked 2026-10-26):

| Field | State |
|---|---|
| `title` | All 107 set. 33 contain HTML entities such as `&amp;`. Up to 100 characters, average 62 |
| `speaker` | 23 are the placeholder "TomoClub Guest" |
| `date` | All 107 set, format "January 29, 2026" |
| `duration` | All set, format `m:ss` or `mm:ss` (no episode is over an hour) |
| `thumbnail` | All match their own id |
| `description` | HTML. 61 share one generic text ("In this episode, we dive into the latest trends…") and 17 share another ("…host Shreya sits down to explore the realities of leading effectiv…"). 29 are unique |

`podcasts_data.js` stays the single source. `podcast-player.html` keeps reading it until the redirect replaces it.

---

## 3. Page content

Built with the shared layout (`_partials/layout.html`): same head, navbar, footer, CTA and scripts as every other page. The body comes from a new `_partials/episode.html`:

1. Back link "All episodes" to `/podcast`.
2. `<h1>` = episode title.
3. Meta bar: speaker (left out when it is "TomoClub Guest"), date, duration.
4. YouTube embed: `https://www.youtube-nocookie.com/embed/<id>?rel=0`, 16:9, `loading="lazy"`, `title` attribute = episode title (accessibility).
5. Description card: the stored description HTML, sanitised to `<p>`, `<a>`, `<strong>`, `<em>`, `<ul>`, `<ol>`, `<li>`, `<br>`.
6. "Watch on YouTube" link to `https://www.youtube.com/watch?v=<id>`.
7. "More episodes": the 3 newest other episodes as cards linking to `/podcast-<id>`. This gives every page unique internal links and helps crawling.

The episode CSS (about 230 lines inside each shell page today) moves once into `styles.css`, under `.episode-*` class names.

---

## 4. Title and description rules

Each page must have a unique `<title>` and meta description, even when the stored description is generic.

- **`<title>`** = `{title} | The Learning Shift Podcast`. If that is longer than 70 characters, use `{title} | TomoClub`.
- **Meta description** and social description:
  - when the stored description is unique: its first sentence or 155 characters of plain text, whichever is shorter;
  - when it is one of the two generic texts: `{speaker} joins The Learning Shift to talk about {title}. A TomoClub podcast episode, {date}.` Without a real speaker: `{title}: an episode of The Learning Shift, the TomoClub podcast for school leaders. {date}.`
- **Social image** = `https://img.youtube.com/vi/<id>/maxresdefault.jpg`.
- **Canonical** and `og:url` = `https://www.tomoclub.org/podcast-<id>`, no trailing slash.
- HTML entities in titles are decoded for the JSON-LD and re-escaped once for HTML.

---

## 5. Structured data

One JSON-LD block per page:

```json
{
  "@context": "https://schema.org",
  "@type": "PodcastEpisode",
  "name": "<title>",
  "url": "https://www.tomoclub.org/podcast-<id>",
  "datePublished": "<YYYY-MM-DD>",
  "timeRequired": "PT<m>M<s>S",
  "description": "<meta description>",
  "partOfSeries": { "@type": "PodcastSeries", "name": "The Learning Shift", "url": "https://www.tomoclub.org/podcast" },
  "actor": [{ "@type": "Person", "name": "<speaker>" }],
  "associatedMedia": {
    "@type": "VideoObject",
    "name": "<title>",
    "description": "<meta description>",
    "thumbnailUrl": "https://img.youtube.com/vi/<id>/maxresdefault.jpg",
    "uploadDate": "<YYYY-MM-DD>",
    "duration": "PT<m>M<s>S",
    "embedUrl": "https://www.youtube-nocookie.com/embed/<id>",
    "contentUrl": "https://www.youtube.com/watch?v=<id>"
  }
}
```

`actor` is left out for "TomoClub Guest".

---

## 6. Build

- `build_podcast_pages.py` at the repo root, Python standard library only.
- It reads `podcasts_data.js` (handles both `"..."` and `` `...` `` strings), builds front-matter values and blocks for each episode in memory, and calls `render()` from `build_pages.py`. No 107 source files in `pages/`.
- It writes `podcast-<id>/index.html` for every episode and replaces the 68 shells.
- `--check` exits 1 if any committed episode page differs from a fresh build, like `build_pages.py --check`.
- `add_podcast_episode.py` runs it after updating `podcasts_data.js`.

---

## 7. Acceptance

1. 107 `podcast-<id>/index.html` exist, one per entry in `podcasts_data.js`.
2. No two pages share a `<title>` or a meta description.
3. Every page has one `<h1>`, a canonical, the video embed, and valid JSON-LD (parses as JSON; required fields present).
4. `build_podcast_pages.py --check` exits 0.
5. Headless Chrome screenshots of 3 episodes (unique description, generic description, generic speaker) at desktop and mobile width look right.
