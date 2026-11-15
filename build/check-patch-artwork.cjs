/* Patch presentation and unchanged-award regression check.
   Run: node build/check-patch-artwork.cjs
   No browser, DOM, network, auth, storage or backend is used. */
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { execFileSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8').replace(/\r\n/g, '\n');
const awardBaseline = '9ced3a171617fafa24ee3e6779c696db13b5fb1c';
const baseline = execFileSync('git', ['show', awardBaseline + ':index.html'], {
  cwd: root,
  encoding: 'utf8',
  maxBuffer: 4 * 1024 * 1024,
  windowsHide: true
}).replace(/\r\n/g, '\n');

// Compile every inline JavaScript block without executing the app.
let compiled = 0;
for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)) {
  const attributes = match[1];
  if (/\bsrc\s*=/i.test(attributes) || !match[2].trim()) continue;
  const type = attributes.match(/\btype\s*=\s*["']([^"']+)["']/i)?.[1];
  if (type && !/^(?:text|application)\/(?:java|ecma)script$/i.test(type)) {
    assert.notEqual(type.toLowerCase(), 'module', 'Add explicit module compilation if inline modules are introduced');
    continue;
  }
  new vm.Script(match[2], { filename: 'index.html:inline-script-' + (++compiled) });
}
assert.ok(compiled > 0, 'Expected inline app JavaScript to compile');

function boundedSource(source, startMarker, endMarker) {
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker, start);
  assert.ok(start >= 0 && end > start, 'Cannot locate source region: ' + startMarker);
  return source.slice(start, end);
}

// The artwork change must not alter the existing badge predicates, thresholds,
// dates, source-video associations, IDs or money/privacy flags.
assert.equal(
  boundedSource(html, 'function badgesOf(', '\nconst BADGE_SEEN='),
  boundedSource(baseline, 'function badgesOf(', '\nconst BADGE_SEEN='),
  'Badge eligibility/award derivation must remain byte-identical to 9ced3a1 after newline normalization'
);
for (const mapping of ['BADGE_PATCH', 'CAT_PATCH']) {
  const expression = new RegExp('const ' + mapping + '=([^;]+);');
  assert.equal(html.match(expression)?.[0], baseline.match(expression)?.[0],
    mapping + ' must preserve existing stable badge/category mapping');
}

const helper = boundedSource(html, 'let patchSerial=0;', '\nconst avRing=');
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);
const context = vm.createContext({
  esc: escapeHtml,
  PATCH_IC: Object.freeze({ star: 'M1 1L2 2', check: 'M3 3L4 4', trophy: 'M5 5L6 6' })
});
vm.runInContext(helper + '\nthis.renderPatch = patch;', context, { timeout: 1000 });
const render = (kind, options) => context.renderPatch(kind, options);

