#!/usr/bin/env python3
"""
Script pour générer l'icône PWA à partir du logo d'Annonay Escalade
Exécutez ce script une fois pour créer static/icon.png
"""

from PIL import Image, ImageDraw
import os

def create_pwa_icon():
    """Crée l'icône PWA 192x192 px"""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOGO_PATH = os.path.join(BASE_DIR, "AnnonayEscaladeLogo.png")
    ICON_PATH = os.path.join(BASE_DIR, "static", "icon.png")
    
    # Créer le répertoire static s'il n'existe pas
    os.makedirs(os.path.join(BASE_DIR, "static"), exist_ok=True)
    
    try:
        # Charger le logo existant
        if os.path.exists(LOGO_PATH):
            logo = Image.open(LOGO_PATH).convert("RGBA")
            
            # Créer une image de fond 192x192 avec gradient
            icon = Image.new("RGBA", (192, 192), (255, 255, 255, 0))
            
            # Créer un fond avec gradient vert (couleurs du thème escalade)
            for y in range(192):
                for x in range(192):
                    # Gradient du vert clair au vert foncé
                    ratio = y / 192
                    r = int(39 + (46 - 39) * ratio)    # 27ae60 -> 2c3e50
                    g = int(174 + (62 - 174) * ratio)
                    b = int(96 + (80 - 96) * ratio)
                    icon.putpixel((x, y), (r, g, b, 255))
            
            # Redimensionner le logo pour qu'il s'adapte (140x140 max)
            logo.thumbnail((140, 140), Image.Resampling.LANCZOS)
            
            # Centrer le logo sur l'icône
            logo_x = (192 - logo.size[0]) // 2
            logo_y = (192 - logo.size[1]) // 2
            
            # Coller le logo avec transparence
            icon.paste(logo, (logo_x, logo_y), logo)
            
        else:
            print(f"⚠️  Logo non trouvé : {LOGO_PATH}")
            print("Création d'une icône générique...")
            
            # Créer une icône générique
            icon = Image.new("RGB", (192, 192), "#27ae60")
            draw = ImageDraw.Draw(icon)
            
            # Dessiner un symbole de montagne simple
            # Montagne principale
            draw.polygon([(60, 140), (96, 80), (130, 140)], fill="#2c3e50")
            # Montagne secondaire
            draw.polygon([(100, 140), (130, 90), (160, 140)], fill="#34495e")
            
            # Ajouter du texte "AE" (Annonay Escalade)
            try:
                from PIL import ImageFont
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            draw.text((96, 45), "AE", fill="white", font=font, anchor="mm")
        
        # Sauvegarder l'icône
        icon.save(ICON_PATH, "PNG", optimize=True)
        print(f"✅ Icône PWA créée : {ICON_PATH}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'icône : {e}")

if __name__ == "__main__":
    create_pwa_icon()