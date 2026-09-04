# austinnnli.github.io

Personal portfolio for **Austin Li** — Waterloo Mechatronics Engineering.
Plain static HTML/CSS/JS. No build step is required to deploy.

---

## Before you publish: add your resume

`assets/resume.pdf` is a **placeholder**. Drop your own PDF in at that exact
path and the header link works everywhere — no code changes needed.

---

## Previewing it locally

Don't open `index.html` by double-clicking it. Browsers block `fetch()` on
`file://` URLs, so the 3D trailer viewer will say it can't load the model
(everything else works). Serve the folder instead:

```bash
cd austinnnli.github.io
python -m http.server 8000
```

Then open <http://localhost:8000>. On GitHub Pages this doesn't apply — it's
served over HTTP, so the viewer works normally.

---

## Deploying to GitHub Pages

1. Create a repository named **`austinnnli.github.io`**.
2. Copy everything in this folder into it (including the hidden `.nojekyll`
   file — it tells GitHub to serve the files as-is).
3. `git add . && git commit -m "portfolio" && git push`
4. Repo **Settings → Pages → Source → Deploy from a branch → `main` / `root`**.

The site goes live at `https://austinnnli.github.io` in a minute or two.

Every project also has its own permanent URL, ready to paste into a paper
portfolio or an application:

| Project | URL |
|---|---|
| PMSM OneWheel Hub Motor | `/projects/pmsm-hub-motor.html` |
| FORC Speed Controller | `/projects/forc-speed-controller.html` |
| Autonomous Pool-Playing Robot | `/projects/pool-robot.html` |
| AutoCleat | `/projects/autocleat.html` |
| Cycloidal Gearbox | `/projects/cycloidal-gearbox.html` |
| Rocket Transport Trailer CAD | `/projects/rocket-trailer.html` |

---

## Layout

```
index.html            main page — hero + all six projects on the timeline
gallery.html          bento-box grid of project covers
projects/*.html       one standalone, shareable page per project
assets/css/site.css   the whole design system
assets/js/site.js     header, contact modal, timeline rail, skip button
assets/js/cadview.js  dependency-free WebGL viewer for the .glb model
assets/img/           WebP photos and video posters
assets/video/         H.264 MP4s (muted, looping, autoplay in view)
assets/model/         trailer.glb — the STEP file, tessellated
tools/                scripts that generated the pages and assets
```

## Editing content

All copy and image ordering lives in one list, `PROJECTS`, at the top of
`tools/build.py`. Edit it and re-run:

```bash
cd tools && python3 build.py
```

That rewrites `index.html`, `gallery.html` and all six project pages so they
never drift apart. Nothing else needs touching. (Requires Python 3 + Pillow.)

To add a project: append a dict to `PROJECTS`, add a `.t-<name>` rule to the
`.bento` grid in `site.css`, and re-run the build.

## The 3D trailer viewer

`tools/tess.py` is a small STEP (AP214) reader and tessellator written for
this site — it parses the B-rep, meshes planes, cylinders, spheres, tori and
NURBS edges, keeps the per-solid colours, and writes a compact `.glb` with a
line primitive holding the real CAD edges. Regenerate with:

```bash
python3 tools/tess.py path/to/trailer.STEP assets/model/trailer.glb 0.0005
```

The last argument is the chord tolerance as a fraction of the model diagonal —
smaller means a finer mesh and a bigger file (0.0005 ≈ 26k triangles, 0.8 MB).

`assets/js/cadview.js` renders it with hand-written WebGL — no three.js, no
CDN, nothing to break.

## Notes

- Fonts come from Google Fonts (Inter / Inter Tight) with a system-sans
  fallback, so the site still looks right if that request is blocked.
- Videos are muted and only play while on screen, so they cost nothing until
  a visitor reaches them.
- Everything respects `prefers-reduced-motion`.
