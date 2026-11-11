// About page: what the generator is, how a picture becomes text, how to run the CLI, the GUI and this web app, credits.
import { route, app, api, esc } from './core.js';

route('about', async () => {
  const info = await api('/info');
  const sets = Object.entries(info.char_sets);
  app().innerHTML = `<p class="kicker">About</p><h1>ASCII Art Generator</h1>
    <p class="lead">${esc(info.description)} It has a command-line tool, a Tkinter desktop app with tabs of settings, and
      now this web version.</p>
    <h2>How a picture becomes text</h2>
    <p>The image is resized (Lanczos) to one pixel per character. Unless you fix the height, the number of lines keeps the
      aspect ratio, halved because a character is about twice as tall as it is wide. The image is turned to grey, then
      the optional steps run in this order: sharpness, contrast, brightness, histogram equalization, edge detection,
      unsharp mask, adaptive thresholding, invert and dithering. Finally each grey level 0–255 picks a character:</p>
    <p class="eq">index = int(grey × (number of characters − 1) / 255)</p>
    <p>Dark pixels get the first characters (a space), bright pixels the last, densest ones, so the art reads as light
      characters on a dark background; use <i>invert</i> for black text on white paper.</p>
    <div class="scroll"><table><tr><th>set</th><th>characters, darkest pixel first</th></tr>
      ${sets.map(([k, v]) => `<tr><td>${esc(k)}</td><td class="mono">${esc(v.replace(/ /g, '␣'))}</td></tr>`).join('')}</table></div>
    <h2>Run the command-line tool and the desktop app</h2>
    <pre>pip install -r requirements.txt
python ascii_art_generator.py photo.jpg -w 120 --char-set basic --contrast 1.2 --preview
python ascii_art_generator.py photo.jpg -o art.txt -H 60 --invert --dither
python gui_application.py      # desktop app (Tkinter)</pre>
    <p>The command line offers width, height, character set, contrast, brightness, invert and dithering. The desktop app
      and this web version add sharpness, histogram equalization, edge detection (standard, Sobel, Canny), unsharp mask,
      adaptive thresholding and your own character set, and save as text, HTML or PNG.</p>
    <h2>Run the web app</h2>
    <pre>pip install -r requirements-web.txt
python run_web.py              # http://127.0.0.1:8174</pre>
    <p>The local web app can convert with the repo's Python code (<code>ascii_pipeline.py</code>, the same steps the desktop
      app runs) and compares the result with the in-browser engine. The GitHub Pages site uses only the in-browser engine,
      a JavaScript port of the Pillow and OpenCV operations involved (<code>ascii_engine.js</code>). A test converts
      ${info.js_test_cases} combinations of options on generated test images in both and requires identical text.</p>
    <p class="small mute">Small differences can still come from decoding the file: browsers and Pillow can decode the same
      JPEG a level apart here and there (PNG is lossless and matches), transparent pixels are read without their colour
      by the browser, and some browsers apply a photo's EXIF rotation, which Pillow does not.</p>
    <h2>Credits</h2>
    <p>Inspired by classic ASCII art generators; thanks to the PIL/Pillow project (and OpenCV for the edge and threshold
      filters). Built with AI assistance from <a href="https://claude.com/" target="_blank" rel="noopener">Claude (Anthropic)</a>.
      Licence: MIT. Source: <a href="https://github.com/gddickinson/${esc(info.repo)}" target="_blank" rel="noopener">github.com/gddickinson/${esc(info.repo)}</a>.</p>`;
});
