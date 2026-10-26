"""Build one page per podcast episode (podcast-<id>/index.html) from podcasts_data.js.

Pages use the shared layout in _partials/ and the episode body in _partials/episode.html,
rendered through build_pages.render(). See docs/seo-real-urls/03-episode-page-spec.md.

Usage (from the repo root):
    py scripts/build_podcast_pages.py           # write every episode page
    py scripts/build_podcast_pages.py --check   # exit 1 if any committed episode page differs from a fresh build
"""
import html
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser

from build_pages import ROOT, BuildError, read, render

DATA = os.path.join(ROOT, "data", "podcasts_data.js")
SITE = "https://www.tomoclub.org"
GENERIC_SPEAKER = "TomoClub Guest"
SERIES = "The Learning Shift"
ALLOWED_TAGS = {"p", "a", "strong", "em", "ul", "ol", "li", "br"}


def load_episodes():
    """Parse podcasts_data.js: an object of id -> {field: "string" | `template string`}."""
    text = read(DATA)
    starts = list(re.finditer(r'^  "([\w-]+)": \{$', text, re.M))
    if not starts:
        raise BuildError("podcasts_data.js: no episodes found")
    episodes = []
    for i, m in enumerate(starts):
        chunk = text[m.end():starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        fields = {}
        for f in re.finditer(r'"(\w+)":\s*("(?:[^"\\]|\\.)*"|`[^`]*`)', chunk):
            raw = f.group(2)
            fields[f.group(1)] = json.loads(raw) if raw.startswith('"') else raw[1:-1]
        missing = {"title", "date", "duration"} - fields.keys()
        if missing:
            raise BuildError(f"podcasts_data.js: episode {m.group(1)} has no {', '.join(sorted(missing))}")
        fields["id"] = m.group(1)
        episodes.append(fields)
    return episodes


class Sanitizer(HTMLParser):
    """Keep a small set of formatting tags; drop every other tag but keep its text."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            return
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if not re.match(r"^(https?://|/)", href):
                return
            self.out.append(f'<a href="{html.escape(href)}" target="_blank" rel="noopener noreferrer">')
        else:
            self.out.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in ALLOWED_TAGS and tag != "br":
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        self.out.append(data)

    def handle_entityref(self, name):
        self.out.append(f"&{name};")

    def handle_charref(self, name):
        self.out.append(f"&#{name};")


def sanitize(fragment):
    s = Sanitizer()
    s.feed(fragment)
    s.close()
    return "".join(s.out).strip()


def plain(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


ABBREVIATIONS = {"dr", "mr", "mrs", "ms", "st", "jr", "sr", "prof", "vs", "etc", "e.g", "i.e"}


def summary(text, limit=155):
    """First sentence, or the first `limit` characters cut at a word, whichever is shorter."""
    for m in re.finditer(r"[.!?](?=\s)", text):
        last_word = re.split(r"\s", text[:m.start()])[-1].lower()
        if last_word in ABBREVIATIONS or m.end() < 60:
            continue  # "Dr." or a very short fragment is not the end of a useful sentence
        if m.end() <= limit:
            return text[:m.end()]
        break
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def iso_duration(duration):
    parts = [int(p) for p in duration.split(":")]
    hours, minutes, seconds = ([0] * (3 - len(parts)) + parts)[-3:]
    return "PT" + (f"{hours}H" if hours else "") + f"{minutes}M{seconds}S"


def attr(text):
    return html.escape(text, quote=True)


def card(ep):
    title = attr(ep["title_text"])
    return f'''                <a href="/podcast-{ep["id"]}" class="glass-card podcast-card">
                    <img src="https://img.youtube.com/vi/{ep["id"]}/hqdefault.jpg" alt="{title}" loading="lazy" style="width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 12px; margin-bottom: 1rem;">
                    <span style="font-size: 0.75rem; color: var(--teal); font-weight: 700; text-transform: uppercase;">{ep["date"]} · {ep["duration"]}</span>
                    <h3 style="font-size: 1.15rem; margin-top: 0.5rem;">{title}</h3>
                </a>
'''


def build():
    episodes = load_episodes()
    shared = Counter(ep.get("description", "") for ep in episodes)
    for ep in episodes:
        ep["title_text"] = html.unescape(ep["title"])
        ep["published"] = datetime.strptime(ep["date"], "%B %d, %Y")
    newest = sorted(episodes, key=lambda e: e["published"], reverse=True)

    results = []
    for ep in episodes:
        vid, title = ep["id"], ep["title_text"]
        speaker = re.sub(r"^feat\.?\s+", "", ep.get("speaker", "").strip(), flags=re.I)
        has_speaker = bool(speaker) and speaker != GENERIC_SPEAKER
        stored = ep.get("description", "")
        iso_date = ep["published"].strftime("%Y-%m-%d")

        if stored and shared[stored] == 1:
            meta = summary(plain(stored))
        elif has_speaker:
            meta = f"{speaker} joins {SERIES} to talk about {title}. A TomoClub podcast episode, {ep['date']}."
        else:
            meta = f"{title}: an episode of {SERIES}, the TomoClub podcast for school leaders. {ep['date']}."

        page_title = f"{title} | {SERIES} Podcast"
        if len(page_title) > 70:
            page_title = f"{title} | TomoClub"
        canonical = f"{SITE}/podcast-{vid}"
        thumb = f"https://img.youtube.com/vi/{vid}/maxresdefault.jpg"
        duration = iso_duration(ep["duration"])

        ld = {
            "@context": "https://schema.org",
            "@type": "PodcastEpisode",
            "name": title,
            "url": canonical,
            "datePublished": iso_date,
            "timeRequired": duration,
            "description": meta,
            "partOfSeries": {"@type": "PodcastSeries", "name": SERIES, "url": f"{SITE}/podcast"},
        }
        if has_speaker:
            ld["actor"] = [{"@type": "Person", "name": speaker}]
        ld["associatedMedia"] = {
            "@type": "VideoObject",
            "name": title,
            "description": meta,
            "thumbnailUrl": thumb,
            "uploadDate": iso_date,
            "duration": duration,
            "embedUrl": f"https://www.youtube-nocookie.com/embed/{vid}",
            "contentUrl": f"https://www.youtube.com/watch?v={vid}",
        }
        ld_json = json.dumps(ld, ensure_ascii=False, indent=2).replace("</", "<\\/")
        ld_block = '    <script type="application/ld+json">\n' + "\n".join(
            "    " + line for line in ld_json.split("\n")) + "\n    </script>\n"

        description = sanitize(stored) if stored else ""
        if not description or shared[stored] > 1:
            # A generic stored text says nothing about this episode; show the specific summary instead.
            description = f"<p>{html.escape(meta)}</p>"
        description_block = "".join(f"            {line}\n" for line in description.split("\n") if line.strip())

        speaker_block = (f'            <span class="episode-meta-unit"><i data-lucide="user"></i> '
                         f'<strong>Speaker:</strong> {html.escape(speaker)}</span>\n') if has_speaker else ""
        more = "".join(card(other) for other in [e for e in newest if e is not ep][:3])

        values = {
            "source": "data/podcasts_data.js",
            "title": attr(page_title),
            "description": attr(meta),
            "keywords": attr(", ".join(["The Learning Shift", "TomoClub Podcast", "Education Podcast"]
                                       + ([speaker] if has_speaker else []))),
            "canonical": canonical,
            "social_description": attr(meta),
            "social_image": thumb,
            "heading": attr(title),
            "video_id": vid,
            "display_date": ep["date"],
            "duration": ep["duration"],
        }
        blocks = {"head_jsonld": ld_block, "speaker": speaker_block,
                  "description": description_block, "more": more}
        page = f"data/podcasts_data.js#{vid}"
        body = render("episode", page, values, blocks, "")
        results.append((f"podcast-{vid}/index.html", render("layout", page, values, blocks, body)))
    return results


def main():
    check = "--check" in sys.argv
    try:
        results = build()
    except BuildError as e:
        print(f"build_podcast_pages: {e}", file=sys.stderr)
        sys.exit(2)

    stale = []
    for output, page_html in results:
        target = os.path.join(ROOT, output)
        if check:
            if not os.path.isfile(target) or read(target) != page_html:
                stale.append(output)
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page_html)

    if check:
        if stale:
            print(f"{len(stale)} episode page(s) out of date; run py scripts/build_podcast_pages.py", file=sys.stderr)
            sys.exit(1)
        print(f"{len(results)} episode page(s) up to date")
    else:
        print(f"Wrote {len(results)} episode pages")


if __name__ == "__main__":
    main()
