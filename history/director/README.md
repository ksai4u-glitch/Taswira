# Director's preview

A separate cinematic experiment for the sourced deep-time and Nok chapters. It does not replace
or publish the history page. No new historical content, images, flags or borders are added.

A ready-to-open build is in [`previews/director.html`](../../previews/director.html). Download the
raw file and open it in a browser. Rebuild that file with the command below when changing the preview.

```sh
python build_director.py --check
python build_director.py --output /tmp/taswira-director.html
```

Open the generated file in a browser. All geography, scripts and styles are embedded; it works
offline. The source/evidence dialog and complete HTML transcript preserve citations, rights and
disagreements. The page remains an unreviewed draft.

The globe uses the existing Merdith et al. plate rotations. Simplified modern continental outlines
are not ancient coastlines; the regional view also uses modern physical geography. The regional
view intentionally adds no modern roads, settlements or political borders. See `../geo/README.md`
for dataset provenance and limitations. This experiment includes neither campaign nor state maps.

Use Play, the scene rail, chapter buttons, arrow controls or the labelled progress slider.
Space toggles playback and arrow keys change scenes when focus is outside a control. Playback
starts only on request and pauses when the tab is hidden or reduced-motion preferences change.
There is no audio. The controls remain outside the canvas and the text version works without JS.

## Reproducible frames

```js
window.TaswiraDirector.seek({ chapter: 0, scene: 2, progress: 0.65 });
window.TaswiraDirector.getState();
```

Seeking pauses playback. Progress is normalized to 0–1; chapter and scene are zero-based indices.
All drawing is derived from this state, including plate rotation, camera position and captions.
At a fixed viewport, repeated seeks render identical canvas pixels. Freeze viewport, device scale,
browser and fonts when capturing a sequence. Caption timing currently follows sentence order;
it has not been aligned to a voice-over. The existing history player is unaffected.

## Checks

```sh
python -m unittest discover -s tests
node --check history/director/director.js
```

Optional browser checks require Playwright and Chromium:

```sh
node tests/director_browser.cjs /tmp/taswira-director.html
```

Set `CHROMIUM_PATH` if Chromium lives elsewhere. These check scene rendering, reproducibility,
playback and seeking, evidence, phone layout, reduced motion and zero network requests.
