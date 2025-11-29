# Assets für Desktop App erstellen

Die folgenden Assets werden für die Desktop-App benötigt:

## 1. DMG Background (dmg-background.png)

**Benötigt:** 660x400 PNG mit transparentem Hintergrund

**So erstellen:**
```bash
# Mit ImageMagick (falls installiert):
convert -background none -size 660x400 assets/dmg-background.svg assets/dmg-background.png

# ODER mit rsvg-convert:
rsvg-convert -w 660 -h 400 -o assets/dmg-background.png assets/dmg-background.svg

# ODER mit Inkscape:
inkscape -w 660 -h 400 assets/dmg-background.svg -o assets/dmg-background.png
```

## 2. App Icon (logo.icns)

**Benötigt:** macOS ICNS Format (Multi-Resolution Icon)

**So erstellen:**
```bash
# 1. Erstelle PNG in verschiedenen Größen:
convert -background none -size 1024x1024 assets/logo.svg assets/icon-1024.png

# 2. Verwende iconutil (macOS Tool):
mkdir icon.iconset
for size in 16 32 64 128 256 512 1024; do
  sips -z $size $size assets/icon-1024.png --out icon.iconset/icon_${size}x${size}.png
  if [ $size -le 512 ]; then
    sips -z $((size*2)) $((size*2)) assets/icon-1024.png --out icon.iconset/icon_${size}x${size}@2x.png
  fi
done
iconutil -c icns icon.iconset -o assets/logo.icns
rm -rf icon.iconset
```

## Alternative: Online-Tools

Wenn keine Tools installiert sind, verwende:
- **PNG**: https://cloudconvert.com/svg-to-png
- **ICNS**: https://cloudconvert.com/png-to-icns

## Hinweis für build.sh

Das build.sh Script versucht automatisch die PNG zu erstellen, falls ImageMagick verfügbar ist.
Falls nicht, erstellt es einen Placeholder und die DMG wird mit dem electron-builder Standard-Hintergrund gebaut.
