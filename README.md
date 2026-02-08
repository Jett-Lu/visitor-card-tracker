# CETI Visitor Card Tracker

A standalone Python + Tkinter desktop application for managing visitor and lab access cards.

<img width="967" height="554" alt="image" src="https://github.com/user-attachments/assets/b4f88fd0-5f89-4f7a-8378-673876ee9f95" />

CETI Visitor Card Tracker keeps track of who signs out lab or visitor cards, when they’re returned, and where each card belongs.  
It uses an SQLite database with WAL mode for safe multi-user access over a shared network drive — no server or external dependencies required.

## Features

- Card tracking — manage sign-outs, returns, and lost/found status  
- Simple interface — clean Tkinter UI with color-coded rows  
- Built-in search — filter by card label, holder, ID, notes, or location  
- Editable database — add, edit, or remove cards within the app  
- History log — view all sign-outs and export results to CSV  
- Shared access — supports concurrent use over a network share  
- Self-contained — no installation, no internet, no dependencies

## Interface Overview

| Status | Highlight | Meaning |
|:--------|:-----------|:---------|
| Available | Normal white | Ready for sign-out |
| Out | Light amber | Currently signed out |
| Lost | Light red | Marked as missing |

**Double-click behavior:**  
- Available: opens the Sign Out dialog  
- Out: marks card as Returned

## Setup

### Option 1 — Run from source
```bash
git clone https://github.com/Jett-Lu/ceti-visitor-card-tracker.git
cd ceti-visitor-card-tracker
python main.py
