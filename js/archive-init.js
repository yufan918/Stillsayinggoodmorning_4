/**
 * Loads archive.json and builds the meme grid, timeline metadata, and column gradients.
 */
(function () {
  var TOTAL_PX = 1440;

  function timeToMinutes(time) {
    var p = time.split(':');
    return parseInt(p[0], 10) * 60 + parseInt(p[1], 10);
  }

  function timeToTopPct(mins) {
    return Math.round((mins / TOTAL_PX) * 10000) / 100;
  }

  /** Month-first labels for 2026 groups; day-first for earlier months. */
  function buildLabel(monthMeta, day, time) {
    var parts = monthMeta.label.split(' ');
    var mon = parts[0];
    var year = parts[1];
    if (/26$/.test(monthMeta.id)) {
      return mon + ' ' + day + ' ' + year + ' ' + time;
    }
    return day + ' ' + mon + ' ' + year + ' ' + time;
  }

  function buildDerived(archive) {
    var monthById = {};
    archive.months.forEach(function (m) {
      monthById[m.id] = m;
    });

    var entriesByMonth = {};
    archive.entries.forEach(function (e) {
      if (!entriesByMonth[e.month]) entriesByMonth[e.month] = {};
      entriesByMonth[e.month][e.day] = e;
    });

    var groupMeta = {};
    var labelsByGroup = {};
    var chronOrder = {};
    var monthLabels = {};

    archive.months.forEach(function (m, idx) {
      var groupClass = 'grid-group--' + m.id;
      chronOrder[groupClass] = idx;
      monthLabels[groupClass] = m.label;

      var tops = {};
      var labels = {};
      var topPct = {};
      var monthEntries = entriesByMonth[m.id] || {};
      Object.keys(monthEntries).forEach(function (dayKey) {
        var day = parseInt(dayKey, 10);
        var entry = monthEntries[day];
        var mins = timeToMinutes(entry.time);
        tops[day] = mins;
        topPct[day] = timeToTopPct(mins);
        labels[day] = entry.label || buildLabel(m, day, entry.time);
      });

      groupMeta[groupClass] = { label: m.label, tops: tops };
      labelsByGroup[groupClass] = labels;
      m._topPct = topPct;
      m._entriesByDay = monthEntries;
    });

    return {
      monthById: monthById,
      groupMeta: groupMeta,
      labelsByGroup: labelsByGroup,
      chronOrder: chronOrder,
      monthLabels: monthLabels
    };
  }

  function buildDom(archive, derived) {
    var wrapper = document.getElementById('archive-scroll');
    if (!wrapper) return;

    var monthOrder = archive.displayOrder || archive.months.map(function (m) { return m.id; });
    var fragment = document.createDocumentFragment();

    monthOrder.forEach(function (mid, idx) {
      var m = derived.monthById[mid];
      if (!m) return;

      var section = document.createElement('section');
      section.className = 'grid-group grid-group--' + m.id;
      section.setAttribute('aria-label', m.ariaLabel);

      var canvas = document.createElement('div');
      canvas.className = 'grid-canvas grid-canvas--' + m.days;

      // The newest month (first in display order) keeps its full calendar width,
      // including the empty trailing columns for the days that haven't happened
      // yet (e.g. June showing up to the 7th leaves 23 empty future columns).
      // Every older month collapses its empty (no-greeting) days so posted days
      // sit flush together. Each column always keeps its original width
      // (1920 / days-in-month), so image size, filter, gradient and time are all
      // unchanged — only the gaps in past months disappear.
      var isNewest = idx === 0;

      var renderDays;
      if (isNewest) {
        renderDays = [];
        for (var d = 1; d <= m.days; d++) renderDays.push(d);
      } else {
        renderDays = [];
        for (var d2 = 1; d2 <= m.days; d2++) {
          if (m._entriesByDay[d2]) renderDays.push(d2);
        }
        var colW = 1920 / m.days;
        var blockW = renderDays.length * colW;
        // Override the fixed 1920px width from the stylesheet.
        section.style.width = blockW + 'px';
        section.style.minWidth = blockW + 'px';
        canvas.style.width = blockW + 'px';
        canvas.style.minWidth = blockW + 'px';
        canvas.style.maxWidth = blockW + 'px';
        canvas.style.gridTemplateColumns = 'repeat(' + renderDays.length + ', 1fr)';
      }

      renderDays.forEach(function (day) {
        var cell = document.createElement('div');
        cell.className = 'grid-cell';
        cell.setAttribute('data-day', String(day));

        var entry = m._entriesByDay[day];
        if (entry) {
          var img = document.createElement('img');
          img.src = 'photos/' + entry.photo;
          var y = entry.photo.slice(0, 2);
          var mo = entry.photo.slice(2, 4);
          var dy = entry.photo.slice(4, 6);
          img.alt = '20' + y + '-' + mo + '-' + dy;
          cell.appendChild(img);
        }
        canvas.appendChild(cell);
      });

      section.appendChild(canvas);
      fragment.appendChild(section);
    });

    wrapper.appendChild(fragment);
  }

  function injectGradients(archive, derived) {
    var stripPx = 30;
    var n = TOTAL_PX / stripPx;
    var defaultTopPct = 50;

    function beebffAlphaAtPosition(p, centerPct) {
      var alpha;
      if (p <= centerPct) alpha = centerPct > 0 ? p / centerPct : 0;
      else alpha = (100 - centerPct) > 0 ? (100 - p) / (100 - centerPct) : 0;
      return 'rgba(237,132,79,' + Math.max(0, Math.min(1, alpha)).toFixed(4) + ')';
    }

    function gradientForDaySep(day, topPctMap) {
      var centerPct = topPctMap && topPctMap[day] != null ? topPctMap[day] : defaultTopPct;
      var stops = [];
      for (var i = 0; i < n; i++) {
        var p = (i + 0.5) / n * 100;
        var col = beebffAlphaAtPosition(p, centerPct);
        var p1 = (i / n) * 100;
        var p2 = ((i + 1) / n) * 100;
        stops.push(col + ' ' + p1.toFixed(3) + '%', col + ' ' + p2.toFixed(3) + '%');
      }
      return 'linear-gradient(to bottom, ' + stops.join(', ') + ')';
    }

    var rules = [];
    archive.months.forEach(function (m) {
      for (var d = 1; d <= m.days; d++) {
        rules.push(
          '.grid-group--' + m.id + ' .grid-cell[data-day="' + d + '"] { background: ' +
          gradientForDaySep(d, m._topPct) + '; }'
        );
      }
    });

    var el = document.createElement('style');
    el.id = 'archive-gradient-styles';
    el.textContent = rules.join('\n');
    document.head.appendChild(el);
  }

  function injectImgTopStyles(archive, derived) {
    var rules = [];
    archive.entries.forEach(function (e) {
      var pct = timeToTopPct(timeToMinutes(e.time));
      rules.push(
        '.grid-group--' + e.month + ' .grid-cell[data-day="' + e.day + '"] img { top: ' + pct + '%; }'
      );
    });
    var el = document.createElement('style');
    el.id = 'archive-img-top-styles';
    el.textContent = rules.join('\n');
    document.head.appendChild(el);
  }

  function applyScrollOrder(archive) {
    var wrapper = document.querySelector('.page-scroll-wrapper');
    if (!wrapper) return;
    var order = archive.displayOrder || [];
    order.forEach(function (mid) {
      var section = wrapper.querySelector('.grid-group--' + mid);
      if (section) wrapper.appendChild(section);
    });
  }

  function setInitialDate(archive) {
    var dateEl = document.querySelector('.page-date');
    var wrapper = document.querySelector('.page-scroll-wrapper');
    if (!wrapper || !dateEl) return;
    var order = archive.displayOrder || [];
    var newest = order[0];
    var m = archive.months.find(function (x) { return x.id === newest; });
    if (m) dateEl.textContent = m.label;
    wrapper.style.scrollBehavior = 'auto';
    wrapper.scrollLeft = 0;
  }

  function hideLoading() {
    var el = document.getElementById('archive-loading');
    if (el) {
      el.classList.remove('is-visible');
      el.classList.remove('is-error');
    }
    var wrapper = document.getElementById('archive-scroll');
    if (wrapper) wrapper.removeAttribute('aria-busy');
  }

  function showLoading(msg, isError) {
    var el = document.getElementById('archive-loading');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('is-visible');
    if (isError) el.classList.add('is-error');
  }

  function init(archive) {
    var derived = buildDerived(archive);
    buildDom(archive, derived);
    injectGradients(archive, derived);
    injectImgTopStyles(archive, derived);
    applyScrollOrder(archive);
    setInitialDate(archive);

    window.__archive = archive;
    window.__timelineMeta = {
      groupMeta: derived.groupMeta,
      labelsByGroup: derived.labelsByGroup,
      chronOrder: derived.chronOrder,
      monthLabels: derived.monthLabels
    };

    hideLoading();
    document.dispatchEvent(new CustomEvent('archive-ready'));
  }

  showLoading('Loading archive…', false);

  fetch('archive.json')
    .then(function (r) {
      if (!r.ok) throw new Error('Failed to load archive.json (' + r.status + ')');
      return r.json();
    })
    .then(init)
    .catch(function (err) {
      console.error('[archive-init]', err);
      showLoading(
        'Could not load archive.json. Hard-refresh (Cmd+Shift+R) or check that the file was deployed.',
        true
      );
    });
})();
