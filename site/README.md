# LLD Preparation Lab

A dependency-free progress tracker for the repository's 15 concise chapters.

## Local use

    python -m http.server 4173 --directory site

Open http://localhost:4173.

## Test

    npm.cmd test --prefix site

Completion is stored only in browser localStorage. Export/import provides a portable JSON backup. The GitHub Pages workflow tests and publishes this directory after pushes to main.
