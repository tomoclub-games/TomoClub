const fs = require('fs');
const names = ['calculator','flask-conical','code-xml','globe','book-open','palette','music','pencil','atom','graduation-cap','rocket','brain','lightbulb','search','sparkles','languages','pi','microscope','puzzle','gamepad-2','video','bot','arrow-right','trophy','headphones','dna','telescope','notebook-pen','star','zap','clapperboard','pencil-ruler','library','landmark','sigma','pointer'];
const out = {};
for (const n of names) {
  const svg = fs.readFileSync(`node_modules/lucide-static/icons/${n}.svg`, 'utf8');
  out[n] = svg.replace(/<!--[\s\S]*?-->/g, '').replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>[\s\S]*$/, '').replace(/\s+/g, ' ').trim();
}
fs.writeFileSync('icons.js', 'window.ICONS = ' + JSON.stringify(out) + ';\n');
console.log(Object.keys(out).length, 'icons');
