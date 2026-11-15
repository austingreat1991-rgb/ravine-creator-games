/* Pure route regression check: no browser, auth, network, storage or live backend.
   Run: node build/check-admin-contest-labels.cjs */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const start = html.indexOf("route('admin_contest',");
const end = html.indexOf('\nfunction top3Html(', start);
assert.ok(start >= 0 && end > start, 'Historical admin contest route must exist');
const routeSource = html.slice(start, end);

async function renderFixture(november, frozen) {
  const calls = [];
  let render;
  const state = {
    campaign: {
      key: '2026-10',
      starts_at: '2026-10-01T05:00:00Z',
      ends_at: '2026-11-01T05:00:00Z',
      tz: 'America/Chicago',
      status: 'published',
      tie_rule: 'shared',
      prizes: [],
      prize_total_cents: 0
    },
    periods: [],
    snapshots: frozen
      ? [{ final: true, taken_at: '2026-11-01T12:00:00Z', top3: [{ rank: 1, name: 'Fixture winner', gmv: 123 }] }]
      : [],
    standings: [{ rank: 1, display_name: 'Fixture creator', score_sales: 456, entries: 7 }],
    imports: [],
    submissions_review: []
  };
  const context = {
    NOV: november,
    API: {
      page: async (name, parameters) => {
        calls.push({ name, parameters });
        return state;
      },
      rpc: () => { throw new Error('Rendering must not mutate a backend'); }
    },
    route: (name, callback) => {
      assert.equal(name, 'admin_contest');
      render = callback;
    },
    esc: value => String(value ?? ''),
    fmt: {
      dt: value => String(value ?? ''),
      date: value => String(value ?? ''),
      usd: value => '$' + value,
      usd2: value => '$' + value
    },
    TIE_TEXT: value => value,
    ph: (title, subtitle) => '<h1>' + title + '</h1><p>' + subtitle + '</p>',
    badge: (_kind, label) => label,
    top3Html: rows => rows.map(row => row.name).join(', '),
    SSTATE: {},
    Date
  };
  vm.runInNewContext(routeSource, context, { timeout: 1000 });
  const output = await render();
  assert.equal(calls.length, 1, 'Render should only read its admin payload');
  assert.equal(calls[0].name, 'admin');
  assert.equal(JSON.stringify(calls[0].parameters), november ? '{"p_campaign":"2026-10"}' : '{}',
    'Keep the historical October payload selection');
  assert.ok(output.includes('<th class="num">GMV (Oct videos)</th>'), 'GMV label must describe loaded October data');
  assert.ok(output.includes('<th class="num">Approved Oct videos</th>'), 'Approved-video label must describe loaded October data');
  assert.ok(!output.includes('GMV (Nov videos)') && !output.includes('Approved Nov videos'),
    'Global November mode must not relabel October records');
  assert.ok(output.includes('Campaign 2026-10') && output.includes('October GMV from October videos only'),
    'Keep campaign identity and historical rules');
  assert.ok(output.includes('Fixture creator') && output.includes('$456') && output.includes('>7</td>'),
    'Keep actual standings data unchanged');
  if (frozen) {
    assert.ok(output.includes('Frozen 2026-11-01T12:00:00Z') && output.includes('Fixture winner'),
      'Keep frozen record and winners visible');
    assert.ok(!output.includes('onclick="freezeAsk(true)"'), 'Do not offer final freeze again');
  } else {
    assert.ok(output.includes('onclick="freezeAsk(true)"') && output.includes('onclick="freezeAsk(false)"'),
      'Keep the existing explicit snapshot/freeze controls');
  }
}

(async () => {
  for (const november of [false, true]) {
    for (const frozen of [false, true]) {
      await renderFixture(november, frozen);
    }
  }
  console.log('PASS: 4 historical admin-contest render fixtures; October labels, data selection and frozen records preserved.');
})().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});


