import io
from flask import Flask, request, send_file, render_template_string
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
      <button type="submit">Générer et télécharger</button>
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
        if not first or not family:
            return render_template_string(HTML_FORM + "<p style='color:red;'>Les deux champs sont requis.</p>")
        
        first = normalize_name(first)
        family = normalize_name(family)
        
        name = f"{family}.{first}"
        img = generate_image(name)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        filename = f"{name}.png"
        return send_file(buf, mimetype="image/png", as_attachment=True, download_name=filename)
    return render_template_string(HTML_FORM)

if __name__ == "__main__":
    # exécution locale (Mac). Installez Flask si nécessaire: pip install Flask
    app.run(host="127.0.0.1", port=5000, debug=True)