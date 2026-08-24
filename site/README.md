# LLD Preparation Lab

This directory is a dependency-free static progress tracker for the 15-topic LLD
Preparation Bible.

## Local use

From the repository root:

```powershell
python -m http.server 4173 --directory site
```

Open `http://localhost:4173`.

## Tests

```powershell
npm.cmd test --prefix site
```

## Persistence

Topic completion is stored in browser `localStorage` under:

```text
lld-preparation-bible:topic-progress:v1
```

Export/import controls provide a portable JSON backup. No progress is sent to a
server.

## Deployment

The repository's `deploy-pages.yml` workflow tests the progress logic and
publishes this directory to GitHub Pages after each push to `main`.
