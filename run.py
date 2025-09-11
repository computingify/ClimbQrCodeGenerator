import qrcode
from PIL import Image, ImageDraw, ImageFont

# === Paramètres Wi-Fi ===
ssid = "MaisonAdriSoph"
password = "MATHIAS1"
security = "WPA"  # ou WEP ou nopass

# === Génération du contenu QR code ===
wifi_config = f"WIFI:T:{security};S:{ssid};P:{password};;"
wifi_config = "Jouve.Adrien"
# === Création du QR Code ===
qr = qrcode.make(wifi_config)

# === Ajout d'un titre au-dessus du QR ===
title = wifi_config  # texte à afficher au dessus du QR
qr_img = qr.convert("RGB")  # s'assurer d'avoir une image RGB
w, h = qr_img.size

# Charger une police système si disponible (Mac)
try:
    font = ImageFont.truetype("/Library/Fonts/Arial.ttf", size=max(14, w // 20))
except Exception:
    font = ImageFont.load_default()

# mesurer le texte
draw_tmp = ImageDraw.Draw(qr_img)
try:
    # Pillow modernes : textbbox retourne (left, top, right, bottom)
    bbox = draw_tmp.textbbox((0, 0), title, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
except Exception:
    # fallback : utiliser la méthode de la police (compatible plus ancienne)
    try:
        text_w, text_h = font.getsize(title)
    except Exception:
        # dernier recours : estimation basique
        text_w, text_h = (len(title) * 8, max(12, font.size if hasattr(font, "size") else 12))

padding = 10

# nouvelle image avec espace en haut pour le titre
new_h = h + text_h + padding
new_img = Image.new("RGB", (w, new_h), "white")
draw = ImageDraw.Draw(new_img)

# dessiner le titre centré
text_x = (w - text_w) // 2
text_y = padding // 2
draw.text((text_x, text_y), title, fill="black", font=font)

# coller le QR sous le titre
new_img.paste(qr_img, (0, text_h + padding))

# === Sauvegarde en image ===
filename = f"{wifi_config}_with_title.png"
new_img.save(filename)