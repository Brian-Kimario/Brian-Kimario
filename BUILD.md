# How this profile is built

Every visual in `README.md` is an SVG generated from source in `tools/`. There is
no builder site and no screenshot. Only the standard library is used, so nothing
here needs `pip install`.

```
tools/
  theme.py         shared palette, type scale, panel chrome
  gen_hero.py      assets/hero.svg     — particle morph + dossier
  gen_panels.py    assets/projects.svg, assets/stack.svg
  gen_stats.py     assets/stats.svg    — live, run by CI daily
  build.sh         regenerates everything except stats
```

## Why SVG and not a GIF

GitHub sanitises README markdown — no `<style>`, no `<script>`. But images are
untouched, and **declarative animation inside an SVG still runs when the SVG is
loaded through `<img>`**: SMIL (`<animate>`, `<animateTransform>`) and CSS
`@keyframes` both work. JavaScript does not. So anything that animates on this
page is doing it declaratively.

`hero.svg` is ~1 MB of text but compresses to ~74 KB, and GitHub serves it
gzipped — the wire cost is roughly one photo.

## The particle morph

`gen_hero.py` samples four point sets of 2,600 points each and animates every
particle between them with one `animateTransform` per circle.

1. **Portrait** — the headshot, reduced to a greyscale PGM by ffmpeg. The
   backdrop is separated with a flood fill from the frame border, not a
   luminance threshold: in this photo the forehead highlights are *lighter* than
   parts of the background, so any global cutoff punches holes in the face.
   Density is `base fill + tone + edge energy`; brightness and radius then track
   the source tone, because density alone renders a silhouette, not a face.
2. **DAG** — extract → transform → branch → load. The shape of `etl_weather`.
3. **BK monogram** — rasterised by ffmpeg's `drawtext`, sampled with the
   letterform outline weighted 6×.
4. **Star schema** — one fact table, four dimensions.

Points in each shape are sorted by angle around their centroid before being
paired up, so particle *i* in one shape lands near particle *i* in the next.
That turns the transition into a sweep instead of 2,600 dots teleporting.

Rebuild the source bitmaps if you change the photo:

```bash
cd tools
ffmpeg -y -i portrait_src.jpg \
  -vf "crop=2300:2900:400:120,scale=340:-1,format=gray" -pix_fmt gray portrait.pgm
ffmpeg -y -f lavfi -i color=c=black:s=320x320 \
  -vf "drawtext=font='Helvetica':text='BK':fontcolor=white:fontsize=190:\
x=(w-text_w)/2:y=(h-text_h)/2-10,format=gray" -frames:v 1 -pix_fmt gray mono.pgm
```

Then `python3 gen_hero.py`. Pass a shape index (`python3 gen_hero.py 0`) to dump
a still of one pose for eyeballing.

## Editing the content

Project cards and the toolchain live in the tables at the top of
`gen_panels.py`. Edit, run `python3 gen_panels.py`, commit the changed SVGs.

## CI

- `refresh.yml` — daily, regenerates `assets/stats.svg` from the GraphQL API and
  commits it if it changed.
- `snake.yml` — daily, builds the contribution snake into the `output` branch
  with the palette from `theme.py`.

Both are also `workflow_dispatch`, so you can trigger them by hand.

## Caveats

- **Camo caching.** GitHub proxies README images and caches them. A freshly
  pushed panel can take a while to appear. Hard-refresh, or wait it out.
- **Private contributions.** The contribution total only includes private work
  if you turn it on: *Settings → Public profile → **Include private
  contributions on my profile***. Without it the headline number counts public
  commits only, which for this account is a small fraction of the real total.
- **Reduced motion.** Every animation is disabled under
  `prefers-reduced-motion: reduce`.
