# 🚀 AutoFilePro - Automated File Organizer (Full Stack)

A modern, high-performance **Full Stack Automated File Organizer** powered by **Python Flask** and an ultra-responsive, glassmorphic frontend.

---

## ✨ Features & Capabilities

- 📁 **Multi-Strategy Organization**:
  - **By Category**: Documents, Images, Videos, Audio, Code, Spreadsheets, Presentations, Archives, Applications, Other.
  - **By Extension**: Groups files into `.pdf/`, `.jpg/`, `.py/`, `.csv/`, etc.
  - **By Date (Month/Year)**: Groups files into `YYYY/MM-Month` or `YYYY/`.
  - **By File Size**: Small (<1MB), Medium (1MB-50MB), Large (50MB-500MB), Huge (>500MB).
- 🔍 **Streaming SHA-256 Duplicate Detection**:
  - Two-pass chunked hashing engine that rapidly identifies duplicate files.
  - Isolates duplicate copies into `Duplicates/` while safely preserving the original.
- 👁️ **Dry Run Simulation / Live Preview**:
  - Simulates all folder moves and presents a detailed diff before executing any file operations.
- ⏪ **Atomic Batch History & 1-Click Rollback**:
  - Every batch operation is logged in an SQLite database.
  - Revert and restore all files back to their exact original locations with a single click.
- ⚡ **Auto-Pilot Real-Time Watcher**:
  - Background daemon using Python `watchdog`.
  - Continuously monitors folders (like `Downloads` or `Desktop`) and automatically organizes new files the moment they arrive.
- ⚙️ **Smart Custom Rules Builder**:
  - Create rules using file extensions, prefixes, keywords, regex patterns, or file size thresholds with custom target subfolders.
- 📊 **Storage Breakdown & Visual Analytics**:
  - Interactive Chart.js doughnut and bar charts for category space utilization and file distributions.
- 🧪 **1-Click Demo Sandbox Generator**:
  - Instantly generates mock test files (PDFs, images, duplicates, spreadsheets, audio, scripts) so users can test risk-free immediately.
- 🖥️ **Live Activity Terminal**:
  - Real-time event and error diagnostics stream.

---

## 🛠️ Architecture & Tech Stack

```
skills learn/
├── app.py                 # Flask Server & REST API endpoints
├── config.py              # Central application configuration & category mappings
├── backend/
│   ├── database.py        # SQLite history tracking & custom rules schema
│   ├── scanner.py         # Directory scanner & SHA-256 duplicate detection
│   ├── organizer.py       # Organization engine, simulation & rollback
│   ├── rules_engine.py    # Custom pattern evaluation & category classifier
│   ├── watcher.py         # Background watchdog daemon for live folder monitoring
│   ├── demo_generator.py  # Instant test sandbox builder
│   ├── logger.py          # Unified activity logger
│   └── utils.py           # Path sanitization, collision-free naming & validation
├── templates/
│   └── index.html         # Modern Glassmorphic dashboard
└── static/
    ├── css/style.css      # Design system with dark/light themes & glows
    └── js/app.js          # Reactive frontend controller & Chart.js integration
```

---

## 🚀 How to Run

1. Start the Flask full-stack application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
3. Click **"Generate Sandbox"** or select your **Downloads** folder to begin organizing!
