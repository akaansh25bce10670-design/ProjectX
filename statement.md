# Project Statement

## Problem Statement
Users often struggle to conveniently search for songs and view their lyrics in one place. Most available solutions either lack accuracy, require paid APIs, or do not provide a user-friendly graphical interface. This project aims to create a GUI-based Lyrics Assistant that allows users to search songs, fetch lyrics from multiple sources, and display results cleanly and efficiently.

## Scope of the Project
- The project focuses on building a desktop-based GUI application.
- Song search is performed via the iTunes Search API.
- Lyrics are fetched from multiple providers to maximize accuracy.
- Local caching is used to reduce repeated API calls.
- The project provides basic search, view, and display functionality—advanced features like playlist management or user accounts are outside the current scope.

## Target Users
- Music listeners who want quick access to song lyrics.
- Students or developers learning about GUI application building.
- Users with limited internet access who benefit from cached lyric retrieval.
- Anyone who needs a lightweight, reliable lyrics lookup tool without needing a browser.

## High-Level Features
- GUI-based search interface for songs.
- Song lookup using the iTunes Search API.
- Lyrics fetching from multiple sources with fallback methods.
- Automatic caching of lyrics for offline or quick future access.
- Non-blocking background threads to ensure smooth UI experience.
- Clean display area for lyrics with scrollable text view.

