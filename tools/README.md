# tools

| file | what it does |
|---|---|
| `build.py` | Renders every HTML page from the single `PROJECTS` list. Run it from this folder. |
| `stepparse.py` | Minimal ISO-10303-21 (STEP) reader — entity table + argument parser. |
| `tess.py` | Tessellates a STEP B-rep into a binary glTF, with CAD edges as a line primitive. |
| `imgs.py` | Original pass over the source photos: crop, resize, WebP. |
| `covers2.py` | Generates the bento gallery cover crops. |
| `fixpairs.py` | Normalises side-by-side image pairs to matching aspect ratios. |

The image scripts expect the extracted source PNGs; they are kept here as a
record of how `assets/img/` was produced rather than as something to re-run.
