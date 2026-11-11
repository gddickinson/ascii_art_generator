"""Web interface for the ASCII Art Generator (python run_web.py -> http://127.0.0.1:8174).

Contents:
    app.py          FastAPI app: front end in static/, JSON API under /api, STATIC_ENDPOINTS for the static site
    convert_api.py  POST /api/convert: decode an uploaded image and run ascii_pipeline.convert (Python)
    static/         plain ES-module front end; ascii_engine.js (+ pil_ops.js, cv_ops.js) is the JS port of
                    ascii_pipeline.py used on the GitHub Pages site, tested by ascii_engine.test.mjs
"""