const assetPath = './art/embroidered-patch-base.svg';
const wrapper = fs.readFileSync(path.join(root, assetPath), 'utf8');
assert.ok(!/<(?:script|foreignObject)\b|\bon[a-z]+\s*=/i.test(wrapper), 'Self-contained artwork wrapper must not contain executable content');
assert.ok(!/\b(?:xlink:)?href\s*=\s*["']https?:/i.test(wrapper), 'Artwork wrapper must not depend on a remote image');
assert.equal((wrapper.match(/<image\b/gi) || []).length, 1, 'Wrapper must contain one original raster image');
const embedded = wrapper.match(/\b(?:xlink:)?href\s*=\s*["']data:image\/png;base64,([A-Za-z0-9+/=\s]+)["']/i)?.[1];
assert.ok(embedded, 'Self-contained SVG must embed the real PNG as a data URI');
const base64 = embedded.replace(/\s/g, '');
const asset = Buffer.from(base64, 'base64');
assert.equal(asset.toString('base64'), base64, 'Embedded PNG base64 must decode without discarded data');
assert.equal(asset.subarray(0, 8).toString('hex'), '89504e470d0a1a0a', 'Embedded patch base must be a real PNG');
const assetWidth = asset.readUInt32BE(16);
const assetHeight = asset.readUInt32BE(20);
assert.ok(assetWidth > 0 && assetHeight > 0, 'PNG must declare positive dimensions');
assert.ok([4, 6].includes(asset[25]), 'PNG should have an alpha channel for its transparent patch silhouette');
const svgRoot = wrapper.match(/<svg\b[^>]*>/i)?.[0];
assert.ok(svgRoot, 'Artwork wrapper must have an SVG root');
const viewBox = svgRoot.match(/\bviewBox\s*=\s*["']([^"']+)["']/i)?.[1]?.trim().split(/[\s,]+/).map(Number);
assert.deepEqual(viewBox, [0, 0, assetWidth, assetHeight], 'SVG viewBox must preserve embedded PNG dimensions and aspect ratio');
assert.ok(html.includes('href="' + assetPath + '" as="image"'), 'Local artwork preload must match renderer path');

const ids = new Set();
let rendered = 0;
for (const state of ['done', 'cur', 'lock']) {
  for (const tone of ['', 'gold', 'silver', 'bronze']) {
    const output = render('trophy', { state, tone, size: 96 });
    rendered++;
    assert.ok(output.includes('class="patch patch-' + state + '"'), 'State must be visible to CSS');
    assert.ok(output.includes('width="96" height="106"'), 'Requested dimensions and intrinsic ratio must be stable');
    assert.ok(output.includes('<image href="' + assetPath + '"'), 'Every state must use the local real artwork');
    assert.ok(!/<image[^>]+href="(?:https?:|data:)/i.test(output), 'No remote/inline-base64 artwork dependency');
    const opening = output.match(/^<svg\b[^>]*>/)?.[0];
    assert.ok(opening?.includes('aria-hidden="true"') && opening.includes('focusable="false"'),
      'Decorative artwork must not add an unlabeled focus stop');
    assert.ok(!opening.includes('role="img"'), 'Decorative root must not be redundantly announced');

    const localIds = new Set();
    for (const item of output.matchAll(/\bid="([^"]+)"/g)) {
      assert.ok(!ids.has(item[1]), 'Gradient/filter SVG IDs must be unique across repeated cards: ' + item[1]);
      ids.add(item[1]);
      localIds.add(item[1]);
    }
    assert.equal(localIds.size, 2, 'Each patch must own its gradient and relief filter');
    for (const reference of output.matchAll(/url\(#([^)]+)\)/g)) {
      assert.ok(localIds.has(reference[1]), 'SVG references must target the same patch instance');
    }
    const earnedIndicator = '<circle cx="79" cy="87"';
    assert.equal(output.includes(earnedIndicator), state === 'done', 'Only earned artwork may show its earned-check marker');
    assert.equal(output.includes('grayscale(1) brightness(.72)'), state === 'lock', 'Locked art must remain visibly muted');
  }
}
assert.equal(ids.size, rendered * 2);

const label = 'Hook "master" & <script>alert(1)</script> \'badge\'';
const labelled = render('check', { label, state: 'done', size: 112 });
const labelledRoot = labelled.match(/^<svg\b[^>]*>/)?.[0];
assert.ok(labelledRoot?.includes('role="img" aria-label="' + escapeHtml(label) + '"'), 'Accessible labels must be HTML-escaped');
assert.ok(!labelledRoot.includes('aria-hidden="true"'), 'Labeled image must remain announced');
assert.ok(!labelled.includes('<script>') && !labelled.includes('aria-label="Hook "master"'), 'Untrusted label must not become markup or break the attribute');
assert.ok(labelledRoot.includes('width="112" height="123"'), 'Large detail preview must preserve sizing');
assert.ok(render('unknown-kind', { state: 'lock' }).includes('d="M1 1L2 2"'), 'Unknown artwork kind must fall back safely');
assert.ok(render('check', { state: 'unknown-state' }).includes('patch-done'), 'State fallback must be deterministic');

// Simulate only the static image-error handler, not any DOM/app code.
const errorHandler = labelled.match(/<image[^>]+onerror="([^"]+)"/)?.[1];
assert.ok(errorHandler, 'A missing local artwork asset must retain its vector fallback');
const fallbackCalls = [];
const fakeImage = {
  previousElementSibling: { removeAttribute: name => fallbackCalls.push('reveal:' + name) },
  remove: () => fallbackCalls.push('remove-image')
};
new Function(errorHandler).call(fakeImage);
assert.deepEqual(fallbackCalls, ['reveal:visibility', 'remove-image'], 'Image failure must reveal fallback and remove broken image');

// Find balanced patch(...) calls and guard against old SVG-string recoloring.
// This intentionally checks the call boundary, rather than matching unrelated
// .replace operations elsewhere in the same template string.
for (const match of html.matchAll(/\bpatch\s*\(/g)) {
  let depth = 1;
  let quote = null;
  let escaped = false;
  let index = match.index + match[0].length;
  for (; index < html.length && depth; index++) {
    const char = html[index];
    if (quote) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === quote) quote = null;
    } else if (char === '"' || char === "'" || char === '`') quote = char;
    else if (char === '(') depth++;
    else if (char === ')') depth--;
  }
  assert.equal(depth, 0, 'patch call signature must close');
  assert.ok(!/^\s*\.replace\s*\(/.test(html.slice(index)),
    'Use explicit patch tone variants instead of fragile SVG string replacements');
}

const legacySurfaces = boundedSource(html, 'function badgesCard(', '\nfunction monthName(');
assert.ok(!legacySurfaces.includes('${b.ic}'), 'Legacy badge strip/drawer must not retain mismatched emoji artwork');
assert.ok(legacySurfaces.includes('size:64') && legacySurfaces.includes('size:112'), 'Retain strip and detail artwork sizing');

console.log('PASS: ' + compiled + ' inline JS blocks compile; ' + rendered +
  ' state/tone render fixtures; unique SVG IDs, escaped labels, local SVG-wrapped alpha PNG ' +
  assetWidth + 'x' + assetHeight + ', fallback, earned/locked distinction and unchanged badge eligibility.');

