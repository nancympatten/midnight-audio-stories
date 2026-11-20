#!/usr/bin/env python3
"""
Midnight Audio Stories — Static Website Generator

Usage:
    python3 build.py

Reads data.csv and generates a complete static website in dist/.

Features:
- Interactive bedtime story reader
- Personalized listener and narrator names
- Auto-scroll and adjustable reading size
- Browser-generated sleep soundscapes
- 18+ age confirmation
- Searchable story cards
- Category, subcategory and tag hubs
- Related stories and FAQs
- Google and Bing verification tags
- 10-site network interlinking
- SEO metadata and structured data
- XML sitemap, sitemap index and styled XSL
- Robots.txt, DMCA and 2257 information pages
- Build validation
"""

import os
import csv
import re
import json
import html
import math
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from urllib.parse import quote
from xml.etree import ElementTree


# ============================================================
# SITE CONFIGURATION
# ============================================================

BASE_URL = os.environ.get(
    "BASE_URL",
    "https://midnight-audio-stories.auravault.workers.dev"
).rstrip("/")

SITE_NAME = "Midnight Audio Stories"

NICHE_TOPIC = (
    "Immersive Adult Bedtime Stories, Sleep Fiction & Voice Scripts"
)

CONTACT_EMAIL = "nancympatten@gmail.com"

AFFILIATE_URL = "#affiliate-link"

AFFILIATE_CTA_TEXT = (
    "Listen to Interactive AI Voice Stories 24/7 (Free Trial)"
)

CURRENT_YEAR = datetime.utcnow().year

DATA_FILE = "data.csv"
OUTPUT_DIR = "dist"

ITEMS_PER_PAGE = 24
RELATED_COUNT = 8
NEWEST_COUNT = 30

RATING_META = "RTA-5042-1996-1400-1577-RTA"

GOOGLE_SITE_VERIFICATION = (
    "Ee2L9A2G2nVVNtBt7HiplcBJf1nSen-Rcz4sNqLuAdc"
)

BING_SITE_VERIFICATION = (
    "4573069C62AEC27DA4F08DC57760BAD4"
)

NETWORK_SITES = [
    (
        "AI Girlfriend Prompts",
        "https://ai-girlfriend-prompts.velvetgrid.workers.dev/"
    ),
    (
        "Couples Intimacy Games",
        "https://couples-intimacy-games.velvetgrid.workers.dev/"
    ),
    (
        "Fantasy Roleplay Hub",
        "https://fantasy-roleplay-hub.velvetgrid.workers.dev/"
    ),
    (
        "Character Persona Hub",
        "https://character-persona-hub.velvetgrid.workers.dev/"
    ),
    (
        "Flirty Chat Openers",
        "https://flirty-chat-openers.velvetgrid.workers.dev/"
    ),
    (
        "Midnight Audio Stories",
        "https://midnight-audio-stories.velvetgrid.workers.dev/"
    ),
    (
        "Spicy Party Games",
        "https://spicy-party-games.velvetgrid.workers.dev/"
    ),
    (
        "Intimacy Quiz Hub",
        "https://intimacy-quiz-hub.velvetgrid.workers.dev/"
    ),
    (
        "Couples Bucket List",
        "https://couples-bucket-list.velvetgrid.workers.dev/"
    ),
    (
        "Adult AI Art Prompts",
        "https://adult-ai-art-prompts.velvetgrid.workers.dev/"
    ),
]

COLUMNS = [
    "slug",
    "title",
    "category",
    "subcategory",
    "target_keyword",
    "story_text",
    "reading_minutes",
    "description",
    "tags",
    "faq_q1",
    "faq_a1",
    "faq_q2",
    "faq_a2",
    "upload_date",
]

COLORS = {
    "background": "#07090f",
    "card": "#111625",
    "card2": "#171e30",
    "border": "#252d42",
    "text": "#edf0fa",
    "muted": "#9ba6bd",
    "indigo": "#6366f1",
    "lavender": "#c084fc",
    "green": "#80d6ae",
}


# ============================================================
# GENERAL HELPERS
# ============================================================

def esc(value):
    return html.escape(str(value or ""), quote=True)


def slugify(value):
    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "uncategorized"


def safe_int(value, default=5):
    try:
        return max(1, int(float(value)))
    except (ValueError, TypeError):
        return default


def parse_tags(value):
    if not value:
        return []

    tags = re.split(r"[,;|]", str(value))
    result = []
    seen = set()

    for tag in tags:
        tag = tag.strip()
        key = slugify(tag)

        if tag and key not in seen:
            seen.add(key)
            result.append(tag)

    return result


