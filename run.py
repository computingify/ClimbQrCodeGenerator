from flask import Flask, request, send_file, render_template
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
import os
import io
import zipfile
import qrcode
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "AnnonayEscaladeLogo.png")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__)

def generate_image(text: str, logo_path: str = LOGO_PATH, bottom_text: str = None, bg_color: str = "white", show_logo: bool = True) -> Image.Image:
    # QR avec correction haute (important si on met un logo)
    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_H,
        box_size=15,
        border=5
    )
    qr.add_data(text)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color=bg_color).convert("RGB")
    w, h = qr_img.size

    # --- Ajouter un logo au centre ---
    if show_logo and logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo_size = int(w * 0.25)  # 15% de la largeur du QR
            logo.thumbnail((logo_size, logo_size))
            pos = ((w - logo.size[0]) // 2, (h - logo.size[1]) // 2)
            qr_img.paste(logo, pos, mask=logo)
        except Exception as e:
            print("⚠️ Erreur logo:", e)

    # --- Ajouter un texte sous le QR ---
    if bottom_text:
        try:
            font = ImageFont.truetype("/Library/Fonts/Arial.ttf", size=max(14, w // 15))
        except Exception:
            font = ImageFont.load_default()

        draw_tmp = ImageDraw.Draw(qr_img)
        try:
            bbox = draw_tmp.textbbox((0, 0), bottom_text, font=font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = font.getsize(bottom_text)

        padding = 10
        bottom_margin = 10
        new_h = h + text_h + padding + bottom_margin
        new_img = Image.new("RGB", (w, new_h), bg_color)
        draw = ImageDraw.Draw(new_img)

        # centrer le texte
        text_x = (w - text_w) // 2
        text_y = h + (padding // 2)
        draw.text((text_x, text_y), bottom_text, fill="black", font=font)

        new_img.paste(qr_img, (0, 0))
        return new_img

    return qr_img

def is_valid_bg_color(color: str) -> bool:
    """Vérifie que la couleur de fond est valide et permet une bonne lisibilité"""
    valid_colors = {
        # Neutres
        "white": "#ffffff",
        "#f5f5f5": "White Smoke",
        
        # Rouges/Roses
        "#fff0f5": "Lavender Blush",
        "#ff69b4": "Hot Pink", 
        "#ff1493": "Deep Pink",
        
        # Oranges/Jaunes
        "#ff4500": "Orange Red",
        "#fff8dc": "Cornsilk",
        "#fdf5e6": "Old Lace",
        "#ffd700": "Gold",
        "#ffff00": "Yellow",
        
        # Verts
        "#7fff00": "Chartreuse",
        "#00ff00": "Lime",
        "#f0fff0": "Honeydew",
        
        # Bleus/Cyans
        "#00ffff": "Cyan",
        "#f0f8ff": "Alice Blue",
        
        # Violets
        "#9400d3": "Dark Violet",
        "#e6e6fa": "Lavender"
    }
    return color in valid_colors

def normalize_name(s: str) -> str:
    # majuscule première lettre, le reste en minuscule ; conserve traits d'union et espaces
    parts = []
    for space_part in s.split():
        hy_parts = [p.capitalize() if p else p for p in space_part.split("-")]
        parts.append("-".join(hy_parts))
    return " ".join(parts)

def create_pwa_zip(name: str, qr_image: Image.Image) -> io.BytesIO:
    """Crée un ZIP contenant tous les fichiers PWA"""
    # Créer le répertoire temporaire pour la PWA
    pwa_dir = os.path.join(BASE_DIR, "pwa_temp", name)
    os.makedirs(pwa_dir, exist_ok=True)
    
    # Sauvegarder l'image QR
    qr_path = os.path.join(pwa_dir, "qr.png")
    qr_image.save(qr_path, format="PNG")
    
    # Copier les fichiers statiques vers le répertoire PWA
    static_files = ["pwa_index.html", "manifest.json", "sw.js", "icon.png"]
    for file in static_files:
        src = os.path.join(STATIC_DIR, file)
        if os.path.exists(src):
            if file == "pwa_index.html":
                # Renommer index.html pour la PWA et personnaliser le titre
                dst = os.path.join(pwa_dir, "index.html")
                with open(src, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = content.replace("{{name}}", name)
                with open(dst, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif file == "manifest.json":
                # Personnaliser le manifest
                dst = os.path.join(pwa_dir, file)
                with open(src, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = content.replace("{{name}}", name)
                with open(dst, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                dst = os.path.join(pwa_dir, file)
                shutil.copy2(src, dst)
    
    # Créer le ZIP
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(pwa_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, pwa_dir)
                z.write(file_path, arc_name)
    
    # Nettoyer le répertoire temporaire
    shutil.rmtree(os.path.join(BASE_DIR, "pwa_temp"), ignore_errors=True)
    
    zip_buf.seek(0)
    return zip_buf

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        first = (request.form.get("first") or "").strip()
        family = (request.form.get("family") or "").strip()
        bg_color = request.form.get("bg_color", "white")
        show_logo = request.form.get("show_logo", "true") == "true"
        action = request.form.get("action")
        
        if not first or not family:
            return render_template("index.html", error="Les deux champs sont requis.")
        
        first = normalize_name(first)
        family = normalize_name(family)
        
        name = f"{family}.{first}"
        img = generate_image(text=name, bottom_text=f"{first} {family}", bg_color=bg_color, show_logo=show_logo)
        
        if action == "png":
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            filename = f"{name}.png"
            return send_file(buf, mimetype="image/png", as_attachment=True, download_name=filename)
            
        elif action == "pwa":
            zip_buf = create_pwa_zip(name, img)
            return send_file(zip_buf, mimetype="application/zip", as_attachment=True, download_name=f"PWA_{name}.zip")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)