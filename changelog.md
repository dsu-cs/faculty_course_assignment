# Changelog

## [PROJ-27] - Shared CSS -11 March 2026
- Added changelog to root directory.
- Added a quickstart guide into the "Docker Section" of fca/readme.md to help devs get started quick with the docker image.
- Modified static/css/project.css to have Color variables according to DSU brand guidelines manual andUsed the new color variables to overrride bootstrap's default colors for info, primary, secondary, light, and dark.
- Added background gradient CSS (bg-dsu-gradient, bg-dsu-gradient-vertical) classes according to DSU brand guidelines manual.
- Added DSU Wordmark SVG file and DSU Logo PNG file to static/img directory.
- Added DSU logo png as the navbar logo.
- Modified base.html to add a footer and move the navbar outside of the content block so that it is visible on all pages that extend base.html.
- Modified base.html to show a sample of common components as a reference for developers
- Replaced Favicon.ico with DSU Logo Favicon