def parse_date(value):
    value = str(value or "").strip()

    if not value:
        return datetime.min

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def json_ld(data):
    return json.dumps(
        data,
        ensure_ascii=False
    ).replace("</", "<\\/")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_file(path, content):
    ensure_dir(os.path.dirname(path) or ".")

    with open(
        path,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as file:
        file.write(content)


def canonical(path=""):
    return BASE_URL + (
        "/" + path.lstrip("/") if path else "/"
    )


# ============================================================
# CSV READER
# ============================================================

def read_data():
    if not os.path.isfile(DATA_FILE):
        raise FileNotFoundError(
            "data.csv was not found. Place data.csv beside build.py."
        )

    rows = []
    used_slugs = set()

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        missing = [
            column
            for column in COLUMNS
            if column not in (reader.fieldnames or [])
        ]

        if missing:
            raise ValueError(
                "Missing required CSV columns: "
                + ", ".join(missing)
            )

        for line_number, raw in enumerate(reader, start=2):

            row = {
                key: (raw.get(key) or "").strip()
                for key in COLUMNS
            }

            if not row["title"] or not row["story_text"]:
                print(
                    "Skipping incomplete CSV row:",
                    line_number
                )
                continue

            original_slug = slugify(
                row["slug"] or row["title"]
            )

            slug = original_slug
            suffix = 2

            while slug in used_slugs:
                slug = f"{original_slug}-{suffix}"
                suffix += 1

            used_slugs.add(slug)

            row["slug"] = slug

            row["category"] = (
                row["category"] or "Uncategorized"
            )

            row["subcategory"] = (
                row["subcategory"] or "General Stories"
            )

            row["category_slug"] = slugify(
                row["category"]
            )

            row["subcategory_slug"] = slugify(
                row["subcategory"]
            )

            row["tags_list"] = parse_tags(
                row["tags"]
            )

            row["reading_minutes"] = safe_int(
                row["reading_minutes"]
            )

            row["date_obj"] = parse_date(
                row["upload_date"]
            )

            row["upload_date"] = (
                row["date_obj"].strftime("%Y-%m-%d")
                if row["date_obj"] != datetime.min
                else ""
            )

            row["target_keyword"] = (
                row["target_keyword"] or row["title"]
            )

            row["description"] = (
                row["description"]
                or (
                    f"Explore {row['title']}, an immersive "
                    f"bedtime story from {SITE_NAME}."
                )
            )

            rows.append(row)

    if not rows:
        raise ValueError(
            "data.csv contains no usable story records."
        )

    return rows


# ============================================================
# GLOBAL CSS
# ============================================================

GLOBAL_CSS = r"""
:root {
    color-scheme: dark;
    --bg: #07090f;
    --card: #111625;
    --card2: #171e30;
    --border: #252d42;
    --text: #edf0fa;
    --muted: #9ba6bd;
    --indigo: #6366f1;
    --lavender: #c084fc;
    --green: #80d6ae;
    --radius: 18px;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                 BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }

html { scroll-behavior: smooth; }

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    min-height: 100vh;
}

a {
    color: var(--lavender);
    text-decoration: none;
}

a:hover { color: white; }

button, input, select, textarea { font: inherit; }

button, .button {
    cursor: pointer;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 16px;
    color: white;
    background: var(--card2);
    transition: .2s ease;
}

button:hover, .button:hover {
    border-color: var(--indigo);
    transform: translateY(-1px);
}

button.primary, .button.primary {
    background: linear-gradient(135deg, var(--indigo), #8157d9);
    border-color: transparent;
    font-weight: 700;
}

button:focus-visible, a:focus-visible, input:focus-visible,
select:focus-visible {
    outline: 2px solid var(--lavender);
    outline-offset: 3px;
}

.container {
    width: min(1120px, calc(100% - 36px));
    margin-inline: auto;
}

.site-header {
    position: sticky;
    top: 0;
    z-index: 20;
    background: rgba(7,9,15,.92);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
}

.nav {
    min-height: 72px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}

.brand {
    font-size: 19px;
    font-weight: 850;
    letter-spacing: -.6px;
    color: white;
}

.brand span { color: var(--lavender); }

.nav-links {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    font-size: 13px;
}

.hero { padding: 68px 0 45px; }

.eyebrow {
    color: var(--lavender);
    text-transform: uppercase;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
}

h1 {
    font-size: clamp(34px, 6vw, 60px);
    line-height: 1.12;
    letter-spacing: -2px;
    margin: 12px 0 18px;
}

h2 {
    font-size: clamp(22px, 3vw, 31px);
    letter-spacing: -.8px;
}

h3 { line-height: 1.35; }

.muted { color: var(--muted); }

.hero p {
    max-width: 680px;
    color: var(--muted);
}

.search-box {
    margin-top: 28px;
    width: min(700px, 100%);
    padding: 15px 18px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    color: white;
    outline: none;
}

.section { padding: 32px 0; }

.section-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(
        auto-fill,
        minmax(min(100%, 250px), 1fr)
    );
    gap: 17px;
}

.story-card, .collection-card, .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 21px;
    transition: border-color .2s, transform .2s;
}

.story-card:hover, .collection-card:hover {
    border-color: var(--indigo);
    transform: translateY(-3px);
}

.story-card h3 {
    margin: 9px 0;
    font-size: 18px;
}

.story-card p {
    color: var(--muted);
    font-size: 13px;
}

.card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    color: var(--muted);
    font-size: 11px;
}

.pill {
    display: inline-flex;
    align-items: center;
    padding: 5px 10px;
    margin: 3px;
    border: 1px solid var(--border);
    border-radius: 30px;
    color: var(--lavender);
    background: rgba(192,132,252,.06);
    font-size: 12px;
}

.tag-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}

.count {
    color: var(--green);
    font-size: 12px;
    font-weight: 700;
}

.empty {
    padding: 30px;
    color: var(--muted);
    text-align: center;
}

.breadcrumb {
    font-size: 12px;
    color: var(--muted);
    padding-top: 25px;
}

.reader {
    background: #0d1220;
    border: 1px solid #28314a;
    border-radius: 20px;
    padding: clamp(18px, 4vw, 35px);
}

.reader-text {
    white-space: pre-wrap;
    line-height: 2;
    font-size: 19px;
    color: #e5e7f3;
    overflow-wrap: anywhere;
}

.reader-controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    margin: 18px 0;
}

.reader select, .customizer input {
    padding: 11px;
    border: 1px solid var(--border);
    background: var(--card2);
    color: white;
    border-radius: 10px;
}

.customizer {
    display: grid;
    grid-template-columns: repeat(
        auto-fit,
        minmax(180px, 1fr)
    );
    gap: 12px;
    margin: 20px 0;
}

.customizer label {
    display: grid;
    gap: 6px;
    font-size: 12px;
    color: var(--muted);
}

.customizer input { width: 100%; }

.soundscape {
    margin-top: 22px;
    background: var(--card);
    border: 1px solid var(--border);
    padding: 20px;
    border-radius: 16px;
}

.soundscape-controls {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
}

.soundscape select {
    padding: 10px;
    border-radius: 9px;
    background: var(--card2);
    color: white;
    border: 1px solid var(--border);
}

.soundscape input { accent-color: var(--lavender); }

.affiliate {
    margin: 25px 0;
    padding: 25px;
    border-radius: 18px;
    background: linear-gradient(120deg, #191a43, #241538);
    border: 1px solid #55429a;
}

.affiliate h3 { margin-top: 0; }

.featured {
    display: inline-block;
    padding: 7px 12px;
    border: 1px solid rgba(192,132,252,.35);
    color: var(--lavender);
    background: rgba(192,132,252,.08);
    border-radius: 40px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .3px;
}

.faq-item {
    border-bottom: 1px solid var(--border);
    padding: 15px 0;
}

.faq-item h3 { font-size: 16px; }

.pagination {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 25px 0;
}

footer {
    border-top: 1px solid var(--border);
    margin-top: 60px;
    padding: 38px 0;
    color: var(--muted);
    font-size: 12px;
}

.footer-links {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin: 12px 0;
}

.age-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    display: none;
    place-items: center;
    background: rgba(0,0,0,.94);
    padding: 20px;
}

.age-dialog {
    max-width: 440px;
    width: 100%;
    padding: 32px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 22px;
    text-align: center;
}

.age-dialog h2 { font-size: 26px; }

.age-dialog p {
    color: var(--muted);
    font-size: 13px;
}

.age-actions {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 20px;
}

.notice {
    color: var(--muted);
    font-size: 11px;
}

.ad-slot { min-height: 0; }

.hidden { display: none !important; }

@media(max-width: 600px) {
    .nav { min-height: 62px; }
    .nav-links { gap: 10px; font-size: 11px; }
    .hero { padding-top: 43px; }
    .reader-text { font-size: 17px; }
    .container { width: calc(100% - 26px); }
}
"""


# ============================================================
# GLOBAL JAVASCRIPT
# ============================================================

GLOBAL_JS = r"""
(function () {
    'use strict';

    function updateFreshness() {
        const now = new Date();
        const year = String(now.getFullYear());

        document.querySelectorAll('.live-year').forEach(el => {
            el.textContent = year;
        });

        document.querySelectorAll('.featured-live').forEach(el => {
            el.textContent = 'Featured Bedtime Story • ' +
                now.toLocaleString(undefined, {month: 'long'}) +
                ' ' + year;
        });
    }

    function setupAgeGate() {
        const key = 'midnight_audio_age_verified_v1';
        const overlay = document.getElementById('ageOverlay');

        if (!overlay) return;

        try {
            if (localStorage.getItem(key) === 'yes') return;
        } catch (e) {}

        overlay.style.display = 'grid';

        const yes = document.getElementById('ageYes');
        const no = document.getElementById('ageNo');

        if (yes) {
            yes.addEventListener('click', function () {
                try {
                    localStorage.setItem(key, 'yes');
                } catch (e) {}

                overlay.style.display = 'none';
            });
        }

        if (no) {
            no.addEventListener('click', function () {
                overlay.innerHTML =
                    '<div class="age-dialog">' +
                    '<h2>Access Restricted</h2>' +
                    '<p>You must be at least 18 years old ' +
                    'to access this website.</p></div>';
            });
        }
    }

    function setupSearch() {
        const input = document.getElementById('storySearch');
        const cards = Array.from(
            document.querySelectorAll('[data-searchable]')
        );
        const count = document.getElementById('searchCount');

        if (!input) return;

        input.addEventListener('input', function () {
            const term = input.value.trim().toLowerCase();
            let visible = 0;

            cards.forEach(card => {
                const text = (
                    card.dataset.searchable || ''
                ).toLowerCase();

                const matches = !term || text.includes(term);

                card.classList.toggle('hidden', !matches);

                if (matches) visible++;
            });

            if (count) {
                count.textContent = term
                    ? visible + ' matching stories'
                    : cards.length + ' stories available';
            }
        });
    }

    function setupReader() {
        const textNode = document.getElementById('readerText');

        if (!textNode) return;

        const original = (
            textNode.dataset.original || textNode.textContent
        );

        const nameInput = document.getElementById('listenerName');
        const narratorInput = document.getElementById('narratorName');
        const sizeLabel = document.getElementById('fontSizeLabel');
        const speed = document.getElementById('scrollSpeed');

        let fontSize = 19;
        let scrolling = false;
        let scrollTimer = null;
        let speedValue = 1;
        let audioContext = null;
        let masterGain = null;
        let oscillators = [];
        let audioRunning = false;

        function personalize() {
            const listener = nameInput && nameInput.value.trim()
                ? nameInput.value.trim()
                : 'Listener';

            const narrator = narratorInput &&
                narratorInput.value.trim()
                ? narratorInput.value.trim()
                : 'Narrator';

            const escaped = value => value.replace(
                /[&<>"']/g,
                ch => ({
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;'
                })[ch]
            );

            const output = original
                .replace(
                    /\[Listener Name\]/gi,
                    escaped(listener)
                )
                .replace(
                    /\[Narrator Name\]/gi,
                    escaped(narrator)
                )
                .replace(
                    /\{\{listener\}\}/gi,
                    escaped(listener)
                )
                .replace(
                    /\{\{narrator\}\}/gi,
                    escaped(narrator)
                );

            textNode.textContent = output;
        }

        [nameInput, narratorInput].forEach(input => {
            if (input) {
                input.addEventListener('input', personalize);
            }
        });

        const decrease = document.getElementById('fontDecrease');
        const increase = document.getElementById('fontIncrease');

        if (decrease) {
            decrease.addEventListener('click', () => {
                fontSize = Math.max(14, fontSize - 2);
                textNode.style.fontSize = fontSize + 'px';

                if (sizeLabel) {
                    sizeLabel.textContent = fontSize + 'px';
                }
            });
        }

        if (increase) {
            increase.addEventListener('click', () => {
                fontSize = Math.min(34, fontSize + 2);
                textNode.style.fontSize = fontSize + 'px';

                if (sizeLabel) {
                    sizeLabel.textContent = fontSize + 'px';
                }
            });
        }

        function stopScroll() {
            scrolling = false;

            if (scrollTimer !== null) {
                cancelAnimationFrame(scrollTimer);
                scrollTimer = null;
            }

            const button = document.getElementById('autoScroll');

            if (button) {
                button.textContent = '▶ Auto-Scroll Play';
            }
        }

        function scrollFrame() {
            if (!scrolling) return;

            window.scrollBy(0, speedValue * 0.55);

            if (
                window.innerHeight + window.scrollY >=
                document.documentElement.scrollHeight - 2
            ) {
                stopScroll();
                return;
            }

            scrollTimer = requestAnimationFrame(scrollFrame);
        }

        const scrollButton = document.getElementById('autoScroll');

        if (scrollButton) {
            scrollButton.addEventListener('click', () => {
                if (scrolling) {
                    stopScroll();
                    return;
                }

                scrolling = true;

                speedValue = (
                    speed && speed.value === 'medium'
                ) ? 2.1 : 0.8;

                scrollButton.textContent = 'Ⅱ Auto-Scroll Pause';

                scrollFrame();
            });
        }

        if (speed) {
            speed.addEventListener('change', () => {
                speedValue = speed.value === 'medium'
                    ? 2.1
                    : 0.8;
            });
        }

        const copyButton = document.getElementById('copyScript');

        if (copyButton) {
            copyButton.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(
                        textNode.textContent
                    );

                    copyButton.textContent = '✓ Script Copied';

                } catch (e) {
                    const range = document.createRange();

                    range.selectNodeContents(textNode);

                    const selection = window.getSelection();

                    selection.removeAllRanges();
                    selection.addRange(range);

                    copyButton.textContent = 'Select and copy script';
                }

                setTimeout(() => {
                    copyButton.textContent = '1-Click Copy Script';
                }, 2200);
            });
        }

        const audioButton = document.getElementById('audioToggle');
        const ambience = document.getElementById('ambience');
        const volume = document.getElementById('volume');

        function cleanupAudio() {
            oscillators.forEach(item => {
                try {
                    item.stop();
                } catch (e) {}
            });

            oscillators = [];
            audioRunning = false;

            if (masterGain && audioContext) {
                masterGain.gain.setTargetAtTime(
                    0,
                    audioContext.currentTime,
                    0.08
                );
            }

            if (audioButton) {
                audioButton.textContent = '▶ Play Sleep Soundscape';
            }
        }

        function startAudio() {
            const AudioContextClass =
                window.AudioContext ||
                window.webkitAudioContext;

            if (!AudioContextClass) {
                alert(
                    'Web Audio API is not supported by this browser.'
                );
                return;
            }

            if (!audioContext) {
                audioContext = new AudioContextClass();
            }

            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }

            cleanupAudio();

            masterGain = audioContext.createGain();

            masterGain.gain.value = Number(volume.value) / 100;

            masterGain.connect(audioContext.destination);

            const mode = ambience.value;
            const now = audioContext.currentTime;

            function oscillator(
                frequency,
                type,
                gainValue,
                detune
            ) {
                const osc = audioContext.createOscillator();
                const gain = audioContext.createGain();

                osc.type = type;
                osc.frequency.value = frequency;
                osc.detune.value = detune || 0;
                gain.gain.value = gainValue;

                osc.connect(gain);
                gain.connect(masterGain);
                osc.start();

                oscillators.push(osc);

                return gain;
            }

            if (mode === 'rain') {
                oscillator(55, 'sine', 0.12, 0);
                oscillator(83, 'triangle', 0.035, -4);
                oscillator(117, 'sine', 0.025, 3);

                const buffer = audioContext.createBuffer(
                    1,
                    audioContext.sampleRate * 2,
                    audioContext.sampleRate
                );

                const channel = buffer.getChannelData(0);

                for (let i = 0; i < channel.length; i++) {
                    channel[i] = (
                        Math.random() * 2 - 1
                    ) * 0.28;
                }

                const noise = audioContext.createBufferSource();
                const filter = audioContext.createBiquadFilter();
                const noiseGain = audioContext.createGain();

                noise.buffer = buffer;
                noise.loop = true;

                filter.type = 'lowpass';
                filter.frequency.value = 650;

                noiseGain.gain.value = 0.13;

                noise.connect(filter);
                filter.connect(noiseGain);
                noiseGain.connect(masterGain);

                noise.start();
                oscillators.push(noise);

            } else if (mode === 'hearth') {
                oscillator(62, 'sine', 0.10, 0);
                oscillator(92, 'triangle', 0.035, 2);
                oscillator(138, 'sine', 0.025, -3);

                const buffer = audioContext.createBuffer(
                    1,
                    audioContext.sampleRate,
                    audioContext.sampleRate
                );

                const channel = buffer.getChannelData(0);

                for (let i = 0; i < channel.length; i++) {
                    channel[i] = Math.random() > 0.997
                        ? (Math.random() * 2 - 1) * 0.8
                        : (Math.random() * 2 - 1) * 0.04;
                }

                const noise = audioContext.createBufferSource();
                const filter = audioContext.createBiquadFilter();

                noise.buffer = buffer;
                noise.loop = true;

                filter.type = 'lowpass';
                filter.frequency.value = 1100;

                noise.connect(filter);
                filter.connect(masterGain);

                noise.start();
                oscillators.push(noise);

            } else {
                oscillator(52, 'sine', 0.13, 0);
                oscillator(54, 'sine', 0.10, 3);
                oscillator(104, 'sine', 0.025, -2);
            }

            audioRunning = true;

            if (audioButton) {
                audioButton.textContent =
                    'Ⅱ Pause Sleep Soundscape';
            }
        }

        if (audioButton) {
            audioButton.addEventListener('click', () => {
                if (audioRunning) {
                    cleanupAudio();
                } else {
                    startAudio();
                }
            });
        }

        if (ambience) {
            ambience.addEventListener('change', () => {
                if (audioRunning) startAudio();
            });
        }

        if (volume) {
            volume.addEventListener('input', () => {
                if (masterGain && audioContext) {
                    masterGain.gain.setTargetAtTime(
                        Number(volume.value) / 100,
                        audioContext.currentTime,
                        0.04
                    );
                }
            });
        }

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) stopScroll();
        });

        personalize();
    }

    document.addEventListener('DOMContentLoaded', function () {
        updateFreshness();
        setupAgeGate();
        setupSearch();
        setupReader();
    });
})();
"""


# ============================================================
# HTML HEAD
# ============================================================

def global_head(title, description, path="", image_url=None):
    url = canonical(path)

    image_url = image_url or canonical("og-image.svg")

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{esc(title)}</title>

<meta name="description" content="{esc(description[:300])}">
<meta name="robots" content="index,follow,max-image-preview:large">

<meta name="google-site-verification"
content="{GOOGLE_SITE_VERIFICATION}">

<meta name="msvalidate.01"
content="{BING_SITE_VERIFICATION}">

<meta name="rating" content="{RATING_META}">
<meta name="theme-color" content="{COLORS['background']}">

<link rel="canonical" href="{esc(url)}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description[:300])}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{esc(image_url)}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description[:200])}">

<style>{GLOBAL_CSS}</style>
<script>{GLOBAL_JS}</script>

</head>
"""


# ============================================================
# AGE GATE, HEADER AND FOOTER
# ============================================================

def age_gate():
    return """
<div class="age-overlay" id="ageOverlay" role="dialog"
     aria-modal="true" aria-labelledby="ageTitle">

    <div class="age-dialog">
        <div class="eyebrow">Age Restricted Experience</div>

        <h2 id="ageTitle">Are You 18 or Older?</h2>

        <p>
            Midnight Audio Stories contains content intended for adults.
            You must be at least 18 years old to continue.
        </p>

        <div class="age-actions">
            <button class="primary" id="ageYes">
                Yes, I am 18+
            </button>

            <button id="ageNo">
                No, Exit
            </button>
        </div>

        <p class="notice">
            Your confirmation is stored locally on this device.
        </p>
    </div>
</div>
"""


def header():
    return """
<header class="site-header">
    <div class="container nav">

        <a href="/" class="brand">
            Midnight <span>Audio Stories</span>
        </a>

        <nav class="nav-links" aria-label="Main navigation">
            <a href="/">Home</a>
            <a href="/#collections">Collections</a>
            <a href="/#latest">Latest Stories</a>
            <a href="/dmca.html">DMCA</a>
        </nav>

    </div>
</header>

<!-- AD_SLOT_TOP_BANNER -->
"""


def footer():
    network_links = "".join(
        f"""
        <a href="{esc(url)}"
           target="_blank"
           rel="noopener noreferrer">
            {esc(name)}
        </a>
        """
        for name, url in NETWORK_SITES
        if url.rstrip("/") != BASE_URL.rstrip("/")
    )

    return f"""
<footer>
    <div class="container">

        <div class="brand">
            Midnight <span>Audio Stories</span>
        </div>

        <p>
            Immersive Adult Bedtime Stories, Sleep Fiction & Voice Scripts.
        </p>

        <div class="footer-links">
            <a href="/">Home</a>
            <a href="/dmca.html">DMCA Policy</a>
            <a href="/2257.html">18 U.S.C. 2257 Statement</a>
            <a href="mailto:{CONTACT_EMAIL}">Contact</a>
        </div>

        <h3>Explore Our Creative Website Network</h3>

        <div class="footer-links">
            {network_links}
        </div>

        <p>
            © <span class="live-year">{CURRENT_YEAR}</span>
            {SITE_NAME}. All rights reserved.
        </p>

        <p class="notice">
            Fictional entertainment content. All stories are intended
            for consenting adult audiences. Use audio responsibly.
        </p>

    </div>
</footer>
"""


def page_end():
    return age_gate() + footer() + """
<!-- AD_SLOT_STICKY_FOOTER -->
</body>
</html>
"""


# ============================================================
# STORY AND COLLECTION CARDS
# ============================================================

def card(row):
    searchable = " ".join([
        row["title"],
        row["target_keyword"],
        row["tags"],
        row["category"],
        row["subcategory"]
    ])

    return f"""
<article class="story-card"
         data-searchable="{esc(searchable)}">

    <div class="card-meta">
        <span>{esc(row['category'])}</span>
        <span>•</span>
        <span>{row['reading_minutes']} min read</span>
    </div>

    <h3>
        <a href="/story/{quote(row['slug'])}.html">
            {esc(row['title'])}
        </a>
    </h3>

    <p>{esc(row['description'][:155])}</p>

    <div class="card-meta">
        <a href="/topic/{quote(row['subcategory_slug'])}.html">
            {esc(row['subcategory'])}
        </a>
    </div>

    <a class="button"
       href="/story/{quote(row['slug'])}.html">
        Read Story →
    </a>

</article>
"""


def collection_card(category, count):
    slug = slugify(category)

    return f"""
<a class="collection-card"
   href="/category/{quote(slug)}/page-1.html">

    <h3>{esc(category)}</h3>

    <span class="count">{count} stories</span>

</a>
"""


# ============================================================
# HOMEPAGE
# ============================================================

def build_home(rows):
    categories = Counter(
        row["category"] for row in rows
    )

    subcategories = Counter(
        row["subcategory"] for row in rows
    )

    tags = Counter(
        tag
        for row in rows
        for tag in row["tags_list"]
    )

    newest = sorted(
        rows,
        key=lambda row: (
            row["date_obj"],
            row["title"].lower()
        ),
        reverse=True
    )[:NEWEST_COUNT]

    content = f"""
<body>

{header()}

<main>

    <section class="hero container">

        <div class="eyebrow">
            Your Midnight Listening Destination
        </div>

        <h1>
            Drift Into a World of
            <span style="color:#c084fc">Dreams</span>
        </h1>

        <p>
            Discover immersive adult bedtime stories, atmospheric sleep
            fiction and narration-ready scripts designed for your
            nightly listening ritual.
        </p>

        <div class="featured">
            Featured Bedtime Stories •
            <span class="live-year">{CURRENT_YEAR}</span>
        </div>

        <input
            type="search"
            class="search-box"
            id="storySearch"
            placeholder="Search stories, keywords or tags..."
            aria-label="Search bedtime stories"
        >

        <p id="searchCount" class="muted">
            {len(rows)} stories available
        </p>

    </section>

    <div class="container">

        <!-- AD_SLOT_MID_CONTENT -->

        <section class="section" id="collections">

            <div class="section-heading">
                <h2>Browse Story Collections</h2>

                <span class="muted">
                    {len(categories)} collections
                </span>
            </div>

            <div class="grid">
                {''.join(
                    collection_card(name, count)
                    for name, count in sorted(
                        categories.items(),
                        key=lambda item: item[0].lower()
                    )
                )}
            </div>

        </section>

        <section class="section">

            <h2>Explore Subcategories</h2>

            <div class="tag-cloud">
                {''.join(
                    f'<a class="pill" href="/topic/{quote(slugify(name))}.html">'
                    f'{esc(name)} · {count}</a>'
                    for name, count in sorted(
                        subcategories.items(),
                        key=lambda item: item[0].lower()
                    )
                )}
            </div>

        </section>

        <section class="section">

            <h2>Popular Story Tags</h2>

            <div class="tag-cloud">
                {''.join(
                    f'<a class="pill" href="/tag/{quote(slugify(name))}.html">'
                    f'#{esc(name)} · {count}</a>'
                    for name, count in tags.most_common(60)
                )}
            </div>

        </section>

        <section class="section" id="latest">

            <div class="section-heading">
                <h2>Latest Bedtime Stories</h2>

                <span class="muted">
                    Newest {len(newest)} stories
                </span>
            </div>

            <div class="grid" id="storyGrid">
                {''.join(card(row) for row in newest)}
            </div>

        </section>

    </div>

</main>

{page_end()}

"""

    html_doc = global_head(
        f"{SITE_NAME} | Immersive Bedtime Stories & Sleep Fiction",
        (
            f"Explore {len(rows)} immersive adult bedtime stories, "
            "sleep fiction, narration scripts and relaxing "
            "midnight reading experiences."
        ),
        ""
    ) + content

    write_file(
        os.path.join(OUTPUT_DIR, "index.html"),
        html_doc
    )


# ============================================================
# RELATED STORIES
# ============================================================

def get_related(current, rows, limit):
    current_tags = {
        slugify(tag)
        for tag in current["tags_list"]
    }

    candidates = []

    for row in rows:
        if row["slug"] == current["slug"]:
            continue

        shared_tags = len(
            current_tags & {
                slugify(tag)
                for tag in row["tags_list"]
            }
        )

        same_subcategory = (
            row["subcategory_slug"]
            == current["subcategory_slug"]
        )

        same_category = (
            row["category_slug"]
            == current["category_slug"]
        )

        score = (
            (100 if same_subcategory else 0)
            + shared_tags * 15
            + (10 if same_category else 0)
        )

        candidates.append(
            (score, row["slug"], row)
        )

    candidates.sort(
        key=lambda item: (-item[0], item[1])
    )

    return [
        item[2]
        for item in candidates[:limit]
    ]


# ============================================================
# INDIVIDUAL STORY READER
# ============================================================

def build_reader(row):
    story = row["story_text"]
    title = row["title"]

    related = get_related(
        row,
        ALL_ROWS,
        RELATED_COUNT
    )

    related_html = "".join(
        card(item)
        for item in related
    )

    tags_html = "".join(
        f'<a class="pill" href="/tag/{quote(slugify(tag))}.html">'
        f'#{esc(tag)}</a>'
        for tag in row["tags_list"]
    )

    faq_items = ""

    for question, answer in [
        (row["faq_q1"], row["faq_a1"]),
        (row["faq_q2"], row["faq_a2"])
    ]:
        if question and answer:
            faq_items += f"""
            <div class="faq-item">
                <h3>{esc(question)}</h3>
                <p class="muted">{esc(answer)}</p>
            </div>
            """

    description = row["description"]

    url = canonical(
        "story/" + row["slug"] + ".html"
    )

    article_schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": title,
                "description": description,
                "mainEntityOfPage": url,
                "url": url,
                "datePublished": row["upload_date"] or None,
                "dateModified": row["upload_date"] or None,
                "author": {
                    "@type": "Organization",
                    "name": SITE_NAME
                },
                "publisher": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                    "url": BASE_URL
                },
                "articleSection": row["category"],
                "keywords": ", ".join(
                    [row["target_keyword"]]
                    + row["tags_list"]
                ),
                "inLanguage": "en"
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": BASE_URL
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": row["category"],
                        "item": canonical(
                            "category/"
                            + row["category_slug"]
                            + "/page-1.html"
                        )
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": title,
                        "item": url
                    }
                ]
            }
        ]
    }

    faq_entities = []

    for question, answer in [
        (row["faq_q1"], row["faq_a1"]),
        (row["faq_q2"], row["faq_a2"])
    ]:
        if question and answer:
            faq_entities.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer
                }
            })

    if faq_entities:
        article_schema["@graph"].append({
            "@type": "FAQPage",
            "mainEntity": faq_entities
        })

    schema_script = (
        '<script type="application/ld+json">'
        + json_ld(article_schema)
        + '</script>'
    )

    body = f"""
<body>

{header()}

<main class="container">

    <div class="breadcrumb">
        <a href="/">Home</a> /

        <a href="/category/{quote(row['category_slug'])}/page-1.html">
            {esc(row['category'])}
        </a> /

        {esc(title)}
    </div>

    <section class="hero">

        <div class="featured featured-live">
            Featured Bedtime Story • {CURRENT_YEAR}
        </div>

        <div class="eyebrow">
            {esc(row['category'])} /
            {esc(row['subcategory'])}
        </div>

        <h1>{esc(title)}</h1>

        <p>{esc(description)}</p>

        <div class="card-meta">
            <span>{row['reading_minutes']} minute read</span>
            <span>•</span>
            <span>{esc(row['upload_date'] or 'Evergreen Story')}</span>
            <span>•</span>
            <span class="live-year">{CURRENT_YEAR}</span>
        </div>

    </section>

    <section class="reader"
             aria-label="Interactive bedtime story reader">

        <div class="section-heading">
            <h2>Interactive Bedtime Reader</h2>

            <span class="muted">
                Comfortable midnight reading
            </span>
        </div>

        <div class="reader-controls">

            <button class="primary" id="autoScroll">
                ▶ Auto-Scroll Play
            </button>

            <label>
                <span class="notice">Scroll Speed</span><br>

                <select id="scrollSpeed">
                    <option value="slow">Slow</option>
                    <option value="medium">Medium</option>
                </select>
            </label>

            <button id="fontDecrease"
                    aria-label="Decrease font size">
                A−
            </button>

            <button id="fontIncrease"
                    aria-label="Increase font size">
                A+
            </button>

            <span id="fontSizeLabel" class="notice">
                19px
            </span>

            <button id="copyScript">
                1-Click Copy Script
            </button>

        </div>

        <div class="customizer">

            <label>
                Listener Name

                <input
                    type="text"
                    id="listenerName"
                    placeholder="Enter listener name"
                    maxlength="60"
                >
            </label>

            <label>
                Narrator Name

                <input
                    type="text"
                    id="narratorName"
                    placeholder="Enter narrator name"
                    maxlength="60"
                >
            </label>

        </div>

        <div
            id="readerText"
            class="reader-text"
            data-original="{esc(story)}"
        >{esc(story)}</div>

        <div class="soundscape">

            <h3>Sleep Soundscape Mixer</h3>

            <p class="muted">
                Original synthesized ambient tones generated locally
                using your browser's Web Audio API.
            </p>

            <div class="soundscape-controls">

                <button class="primary" id="audioToggle">
                    ▶ Play Sleep Soundscape
                </button>

                <select id="ambience"
                        aria-label="Choose ambience">

                    <option value="rain">
                        Midnight Rainstorm
                    </option>

                    <option value="hearth">
                        Warm Crackling Hearth
                    </option>

                    <option value="delta">
                        Deep Delta Sleep Hum
                    </option>

                </select>

                <label>
                    <span class="notice">Volume</span>

                    <input
                        id="volume"
                        type="range"
                        min="0"
                        max="100"
                        value="25"
                    >
                </label>

            </div>

        </div>

    </section>

    <!-- AD_SLOT_MID_CONTENT -->

    <section class="affiliate">

        <div class="eyebrow">
            Discover More Audio Experiences
        </div>

        <h3>Take Your Bedtime Listening Further</h3>

        <p>
            Explore interactive AI voice stories and discover new
            narration experiences for your nightly routine.
        </p>

        <a
            class="button primary"
            href="{esc(AFFILIATE_URL)}"
            rel="nofollow sponsored noopener"
            target="_blank"
        >
            {esc(AFFILIATE_CTA_TEXT)} →
        </a>

        <p class="notice">
            Affiliate disclosure: This page may contain promotional
            links. We may earn a commission from qualifying purchases
            or registrations at no additional cost to you.
        </p>

    </section>

    <section class="section">

        <h2>Explore This Story's Topics</h2>

        <p>
            <a class="pill"
               href="/topic/{quote(row['subcategory_slug'])}.html">
                {esc(row['subcategory'])}
            </a>
        </p>

        <div class="tag-cloud">
            {tags_html}
        </div>

    </section>

    {
        (
            '<section class="section">'
            '<h2>Frequently Asked Questions</h2>'
            + faq_items
            + '</section>'
        ) if faq_items else ''
    }

    <section class="section">

        <div class="section-heading">
            <h2>Related Bedtime Stories</h2>

            <span class="muted">
                More midnight discoveries
            </span>
        </div>

        <div class="grid">
            {
                related_html
                if related_html
                else '<p class="muted">More stories coming soon.</p>'
            }
        </div>

    </section>

</main>

{page_end()}

"""

    document = global_head(
        f"{title} | {SITE_NAME}",
        description,
        "story/" + row["slug"] + ".html"
    )

    document = document.replace(
        "</head>",
        schema_script + "\n</head>"
    )

    document += body

    write_file(
        os.path.join(
            OUTPUT_DIR,
            "story",
            row["slug"] + ".html"
        ),
        document
    )


# ============================================================
# CATEGORY HUBS
# ============================================================

def build_category_hubs(rows):
    grouped = defaultdict(list)

    for row in rows:
        grouped[row["category_slug"]].append(row)

    for cat_slug, items in grouped.items():

        items.sort(
            key=lambda row: (
                row["date_obj"],
                row["title"].lower()
            ),
            reverse=True
        )

        category_name = items[0]["category"]

        total_pages = max(
            1,
            math.ceil(len(items) / ITEMS_PER_PAGE)
        )

        for page_number in range(1, total_pages + 1):

            start = (
                page_number - 1
            ) * ITEMS_PER_PAGE

            page_items = items[
                start:start + ITEMS_PER_PAGE
            ]

            relative = (
                f"category/{cat_slug}/page-{page_number}.html"
            )

            prev_link = (
                f'<a class="button" rel="prev" '
                f'href="page-{page_number - 1}.html">'
                f'← Previous</a>'
                if page_number > 1
                else ""
            )

            next_link = (
                f'<a class="button" rel="next" '
                f'href="page-{page_number + 1}.html">'
                f'Next →</a>'
                if page_number < total_pages
                else ""
            )

            cards = "".join(
                card(row)
                for row in page_items
            )

            body = f"""
<body>

{header()}

<main class="container">

    <div class="breadcrumb">
        <a href="/">Home</a> / Collections
    </div>

    <section class="hero">

        <div class="eyebrow">Story Collection</div>

        <h1>{esc(category_name)}</h1>

        <p>
            Explore {len(items)} immersive bedtime stories
            in this collection.
        </p>

    </section>

    <section class="section">

        <div class="grid">
            {cards}
        </div>

        <nav class="pagination"
             aria-label="Category pagination">

            {prev_link}

            <span class="pill">
                Page {page_number} of {total_pages}
            </span>

            {next_link}

        </nav>

    </section>

</main>

{page_end()}

"""

            document = global_head(
                (
                    f"{category_name} Bedtime Stories | "
                    f"Page {page_number} | {SITE_NAME}"
                ),
                (
                    f"Browse {len(items)} stories in "
                    f"{category_name}. Page {page_number} "
                    f"of {total_pages}."
                ),
                relative
            )

            if page_number > 1:
                document = document.replace(
                    "</head>",
                    (
                        '<link rel="prev" href="'
                        + esc(canonical(
                            f"category/{cat_slug}/"
                            f"page-{page_number - 1}.html"
                        ))
                        + '">\n</head>'
                    )
                )

            if page_number < total_pages:
                document = document.replace(
                    "</head>",
                    (
                        '<link rel="next" href="'
                        + esc(canonical(
                            f"category/{cat_slug}/"
                            f"page-{page_number + 1}.html"
                        ))
                        + '">\n</head>'
                    )
                )

            write_file(
                os.path.join(
                    OUTPUT_DIR,
                    "category",
                    cat_slug,
                    f"page-{page_number}.html"
                ),
                document + body
            )


# ============================================================
# TOPIC AND TAG HUBS
# ============================================================

def build_taxonomy_hubs(rows):
    subgroups = defaultdict(list)
    taggroups = defaultdict(list)

    for row in rows:
        subgroups[
            row["subcategory_slug"]
        ].append(row)

        for tag in row["tags_list"]:
            taggroups[
                slugify(tag)
            ].append(row)

    for slug, items in subgroups.items():

        name = items[0]["subcategory"]

        build_taxonomy_page(
            "topic",
            slug,
            name,
            items,
            f"Explore bedtime stories and sleep fiction about {name}."
        )

    for slug, items in taggroups.items():

        name = next(
            (
                tag
                for row in rows
                for tag in row["tags_list"]
                if slugify(tag) == slug
            ),
            slug.replace("-", " ").title()
        )

        build_taxonomy_page(
            "tag",
            slug,
            name,
            items,
            f"Discover stories tagged {name} on {SITE_NAME}."
        )


def build_taxonomy_page(
    folder,
    slug,
    name,
    items,
    description
):
    unique = {
        row["slug"]: row
        for row in items
    }

    items = sorted(
        unique.values(),
        key=lambda row: (
            row["date_obj"],
            row["title"].lower()
        ),
        reverse=True
    )

    body = f"""
<body>

{header()}

<main class="container">

    <div class="breadcrumb">
        <a href="/">Home</a> / {esc(folder.title())}
    </div>

    <section class="hero">

        <div class="eyebrow">
            {esc(folder.title())} Hub
        </div>

        <h1>{esc(name)}</h1>

        <p>{esc(description)}</p>

        <span class="pill">
            {len(items)} stories
        </span>

    </section>

    <section class="section">

        <div class="grid">
            {''.join(card(row) for row in items)}
        </div>

    </section>

</main>

{page_end()}

"""

    path = f"{folder}/{slug}.html"

    document = global_head(
        f"{name} Bedtime Stories | {SITE_NAME}",
        description,
        path
    )

    write_file(
        os.path.join(
            OUTPUT_DIR,
            folder,
            slug + ".html"
        ),
        document + body
    )


# ============================================================
# STATIC AND LEGAL PAGES
# ============================================================

def build_static_page(
    filename,
    title,
    description,
    content
):
    document = global_head(
        title,
        description,
        filename
    )

    body = f"""
<body>

{header()}

<main class="container">

    <section class="hero">

        <div class="eyebrow">{esc(SITE_NAME)}</div>

        <h1>{esc(title)}</h1>

        <p>{esc(description)}</p>

    </section>

    <section class="panel section">
        {content}
    </section>

</main>

{page_end()}

"""

    write_file(
        os.path.join(OUTPUT_DIR, filename),
        document + body
    )


def build_legal_pages():

    dmca = f"""
<h2>Digital Millennium Copyright Act (DMCA) Policy</h2>

<p>
    {esc(SITE_NAME)} respects intellectual property rights and
    expects visitors and contributors to do the same.
</p>

<h3>Submitting a Copyright Notice</h3>

<p>
    If you believe content on this website infringes your copyright,
    send a written notice to:
</p>

<p>
    <a href="mailto:{CONTACT_EMAIL}">
        {CONTACT_EMAIL}
    </a>
</p>

<p>Your notice should include:</p>

<ul>
    <li>Identification of the copyrighted work.</li>
    <li>Identification of the allegedly infringing material and its URL.</li>
    <li>Your contact information.</li>
    <li>A good-faith statement that the use is unauthorized.</li>
    <li>A statement, under penalty of perjury, that the information is accurate.</li>
    <li>Your physical or electronic signature.</li>
</ul>

<h3>Review and Removal</h3>

<p>
    We will review properly submitted notices and take appropriate
    action where warranted. Counter-notifications may be submitted
    where legally applicable.
</p>

<h3>Repeat Infringement</h3>

<p>
    Appropriate measures may be taken against repeat infringers,
    consistent with applicable law.
</p>

<p class="notice">
    This policy provides general information and is not legal advice.
    Submit notices only when you have a legitimate basis.
</p>
"""

    build_static_page(
        "dmca.html",
        "DMCA Copyright Policy",
        "Learn how to submit a copyright infringement notice.",
        dmca
    )

    compliance = f"""
<h2>18 U.S.C. § 2257 Statement</h2>

<p>
    {esc(SITE_NAME)} publishes fictional text-based bedtime stories,
    literary entertainment, and narration scripts.
</p>

<p>
    This website does not knowingly publish visual depictions of
    actual sexually explicit conduct.
</p>

<p>
    The site is intended for adult audiences and may contain
    fictional mature themes. Any applicable legal obligations
    will be assessed according to the nature of the material
    actually published.
</p>

<h3>Contact</h3>

<p>
    Questions concerning this statement may be directed to
    <a href="mailto:{CONTACT_EMAIL}">
        {CONTACT_EMAIL}
    </a>.
</p>

<p class="notice">
    This statement is informational and does not represent a
    legal determination that any statutory exemption applies.
</p>
"""

    build_static_page(
        "2257.html",
        "18 U.S.C. 2257 Compliance Statement",
        (
            "Information regarding the nature of content "
            "published on this website."
        ),
        compliance
    )


# ============================================================
# ROBOTS.TXT
# ============================================================

def build_robots():
    content = f"""User-agent: *
Allow: /

Sitemap: {canonical('sitemap.xml')}
"""

    write_file(
        os.path.join(OUTPUT_DIR, "robots.txt"),
        content
    )


# ============================================================
# SITEMAP STYLESHEET
# ============================================================

def sitemap_xsl():
    return r"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">

<html lang="en">

<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>

<title>Midnight Audio Stories Sitemap</title>

<style>
body{
    background:#07090f;
    color:#edf0fa;
    font-family:system-ui,sans-serif;
    margin:0;
    padding:30px
}
main{
    max-width:900px;
    margin:auto
}
h1{
    color:#c084fc
}
table{
    width:100%;
    border-collapse:collapse;
    background:#111625;
    border-radius:14px
}
td,th{
    padding:13px;
    text-align:left;
    border-bottom:1px solid #252d42
}
a{
    color:#c084fc;
    overflow-wrap:anywhere
}
small{
    color:#9ba6bd
}
</style>

</head>

<body>

<main>

<h1>Midnight Audio Stories Sitemap</h1>

<p><small>XML sitemap directory</small></p>

<table>

<tr>
<th>Location</th>
<th>Last Modified</th>
</tr>

<xsl:for-each select="s:sitemapindex/s:sitemap | s:urlset/s:url">

<tr>

<td>
<a href="{s:loc}">
<xsl:value-of select="s:loc"/>
</a>
</td>

<td>
<xsl:value-of select="s:lastmod"/>
</td>

</tr>

</xsl:for-each>

</table>

</main>

</body>

</html>

</xsl:template>

</xsl:stylesheet>
"""


# ============================================================
# XML HELPERS AND SITEMAPS
# ============================================================

def xml_escape(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_sitemaps(rows):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    urls = {
        canonical("")
    }

    for row in rows:
        urls.add(
            canonical(
                "story/" + row["slug"] + ".html"
            )
        )

    categories = defaultdict(list)

    for row in rows:
        categories[
            row["category_slug"]
        ].append(row)

    for slug, items in categories.items():

        pages = max(
            1,
            math.ceil(len(items) / ITEMS_PER_PAGE)
        )

        for page in range(1, pages + 1):
            urls.add(
                canonical(
                    f"category/{slug}/page-{page}.html"
                )
            )

    for row in rows:

        urls.add(
            canonical(
                "topic/"
                + row["subcategory_slug"]
                + ".html"
            )
        )

        for tag in row["tags_list"]:
            urls.add(
                canonical(
                    "tag/" + slugify(tag) + ".html"
                )
            )

    urls.update([
        canonical("dmca.html"),
        canonical("2257.html")
    ])

    urls = sorted(urls)

    chunk_size = 45000

    chunks = [
        urls[index:index + chunk_size]
        for index in range(0, len(urls), chunk_size)
    ]

    if not chunks:
        chunks = [[]]

    sitemap_files = []

    for index, chunk in enumerate(chunks, start=1):

        filename = f"sitemap-{index}.xml"

        sitemap_files.append(filename)

        url_entries = "".join(
            f"""
    <url>
        <loc>{xml_escape(url)}</loc>
        <lastmod>{today}</lastmod>
    </url>"""
            for url in chunk
        )

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="sitemap.xsl"?>

<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

{url_entries}

</urlset>
"""

        write_file(
            os.path.join(OUTPUT_DIR, filename),
            xml
        )

    sitemap_entries = "".join(
        f"""
    <sitemap>
        <loc>{xml_escape(canonical(filename))}</loc>
        <lastmod>{today}</lastmod>
    </sitemap>"""
        for filename in sitemap_files
    )

    index_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="sitemap.xsl"?>

<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

{sitemap_entries}

</sitemapindex>
"""

    write_file(
        os.path.join(OUTPUT_DIR, "sitemap.xml"),
        index_xml
    )

    write_file(
        os.path.join(OUTPUT_DIR, "sitemap.xsl"),
        sitemap_xsl()
    )


# ============================================================
# OPEN GRAPH IMAGE
# ============================================================

def build_og_image():
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
width="1200" height="630" viewBox="0 0 1200 630">

<defs>
<linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
<stop offset="0%" stop-color="#10172c"/>
<stop offset="100%" stop-color="#301b50"/>
</linearGradient>
</defs>

<rect width="1200" height="630" fill="#07090f"/>

<rect x="35" y="35" width="1130" height="560"
rx="36" fill="url(#g)"/>

<circle cx="940" cy="160" r="90"
fill="#c084fc" opacity=".16"/>

<circle cx="1000" cy="125" r="70"
fill="#c084fc" opacity=".45"/>

<text x="90" y="260" font-size="32" fill="#c084fc"
font-family="Arial,sans-serif">
YOUR MIDNIGHT LISTENING DESTINATION
</text>

<text x="90" y="355" font-size="72"
font-weight="bold" fill="#ffffff"
font-family="Arial,sans-serif">
Midnight Audio Stories
</text>

<text x="95" y="425" font-size="28" fill="#c4cbe0"
font-family="Arial,sans-serif">
Bedtime Stories • Sleep Fiction • Voice Scripts
</text>

</svg>"""

    write_file(
        os.path.join(OUTPUT_DIR, "og-image.svg"),
        svg
    )


# ============================================================
# SEARCH INDEX
# ============================================================

def build_search_fallback():
    """
    Produce a small local search index for future enhancements.
    The homepage search itself operates on rendered story cards.
    """

    data = []

    for row in ALL_ROWS:
        data.append({
            "slug": row["slug"],
            "title": row["title"],
            "keyword": row["target_keyword"],
            "category": row["category"],
            "subcategory": row["subcategory"],
            "tags": row["tags_list"]
        })

    write_file(
        os.path.join(
            OUTPUT_DIR,
            "search-index.json"
        ),
        json.dumps(
            data,
            ensure_ascii=False,
            separators=(",", ":")
        )
    )


# ============================================================
# BUILD VALIDATION
# ============================================================

def validate_output(rows):

    expected = [
        os.path.join(OUTPUT_DIR, "index.html"),
        os.path.join(OUTPUT_DIR, "robots.txt"),
        os.path.join(OUTPUT_DIR, "sitemap.xml"),
        os.path.join(OUTPUT_DIR, "sitemap-1.xml"),
        os.path.join(OUTPUT_DIR, "sitemap.xsl"),
        os.path.join(OUTPUT_DIR, "dmca.html"),
        os.path.join(OUTPUT_DIR, "2257.html"),
        os.path.join(OUTPUT_DIR, "og-image.svg"),
        os.path.join(OUTPUT_DIR, "search-index.json"),
    ]

    for path in expected:
        if not os.path.isfile(path):
            raise RuntimeError(
                "Missing generated file: " + path
            )

    for row in rows:

        path = os.path.join(
            OUTPUT_DIR,
            "story",
            row["slug"] + ".html"
        )

        if not os.path.isfile(path):
            raise RuntimeError(
                "Missing story page: " + path
            )

    if len(rows) != len({
        row["slug"]
        for row in rows
    }):
        raise RuntimeError(
            "Duplicate story slugs detected."
        )

    html_files = []

    for root, _, files in os.walk(OUTPUT_DIR):

        for filename in files:

            if filename.endswith(".html"):
                html_files.append(
                    os.path.join(root, filename)
                )

    if not html_files:
        raise RuntimeError(
            "No HTML pages were generated."
        )

    for path in html_files:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:
            content = file.read()

        checks = [
            (
                GOOGLE_SITE_VERIFICATION,
                "Google verification"
            ),
            (
                BING_SITE_VERIFICATION,
                "Bing verification"
            ),
            (
                "live-year",
                "Live-year element"
            ),
            (
                "Explore Our Creative Website Network",
                "Network footer"
            ),
        ]

        for expected_text, label in checks:

            if expected_text not in content:
                raise RuntimeError(
                    label + " missing from: " + path
                )

    # Check sitemap XML files are valid.
    for filename in os.listdir(OUTPUT_DIR):

        if (
            filename == "sitemap.xml"
            or re.fullmatch(r"sitemap-\d+\.xml", filename)
        ):

            path = os.path.join(
                OUTPUT_DIR,
                filename
            )

            try:
                ElementTree.parse(path)
            except ElementTree.ParseError as error:
                raise RuntimeError(
                    "Invalid XML sitemap "
                    + filename
                    + ": "
                    + str(error)
                )

    print("Verified HTML pages:", len(html_files))
    print("Google verification: OK")
    print("Bing verification: OK")
    print("Live-year elements: OK")
    print("Network footer: OK")
    print("XML sitemap files: OK")


# ============================================================
# MAIN BUILD
# ============================================================

def main():
    global ALL_ROWS

    print("=" * 60)
    print(SITE_NAME, "Static Website Builder")
    print("Build year:", CURRENT_YEAR)
    print("Base URL:", BASE_URL)
    print("=" * 60)

    rows = read_data()

    ALL_ROWS = rows

    print(f"Loaded {len(rows)} stories.")

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    ensure_dir(OUTPUT_DIR)

    print("Generating Open Graph image...")
    build_og_image()

    print("Generating homepage...")
    build_home(rows)

    print("Generating story pages...")

    for index, row in enumerate(rows, start=1):

        build_reader(row)

        if index % 50 == 0 or index == len(rows):
            print(
                f"Generated story pages: {index}/{len(rows)}"
            )

    print("Generating category hubs...")
    build_category_hubs(rows)

    print("Generating topic and tag hubs...")
    build_taxonomy_hubs(rows)

    print("Generating legal pages...")
    build_legal_pages()

    print("Generating robots.txt...")
    build_robots()

    print("Generating XML sitemaps...")
    build_sitemaps(rows)

    print("Generating search index...")
    build_search_fallback()

    print("Validating generated website...")
    validate_output(rows)

    print()
    print("BUILD SUCCESSFUL")
    print("-" * 60)

    print("Stories:", len(rows))

    print(
        "Categories:",
        len({
            row["category_slug"]
            for row in rows
        })
    )

    print(
        "Subcategories:",
        len({
            row["subcategory_slug"]
            for row in rows
        })
    )

    print(
        "Tags:",
        len({
            slugify(tag)
            for row in rows
            for tag in row["tags_list"]
        })
    )

    print("Output:", os.path.abspath(OUTPUT_DIR))
    print("Homepage:", canonical(""))
    print("Sitemap:", canonical("sitemap.xml"))

    print("-" * 60)


ALL_ROWS = []


if __name__ == "__main__":
    main()
