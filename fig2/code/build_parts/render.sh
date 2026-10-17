#!/bin/sh
# usage: render.sh <svg> <png> [height]
cd "$(dirname "$0")"
HH=${3:-1210}
printf '<html><body style="margin:0"><img src="%s" width="1840" height="%s"></body></html>' "$1" "$HH" > wrap.html
/opt/pw-browsers/chromium-1194/chrome-linux/chrome --headless --no-sandbox --disable-gpu --hide-scrollbars --window-size=1840,$((HH+200)) --screenshot="$PWD/$2" "file://$PWD/wrap.html" 2>/dev/null
python3 -c "from PIL import Image; Image.open('$2').crop((0,0,1840,$HH)).save('$2')"
rm -f wrap.html
