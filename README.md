# CETI Visitor Card Tracker

- This application was originally developed for internal use within the Engineering Materials Office (EMO) at the Ministry of Transportation (MTO), supporting administrative tracking needs in a laboratory and office environment. It has since been generalized and released as a standalone tool suitable for other lab, office, and shared-access settings.
- This project is not an official Government of Ontario or MTO product and is provided here as an independent, general-purpose application.

A lightweight Windows desktop application for tracking visitor and lab access cards.  
Built with Python, Tkinter, and SQLite, and distributed as a portable `.exe`.

## Overview
CETI Visitor Card Tracker is designed for shared lab and office environments where physical access cards must be tracked reliably. The application records which cards are available, who has signed them out, when they were issued, and when they are returned.

The system supports normal operation, lost cards, recovery, and full historical audit logs, all without requiring a server or installation.

<img width="2082" height="1156" alt="image" src="https://github.com/user-attachments/assets/a3705157-e25f-42f1-bd0c-ad5022c10e60" />

## Features
- Track card status: **Available**, **Out**, **Lost**
- Record holder name, sign-out time, and optional notes
- One-click return, mark lost, and mark found
- Search by card name, holder, ID, notes, or location
- Status filter for quick review
- Full sign-out history with CSV export
- Color-coded rows for quick visual status checks
- First-run setup with optional preset cards
- Portable database stored next to the executable

## How to Use (Windows EXE)

1. Download the latest `.exe` from **Releases**
2. Place the exe in a folder (local or shared drive)
3. Double-click to run

No installation or Python required.

### First Run

<img width="388" height="251" alt="image" src="https://github.com/user-attachments/assets/d449be2c-6081-4594-95f3-02db8caeffa5" />

On first launch, you will be prompted to:
- Add preset cards, or
- Start with a blank list

## Basic Operation

### Signing Out a Card
- Double-click an **Available** card
- Enter the holder name and optional notes
- Card status changes to **Out**

### Returning a Card
- Double-click an **Out** card, or
- Select the card and click **Return**

### Lost and Found
- **Mark Lost** when a card cannot be located
- **Mark Found** when it is recovered and returned to storage

### History
- View all sign-out records in the **History** window
- Filter by card or holder
- Export history to CSV for reporting or audits

## Visual Indicators
- **Available**: normal background
- **Out**: light amber
- **Lost**: light red

## Data Storage
- All data is stored in `cards.db` in the same folder as the exe
- Designed for **portable use** and **shared network folders**
- Multiple users can run the app from the same folder and share one database

### Backup
- Close the app
- Copy `cards.db` to a safe location

### Restore
- Replace `cards.db` with a backup copy

## Notes on Shared Drives
- The app uses SQLite with WAL mode and retry timeouts
- If you see “database is locked”, another user is saving data. Try again shortly

## Build Information
- Python + Tkinter GUI
- SQLite backend
- Packaged as a Windows executable using PyInstaller

## How to Run (Python)

**Requirements:** 
- Python 3.9 or newer on Windows, macOS, or Linux.

**Steps:** 
1. Clone or download this repository (`git clone https://github.com/Jett-Lu/visitor-card-tracker.git`), or download the ZIP and extract it.
2. Navigate to the project folder (`cd visitor-card-tracker`), then run the application with `python JettCardHelper.py`.
3. The application window will open automatically.

**Files Created on First Run:** 
- `cards.db` (This is the SQLite database containing all card and history data. Do not delete `cards.db` unless you intend to reset all data.)

**Notes:**
The database file is created in the same folder as the script. The project can be placed on a shared network drive. If you see a “database is locked” message, another user is writing to the database; wait briefly and try again.
