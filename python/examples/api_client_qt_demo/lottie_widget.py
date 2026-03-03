"""
LottieWidget — PySide6  (offline, lottie.min.js locale)
Visualizza animazioni Lottie (come bytes) tramite QWebEngineView.

Due modalità per caricare lottie.min.js da disco:
  • INLINE  (default) — il contenuto del .js viene incorporato direttamente
                        nell'HTML; funziona sempre, anche con baseUrl vuoto.
  • BASEURL            — l'HTML referenzia il file con <script src="lottie.min.js">
                        e setHtml riceve baseUrl=QUrl.fromLocalFile(cartella).
                        Richiede che QtWebEngine abbia i permessi di lettura locale.
"""
#-------------------------------------------------------------------------------
# Name:         lottie_widget
#
# Purpose:      QT User Dialogs
#
# Note          Compatible with API server version 1.5.3
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note          Checked with Python 3.11.9
#
# Author:       rosettacnc-classroom@gmail.com
#
# Created:      03/03/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
import json
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView


# ─────────────────────────────────────────────────────────────
#  Template HTML — il placeholder {lottie_script} viene
#  rimpiazzato con il tag <script> appropriato al metodo scelto
# ─────────────────────────────────────────────────────────────
_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      width: 100%; height: 100%;
      background: {background};
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }}
    #lottie-container {{
      width: {width};
      height: {height};
    }}
  </style>
</head>
<body>
  <div id="lottie-container"></div>

  {lottie_script}

  <script>
    lottie.loadAnimation({{
      container: document.getElementById('lottie-container'),
      renderer: '{renderer}',
      loop: {loop},
      autoplay: {autoplay},
      animationData: {animation_json},
    }});
  </script>
</body>
</html>
"""


def _load_lottie_inline(js_path: str | Path) -> str:
    """Legge lottie.min.js e lo restituisce come tag <script> inline."""
    js_content = Path(js_path).read_text(encoding="utf-8")
    return f"<script>{js_content}</script>"


def _load_lottie_baseurl(js_filename: str = "lottie.min.js") -> str:
    """Restituisce un tag <script src="..."> relativo (usato con baseUrl)."""
    return f'<script src="{js_filename}"></script>'


class LottieWidget(QWebEngineView):
    """
    Widget PySide6 per visualizzare un'animazione Lottie da bytes, offline.

    Parametri
    ---------
    lottie_bytes : bytes
        Contenuto del file .json Lottie.
    js_path : str | Path
        Percorso al file lottie.min.js scaricato localmente.
    inline_js : bool
        True  → incorpora lottie.min.js direttamente nell'HTML (consigliato).
        False → usa <script src="..."> + setHtml con baseUrl locale.
    width, height : str
        Dimensioni CSS del contenitore animazione.
    loop : bool
        Loop automatico.
    autoplay : bool
        Parte immediatamente.
    renderer : str
        "svg" | "canvas" | "html".
    background : str
        Colore CSS sfondo (es. "transparent", "#1a1a2e").
    parent : QWidget | None
    """

    def __init__(
        self,
        lottie_bytes: bytes,
        js_path: str | Path,
        *,
        inline_js: bool = True,
        width: str = "100%",
        height: str = "100%",
        loop: bool = True,
        autoplay: bool = True,
        renderer: str = "svg",
        background: str = "transparent",
        parent=None,
    ):
        super().__init__(parent)

        js_path = Path(js_path)

        # — Prepara il tag <script> per lottie.min.js —
        if inline_js:
            # ✅ METODO 1 — INLINE (consigliato)
            # Il JS viene incollato nell'HTML: nessun problema di permessi,
            # funziona con qualsiasi baseUrl (anche "about:blank").
            lottie_script = _load_lottie_inline(js_path)
            base_url = QUrl("about:blank")
        else:
            # METODO 2 — BASEURL
            # L'HTML carica il file con <script src="lottie.min.js">.
            # setHtml riceve come baseUrl la cartella in cui si trova il .js,
            # così QtWebEngine risolve il percorso relativo correttamente.
            lottie_script = _load_lottie_baseurl(js_path.name)
            base_url = QUrl.fromLocalFile(str(js_path.parent) + "/")

        # — Serializza l'animazione Lottie —
        animation_data = json.loads(lottie_bytes.decode("utf-8"))
        animation_json = json.dumps(animation_data)

        html = _HTML_TEMPLATE.format(
            lottie_script=lottie_script,
            animation_json=animation_json,
            width=width,
            height=height,
            loop="true" if loop else "false",
            autoplay="true" if autoplay else "false",
            renderer=renderer,
            background=background,
        )

        if background == "transparent":
            self.page().setBackgroundColor(Qt.GlobalColor.transparent)

        self.setHtml(html, base_url)

    # ── Controllo runtime ────────────────────────────────────────────────

    def play(self):
        self.page().runJavaScript("lottie.play();")

    def pause(self):
        self.page().runJavaScript("lottie.pause();")

    def stop(self):
        self.page().runJavaScript("lottie.stop();")

    def set_speed(self, speed: float):
        self.page().runJavaScript(f"lottie.setSpeed({speed});")

    def set_direction(self, forward: bool = True):
        self.page().runJavaScript(f"lottie.setDirection({1 if forward else -1});")
