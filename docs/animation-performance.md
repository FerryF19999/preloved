# Animation optimization evidence

Baseline: commit `28f1fa6`. Test: `tests/measure_animation.py`.
Environment: headless Chromium, 390×844 mobile viewport, 4× CPU throttling, local HTTP, fresh browser contexts. One recorded baseline and final sample; these numbers are laboratory measurements, **not physical-phone FPS or a device-wide guarantee**.

## Changes

- Virtual Fit stops its animation-frame loop after motion settles, wakes for navigation/drag/resize/pointer input, and suspends on visibility change. Removed continuous decorative bobbing.
- Mobile cards retain their spatial layout but avoid moving backdrop blur. The center uses the local catalogue thumbnail on mobile instead of decoding the remote full-size original.
- Runway mobile uses a bounded 360ms ease-out transition instead of waiting for per-actor springs to converge to an imperceptible tolerance. Desktop physics remain unchanged.
- Invisible actors skip style updates. Mobile morph transitions and decorative pulse animations do not keep repainting after navigation.
- Original layouts, catalog identity, source links, swipe, play/pause, zoom and shared bag are retained.

## Recorded results

- Virtual Fit idle, over 2 seconds: app animation callbacks **39 → 0**; browser task time **416.69ms → 7.14ms**.
- Virtual Fit next-product: browser task time **873.95ms → 366.63ms** (58.0% less); navigation settled **3045.27ms → 824.57ms**.
- Runway next-look: browser task time **1203.22ms → 401.57ms** (66.6% less); navigation settled **2217.50ms → 557.90ms**.
- Runway idle: zero app animation callbacks before and after. Idle performance was not the runway bottleneck.
- App callback counts measure scheduled JavaScript work, not display FPS.

Raw samples: `performance-before.json`, `performance-after.json`.

## Verification

`tests/test_studio.py` passed at 320px, 390px and 1440px, including virtual-fit selection, mobile runway drag, visible controls, autoplay advance/pause, exact catalog UUID bundle insertion, parent bag synchronization, deduplication, no horizontal overflow, and no page errors.

Run the lab probe with:

```sh
python tests/measure_animation.py animation-lab
```

Generated reports and screenshots stay in `.test-results/`.
