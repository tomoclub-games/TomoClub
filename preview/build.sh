#!/usr/bin/env bash
# Assembles the in-browser preview from the app's own files.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=preview/dist
rm -rf "$OUT" && mkdir -p "$OUT/shared" "$OUT/vendor" "$OUT/data"
cp preview/index.html preview/preview.css preview/preview-api.js "$OUT/"
cp public/app.js public/styles.css "$OUT/"                    # the real interface, unchanged
cp src/shared/text.js src/shared/answering.js src/shared/pdf.js "$OUT/shared/"
cp src/categories.js "$OUT/shared/categories.js"
cp preview/vendor/stemmer.js preview/vendor/stemmer-LICENSE.txt "$OUT/vendor/"
cp node_modules/unpdf/LICENSE.md "$OUT/vendor/unpdf-LICENSE.txt" 2>/dev/null || cp node_modules/unpdf/LICENSE "$OUT/vendor/unpdf-LICENSE.txt"
cp node_modules/unpdf/dist/pdfjs.mjs "$OUT/vendor/pdfjs.js"
sed 's#import("unpdf/pdfjs")#import("./pdfjs.js")#' node_modules/unpdf/dist/index.mjs > "$OUT/vendor/unpdf.js"
sed -i "s#import('./vendor/unpdf.mjs')#import('./vendor/unpdf.js')#" "$OUT/preview-api.js"
cp preview/data/saved-districts.json "$OUT/data/"
echo "built $OUT"; find "$OUT" -type f | sort
