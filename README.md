# Khabar Bila Hudood Automation

<p align="center">
  <h2 align="center">📰 خبر بلا حدود - نظام إنتاج فيديوهات الأخبار الآلي</h2>
</p>

---

## Overview

Khabar Bila Hudood Automation is a fully automated AI-powered pipeline that transforms breaking news into ready-to-publish YouTube videos.

The system automatically:

- Collects important news
- Prioritizes Italy news
- Prioritizes immigration news
- Selects important world news
- Rewrites articles professionally in Arabic
- Generates YouTube SEO
- Creates thumbnails
- Produces HD videos
- Uploads videos automatically to YouTube as **Private**
- Prevents duplicate publications

---

# Priority

The publishing priority is:

1. 🇮🇹 Italy News
2. 🌍 Immigration News
3. 🌎 Global News

Economy news is intentionally ignored.

---

# Features

## News Engine

- Automatic news collection
- Multiple trusted sources
- Duplicate detection
- AI ranking
- Category filtering

---

## AI Engine

Powered by Google Gemini.

Functions:

- Rewrite articles
- Generate titles
- Generate YouTube descriptions
- Generate tags
- Generate hashtags
- Quality review

---

## Thumbnail Engine

Automatically creates attractive thumbnails.

Features:

- AI prompt generation
- Text placement
- Branding support
- Quality validation

---

## Video Engine

Creates Full HD videos automatically.

Features:

- Scene generation
- Background music
- Smooth transitions
- 1080p export
- FFmpeg optimization

---

## YouTube Publisher

Uploads automatically.

Features:

- Private uploads
- Playlist support
- Metadata generation
- Automatic retry

---

## Database

SQLite database stores:

- Published news
- Rejected news
- Duplicate fingerprints
- Upload history
- Processing logs

---

# Project Structure

```
Khabar-Bila-Hudood-Automation/

├── assets/
├── data/
├── logs/
├── prompts/
├── src/
│   ├── ai/
│   ├── database/
│   ├── news/
│   ├── utils/
│   ├── video/
│   └── youtube/
│
├── tests/
├── config.yaml
├── requirements.txt
├── README.md
└── .env.example
```

---

# Workflow

```
Collect News
      │
      ▼
Filter
      │
      ▼
Rank
      │
      ▼
Rewrite using Gemini
      │
      ▼
Generate SEO
      │
      ▼
Generate Thumbnail
      │
      ▼
Generate Video
      │
      ▼
Upload to YouTube
      │
      ▼
Store in Database
```

---

# Technologies

- Python 3.12
- Google Gemini
- SQLite
- MoviePy
- FFmpeg
- YouTube Data API v3
- GitHub Actions

---

# Configuration

All settings are stored inside:

```
config.yaml
```

Secrets are stored in:

```
.env
```

---

# Logging

Every execution is logged.

Logs include:

- Errors
- Uploads
- Processing time
- AI responses
- Retry attempts

---

# Duplicate Protection

The system never publishes the same news twice.

Duplicate detection uses:

- URL comparison
- Title similarity
- Content fingerprinting

---

# Video Output

Resolution:

```
1920 × 1080
```

Format:

```
MP4
```

Upload mode:

```
Private
```

---

# Future Improvements

- Multi-language support
- AI voice generation
- Live news mode
- Trend detection
- Automatic playlists
- Analytics dashboard

---

# License

Private Project.

All rights reserved.

---

## Author

Developed for **Khabar Bila Hudood** using modern AI automation technologies.
