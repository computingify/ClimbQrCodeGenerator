import io
import base64
import zipfile
from flask import Flask, request, send_file, render_template_string, Response
import qrcode
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

HTML_FORM = """
<!doctype html>
<html lang="fr">
  <head><meta charset="utf-8"><title>Générateur QR</title></head>
  <body>
    <h1>Générer un QR numérique pour Annonay Escalade</h1>
    <form method="post" action="/" >
      <label>Prénom: <input type="text" name="first" required></label><br><br>
      <label>Nom de famille: <input type="text" name="family" required></label><br><br>
      <button type="submit" name="action" value="png">Télécharger PNG</button>
      <button type="submit" name="action" value="pwa">Télécharger Application</button>
    </form>
  </body>
</html>
"""

def generate_image(text: str) -> Image.Image:
    # création du QR
    qr = qrcode.make(text)
    title = text
    qr_img = qr.convert("RGB")
    w, h = qr_img.size

    # police système Mac ou police par défaut
    try:
        font = ImageFont.truetype("/Library/Fonts/Arial.ttf", size=max(14, w // 20))
    except Exception:
        font = ImageFont.load_default()

    # mesurer le texte (compatibilité Pillow)
    draw_tmp = ImageDraw.Draw(qr_img)
    try:
        bbox = draw_tmp.textbbox((0, 0), title, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        try:
            text_w, text_h = font.getsize(title)
        except Exception:
            text_w, text_h = (len(title) * 8, max(12, font.size if hasattr(font, "size") else 12))

    padding = 10
    new_h = h + text_h + padding
    new_img = Image.new("RGB", (w, new_h), "white")
    draw = ImageDraw.Draw(new_img)

    text_x = (w - text_w) // 2
    text_y = padding // 2
    draw.text((text_x, text_y), title, fill="black", font=font)

    new_img.paste(qr_img, (0, text_h + padding))
    return new_img

def normalize_name(s: str) -> str:
    # majuscule première lettre, le reste en minuscule ; conserve traits d'union et espaces
    parts = []
    for space_part in s.split():
        hy_parts = [p.capitalize() if p else p for p in space_part.split("-")]
        parts.append("-".join(hy_parts))
    return " ".join(parts)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        first = (request.form.get("first") or "").strip()
        family = (request.form.get("family") or "").strip()
        action = request.form.get("action")
        if not first or not family:
            return render_template_string(HTML_FORM + "<p style='color:red;'>Les deux champs sont requis.</p>")
        
        first = normalize_name(first)
        family = normalize_name(family)
        
        name = f"{family}.{first}"
        img = generate_image(name)
        if action == "png":
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            filename = f"{name}.png"
            return send_file(buf, mimetype="image/png", as_attachment=True, download_name=filename)
        elif action == "pwa":
            # Générer PWA ZIP (même logique que ta route /pwa)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            index_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>QR {name}</title>
  <link rel="manifest" href="manifest.json">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      margin: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background: #fff;
    }}
    img {{
      max-width: 90vw;
      max-height: 90vh;
    }}
  </style>
</head>
<body>
  <img src="data:image/png;base64,{b64}" alt="QR Code">
  <script>
    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('sw.js');
    }}
  </script>
</body>
</html>
"""

            manifest_json = f"""{{
  "name": "QR {name}",
  "short_name": "QR",
  "start_url": "index.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#ffffff",
  "icons": [{{ "src": "icon.png", "sizes": "192x192", "type": "image/png" }}]
}}
"""

            sw_js = """self.addEventListener("install", event => {
  event.waitUntil(
    caches.open("qr-cache").then(cache => {
      return cache.addAll(["index.html", "manifest.json", "icon.png"]);
    })
  );
});
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});
"""

            # Icône placeholder
            icon = Image.new("RGB", (192,192), "white")
            icon_buf = io.BytesIO()
            icon.save(icon_buf, format="PNG")
            icon_buf.seek(0)

            # ZIP
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as z:
                z.writestr("index.html", index_html)
                z.writestr("manifest.json", manifest_json)
                z.writestr("sw.js", sw_js)
                z.writestr("icon.png", icon_buf.read())
            zip_buf.seek(0)

            return send_file(zip_buf, mimetype="application/zip", as_attachment=True, download_name=f"PWA_{name}.zip")

    return render_template_string(HTML_FORM)

if __name__ == "__main__":
    # exécution locale (Mac). Installez Flask si nécessaire: pip install Flask
    app.run(host="127.0.0.1", port=5000, debug=True)