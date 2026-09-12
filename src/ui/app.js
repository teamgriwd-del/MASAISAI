/* MASAISAI operations console.
 *
 * Renders entirely from window.MASAISAI_DATA, which dashboard_data.py builds from the real
 * backend (sensing_sim -> occupancy_model -> constraint_engine). Nothing here invents
 * spectrum values; it only lays them out.
 *
 * One rule is enforced throughout: the ML layer is always shown as advisory. Authorisation
 * only ever appears downstream of the POTRAZ rules engine.
 */
(function () {
  'use strict';
  const D = window.MASAISAI_DATA;
  window.MASAISAI_VERSION = '1.0.0';

  /* ------------------------------------------------------------ helpers -- */
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const pct = (x, d = 0) => (x * 100).toFixed(d) + '%';
  const hh = (h) => String(((h % 24) + 24) % 24).padStart(2, '0') + ':00';
  const circ = (cx, cy, r) => `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0`;

  /* ------------------------------------------------------------- icons -- */
  const P = {
    logo: `${circ(12, 11, 1.8)}M7.6 6.6a6.2 6.2 0 0 0 0 8.8M16.4 15.4a6.2 6.2 0 0 0 0-8.8M4.6 3.6a10.4 10.4 0 0 0 0 14.8M19.4 18.4a10.4 10.4 0 0 0 0-14.8M12 13v8.5`,
    home: 'M3 10.5 12 3l9 7.5V21h-6.2v-6.2H9.2V21H3z',
    map: 'M9 3.5 3 6v14.5l6-2.5 6 2.5 6-2.5V3.5L15 6 9 3.5zm0 0V18m6-12v14.5',
    activity: 'M22 12h-4l-3 8.5L9 3.5 6 12H2',
    wave: 'M2 12h3l2.2-5.5 3.3 11 3-8 2.2 5 1.8-2.5H22',
    usercheck: `M15 20.5v-1.8a3.7 3.7 0 0 0-3.7-3.7H5.7A3.7 3.7 0 0 0 2 18.7v1.8${circ(8.5, 7.5, 3.6)}M16 11l2.2 2.2L22.5 9`,
    rules: 'M14 2.5H6.5A2 2 0 0 0 4.5 4.5v15a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V8zM14 2.5V8h5.5M8.5 12.5h7M8.5 16.5h4.5',
    chart: 'M3.5 3.5v17h17M8 16.5v-5M12.5 16.5v-9M17 16.5v-7',
    audit: 'M9 3.5h6v3H9zM8.5 5H6.5a2 2 0 0 0-2 2v12.5a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M8.5 12h7M8.5 16h4.5',
    health: 'M12 21.5s8-3.8 8-10V5l-8-3-8 3v6.5c0 6.2 8 10 8 10zM8.8 11.8l2.2 2.2 4.4-4.4',
    settings: `${circ(12, 12, 3)}M19.3 14.9a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5v.2a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3h.1a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8v.1a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z`,
    antenna: `${circ(12, 9.5, 1.6)}M8 5.5a5.7 5.7 0 0 0 0 8M16 13.5a5.7 5.7 0 0 0 0-8M5.2 2.8a9.6 9.6 0 0 0 0 13.4M18.8 16.2a9.6 9.6 0 0 0 0-13.4M12 11.5l-3.5 10M12 11.5l3.5 10M9.6 18.5h4.8`,
    tv: 'M3.5 6.5h17a1.5 1.5 0 0 1 1.5 1.5v11a1.5 1.5 0 0 1-1.5 1.5h-17A1.5 1.5 0 0 1 2 19V8a1.5 1.5 0 0 1 1.5-1.5zM8 2.5 12 6.5l4-4',
    signal: 'M1.5 12h4l2.5-7 4 14 3.5-9 1.8 4H22.5',
    users: `M16 20.5v-1.8a3.7 3.7 0 0 0-3.7-3.7H5.2a3.7 3.7 0 0 0-3.7 3.7v1.8${circ(8.7, 7.5, 3.6)}M22.5 20.5v-1.8a3.7 3.7 0 0 0-2.8-3.6M16 4a3.7 3.7 0 0 1 0 7.2`,
    shield: 'M12 21.5s8-3.8 8-10V5l-8-3-8 3v6.5c0 6.2 8 10 8 10z',
    cpu: 'M8 8h8v8H8zM4.5 4.5h15v15h-15zM9 1.5v3M15 1.5v3M9 19.5v3M15 19.5v3M19.5 9h3M19.5 15h3M1.5 9h3M1.5 15h3',
    database: 'M12 8c4.4 0 8-1.3 8-3s-3.6-3-8-3-8 1.3-8 3 3.6 3 8 3zM4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',
    scale: 'M12 3v18M6 21h12M3.5 7h17M6.5 7l-3 7a3 3 0 0 0 6 0zM17.5 7l-3 7a3 3 0 0 0 6 0z',
    key: `${circ(7.5, 15.5, 4.5)}M10.7 12.3 20.5 2.5M16.5 6.5l3 3M14 9l2 2`,
    list: 'M8.5 6h12M8.5 12h12M8.5 18h12M3.5 6h.01M3.5 12h.01M3.5 18h.01',
    check: 'M20 6.5 9 17.5l-5-5',
    x: 'M18 6 6 18M6 6l12 12',
    alert: 'M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h16.9a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01',
    minus: 'M5 12h14',
    plus: 'M12 5v14M5 12h14',
    info: `${circ(12, 12, 9.5)}M12 16v-4.5M12 8h.01`,
    chev: 'M6 9l6 6 6-6',
    arrow: 'M5 12h14M13 6l6 6-6 6',
    tower: 'M12 2.5v19M8 21.5h8M9.2 7.5 12 2.5l2.8 5M7.5 13 12 7.5l4.5 5.5M5.5 21.5l6.5-14 6.5 14M8.5 16.5h7',
    clock: `${circ(12, 12, 9.5)}M12 7v5l3.2 2`,
    potraz: 'M12 2.5v4M12 17.5v4M4.6 5.3l2.8 2.8M16.6 15.9l2.8 2.8M2.5 12h4M17.5 12h4M4.6 18.7l2.8-2.8M16.6 8.1l2.8-2.8',
  };
  const icon = (name, cls = '') =>
    `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="${P[name]}"/></svg>`;

  /* ------------------------------------------------------------ colours -- */
  const COL = { green: '#2fd08a', blue: '#3b82f6', cyan: '#2dc6f0', amber: '#f2b52d',
    red: '#ef5350', gray: '#6b7c97', violet: '#9b7bf2' };
  const AVAIL = { high: COL.green, moderate: COL.amber, low: COL.red, offline: COL.gray };
  const STATUS_PILL = { AVAILABLE: 'green', OCCUPIED: 'red', PROTECTED: 'gray', FLAGGED: 'amber' };
  const DECISION_PILL = { Granted: 'green', Denied: 'red', Revoked: 'amber' };
  // The fusion model is decisive, so most cells sit at either end of the ramp. The top stop
  // is kept to a muted lime rather than a saturated yellow so a mostly-occupied band reads
  // as instrumentation rather than a warning sign.
  const RAMP = [[0, [17, 45, 88]], [0.3, [27, 86, 160]], [0.55, [38, 150, 190]],
    [0.8, [112, 190, 150]], [1, [188, 208, 104]]];
  function ramp(t) {
    t = Math.max(0, Math.min(1, t));
    for (let i = 1; i < RAMP.length; i++) {
      if (t <= RAMP[i][0]) {
        const [t0, a] = RAMP[i - 1], [t1, b] = RAMP[i];
        const k = (t - t0) / (t1 - t0);
        return `rgb(${a.map((v, j) => Math.round(v + (b[j] - v) * k)).join(',')})`;
      }
    }
    return 'rgb(226,240,88)';
  }

  /* ---------------------------------------------------------- component: panel */
  function panel(title, body, opts = {}) {
    const sub = opts.sub ? `<div class="panel-sub">${opts.sub}</div>` : '';
    const right = opts.right || '';
    return `<section class="panel ${opts.cls || ''}" ${opts.style ? `style="${opts.style}"` : ''}>
      <div class="panel-head"><div><div class="panel-title">${title}</div>${sub}</div>${right}</div>
      ${body}</section>`;
  }

  /* ---------------------------------------------------------- component: KpiCard */
  function KpiCard({ icon: ic, tone = '', value, label, meta, go, hint }) {
    const nav = go ? ` data-go="${go}" role="button" tabindex="0"
      aria-label="${esc(label)}: ${esc(hint || 'view details')}"` : '';
    return `<section class="panel kpi${go ? ' is-link' : ''}"${nav}>${icon(ic, 'kpi-icon ' + tone)}
      <div><div class="kpi-value">${esc(value)}</div><div class="kpi-label">${esc(label)}</div>
      <div class="kpi-meta">${meta}</div></div>
      ${go ? `<span class="kpi-hint">${esc(hint || 'View details')}${icon('arrow')}</span>` : ''}</section>`;
  }

  function kpiRow() {
    const k = D.kpis;
    const band = D.meta.band_monitored.replace('-', ' &ndash; ');
    return `<div class="kpis">
      ${KpiCard({ icon: 'antenna', value: k.nodes_total, label: 'Sensing Nodes',
        go: 'sensing', hint: 'View sensing nodes',
        meta: `<span class="ok"><i class="dot green"></i>${k.nodes_online} Online</span>
               ${k.nodes_offline ? `<span class="bad"><i class="dot red"></i>${k.nodes_offline} Offline</span>`
                 : `<span><i class="dot gray"></i>${k.nodes_degraded} weak link</span>`}` })}
      ${KpiCard({ icon: 'tv', value: k.channels_monitored, label: 'TV Channels Monitored',
        go: 'channels', hint: 'View all channels',
        meta: `<span>${band} (UHF)</span>` })}
      ${KpiCard({ icon: 'signal', tone: 'green', value: k.idle, label: 'Channels Verified Idle',
        go: 'channels?filter=AVAILABLE', hint: 'View verified-idle channels',
        meta: `<span class="ok">${k.idle_pct}% Available</span>` })}
      ${KpiCard({ icon: 'users', value: k.active_grants, label: 'Active Access Grants',
        go: 'access', hint: 'View access grants',
        meta: `<span>${D.config.grant_window_min}-min rule-checked windows</span>` })}
      ${KpiCard({ icon: 'shield', value: k.grants_on_protected, label: 'Incumbent Interference',
        go: 'channels?filter=PROTECTED', hint: 'View incumbent protection',
        meta: k.grants_on_protected === 0
          ? `<span class="ok"><i class="dot green"></i>All Clear</span>`
          : `<span class="bad"><i class="dot red"></i>Investigate</span>` })}
    </div>`;
  }

  /* ---------------------------------------------------- component: DecisionPipeline */
  function DecisionPipeline() {
    const L = D.live;
    const passed = L.checks.filter((c) => c.state === 'PASS').length;
    const enforced = L.checks.filter((c) => c.state === 'PASS' || c.state === 'FAIL').length;
    const allPass = L.checks.every((c) => c.state !== 'FAIL');
    const nodesHeard = (D.rf[L.channel] || []).length;
    const stage = (cls, ic, name, state, stateCls, detail, tag = '') => `
      <div class="stage ${cls}"><div class="stage-icon">${icon(ic)}</div>
        <div class="stage-body"><div class="stage-name">${name}</div>
          <div class="stage-state ${stateCls}">${state}</div>
          <div class="stage-detail">${detail}</div>${tag}</div></div>`;
    return `<section class="panel pipeline">
      <div class="pipe-intro">
        <div class="panel-title">Live Spectrum Decision</div>
        <div class="target">${esc(L.channel)}<small>${L.freq_mhz.toFixed(0)} MHz</small></div>
        <div class="where">${esc(L.node)} &middot; ${esc(L.town)}</div>
      </div>
      <div class="stages">
        ${stage('', 'antenna', 'RF Sensing', 'LIVE', 'green',
          `${L.rssi.toFixed(1)} dBm mean &middot; ${nodesHeard} nodes`)}
        ${stage('', 'wave', 'Signal Processing', L.naive_state, L.naive_state === 'IDLE' ? 'green' : 'red',
          `Naive vote ${Math.round(L.naive_vote * nodesHeard)}/${nodesHeard} occupied`)}
        ${stage('ml', 'cpu', 'ML Prediction', `${pct(L.p_idle)} IDLE`, 'violet',
          'Fused P(idle), current window', '<span class="stage-tag adv">ADVISORY &middot; NOT AN AUTHORISATION</span>')}
        ${stage('rules', 'scale', 'POTRAZ Rules', allPass ? 'PASS' : 'FAIL', allPass ? 'blue' : 'red',
          `${passed}/${enforced} enforced checks pass`, '<span class="stage-tag auth">FINAL AUTHORITY</span>')}
        ${stage(L.granted ? 'decide' : 'decide flag', 'key', 'Access Decision',
          L.granted ? 'GRANTED' : 'FLAGGED FOR REVIEW', L.granted ? 'green' : 'amber',
          L.granted ? `${D.config.grant_window_min}-min window, then re-checked` : 'Held until rules clear')}
      </div></section>`;
  }

  /* ------------------------------------------------------ component: SpectrumMap */
  const ZW = [[25.26,-17.79],[25.85,-17.93],[26.40,-17.93],[27.05,-17.83],[27.60,-17.45],[28.10,-17.00],
    [28.76,-16.52],[28.87,-16.03],[29.60,-15.72],[30.42,-15.63],[31.20,-16.00],[31.90,-16.30],
    [32.40,-16.50],[32.75,-16.80],[32.98,-17.20],[32.90,-17.90],[32.95,-18.50],[32.85,-19.00],
    [32.90,-19.50],[33.05,-19.95],[32.75,-20.55],[32.50,-21.00],[32.35,-21.35],[31.90,-21.90],
    [31.30,-22.42],[30.70,-22.30],[30.00,-22.22],[29.37,-22.19],[28.80,-21.85],[28.10,-21.50],
    [27.95,-20.95],[27.72,-20.55],[27.25,-20.10],[26.20,-19.55],[25.95,-18.95],[25.55,-18.40]];
  // Equirectangular with a cos(latitude) correction -- adequate at Zimbabwe's scale. Bounds
  // are fitted tightly to the border so the country fills its panel instead of floating.
  const K = 58, COSL = Math.cos((19.1 * Math.PI) / 180), PAD = 8;
  const LON0 = 25.15, LAT0 = -15.5, SPAN_LON = 8.0, SPAN_LAT = 7.05;
  const proj = (lon, lat) => [(lon - LON0) * K * COSL + PAD, (LAT0 - lat) * K + PAD];
  // cx/cy are the viewport centre in map units; panning moves them.
  const mapState = { zoom: 1, cx: null, cy: null };

  function SpectrumMap(opts = {}) {
    const W = SPAN_LON * K * COSL + 2 * PAD, H = SPAN_LAT * K + 2 * PAD;
    const z = mapState.zoom, vw = W / z, vh = H / z;
    if (mapState.cx == null) { mapState.cx = W / 2; mapState.cy = H / 2; }
    // Keep the viewport inside the map however far the user pans.
    mapState.cx = Math.max(vw / 2, Math.min(W - vw / 2, mapState.cx));
    mapState.cy = Math.max(vh / 2, Math.min(H - vh / 2, mapState.cy));
    const vx = mapState.cx - vw / 2, vy = mapState.cy - vh / 2;
    // Labels and markers are sized in map units, so they are scaled to stay a constant
    // on-screen size across panel heights and zoom levels.
    const u = (opts.unit || 1.75) / z;
    const outline = ZW.map((p, i) => (i ? 'L' : 'M') + proj(...p).map((v) => v.toFixed(1)).join(' ')).join('') + 'Z';
    const grid = [];
    for (let lon = 26; lon <= 33; lon++) {
      const [x] = proj(lon, LAT0);
      grid.push(`<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="#12233d" stroke-width="${0.5 * u}"/>`);
    }
    for (let lat = -16; lat >= -22; lat--) {
      const [, y] = proj(LON0, lat);
      grid.push(`<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="#12233d" stroke-width="${0.5 * u}"/>`);
    }
    const nodes = D.nodes.map((n) => {
      const [x, y] = proj(n.lon, n.lat);
      const c = AVAIL[n.availability];
      // Eastern sites label to the left so they never run off the border edge.
      const right = n.lon < 32.2;
      const lx = right ? x + 7.5 * u : x - 7.5 * u, anchor = right ? 'start' : 'end';
      return `<g class="map-node" data-node="${esc(n.id)}" tabindex="0" role="button"
          aria-label="${esc(n.label)} ${esc(n.town)}, ${n.availability} availability">
        <circle class="map-node-halo" cx="${x}" cy="${y}" r="${7 * u}" fill="${c}" opacity="0.20"/>
        <circle class="map-node-hit" cx="${x}" cy="${y}" r="${11 * u}" fill="transparent"/>
        <circle class="map-node-dot" cx="${x}" cy="${y}" r="${3.8 * u}" fill="${c}" stroke="#07111f" stroke-width="${1.2 * u}">
          <title>${esc(n.label)} ${esc(n.town)} -- ${n.availability} availability, ${pct(n.idle_fraction)} of channels idle, link ${n.quality}</title></circle>
        <text class="node-label" style="font-size:${12 * u}px" x="${lx}" y="${y + 4.2 * u}" text-anchor="${anchor}">${esc(n.town)}</text>
        ${opts.detail ? `<text class="node-label small" style="font-size:${9.5 * u}px" x="${lx}" y="${y + 15 * u}" text-anchor="${anchor}">${esc(n.label)}</text>` : ''}</g>`;
    }).join('');
    const grad = Object.entries(AVAIL).map(([k, c]) =>
      `<radialGradient id="g-${k}"><stop offset="0" stop-color="${c}" stop-opacity="0.28"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`).join('');
    return `<div class="map-wrap" data-map tabindex="0" role="application"
        aria-label="Zimbabwe spectrum map. Scroll to zoom, drag to pan.">
      <svg class="map-svg" viewBox="${vx.toFixed(1)} ${vy.toFixed(1)} ${vw.toFixed(1)} ${vh.toFixed(1)}" preserveAspectRatio="xMidYMid meet">
        <defs>${grad}<linearGradient id="land" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#15375a"/><stop offset="1" stop-color="#0f2a47"/></linearGradient>
          <clipPath id="zw"><path d="${outline}"/></clipPath></defs>
        ${grid.join('')}
        <path d="${outline}" fill="url(#land)" stroke="#2f5b86" stroke-width="${1.1 * u}" stroke-linejoin="round"/>
        <g clip-path="url(#zw)">${D.nodes.map((n) => { const [x, y] = proj(n.lon, n.lat);
          return `<circle cx="${x}" cy="${y}" r="60" fill="url(#g-${n.availability})"/>`; }).join('')}</g>
        ${nodes}
      </svg>
      <div class="map-legend">
        <span><i class="dot green"></i>High Availability</span>
        <span><i class="dot amber"></i>Moderate</span>
        <span><i class="dot red"></i>Low Availability</span>
        <span><i class="dot gray"></i>Node Offline</span>
      </div>
      <div class="map-zoom"><button type="button" data-zoom="in" title="Zoom in" aria-label="Zoom in">${icon('plus')}</button>
        <button type="button" data-zoom="out" title="Zoom out" aria-label="Zoom out">${icon('minus')}</button>
        <button type="button" data-zoom="reset" title="Reset view" aria-label="Reset view">${icon('home')}</button></div>
      <div class="map-note">Illustrative node siting &middot; scroll to zoom, drag to pan</div>
      <div class="map-pop" hidden></div>
    </div>`;
  }

  /* ------------------------------------------------- component: OccupancyHeatmap */
  function OccupancyHeatmap(chs) {
    const H = D.heatmap, rows = chs || H.channels;
    const W = 420, rowH = 20, top = 6, left = 44, gw = W - left - 8, cw = gw / 24;
    const hgt = top + rows.length * rowH;
    let cells = '';
    rows.forEach((ch, r) => {
      (H.values[ch] || []).forEach((v, h) => {
        cells += `<rect class="heat-cell" data-tip="${ch} &middot; ${hh(h)}|P(occupied) ${v.toFixed(2)}|${v > 0.5 ? 'Occupied' : 'Idle'} in this window"
          x="${(left + h * cw).toFixed(2)}" y="${top + r * rowH}" width="${(cw - 1.1).toFixed(2)}" height="${rowH - 1.4}" rx="1.2" fill="${ramp(v)}"></rect>`;
      });
      cells += `<text class="axis-text" x="${left - 8}" y="${top + r * rowH + 14}" text-anchor="end">${ch}</text>`;
    });
    const nx = left + H.now_hour * cw;
    const axis = [0, 4, 8, 12, 16, 20, 24].map((h) =>
      `<text class="axis-text" x="${left + h * cw}" y="${hgt + 18}" text-anchor="middle">${String(h).padStart(2, '0')}:00</text>`).join('');
    return `<svg class="chart" viewBox="0 0 ${W} ${hgt + 24}" preserveAspectRatio="xMidYMid meet" style="height:calc(100% - 64px)">
        <rect x="${left - 1}" y="${top - 1}" width="${gw + 1}" height="${rows.length * rowH + 1}" fill="none" stroke="#1b2d4a"/>
        ${cells}
        <rect x="${nx - 0.8}" y="${top - 3}" width="${cw + 0.4}" height="${rows.length * rowH + 4}" fill="none" stroke="#eaf0f8" stroke-width="1.1" rx="2"/>
        ${axis}</svg>
      <div class="legend-row"><span><i class="swatch" style="background:${ramp(0.05)}"></i>Idle</span>
        <span><i class="swatch" style="background:${ramp(0.95)}"></i>Occupied</span>
        <span style="color:var(--ink-3)"><i class="swatch" style="border:1px solid #eaf0f8"></i>Now (${hh(H.now_hour)})</span></div>`;
  }

  /* ------------------------------------------------ component: ForecastChart (outlook) */
  function OutlookChart() {
    const O = D.outlook;
    if (!O.length) return '<div class="empty">No candidate channels</div>';
    const W = 360, H = 200, L = 38, R = 8, T = 8, B = 24;
    const pts = O[0].measured.length + O[0].expected.length;
    const x = (i) => L + (i / (pts - 1)) * (W - L - R);
    const y = (v) => T + (1 - v) * (H - T - B);
    const colours = [COL.blue, COL.green];
    let g = '';
    [0, 0.25, 0.5, 0.75, 1].forEach((v) => {
      g += `<line x1="${L}" y1="${y(v)}" x2="${W - R}" y2="${y(v)}" stroke="#172a47" stroke-width="1"/>
            <text class="axis-text" x="${L - 7}" y="${y(v) + 4}" text-anchor="end">${v * 100}%</text>`;
    });
    const nowI = O[0].measured.length - 1;
    g += `<rect x="${x(nowI)}" y="${T}" width="${W - R - x(nowI)}" height="${H - T - B}" fill="rgba(155,123,242,0.05)"/>
          <line x1="${x(nowI)}" y1="${T}" x2="${x(nowI)}" y2="${H - B}" stroke="#56688a" stroke-dasharray="2 3"/>
          <text class="axis-text dim" x="${x(nowI) + 5}" y="${T + 11}">NOW</text>`;
    // Each value is one discrete sensing window, so it is drawn as a step that holds for the
    // hour -- the way a spectrum monitor logs occupancy. Joining the points instead produced
    // ticker-style spikes, because the fusion verdicts are close to binary.
    const step = (a) => a.map((p, i) => i ? `H${p[0].toFixed(1)}V${p[1].toFixed(1)}`
      : `M${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join('');
    O.forEach((s, k) => {
      const c = colours[k % colours.length];
      // Slight vertical offset keeps two channels that agree from drawing as one line.
      const off = k * 2.2;
      const m = s.measured.map((p, i) => [x(i), y(p.p_idle) + off]);
      const e = [m[m.length - 1]].concat(s.expected.map((p, i) => [x(nowI + 1 + i), y(p.p_idle) + off]));
      s.measured.forEach((p, i) => {
        g += `<rect class="pt" data-tip="${s.channel} &middot; ${hh(p.hour)}|Measured idle ${pct(p.p_idle, 0)}|Fused sensing verdict"
          x="${(x(i) - 6).toFixed(1)}" y="${T}" width="12" height="${H - T - B}" fill="transparent"/>`;
      });
      s.expected.forEach((p, i) => {
        g += `<rect class="pt" data-tip="${s.channel} &middot; ${hh(p.hour)}|Expected idle ${pct(p.p_idle, 0)}|Historical hourly profile, not a forecast"
          x="${(x(nowI + 1 + i) - 6).toFixed(1)}" y="${T}" width="12" height="${H - T - B}" fill="transparent"/>`;
      });
      g += `<path class="s${k}" d="${step(m)}V${H - B}H${m[0][0]}Z" fill="${c}" opacity="0.09"/>
            <path class="s${k}" d="${step(m)}" fill="none" stroke="${c}" stroke-width="2.2" stroke-linejoin="round"/>
            <path class="s${k}" d="${step(e)}" fill="none" stroke="${c}" stroke-width="1.8" stroke-dasharray="4 4" opacity="0.9"/>
            <circle class="s${k}" cx="${m[m.length - 1][0]}" cy="${m[m.length - 1][1]}" r="3.8" fill="${c}" stroke="#0e1c32" stroke-width="1.6"/>`;
    });
    const labels = O[0].measured.map((p) => p.hour).concat(O[0].expected.map((p) => p.hour));
    labels.forEach((h, i) => {
      if (i % 3 === 0 || i === labels.length - 1)
        g += `<text class="axis-text" x="${x(i)}" y="${H - 6}" text-anchor="middle">${hh(h)}</text>`;
    });
    const legend = O.map((s, k) => `<span class="legend-toggle" data-series="${esc(s.channel)}" role="button" tabindex="0"
        title="Show only ${esc(s.channel)}"><i class="swatch line" style="background:${colours[k]}"></i>${s.channel}</span>`).join('')
      + `<span style="color:var(--ink-3)"><i class="swatch line" style="background:var(--ink-3)"></i>measured</span>
         <span style="color:var(--ink-3)"><i class="swatch dash" style="border-color:var(--ink-3)"></i>expected</span>`;
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet" style="height:calc(100% - 86px)">${g}</svg>
      <div class="legend-row" style="gap:16px">${legend}</div>
      <div class="chart-foot">Probability idle. Dashed = historical hourly profile, not a forecast.</div>`;
  }

  /* ---------------------------------------------- component: AccessDecisionTable */
  function AccessDecisionTable(rows, opts = {}) {
    if (!rows.length) return '<div class="empty">No decisions in this period</div>';
    const body = rows.map((r) => `<tr class="row-link" data-decision="${D.decisions.indexOf(r)}" tabindex="0"><td class="mono">${esc(r.time)}</td><td><b>${esc(r.channel)}</b></td>
      <td class="dim">${esc(r.location)}</td>${opts.node ? `<td class="mono dim">${esc(r.node)}</td>` : ''}
      <td><span class="pill ${DECISION_PILL[r.decision]}">${esc(r.decision)}</span></td>
      <td class="dim">${r.duration ? esc(r.duration) : '&ndash;'}</td>
      <td class="dim">${esc(r.reason)}</td>
      ${opts.actions ? `<td class="row-actions">
        <button type="button" class="btn btn-ghost" data-decision-view="${D.decisions.indexOf(r)}">View</button>
        ${r.decision === 'Granted' ? `<button type="button" class="btn btn-danger" data-revoke="${D.decisions.indexOf(r)}">Revoke</button>` : ''}
      </td>` : ''}</tr>`).join('');
    return `<table class="table ${opts.dense ? 'dense' : ''}"><thead><tr><th>Time</th><th>Channel</th><th>Location</th>
      ${opts.node ? '<th>Node</th>' : ''}<th>Decision</th><th>Duration</th><th>Reason</th>
      ${opts.actions ? '<th>Actions</th>' : ''}</tr></thead><tbody>${body}</tbody></table>`;
  }

  /* ------------------------------------------------------ component: SystemHealth */
  function SystemHealth() {
    const h = D.health;
    const rows = [
      ['antenna', 'sensing', 'Sensing Nodes', `${h.nodes} Online`,
        `Every node reporting this window. Link quality reflects simulated distance to the transmitter, not failure.`],
      ['database', 'health', 'Data Pipeline', 'Healthy',
        `${h.readings.toLocaleString()} per-node readings ingested and fused into per-channel windows.`],
      ['cpu', 'analytics', 'ML Fusion Engine', 'Healthy',
        `${D.config.model}. Held-out accuracy ${h.ml_accuracy}%, ${h.ml_latency_ms} ms per prediction. Advisory only.`],
      ['scale', 'rules', 'Rules Engine', 'Active',
        `Rules ${h.rules_version} loaded, ${h.protected_count} protected channels. Final authority on every decision.`],
      ['key', 'access', 'Access Layer', 'Healthy',
        `${h.active_grants} channels granted for ${D.config.grant_window_min}-minute windows, each re-checked on expiry.`],
      ['list', 'audit', 'Audit Logging', 'Healthy', `${h.audit_events} events recorded this session.`],
    ];
    return `<div class="health-list">${rows.map(([ic, go, label, state, tip]) =>
      `<div class="health-row row-link" data-go="${go}" tabindex="0" role="button">${icon(ic)}<span class="label">${label}</span>
        <span class="state"><i class="dot green"></i>${state}</span>${icon('arrow', 'row-arrow')}
        <div class="tip">${esc(tip)}</div></div>`).join('')}</div>`;
  }

  /* ------------------------------------------------------ component: SpectrumUsage */
  function SpectrumUsage() {
    const u = D.usage, T = u.total;
    const segs = [['Idle', u.idle, COL.green], ['Occupied', u.occupied, COL.blue],
      ['Reserved/Protected', u.protected, '#8a9bb3']];
    if (u.flagged) segs.push(['Flagged (fail-safe)', u.flagged, COL.amber]);
    const R = 60, C = 2 * Math.PI * R;
    let off = 0, arcs = '';
    segs.forEach(([, n, c]) => {
      if (!n) return;
      const len = (n / T) * C;
      arcs += `<circle cx="79" cy="79" r="${R}" fill="none" stroke="${c}" stroke-width="18"
        stroke-dasharray="${(len - 2).toFixed(2)} ${(C - len + 2).toFixed(2)}" stroke-dashoffset="${(-off).toFixed(2)}"
        transform="rotate(-90 79 79)"/>`;
      off += len;
    });
    return `<div class="usage"><svg viewBox="0 0 158 158" width="158" height="158">
        <circle cx="79" cy="79" r="${R}" fill="none" stroke="#13243f" stroke-width="18"/>${arcs}
        <text x="79" y="80" text-anchor="middle" style="font:800 27px var(--font);fill:#eaf0f8">${Math.round((u.idle / T) * 100)}%</text>
        <text x="79" y="100" text-anchor="middle" style="font:500 11.5px var(--font);fill:#b6c3d6">Channels Idle</text></svg>
      <div class="usage-legend">${segs.map(([l, n, c]) =>
        `<div><i class="dot" style="background:${c}"></i><span>${l}</span><span class="n">${n} (${Math.round((n / T) * 100)}%)</span></div>`).join('')}</div></div>
      <div class="notice">${icon('info')}<span>All access decisions are subject to POTRAZ rules and can be instantly revoked.</span></div>`;
  }

  /* -------------------------------------------------------- component: RulesPanel */
  function RulesPanel(checks) {
    const mark = (s) => s === 'PASS' ? ['check', COL.green, 'green']
      : s === 'FAIL' ? ['x', COL.red, 'red'] : ['alert', COL.amber, 'amber'];
    return `<div class="checks">${checks.map((c, i) => {
      const [ic, colour, pill] = mark(c.state);
      return `<div class="check is-expandable" data-rule="${i}" tabindex="0" role="button" aria-expanded="false">
        <span style="color:${colour}">${icon(ic)}</span>
        <div><div class="name">${esc(c.name)}${icon('chev', 'check-chev')}</div><div class="detail">${esc(c.detail)}</div></div>
        <span class="pill ${pill}">${esc(c.state)}</span>
        <div class="check-body">${esc(RULE_WHY[c.name] || 'This constraint is evaluated by the POTRAZ rules engine on every sensing window. The ML layer cannot override its verdict.')}</div></div>`;
    }).join('')}</div>`;
  }

  function AuthorityStrip() {
    return `<div class="authority">
      <div class="step"><b style="color:var(--violet)">AI PREDICTS</b><small>Fusion model scores each channel</small></div>
      ${icon('arrow', 'arrow')}
      <div class="step"><b style="color:#7fb0ff">POTRAZ RULES VERIFY</b><small>Every enforced check must pass</small></div>
      ${icon('arrow', 'arrow')}
      <div class="step"><b style="color:var(--green)">POTRAZ RULES DECIDE</b><small>AI cannot override a rule</small></div></div>`;
  }

  /* --------------------------------------------------------- component: AuditLog */
  const AUDIT_PILL = { granted: 'green', denied: 'red', occupied: 'red', protected: 'gray',
    ingest: 'blue', ml: 'violet', rules: 'blue' };
  const AUDIT_KIND = { granted: 'ACCESS', denied: 'REVOKE', occupied: 'SENSING', protected: 'RULES',
    ingest: 'INGEST', ml: 'ML', rules: 'RULES' };
  function AuditLog(rows) {
    return `<table class="table dense"><thead><tr><th>Timestamp</th><th>Layer</th><th>Channel</th><th>Event</th></tr></thead>
      <tbody>${rows.map((r) => `<tr class="audit-row row-link" data-audit="${D.audit.indexOf(r)}" tabindex="0"><td>${esc(r.time)}</td>
        <td><span class="pill ${AUDIT_PILL[r.kind] || 'gray'} kind">${AUDIT_KIND[r.kind] || r.kind}</span></td>
        <td class="mono">${r.channel ? esc(r.channel) : '&ndash;'}</td><td>${esc(r.text)}</td></tr>`).join('')}</tbody></table>`;
  }

  /* ------------------------------------------------------- component: ChannelStatus */
  function ChannelStatus(chs) {
    chs = chs || D.channels;
    if (!chs.length) return '<div class="empty">No channels match this filter</div>';
    return `<table class="table"><thead><tr><th>Channel</th><th>Frequency</th><th>Mean RSSI</th><th>Naive</th>
      <th>P(occupied)</th><th>ML Confidence</th><th>Sensing</th><th>Protection</th><th>Status</th><th>Reporting Node</th></tr></thead>
      <tbody>${chs.map((c) => `<tr class="row-link" data-channel="${c.channel}" tabindex="0"><td><b>${c.channel}</b></td><td class="mono dim">${c.freq_mhz.toFixed(0)} MHz</td>
        <td class="mono">${c.mean_rssi.toFixed(1)} dBm</td>
        <td><span class="pill ${c.naive_state === 'IDLE' ? 'green' : 'red'}" style="min-width:0">${c.naive_state}</span></td>
        <td><span class="bar"><i style="width:${c.p_occ * 100}%;background:${ramp(c.p_occ)}"></i></span>
          <span class="mono" style="margin-left:8px">${c.p_occ.toFixed(2)}</span></td>
        <td class="mono">${c.ml_confidence.toFixed(2)}</td><td class="mono">${c.sensing_confidence.toFixed(2)}</td>
        <td class="dim">${c.protected ? 'Protected' : 'Clear'}</td>
        <td><span class="pill ${STATUS_PILL[c.status]}">${c.status}</span></td>
        <td class="mono dim">${esc(c.node)} &middot; ${esc(c.town)}</td></tr>`).join('')}</tbody></table>`;
  }

  /* ---------------------------------------------------- component: RfAttribution */
  const rfState = { channel: D.rf_focus.channel };
  function RfAttribution() {
    const ch = rfState.channel;
    const c = D.channels.find((x) => x.channel === ch);
    const readings = D.rf[ch] || [];
    const occupied = c.p_occ > D.config.occupancy_threshold;
    const heard = readings.filter((r) => r.naive_occupied).length;
    const minR = -120, maxR = -20, thr = D.config.energy_threshold_dbm;
    const scale = (v) => Math.max(0, Math.min(100, ((v - minR) / (maxR - minR)) * 100));
    const bars = readings.map((r) => `<div class="rssi-row"><span class="mono">${esc(r.node)}</span>
        <span class="dim" style="color:var(--ink-2)">${esc(r.town)}</span>
        <div class="rssi-track"><i style="width:${scale(r.rssi)}%;background:${r.naive_occupied ? COL.red : COL.cyan};opacity:${0.35 + 0.65 * r.confidence}"></i>
          <span class="rssi-thr" style="left:${scale(thr)}%"></span></div>
        <span class="mono">${r.rssi.toFixed(1)} dBm</span><span class="mono dim" style="color:var(--ink-3)">conf ${r.confidence.toFixed(2)}</span></div>`).join('');
    const picker = D.channels.map((x) => `<button class="chan-btn ${x.channel === ch ? 'sel' : ''}" data-ch="${x.channel}">
        <i style="background:${{ AVAILABLE: COL.green, OCCUPIED: COL.red, PROTECTED: '#8a9bb3', FLAGGED: COL.amber }[x.status]}"></i>${x.channel}</button>`).join('');
    const n = parseInt(ch.slice(2), 10);
    const neigh = [n + 1, n + 2].map((k) => D.channels.find((x) => x.channel === 'CH' + k)).filter(Boolean);
    return `<div class="chan-picker" style="margin-bottom:14px">${picker}</div>
      <div class="chain">
        <div><small>RF Source</small><b style="color:${occupied ? COL.red : COL.green}">${occupied ? 'Existing UHF Transmitter' : 'No incumbent energy'}</b>
          <span>${occupied ? 'Incumbent DTT broadcast (simulated)' : 'Channel quiet this window'}</span></div>
        <div><small>RF Signal</small><b>${ch} &middot; ${c.freq_mhz.toFixed(0)} MHz</b><span>8 MHz UHF raster</span></div>
        <div><small>MASAISAI Sensors</small><b>${heard}/${readings.length} nodes above ${thr} dBm</b><span>Mean ${c.mean_rssi.toFixed(1)} dBm</span></div>
        <div><small>Spectrum Measurement</small><b><span class="pill ${STATUS_PILL[c.status]}">${c.status}</span></b>
          <span>Fused P(occupied) ${c.p_occ.toFixed(2)}</span></div>
      </div>
      <div class="panel-sub" style="margin:14px 0 10px">Per-node readings &mdash; the raw evidence behind the fused verdict. Amber line = ${thr} dBm energy-detection threshold.</div>
      <div class="rssi-bars">${bars}</div>
      <div class="panel-sub" style="margin:16px 0 10px">Adjacent channels</div>
      <div class="neighbours">${neigh.map((x) => `<div class="neighbour"><b>${x.channel}</b>
        <span class="dim" style="margin-left:8px;color:var(--ink-3)">${x.freq_mhz.toFixed(0)} MHz</span>
        <div><span class="pill ${STATUS_PILL[x.status]}">${x.status}</span>
        <span class="mono" style="margin-left:10px;color:var(--ink-2)">P(idle) ${x.p_idle.toFixed(2)}</span></div></div>`).join('')}</div>`;
  }

  /* ------------------------------------------------------------- views -- */
  const S = D.meta;
  const views = {
    dashboard: () => `
      ${welcome()}
      ${kpiRow()}
      ${DecisionPipeline()}
      <div class="row-3">
        ${panel('Spectrum Map &ndash; Zimbabwe', SpectrumMap(), { sub: 'Live channel availability across sensing nodes', cls: 'h-fixed' })}
        ${panel('Channel Occupancy <span class="muted">(Last 24 Hours)</span>', OccupancyHeatmap(), { cls: 'h-fixed' })}
        ${panel('Occupancy Outlook <span class="muted">(Next 6 Hours)</span>', OutlookChart(),
          { cls: 'h-fixed', right: '<span class="chip violet">ML Fusion Engine</span>' })}
      </div>
      <div class="row-3b">
        ${panel('Recent Access Decisions', `<div class="scroll" style="height:calc(100% - 38px)">${AccessDecisionTable(D.decisions.slice(0, 6), { dense: true })}</div>`,
          { cls: 'h-fixed-b', right: `<button class="link" data-go="access">View All ${icon('arrow')}</button>` })}
        ${panel('System Health', SystemHealth(), { cls: 'h-fixed-b' })}
        ${panel('Spectrum Usage Summary', SpectrumUsage(), { cls: 'h-fixed-b' })}
      </div>
      ${footer()}`,

    map: () => `
      ${title('Spectrum Map', 'Distributed RTL-SDR sensing across Zimbabwe. Node siting is illustrative; readings are from the simulator.')}
      <div class="row-2">
        ${panel('Spectrum Map &ndash; Zimbabwe', SpectrumMap({ detail: true, unit: 0.95 }), { sub: 'Availability = share of channels each node hears as idle this window', style: 'height:560px' })}
        ${panel('Sensing Nodes', `<div class="scroll" style="height:calc(100% - 10px)"><table class="table"><thead><tr><th>Node</th><th>Site</th><th>Status</th><th>Link</th><th>Channels idle</th></tr></thead><tbody>
          ${D.nodes.map((n) => `<tr class="row-link" data-node="${esc(n.id)}" tabindex="0"><td class="mono">${n.label}</td><td>${esc(n.town)}</td>
            <td><span class="pill ${n.status === 'online' ? 'green' : 'red'}">${n.status}</span></td>
            <td class="dim">${n.quality} (${n.confidence.toFixed(2)})</td>
            <td><span class="bar"><i style="width:${n.idle_fraction * 100}%;background:${AVAIL[n.availability]}"></i></span>
              <span class="mono" style="margin-left:8px">${pct(n.idle_fraction)}</span></td></tr>`).join('')}</tbody></table></div>`, { style: 'height:560px' })}
      </div>${footer()}`,

    sensing: () => `
      ${title('Live Sensing', 'Trace any channel from the RF environment to the measurement MASAISAI makes of it.')}
      ${DecisionPipeline()}
      <div class="row-2">
        ${panel('RF Source Attribution', RfAttribution(), { sub: 'Transmitter &rarr; RF signal &rarr; MASAISAI sensors &rarr; measurement' })}
        ${panel('POTRAZ Rule Check &mdash; ' + esc(D.live.channel), RulesPanel(D.live.checks) + '<div style="height:14px"></div>' + AuthorityStrip(),
          { sub: 'Checks applied to the current live decision' })}
      </div>${footer()}`,

    channels: (q) => {
      const f = (q && q.filter) || 'ALL';
      const chs = f === 'ALL' ? D.channels : D.channels.filter((c) => c.status === f);
      const tabs = ['ALL', 'AVAILABLE', 'OCCUPIED', 'PROTECTED', 'FLAGGED'].map((k) =>
        `<button type="button" class="chan-btn ${k === f ? 'sel' : ''}" data-filter="${k}">${k === 'ALL' ? 'All channels' : k}</button>`).join('');
      return `
      ${title('Channel Status', `Every monitored channel in ${S.band_monitored} (${S.band_mhz}), current window.`)}
      ${panel('Channel Status', `<div class="chan-picker" style="margin-bottom:12px">${tabs}</div>
        <div class="scroll">${ChannelStatus(chs)}</div>`,
        { sub: `${chs.length} of ${D.channels.length} channels shown`,
          right: `<span class="chip blue">Window ${String(S.snapshot_hour).padStart(2, '0')}:00</span>` })}
      ${footer()}`;
    },

    access: () => {
      const n = (d) => D.decisions.filter((x) => x.decision === d).length;
      return `
      ${title('Access Management', 'Every state change the rules engine made over the last six sensing windows.')}
      <div class="kpis" style="grid-template-columns:repeat(3,1fr)">
        ${KpiCard({ icon: 'check', tone: 'green', value: n('Granted'), label: 'Grants issued', meta: '<span>Verified idle, rule-checked</span>' })}
        ${KpiCard({ icon: 'x', value: n('Denied'), label: 'Requests denied', meta: '<span>Protected, fail-safe or occupied</span>' })}
        ${KpiCard({ icon: 'alert', value: n('Revoked'), label: 'Grants revoked', meta: '<span class="warn">Incumbent signal detected</span>' })}
      </div>
      ${panel('Access Decisions', `<div class="scroll">${AccessDecisionTable(D.decisions, { node: true, actions: true })}</div>`,
        { sub: 'Operator actions apply to this session\'s state and are written to the audit log.' })}
      ${footer()}`;
    },

    rules: () => `
      ${title('Rules & Policies', 'The regulatory layer. It is consulted after the ML layer, and it always has the final word.')}
      ${panel('Decision Authority', AuthorityStrip())}
      <div class="row-2e">
        ${panel('POTRAZ Rule Check &mdash; ' + esc(D.live.channel), RulesPanel(D.live.checks), { sub: 'Enforced checks decide. Unmodelled items are shown, not assumed to pass.' })}
        ${panel('Loaded Constraints', `<dl class="kv">
          <dt>Final authority</dt><dd>POTRAZ rule engine</dd>
          <dt>Protected channels</dt><dd class="mono">${D.config.protected_channels.join(', ') || 'none'}</dd>
          <dt>Exclusion zones</dt><dd>${D.config.excluded_nodes.length ? D.config.excluded_nodes.join(', ') : 'None loaded'}</dd>
          <dt>Sensing fail-safe</dt><dd>Best-node confidence &ge; ${D.config.confidence_threshold.toFixed(2)}</dd>
          <dt>Verified-idle threshold</dt><dd>Fused P(occupied) &le; ${D.config.occupancy_threshold.toFixed(2)}</dd>
          <dt>Grant window</dt><dd>${D.config.grant_window_min} minutes, then re-checked</dd>
          <dt>Rules version</dt><dd class="mono">${esc(S.rules_version)}</dd>
          <dt>Source</dt><dd>${esc(S.rules_source)}</dd></dl>
          <div class="notice" style="border-color:rgba(242,181,45,0.45);background:rgba(242,181,45,0.06)">${icon('alert')}
            <span>Illustrative rules placeholder. Real deployment requires POTRAZ-supplied ZNFAP data, exclusion radii and power limits.</span></div>`)}
      </div>${footer()}`,

    analytics: () => {
      const a = D.analytics;
      const bars = ['accuracy', 'recall', 'precision', 'f1'].map((m) => `<div class="metric-bar"><span style="text-transform:capitalize">${m}</span>
        <div class="track"><i style="width:${a.ml[m] * 100}%;background:${COL.violet}"></i><i class="base" style="width:${a.baseline[m] * 100}%"></i></div>
        <span class="mono">${(a.ml[m] * 100).toFixed(1)}%</span></div>`).join('');
      const u = a.hourly_utilisation, W = 560, H = 210, L = 40, B = 24;
      const x = (i) => L + (i / 23) * (W - L - 10), y = (v) => 8 + (1 - v / 100) * (H - 8 - B);
      const line = u.map((v, i) => (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(v).toFixed(1)).join('');
      const grid = [0, 25, 50, 75, 100].map((v) => `<line x1="${L}" y1="${y(v)}" x2="${W - 10}" y2="${y(v)}" stroke="#172a47"/>
        <text class="axis-text" x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${v}%</text>`).join('');
      const xl = [0, 4, 8, 12, 16, 20, 23].map((i) => `<text class="axis-text" x="${x(i)}" y="${H - 6}" text-anchor="middle">${hh(i)}</text>`).join('');
      return `
      ${title('Analytics', 'Why fusion was necessary: the ML layer against the simple majority vote it has to beat.')}
      <div class="row-2e">
        ${panel('Fusion Model vs Naive Vote', `<div class="metric-bars">${bars}</div>
          <div class="legend-row" style="justify-content:flex-start;margin-top:16px"><span><i class="swatch" style="background:${COL.violet}"></i>ML fusion</span>
          <span><i class="swatch" style="background:#4c5f80"></i>Naive vote baseline</span></div>
          <dl class="kv" style="margin-top:18px"><dt>Model</dt><dd>${esc(D.config.model)}</dd>
          <dt>Latency</dt><dd class="mono">${a.latency_ms} ms / prediction (budget 100 ms)</dd>
          <dt>Evaluation</dt><dd class="mono">${a.train_windows.toLocaleString()} train / ${a.test_windows.toLocaleString()} held-out windows</dd></dl>`,
          { sub: 'Held-out period with unannounced schedule irregularities' })}
        ${panel('Band Utilisation by Hour', `<svg class="chart" viewBox="0 0 ${W} ${H}" style="height:240px">${grid}
          <path d="${line}L${x(23)} ${H - B}L${x(0)} ${H - B}Z" fill="${COL.cyan}" opacity="0.10"/>
          <path d="${line}" fill="none" stroke="${COL.cyan}" stroke-width="2.2"/>${xl}</svg>`,
          { sub: 'Share of channels occupied, held-out period &mdash; the visibility a static allocation table does not give' })}
      </div>${footer()}`;
    },

    audit: () => `
      ${title('Audit Logs', 'Every ingest, prediction, rule check and access change, in order. Decisions are explainable and replayable.')}
      ${panel('Audit Log', `<div class="scroll">${AuditLog(D.audit)}</div>`,
        { right: `<span class="chip">${D.audit.length} events</span>` })}${footer()}`,

    health: () => `
      ${title('System Health', 'Status of each layer in the sensing-to-decision pipeline.')}
      <div class="row-2e">${panel('Pipeline Components', SystemHealth())}
        ${panel('Spectrum Usage Summary', SpectrumUsage())}</div>${footer()}`,

    settings: () => `
      ${title('Settings', 'Operating parameters currently loaded. Read-only in this build.')}
      <div class="row-2e">
        ${panel('Decision Thresholds', `<dl class="kv">
          <dt>Energy detection (per node)</dt><dd class="mono">${D.config.energy_threshold_dbm} dBm</dd>
          <dt>Sensing fail-safe</dt><dd class="mono">${D.config.confidence_threshold.toFixed(2)}</dd>
          <dt>Verified-idle threshold</dt><dd class="mono">P(occ) &le; ${D.config.occupancy_threshold.toFixed(2)}</dd>
          <dt>Grant window</dt><dd class="mono">${D.config.grant_window_min} min</dd></dl>`)}
        ${panel('Data & Model', `<dl class="kv"><dt>Data source</dt><dd>${esc(S.data_notice)}</dd>
          <dt>Node siting</dt><dd>${esc(S.site_notice)}</dd><dt>Model</dt><dd>${esc(D.config.model)}</dd>
          <dt>Rules</dt><dd class="mono">${esc(S.rules_version)}</dd>
          <dt>Band</dt><dd>${esc(S.band_monitored)} &middot; ${esc(S.band_mhz)}</dd></dl>`)}
      </div>${footer()}`,
  };

  /* =========================================================== chrome == */

  function title(t, sub) {
    return `<div class="welcome" style="grid-template-columns:1fr auto"><div><h1 style="font-size:28px">${t}</h1><p style="font-size:14px">${sub}</p></div>
      <span class="chip amber">Simulated sensing data</span></div>`;
  }

  function welcome() {
    return `<div class="welcome">
      <div><h1>Welcome to MASAISAI</h1><p>${esc(S.description)}</p></div>
      <div><div class="clock-date" id="clk-date"></div><div class="clock-time" id="clk-time"></div>
        <div class="op-status"><i class="dot green live"></i>System Operational</div></div>
      <div class="vr q"></div>
      <div class="quote">&ldquo;Same airwaves.<br>Greater opportunities.&rdquo;<cite>&mdash; MASAISAI</cite></div></div>`;
  }

  function footer() {
    return `<div class="footer"><b style="color:var(--ink)">MASAISAI</b><span class="sep"></span>
      <span>Owned and operated by POTRAZ</span><span class="sep"></span>
      <span>Dynamic Spectrum Access for Rural Broadband</span><span class="grow"></span>
      <span class="warn">SIMULATED SENSING DATA</span><span class="sep"></span>
      <span>Version 1.0.0</span><span class="sep"></span><span>AI4I Project</span></div>`;
  }

  /* Why each constraint exists, shown when a rule row is expanded. */
  const RULE_WHY = {
    'Frequency Allocation': 'The channel must fall inside the UHF band MASAISAI is licensed to sense and inside the range the national frequency allocation plan opens to secondary use. A channel outside that range is never offered, whatever the sensing says.',
    'Incumbent Protection': 'The licensed broadcaster on this channel has absolute priority. If fused sensing places any incumbent energy on the channel, this check fails and no grant can stand -- including one already issued, which is revoked immediately.',
    'Geographic Restriction': 'Grants are bound to the node that measured them. A channel verified idle at one site says nothing about the same channel elsewhere, so the decision does not travel.',
    'Channel Availability': 'Fused P(occupied) must sit at or below the verified-idle threshold. This is the only check the ML layer feeds, and it is one vote among several -- it cannot carry a decision on its own.',
    'Transmission Constraint': 'Secondary transmission must stay inside the emission mask and the adjacent-channel limits, so a grant on one channel cannot degrade the neighbours.',
    'Permitted Power': 'Transmit power is capped for the site class. The cap is a regulatory input, not something the platform derives from sensing.',
    'Regulatory Conditions': 'Any remaining licence conditions POTRAZ attaches to secondary use. Items not modelled in this build are shown as such rather than assumed to pass.',
  };

  /* ============================================================ router == */

  const NAV = [['dashboard', 'home', 'Dashboard'], ['map', 'map', 'Spectrum Map'], ['sensing', 'activity', 'Live Sensing'],
    ['channels', 'wave', 'Channel Status'], ['access', 'usercheck', 'Access Management'], ['rules', 'rules', 'Rules & Policies'],
    ['analytics', 'chart', 'Analytics'], ['audit', 'audit', 'Audit Logs'], ['health', 'health', 'System Health'],
    ['settings', 'settings', 'Settings']];

  // Readable slugs for the address. The console runs inside a sandboxed
  // component frame with an opaque origin, where history.pushState throws, so
  // routes live in the fragment -- which still creates real history entries,
  // so browser back/forward work. sessionStorage survives a host rerun.
  const SLUG = { dashboard: 'dashboard', map: 'spectrum-map', sensing: 'live-sensing',
    channels: 'channel-status', access: 'access-management', rules: 'rules-policies',
    analytics: 'analytics', audit: 'audit-logs', health: 'system-health', settings: 'settings' };
  const VIEW_OF = Object.fromEntries(Object.entries(SLUG).map(([v, s]) => [s, v]));
  const STORE_KEY = 'masaisai.route';

  // Two hosts, one build. Served as a normal page (the VPS build) the console
  // uses real paths and pushState. Inside Streamlit's component frame the
  // origin is opaque and pushState throws, so routes fall back to the
  // fragment -- which still creates genuine history entries.
  const BASE = (window.MASAISAI_BASE || '/').replace(/\/*$/, '/');
  const CAN_PUSH = (() => {
    try { return location.origin !== 'null' && typeof history.pushState === 'function'; }
    catch (e) { return false; }
  })();

  let current = 'dashboard';
  let currentQuery = {};

  /** Accepts '#/slug?x=1', '/base/slug?x=1' or 'slug'. */
  function parseRoute(raw) {
    let h = String(raw || '');
    if (h.startsWith('#')) h = h.replace(/^#\/?/, '');
    else if (h.startsWith(BASE)) h = h.slice(BASE.length);
    h = h.replace(/^\/+/, '');
    if (!h) return null;
    const [slug, qs] = h.split('?');
    const view = VIEW_OF[slug] || (slug in views ? slug : null);
    if (!view) return null;
    const q = {};
    (qs || '').split('&').filter(Boolean).forEach((p) => {
      const [k, v] = p.split('=');
      q[decodeURIComponent(k)] = decodeURIComponent(v || '');
    });
    return { view, query: q };
  }

  function queryString(query) {
    return Object.entries(query || {}).filter(([, v]) => v != null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
  }
  function routeHash(view, query) {
    const qs = queryString(query);
    return `#/${SLUG[view] || view}${qs ? '?' + qs : ''}`;
  }
  function routeUrl(view, query) {
    const qs = queryString(query);
    return CAN_PUSH ? `${BASE}${SLUG[view] || view}${qs ? '?' + qs : ''}`
      : routeHash(view, query);
  }

  function store(view, query) {
    try { sessionStorage.setItem(STORE_KEY, routeHash(view, query)); } catch (e) { /* private mode */ }
  }

  /** Navigate. `replace` avoids stacking a history entry for filter toggles. */
  function navigate(target, opts = {}) {
    const [v, qs] = String(target).split('?');
    const parsed = parseRoute('#/' + (SLUG[v] || v) + (qs ? '?' + qs : ''));
    if (!parsed) return;
    const url = routeUrl(parsed.view, parsed.query);
    if (CAN_PUSH) {
      const here = location.pathname + location.search;
      if (here !== url) {
        history[opts.replace ? 'replaceState' : 'pushState']({ v: parsed.view }, '', url);
      }
      render(parsed.view, parsed.query);
      return;
    }
    if (location.hash === url) { render(parsed.view, parsed.query); return; }
    try {
      if (opts.replace) location.replace(location.href.split('#')[0] + url);
      else location.hash = url;                  // real history entry
    } catch (e) {
      render(parsed.view, parsed.query);         // fragment blocked: render anyway
      return;
    }
    if (!('onhashchange' in window)) render(parsed.view, parsed.query);
  }

  function render(view, query) {
    current = view in views ? view : 'dashboard';
    currentQuery = query || {};
    store(current, currentQuery);
    document.querySelectorAll('.nav-item').forEach((b) => {
      const on = b.dataset.view === current;
      b.classList.toggle('active', on);
      b.setAttribute('aria-current', on ? 'page' : 'false');
    });
    const main = document.getElementById('main');
    main.classList.remove('view-in');
    main.innerHTML = `<div class="view">${views[current](currentQuery)}</div>`;
    void main.offsetWidth;                        // restart the entrance transition
    main.classList.add('view-in');
    main.scrollTop = 0;
    closeMenu();
    tick();
    onViewMounted();
  }

  function currentRoute() {
    if (CAN_PUSH) {
      const r = parseRoute(location.pathname + location.search);
      if (r) return r;
    }
    return parseRoute(location.hash);
  }

  function onPop() {
    const r = currentRoute();
    render(r ? r.view : 'dashboard', r ? r.query : {});
  }

  /* ============================================================= shell == */

  /** Brand mark with the RF pulse: three arcs expanding from the antenna node. */
  function brandMark() {
    const arcs = `<path d="M7.6 6.6a6.2 6.2 0 0 0 0 8.8"/><path d="M16.4 15.4a6.2 6.2 0 0 0 0-8.8"/>`;
    return `<svg class="brand-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <g class="rf-pulse"><g class="rf-arc a1">${arcs}</g><g class="rf-arc a2">${arcs}</g>
        <g class="rf-arc a3">${arcs}</g></g>
      <path d="${P.logo}"/></svg>`;
  }

  const MENU = [['profile', 'usercheck', 'Profile'], ['prefs', 'settings', 'System Preferences'],
    ['activity', 'list', 'Operator Activity'], ['signout', 'x', 'Sign Out']];

  function shell() {
    document.getElementById('app').innerHTML = `
      <header class="header">
        <button type="button" class="brand" data-go="dashboard" aria-label="MASAISAI home">
          ${brandMark()}<div><div class="brand-name">MASAISAI</div>
          <div class="brand-tag">${esc(S.tagline)}</div></div></button>
        <div class="vr"></div>
        <button type="button" class="context" data-go="rules" aria-label="Regulatory context">
          <div class="context-title">${esc(S.context)}</div>
          <div class="context-sub">${esc(S.context_sub)}</div></button>
        <div class="header-spacer"></div>
        <button type="button" class="regulator" data-go="rules" aria-label="POTRAZ regulatory authority">
          ${icon('potraz', 'regulator-mark')}<div><div class="regulator-name">POTRAZ</div>
          <div class="regulator-sub">Regulator &middot; Final authority<br>on spectrum access</div></div></button>
        <div class="vr"></div>
        <div class="user-wrap">
          <button type="button" class="user" id="user-btn" aria-haspopup="menu" aria-expanded="false">
            <div class="avatar">PA</div><span class="user-name">POTRAZ Admin</span>${icon('chev', 'chev')}</button>
          <div class="menu" id="user-menu" role="menu" hidden>
            <div class="menu-head"><div class="avatar">PA</div>
              <div><b>POTRAZ Admin</b><small>Regulatory operator &middot; full access</small></div></div>
            ${MENU.map(([k, ic, l]) => `<button type="button" class="menu-item" role="menuitem" data-menu="${k}">${icon(ic)}<span>${l}</span></button>`).join('')}
          </div></div>
      </header>
      <nav class="sidebar" aria-label="Primary"><div class="nav">${NAV.map(([k, ic, l]) =>
        `<button type="button" class="nav-item" data-view="${k}">${icon(ic)}<span>${l}</span></button>`).join('')}</div>
        <div class="sidebar-foot"><svg viewBox="0 0 100 90"><path d="${ZW.map((p, i) => (i ? 'L' : 'M') +
          ((p[0] - 25) * 11.4).toFixed(1) + ' ' + ((-15.5 - p[1]) * 12).toFixed(1)).join('')}Z" fill="currentColor"/></svg>
          <div>Zimbabwe's Spectrum</div><div>For a Brighter Tomorrow</div>
          <div class="sim">&#9679; SIMULATED DATA</div></div></nav>
      <main class="main" id="main" tabindex="-1"></main>
      <div class="toasts" id="toasts" role="status" aria-live="polite"></div>
      <div class="tip-float" id="tipf" hidden></div>
      <div class="modal-scrim" id="scrim" hidden><div class="modal" role="dialog" aria-modal="true"
        aria-labelledby="modal-title" tabindex="-1"></div></div>`;
  }

  function tick() {
    const now = new Date();
    const d = document.getElementById('clk-date'), t = document.getElementById('clk-time');
    if (d) d.textContent = now.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
    if (t) t.textContent = now.toLocaleTimeString('en-GB', { hour12: false });
    document.querySelectorAll('[data-livestamp]').forEach((el) => {
      el.textContent = now.toLocaleTimeString('en-GB', { hour12: false });
    });
  }

  /* ============================================================ toasts == */

  function toast(kind, title, body, ms = 4600) {
    const host = document.getElementById('toasts');
    if (!host) return;
    const ic = { ok: 'check', warn: 'alert', bad: 'x', info: 'info' }[kind] || 'info';
    const el = document.createElement('div');
    el.className = `toast ${kind}`;
    el.innerHTML = `<span class="toast-icon">${icon(ic)}</span>
      <div><div class="toast-title">${esc(title)}</div><div class="toast-body">${esc(body)}</div></div>
      <button type="button" class="toast-x" aria-label="Dismiss">${icon('x')}</button>`;
    host.appendChild(el);
    const close = () => {
      el.classList.add('out');
      setTimeout(() => el.remove(), 220);
    };
    el.querySelector('.toast-x').addEventListener('click', close);
    const timer = setTimeout(close, ms);
    el.addEventListener('mouseenter', () => clearTimeout(timer));
    requestAnimationFrame(() => el.classList.add('in'));
  }

  /* ============================================================= modal == */

  let lastFocus = null;

  function openModal(opts) {
    const scrim = document.getElementById('scrim');
    const box = scrim.querySelector('.modal');
    lastFocus = document.activeElement;
    box.innerHTML = `<div class="modal-head">
        <div><div class="modal-title" id="modal-title">${opts.title}</div>
          ${opts.sub ? `<div class="modal-sub">${opts.sub}</div>` : ''}</div>
        <button type="button" class="icon-btn" data-close aria-label="Close">${icon('x')}</button></div>
      <div class="modal-body">${opts.body}</div>
      ${opts.actions ? `<div class="modal-foot">${opts.actions}</div>` : ''}`;
    scrim.hidden = false;
    requestAnimationFrame(() => scrim.classList.add('in'));
    (box.querySelector('[data-autofocus]') || box.querySelector('[data-close]')).focus();
  }

  function closeModal() {
    const scrim = document.getElementById('scrim');
    if (!scrim || scrim.hidden) return;
    scrim.classList.remove('in');
    setTimeout(() => { scrim.hidden = true; scrim.querySelector('.modal').innerHTML = ''; }, 180);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  const kv = (pairs) => `<dl class="kv">${pairs.filter(Boolean)
    .map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`;

  /* ------------------------------------------------------ detail bodies -- */

  function channelDetail(code) {
    const c = D.channels.find((x) => x.channel === code);
    if (!c) return null;
    const readings = D.rf[code] || [];
    const heard = readings.filter((r) => r.naive_occupied).length;
    return {
      title: `${esc(c.channel)} <span class="pill ${STATUS_PILL[c.status]}">${c.status}</span>`,
      sub: `${c.freq_mhz.toFixed(0)} MHz &middot; 8 MHz UHF raster &middot; window ${String(S.snapshot_hour).padStart(2, '0')}:00`,
      body: kv([
        ['Current occupancy', `<b>${c.p_occ.toFixed(2)}</b> fused P(occupied)`],
        ['Mean RSSI', `<span class="mono">${c.mean_rssi.toFixed(1)} dBm</span>`],
        ['Naive vote', `${c.naive_state} &middot; ${heard}/${readings.length} nodes above ${D.config.energy_threshold_dbm} dBm`],
        ['ML confidence', `<span class="mono">${c.ml_confidence.toFixed(2)}</span> <span class="chip violet">Advisory</span>`],
        ['Sensing confidence', `<span class="mono">${c.sensing_confidence.toFixed(2)}</span>`],
        ['Protection status', c.protected
          ? '<span class="pill gray">Protected</span> incumbent channel, never offered'
          : '<span class="pill green">Clear</span> no standing protection'],
        ['Current state', `<span class="pill ${STATUS_PILL[c.status]}">${c.status}</span>`],
        ['Reporting node', `<span class="mono">${esc(c.node)}</span> &middot; ${esc(c.town)}`],
        ['Latest observation', `${S.snapshot_hour.toString().padStart(2, '0')}:00, day ${S.snapshot_day}`],
      ]) + `<div class="notice">${icon('info')}<span>ML confidence is advisory. ${esc(c.channel)} is only usable if every enforced POTRAZ check passes.</span></div>`,
      actions: `<button type="button" class="btn btn-ghost" data-close>Close</button>
        <button type="button" class="btn btn-primary" data-go="sensing" data-close-first data-autofocus>Trace in Live Sensing ${icon('arrow')}</button>`,
    };
  }

  function nodeDetail(id) {
    const n = D.nodes.find((x) => x.id === id);
    if (!n) return null;
    const rows = Object.keys(D.rf).map((ch) => (D.rf[ch] || []).find((r) => r.node === n.label))
      .filter(Boolean);
    const mean = rows.length ? rows.reduce((a, r) => a + r.rssi, 0) / rows.length : null;
    return {
      title: `${esc(n.label)} <span class="pill ${n.status === 'online' ? 'green' : 'red'}">${n.status.toUpperCase()}</span>`,
      sub: `${esc(n.town)} &middot; RTL-SDR sensing node &middot; illustrative siting`,
      body: kv([
        ['Status', `<span class="pill ${n.status === 'online' ? 'green' : 'red'}">${n.status.toUpperCase()}</span>`],
        ['Availability', `<span class="pill ${{ high: 'green', moderate: 'amber', low: 'red', offline: 'gray' }[n.availability]}">${n.availability}</span>`],
        mean != null && ['Mean RSSI', `<span class="mono">${mean.toFixed(1)} dBm</span> across ${rows.length} channels`],
        ['Confidence', `<span class="mono">${n.confidence.toFixed(2)}</span> &middot; link ${n.quality}`],
        ['Channels monitored', `${Object.keys(D.rf).length} of ${D.channels.length} carry a reading from this node`],
        ['Channels idle', `${pct(n.idle_fraction)} this window`],
        ['Coordinates', `<span class="mono">${n.lat.toFixed(2)}, ${n.lon.toFixed(2)}</span>`],
        ['Latest reading', `window ${String(S.snapshot_hour).padStart(2, '0')}:00`],
      ]),
      actions: `<button type="button" class="btn btn-ghost" data-close>Close</button>
        <button type="button" class="btn btn-primary" data-go="sensing" data-close-first data-autofocus>View node details ${icon('arrow')}</button>`,
    };
  }

  function decisionDetail(i) {
    const r = D.decisions[i];
    if (!r) return null;
    return {
      title: `${esc(r.channel)} <span class="pill ${DECISION_PILL[r.decision]}">${r.decision}</span>`,
      sub: `${esc(r.time)} &middot; ${esc(r.location)}`,
      body: kv([
        ['Channel', `<b>${esc(r.channel)}</b>`],
        ['Location', esc(r.location)],
        ['Reporting node', `<span class="mono">${esc(r.node || '-')}</span>`],
        ['Decision', `<span class="pill ${DECISION_PILL[r.decision]}">${r.decision}</span>`],
        ['Duration', r.duration ? esc(r.duration) : 'Not granted'],
        ['Reason', esc(r.reason)],
        ['Decision authority', 'POTRAZ rules engine'],
        ['Prediction role', '<span class="chip violet">Advisory input only</span>'],
      ]),
      actions: `<button type="button" class="btn btn-ghost" data-close>Close</button>
        ${r.decision === 'Granted' ? `<button type="button" class="btn btn-danger" data-revoke="${i}" data-autofocus>Revoke access</button>` : ''}`,
    };
  }

  function auditDetail(i) {
    const e = D.audit[i];
    if (!e) return null;
    return {
      title: `${e.channel ? esc(e.channel) + ' ' : ''}<span class="pill ${AUDIT_PILL[e.kind] || 'gray'}">${AUDIT_KIND[e.kind] || e.kind}</span>`,
      sub: `Audit event &middot; ${esc(e.time)}`,
      body: kv([
        ['Timestamp', `<span class="mono">${esc(e.time)}</span>`],
        ['Channel', e.channel ? `<span class="mono">${esc(e.channel)}</span>` : 'Not channel-specific'],
        ['Layer', `${AUDIT_KIND[e.kind] || e.kind}`],
        ['Event', esc(e.text)],
        ['Trigger', e.kind === 'occupied' ? 'Fused sensing detected incumbent energy'
          : e.kind === 'denied' ? 'Rules engine withdrew the grant'
          : e.kind === 'granted' ? 'All enforced checks passed'
          : 'Pipeline stage completed'],
        ['Decision authority', e.kind === 'ml' ? 'ML layer (advisory)' : 'POTRAZ rules engine'],
        ['Audit identifier', `<span class="mono">AUD-${String(i + 1).padStart(5, '0')}</span>`],
      ]),
      actions: `<button type="button" class="btn btn-ghost" data-close data-autofocus>Close</button>`,
    };
  }

  /* ----------------------------------------------------------- revoke --- */

  function confirmRevoke(i) {
    const r = D.decisions[i];
    if (!r) return;
    openModal({
      title: 'Revoke access?',
      sub: 'This withdraws the grant and records the change in the audit log.',
      body: kv([
        ['Channel', `<b>${esc(r.channel)}</b>`],
        ['Location', esc(r.location)],
        ['Granted at', `<span class="mono">${esc(r.time)}</span>`],
        ['Reason', 'Manual operator intervention'],
      ]) + `<div class="notice" style="border-color:rgba(239,83,80,.45);background:rgba(239,83,80,.07)">${icon('alert')}
        <span>The secondary user on ${esc(r.channel)} stops transmitting immediately. Re-authorisation requires a fresh rule check.</span></div>`,
      actions: `<button type="button" class="btn btn-ghost" data-close>Cancel</button>
        <button type="button" class="btn btn-danger" data-revoke-confirm="${i}" data-autofocus>Revoke access</button>`,
    });
  }

  function doRevoke(i) {
    const r = D.decisions[i];
    if (!r || r.decision !== 'Granted') return;
    const now = new Date().toLocaleTimeString('en-GB', { hour12: false }).slice(0, 5);
    r.decision = 'Revoked';
    r.duration = null;
    r.reason = 'Manual operator intervention';
    D.decisions.unshift({
      time: now, hour: new Date().getHours(), channel: r.channel, location: r.location,
      node: r.node, decision: 'Revoked', duration: null,
      reason: 'Manual operator intervention',
    });
    D.audit.unshift({ time: now + ':00', kind: 'denied', channel: r.channel,
      text: `${r.channel} ACCESS REVOKED BY OPERATOR` });
    D.kpis.active_grants = Math.max(0, D.kpis.active_grants - 1);
    D.health.active_grants = D.kpis.active_grants;
    D.health.audit_events = (D.health.audit_events || 0) + 1;
    closeModal();
    render(current, currentQuery);
    toast('warn', 'Access revoked', `${r.channel} withdrawn at ${r.location}. Audit entry written.`);
  }

  /* ============================================================ tooltip == */

  function showTip(el, ev) {
    const f = document.getElementById('tipf');
    const parts = String(el.dataset.tip || '').split('|');
    if (!parts[0]) return;
    f.innerHTML = `<b>${parts[0]}</b>${parts.slice(1).map((p) => `<span>${p}</span>`).join('')}`;
    f.hidden = false;
    const r = f.getBoundingClientRect();
    let x = ev.clientX + 14, y = ev.clientY - r.height - 12;
    if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
    if (y < 8) y = ev.clientY + 18;
    f.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
  }
  const hideTip = () => { const f = document.getElementById('tipf'); if (f) f.hidden = true; };

  /* ================================================================ map == */

  const MAP_MIN = 1, MAP_MAX = 6;

  /* Two-speed repaint. The viewBox moves on every frame of a gesture, which is
     one attribute write; the full rebuild -- which also rescales markers and
     labels so they keep a constant on-screen size -- is deferred to the next
     animation frame. Rebuilding on every wheel tick replaced the node under
     the cursor mid-gesture and dropped frames. */
  let repaintQueued = false;

  function mapViewBox() {
    const W = SPAN_LON * K * COSL + 2 * PAD, H = SPAN_LAT * K + 2 * PAD;
    const vw = W / mapState.zoom, vh = H / mapState.zoom;
    if (mapState.cx == null) { mapState.cx = W / 2; mapState.cy = H / 2; }
    mapState.cx = Math.max(vw / 2, Math.min(W - vw / 2, mapState.cx));
    mapState.cy = Math.max(vh / 2, Math.min(H - vh / 2, mapState.cy));
    return `${(mapState.cx - vw / 2).toFixed(1)} ${(mapState.cy - vh / 2).toFixed(1)} ${vw.toFixed(1)} ${vh.toFixed(1)}`;
  }

  function rebuildMap() {
    const wrap = document.querySelector('[data-map]');
    if (!wrap) return;
    const open = wrap.querySelector('.map-pop:not([hidden])');
    const fresh = document.createElement('div');
    fresh.innerHTML = SpectrumMap(mapState.opts || {});
    wrap.parentNode.replaceChild(fresh.firstElementChild, wrap);
    if (open) closePopup();
  }

  function repaintMap() {
    const svg = document.querySelector('.map-svg');
    if (svg) svg.setAttribute('viewBox', mapViewBox());
    if (repaintQueued) return;
    repaintQueued = true;
    requestAnimationFrame(() => { repaintQueued = false; rebuildMap(); });
  }

  function mapZoom(factor, ev) {
    const wrap = document.querySelector('[data-map]');
    if (!wrap) return;
    const svg = wrap.querySelector('.map-svg');
    const before = mapState.zoom;
    const next = Math.max(MAP_MIN, Math.min(MAP_MAX, before * factor));
    if (next === before) return;
    // Zoom about the cursor: the map point under the pointer stays put.
    if (ev && svg) {
      const b = svg.getBoundingClientRect();
      const vb = svg.viewBox.baseVal;
      const px = vb.x + ((ev.clientX - b.left) / b.width) * vb.width;
      const py = vb.y + ((ev.clientY - b.top) / b.height) * vb.height;
      mapState.cx = px + (mapState.cx - px) * (before / next);
      mapState.cy = py + (mapState.cy - py) * (before / next);
    }
    mapState.zoom = next;
    repaintMap();
  }

  function mapReset() {
    mapState.zoom = 1; mapState.cx = null; mapState.cy = null;
    repaintMap();
  }

  function nodePopup(id, wrap) {
    const n = D.nodes.find((x) => x.id === id);
    const pop = wrap.querySelector('.map-pop');
    if (!n || !pop) return;
    const rows = Object.keys(D.rf).map((ch) => (D.rf[ch] || []).find((r) => r.node === n.label)).filter(Boolean);
    const mean = rows.length ? rows.reduce((a, r) => a + r.rssi, 0) / rows.length : null;
    pop.innerHTML = `<div class="map-pop-head"><b>${esc(n.label)}</b>
        <span class="pill ${n.status === 'online' ? 'green' : 'red'}">${n.status.toUpperCase()}</span>
        <button type="button" class="icon-btn" data-pop-close aria-label="Close">${icon('x')}</button></div>
      <div class="map-pop-town">${esc(n.town)}</div>
      <dl class="kv compact">
        <dt>RSSI</dt><dd class="mono">${mean != null ? mean.toFixed(1) + ' dBm' : '-'}</dd>
        <dt>Confidence</dt><dd class="mono">${n.confidence.toFixed(2)} &middot; ${n.quality}</dd>
        <dt>Channels</dt><dd>${rows.length} monitored &middot; ${pct(n.idle_fraction)} idle</dd>
        <dt>Latest</dt><dd>window ${String(S.snapshot_hour).padStart(2, '0')}:00</dd></dl>
      <button type="button" class="link" data-node-detail="${esc(n.id)}">View node details ${icon('arrow')}</button>`;
    pop.hidden = false;
    requestAnimationFrame(() => pop.classList.add('in'));
  }

  function closePopup() {
    document.querySelectorAll('.map-pop').forEach((p) => { p.hidden = true; p.classList.remove('in'); });
  }

  /* Wheel must be non-passive to be cancellable, so it is bound once here
     rather than per render. Outside the map the page scrolls normally. */
  document.addEventListener('wheel', (e) => {
    const wrap = e.target.closest && e.target.closest('[data-map]');
    if (!wrap) return;
    e.preventDefault();                       // never let the host page scroll or zoom
    e.stopPropagation();
    mapZoom(e.deltaY < 0 ? 1.18 : 1 / 1.18, e);
  }, { passive: false });

  let drag = null;
  document.addEventListener('pointerdown', (e) => {
    const wrap = e.target.closest && e.target.closest('[data-map]');
    if (!wrap || e.target.closest('.map-zoom, .map-pop, .map-node')) return;
    const svg = wrap.querySelector('.map-svg');
    if (!svg) return;
    const b = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
    drag = { x: e.clientX, y: e.clientY, cx: mapState.cx, cy: mapState.cy,
      k: vb.width / b.width, moved: false };
    wrap.classList.add('grabbing');
  });
  document.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 3) return;
    drag.moved = true;
    mapState.cx = drag.cx - dx * drag.k;
    mapState.cy = drag.cy - dy * drag.k;
    repaintMap();
    document.querySelector('[data-map]') && document.querySelector('[data-map]').classList.add('grabbing');
  });
  document.addEventListener('pointerup', () => {
    drag = null;
    document.querySelectorAll('[data-map]').forEach((w) => w.classList.remove('grabbing'));
  });
  document.addEventListener('dblclick', (e) => {
    if (e.target.closest && e.target.closest('[data-map]')) { e.preventDefault(); mapZoom(1.5, e); }
  });

  /* ====================================================== admin menu ===== */

  function toggleMenu(force) {
    const btn = document.getElementById('user-btn'), menu = document.getElementById('user-menu');
    if (!btn || !menu) return;
    const open = force != null ? force : menu.hidden;
    menu.hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
    btn.classList.toggle('open', open);
    if (open) {
      requestAnimationFrame(() => menu.classList.add('in'));
      const first = menu.querySelector('.menu-item');
      if (first) first.focus();
    } else {
      menu.classList.remove('in');
    }
  }
  const closeMenu = () => toggleMenu(false);

  const MENU_ACTION = {
    profile: () => openModal({
      title: 'POTRAZ Admin', sub: 'Regulatory operator &middot; full access',
      body: kv([['Role', 'Regulatory operator'], ['Organisation', 'POTRAZ'],
        ['Permissions', 'View all &middot; revoke grants &middot; export audit'],
        ['Session', 'Local demonstration build'],
        ['Data', `<span class="chip amber">Simulated sensing data</span>`]]),
      actions: `<button type="button" class="btn btn-ghost" data-close data-autofocus>Close</button>`,
    }),
    prefs: () => navigate('settings'),
    activity: () => navigate('audit'),
    signout: () => toast('info', 'Sign out unavailable',
      'This build runs without authentication. Close the browser tab to end the session.'),
  };

  /* ================================================= live sensing drift == */

  let driftTimer = null;

  function startDrift() {
    stopDrift();
    const bars = Array.from(document.querySelectorAll('.rssi-row'));
    if (!bars.length) return;
    const base = bars.map((row) => {
      const val = row.querySelector('.mono:nth-of-type(1)');
      const out = row.querySelectorAll('.mono');
      const el = out[out.length - 2];
      return { el, v: parseFloat((el && el.textContent) || '0') };
    }).filter((b) => b.el && !Number.isNaN(b.v));
    // A sensing node's reported level wanders by a few tenths of a dB between
    // windows. It never crosses the detection threshold on its own -- the
    // verdict comes from the backend, not from this animation.
    driftTimer = setInterval(() => {
      base.forEach((b) => {
        const j = (Math.random() - 0.5) * 0.6;
        b.el.textContent = (b.v + j).toFixed(1) + ' dBm';
        b.el.classList.remove('flick');
        void b.el.offsetWidth;
        b.el.classList.add('flick');
      });
    }, 2200);
  }
  function stopDrift() { if (driftTimer) { clearInterval(driftTimer); driftTimer = null; } }

  function onViewMounted() {
    stopDrift();
    if (current === 'sensing') startDrift();
    mapState.opts = current === 'map' ? { detail: true, unit: 0.95 } : {};
  }

  /* =========================================================== events === */

  function activate(el, ev) {
    // Order matters: the most specific control wins.
    if (el.closest('[data-close]')) {
      const go = el.closest('[data-go]');
      closeModal();
      if (go && go.hasAttribute('data-close-first')) navigate(go.dataset.go);
      return true;
    }
    const revokeOk = el.closest('[data-revoke-confirm]');
    if (revokeOk) { doRevoke(+revokeOk.dataset.revokeConfirm); return true; }
    const revoke = el.closest('[data-revoke]');
    if (revoke) { confirmRevoke(+revoke.dataset.revoke); return true; }
    const popClose = el.closest('[data-pop-close]');
    if (popClose) { closePopup(); return true; }
    const nodeDet = el.closest('[data-node-detail]');
    if (nodeDet) {
      const d = nodeDetail(nodeDet.dataset.nodeDetail);
      closePopup(); if (d) openModal(d); return true;
    }
    const zoom = el.closest('[data-zoom]');
    if (zoom) {
      const k = zoom.dataset.zoom;
      if (k === 'reset') mapReset(); else mapZoom(k === 'in' ? 1.35 : 1 / 1.35, ev);
      return true;
    }
    const marker = el.closest('.map-node');
    if (marker) { nodePopup(marker.dataset.node, marker.closest('[data-map]')); return true; }
    const menuBtn = el.closest('#user-btn');
    if (menuBtn) { toggleMenu(); return true; }
    const menuItem = el.closest('[data-menu]');
    if (menuItem) { closeMenu(); (MENU_ACTION[menuItem.dataset.menu] || (() => {}))(); return true; }
    const nav = el.closest('[data-view]');
    if (nav) { navigate(nav.dataset.view); return true; }
    const decView = el.closest('[data-decision-view]');
    if (decView) { const d = decisionDetail(+decView.dataset.decisionView); if (d) openModal(d); return true; }
    const filt = el.closest('[data-filter]');
    if (filt) {
      navigate('channels' + (filt.dataset.filter === 'ALL' ? '' : '?filter=' + filt.dataset.filter),
        { replace: true });
      return true;
    }
    const go = el.closest('[data-go]');
    if (go) { navigate(go.dataset.go); return true; }
    const ch = el.closest('[data-ch]');
    if (ch) { rfState.channel = ch.dataset.ch; render(current, currentQuery); return true; }
    const rule = el.closest('[data-rule]');
    if (rule) {
      const on = rule.classList.toggle('open');
      rule.setAttribute('aria-expanded', String(on));
      return true;
    }
    const series = el.closest('[data-series]');
    if (series) {
      series.classList.toggle('muted');
      const i = Array.from(series.parentNode.querySelectorAll('[data-series]')).indexOf(series);
      const svg = series.closest('.panel').querySelector('.chart');
      if (svg) svg.classList.toggle('hide-s' + i, series.classList.contains('muted'));
      return true;
    }
    const chRow = el.closest('[data-channel]');
    if (chRow) { const d = channelDetail(chRow.dataset.channel); if (d) openModal(d); return true; }
    const nodeRow = el.closest('[data-node]');
    if (nodeRow) { const d = nodeDetail(nodeRow.dataset.node); if (d) openModal(d); return true; }
    const decRow = el.closest('[data-decision]');
    if (decRow) { const d = decisionDetail(+decRow.dataset.decision); if (d) openModal(d); return true; }
    const audRow = el.closest('[data-audit]');
    if (audRow) { const d = auditDetail(+audRow.dataset.audit); if (d) openModal(d); return true; }
    return false;
  }

  document.addEventListener('click', (e) => {
    const scrim = document.getElementById('scrim');
    if (scrim && !scrim.hidden && e.target === scrim) return closeModal();
    if (!e.target.closest('.user-wrap')) closeMenu();
    if (!e.target.closest('[data-map]')) closePopup();
    activate(e.target, e);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const scrim = document.getElementById('scrim');
      if (scrim && !scrim.hidden) return closeModal();
      const menu = document.getElementById('user-menu');
      if (menu && !menu.hidden) { closeMenu(); document.getElementById('user-btn').focus(); return; }
      closePopup();
      return;
    }
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
      const t = e.target;
      if (t && t.matches && t.matches('[tabindex="0"], [role="button"]') && !t.matches('button, a, input')) {
        e.preventDefault();
        activate(t, e);
      }
      return;
    }
    const menu = document.getElementById('user-menu');
    if (menu && !menu.hidden && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      const items = Array.from(menu.querySelectorAll('.menu-item'));
      const i = items.indexOf(document.activeElement);
      const next = e.key === 'ArrowDown' ? (i + 1) % items.length : (i - 1 + items.length) % items.length;
      items[next].focus();
      return;
    }
    if (e.target.closest && e.target.closest('[data-map]')) {
      const step = 18 / mapState.zoom;
      const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
      if (moves[e.key]) {
        e.preventDefault();
        mapState.cx += moves[e.key][0]; mapState.cy += moves[e.key][1];
        repaintMap();
      } else if (e.key === '+' || e.key === '=') { e.preventDefault(); mapZoom(1.35); }
      else if (e.key === '-') { e.preventDefault(); mapZoom(1 / 1.35); }
    }
  });

  document.addEventListener('mouseover', (e) => {
    const t = e.target.closest && e.target.closest('[data-tip]');
    if (t) showTip(t, e);
  });
  document.addEventListener('mousemove', (e) => {
    const t = e.target.closest && e.target.closest('[data-tip]');
    if (t) showTip(t, e); else hideTip();
  });
  document.addEventListener('mouseleave', hideTip, true);

  window.addEventListener(CAN_PUSH ? 'popstate' : 'hashchange', onPop);
  if (CAN_PUSH) window.addEventListener('hashchange', onPop);

  /* ============================================================== boot == */

  function boot() {
    try {
      if (!D || !D.meta || !Array.isArray(D.channels) || !D.channels.length) {
        throw new Error('The session payload is missing or empty. The sensing backend may not have finished building this window.');
      }
      shell();
      let start = currentRoute();
      if (!start) {
        let saved = null;
        try { saved = sessionStorage.getItem(STORE_KEY); } catch (err) { /* ignore */ }
        start = parseRoute(saved) || { view: 'dashboard', query: {} };
      }
      render(start.view, start.query);
      // Normalise the address so a deep link and a fresh load look the same.
      try {
        const url = routeUrl(start.view, start.query);
        if (CAN_PUSH) { if (location.pathname + location.search !== url) history.replaceState({ v: start.view }, '', url); }
        else if (!location.hash) location.replace(location.href.split('#')[0] + url);
      } catch (err) { /* ignore */ }
      setInterval(tick, 1000);
    } catch (err) {
      const app = document.getElementById('app');
      if (app) {
        app.innerHTML = `<div class="fatal"><div class="fatal-box">
          <div class="fatal-title">Spectrum data unavailable</div>
          <p>The console could not render this session's payload. Nothing has been
             lost -- reloading rebuilds the sensing window from the backend.</p>
          <pre>${esc(err && err.message || err)}</pre>
          <button type="button" class="btn btn-primary" onclick="location.reload()">Retry</button>
        </div></div>`;
      }
      throw err;
    }
  }

  boot();
})();
