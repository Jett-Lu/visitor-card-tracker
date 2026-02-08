# Visitor Card Tracker

A lightweight Tkinter + SQLite app to track visitor and lab access cards:
- Status: Available, Out, Lost
- Holder name, sign-out time, notes
- History log with CSV export
- Portable database file so the whole folder can be placed on a shared drive

## Run (Python)
```bash
python JettCardHelper.py
```

This project uses only the Python standard library.

## Database
The app stores data in `cards.db` in the same folder as the script/executable.
This is intentional so multiple staff can run the app from a shared network folder and use the same database.

Backup: copy `cards.db` when the app is closed or idle.

## How to use
- Double-click a row:
  - Available: opens Sign Out
  - Out: returns the card
- Use Search to filter by label, holder, ID, notes, or location
- Use Status filter to view Available, Out, or Lost
- Use History to export records to CSV

## Author
Jett Lu
