/**
 * HumanNature v3.6.0 Analog Web Edition
 * 1:1 Pixel-Perfect Replica & Full OS Keystroke Simulation
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements: Main Window Left Panel
  const wpmSlider = document.getElementById('wpmSlider');
  const accSlider = document.getElementById('accSlider');
  const accValue = document.getElementById('accValue');
  const autoAccCheck = document.getElementById('autoAccCheck');
  const delaySlider = document.getElementById('delaySlider');
  const delayValue = document.getElementById('delayValue');
  const engineSelect = document.getElementById('engineSelect');
  const burstCheck = document.getElementById('burstCheck');
  const fragmentsCheck = document.getElementById('fragmentsCheck');

  const startBtn = document.getElementById('startBtn');
  const pauseBtn = document.getElementById('pauseBtn');
  const stopBtn = document.getElementById('stopBtn');
  const pasteEssayBtn = document.getElementById('pasteEssayBtn');
  const playgroundBtn = document.getElementById('playgroundBtn');
  const settingsBtn = document.getElementById('settingsBtn');
  const terminalOutput = document.getElementById('terminalOutput');

  // Elements: Main Window Right Panel
  const wpmHugeDisplay = document.getElementById('wpmHugeDisplay');
  const statusLabel = document.getElementById('statusLabel');
  const valLastKey = document.getElementById('valLastKey');
  const valKeystrokes = document.getElementById('valKeystrokes');
  const valTypos = document.getElementById('valTypos');
  const telemetryLabel = document.getElementById('telemetryLabel');
  const analogCanvas = document.getElementById('analogCanvas');
  const liveClock = document.getElementById('liveClock');
  const ctx = analogCanvas.getContext('2d');

  // Elements: Playground Modal
  const playgroundModal = document.getElementById('playgroundModal');
  const closePlaygroundBtn = document.getElementById('closePlaygroundBtn');
  const pgEngineSelect = document.getElementById('pgEngineSelect');
  const pgCasualCheck = document.getElementById('pgCasualCheck');
  const pgSampleEnBtn = document.getElementById('pgSampleEnBtn');
  const pgSampleEsBtn = document.getElementById('pgSampleEsBtn');
  const pgPasteBtn = document.getElementById('pgPasteBtn');
  const pgClearBtn = document.getElementById('pgClearBtn');
  const pgRunBtn = document.getElementById('pgRunBtn');
  const pgCleanMarkdownBtn = document.getElementById('pgCleanMarkdownBtn');
  const pgCopyBtn = document.getElementById('pgCopyBtn');
  const pgUseAutotyperBtn = document.getElementById('pgUseAutotyperBtn');
  
  const pgInputText = document.getElementById('pgInputText');
  const pgOutputText = document.getElementById('pgOutputText');

  // Analytics Cards
  const cardInWords = document.getElementById('cardInWords');
  const cardOutWords = document.getElementById('cardOutWords');
  const cardDiff = document.getElementById('cardDiff');
  const cardLang = document.getElementById('cardLang');
  const cardTiming = document.getElementById('cardTiming');

  // Bookmarklet
  const pgBookmarkletLink = document.getElementById('pgBookmarkletLink');

  // Elements: Settings Modal
  const settingsModal = document.getElementById('settingsModal');
  const closeSettingsBtn = document.getElementById('closeSettingsBtn');
  const setShiftEnter = document.getElementById('setShiftEnter');
  const setStripMarkdown = document.getElementById('setStripMarkdown');
  const setStripEmojis = document.getElementById('setStripEmojis');
  const setDesktopBridgeBtn = document.getElementById('setDesktopBridgeBtn');

  // Sample texts
  const SAMPLE_TEXT_EN = 
    "Furthermore, it is important to note that utilizing this framework ensures optimal results. " +
    "In order to delve into the realm of artificial intelligence, we must meticulously analyze every aspect " +
    "and take into consideration various factors to revolutionize our workflow.";

  const SAMPLE_TEXT_ES = 
    "Es crucial destacar que la inteligencia artificial juega un papel fundamental en el vertiginoso mundo actual. " +
    "Asimismo, cabe señalar que para optimizar los procesos debemos sumergirnos en un sinfín de posibilidades " +
    "con el fin de arrojar luz sobre esta materia y desentrañar los misterios de la tecnología.";

  let currentEssay = SAMPLE_TEXT_ES;
  let flightLatencies = new Array(65).fill(160);
  let statusPollTimer = null;
  let isTyping = false;

  // Live Clock
  function updateLiveClock() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    const hoursStr = String(hours).padStart(2, '0');
    liveClock.textContent = `${hoursStr}:${minutes} ${ampm}`;
  }
  setInterval(updateLiveClock, 1000);
  updateLiveClock();

  // Terminal Logger
  function logTerminal(msg) {
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.textContent = `> ${msg}`;
    terminalOutput.appendChild(line);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
    while (terminalOutput.children.length > 25) {
      terminalOutput.removeChild(terminalOutput.firstChild);
    }
  }

  // Presets Definition
  const PRESET_CONFIGS = {
    formal: { wpm: 55, acc: 98.5, engine: "🎓 Academic Master", burst: false, frag: false, delay: 3 },
    casual: { wpm: 85, acc: 94.0, engine: "🌊 Natural Flow", burst: true, frag: true, delay: 2 },
    espanol: { wpm: 72, acc: 95.5, engine: "⚡ HumanizeAI Pro", burst: true, frag: true, delay: 3 },
    essay: { wpm: 62, acc: 97.0, engine: "🎓 Academic Master", burst: true, frag: true, delay: 4 },
    coder: { wpm: 95, acc: 99.2, engine: "⚡ HumanizeAI Pro", burst: false, frag: false, delay: 2 },
    turbo: { wpm: 120, acc: 91.0, engine: "⚡ HumanizeAI Pro", burst: true, frag: false, delay: 1 },
    stealth: { wpm: 68, acc: 96.5, engine: "👻 GhostWriter Ultra", burst: true, frag: true, delay: 4 }
  };

  function applyPreset(name) {
    const p = PRESET_CONFIGS[name];
    if (!p) return;
    wpmSlider.value = p.wpm;
    wpmHugeDisplay.textContent = p.wpm;
    
    autoAccCheck.checked = false;
    accSlider.disabled = false;
    accSlider.value = p.acc;
    accValue.textContent = `${p.acc.toFixed(1)}%`;

    delaySlider.value = p.delay;
    delayValue.textContent = `${p.delay}s`;

    engineSelect.value = p.engine;
    pgEngineSelect.value = p.engine;

    burstCheck.checked = p.burst;
    fragmentsCheck.checked = p.frag;

    logTerminal(`[Preset] Applied ${name}: ${p.wpm} WPM • ${p.acc}% Acc • ${p.engine.split(' ').slice(-1)[0]}`);
  }

  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyPreset(btn.dataset.preset);
    });
  });

  // Sliders
  wpmSlider.addEventListener('input', (e) => {
    const val = parseInt(e.target.value, 10);
    wpmHugeDisplay.textContent = val;
    if (autoAccCheck.checked) {
      let calcAcc = 98.8 - (val - 30) * 0.055;
      calcAcc = Math.max(88.0, Math.min(99.4, calcAcc));
      accSlider.value = calcAcc.toFixed(1);
      accValue.textContent = `${calcAcc.toFixed(1)}%`;
    }
    updateAnalytics();
  });

  accSlider.addEventListener('input', (e) => {
    accValue.textContent = `${parseFloat(e.target.value).toFixed(1)}%`;
  });

  autoAccCheck.addEventListener('change', () => {
    accSlider.disabled = autoAccCheck.checked;
    if (autoAccCheck.checked) {
      const val = parseInt(wpmSlider.value, 10);
      let calcAcc = 98.8 - (val - 30) * 0.055;
      calcAcc = Math.max(88.0, Math.min(99.4, calcAcc));
      accSlider.value = calcAcc.toFixed(1);
      accValue.textContent = `${calcAcc.toFixed(1)}%`;
    }
  });

  delaySlider.addEventListener('input', (e) => {
    delayValue.textContent = `${e.target.value}s`;
  });

  engineSelect.addEventListener('change', () => {
    pgEngineSelect.value = engineSelect.value;
  });

  pgEngineSelect.addEventListener('change', () => {
    engineSelect.value = pgEngineSelect.value;
  });

  // Modals
  playgroundBtn.addEventListener('click', () => {
    pgInputText.value = currentEssay;
    updateAnalytics();
    playgroundModal.classList.add('open');
  });

  closePlaygroundBtn.addEventListener('click', () => {
    playgroundModal.classList.remove('open');
  });

  settingsBtn.addEventListener('click', () => {
    settingsModal.classList.add('open');
  });

  closeSettingsBtn.addEventListener('click', () => {
    settingsModal.classList.remove('open');
  });

  // -------------------------------------------------------------
  // Real-time Canvas Waveform
  // -------------------------------------------------------------
  function drawCanvas() {
    const w = analogCanvas.width;
    const h = analogCanvas.height;
    ctx.clearRect(0, 0, w, h);

    // Grid
    ctx.strokeStyle = '#141A26';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 30) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 20) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Baseline
    const avg = flightLatencies.reduce((a, b) => a + b, 0) / flightLatencies.length;
    const normAvgY = h - Math.min(h - 6, Math.max(6, (avg / 420) * h));
    ctx.strokeStyle = 'rgba(6, 182, 212, 0.2)';
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(0, normAvgY);
    ctx.lineTo(w, normAvgY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Line
    const step = w / (flightLatencies.length - 1);
    ctx.beginPath();
    flightLatencies.forEach((val, idx) => {
      const clamped = Math.min(420, Math.max(20, val));
      const y = h - (clamped / 420) * (h - 12) - 6;
      const x = idx * step;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, '#0E7490');
    grad.addColorStop(0.7, '#06B6D4');
    grad.addColorStop(1, '#10B981');

    ctx.strokeStyle = grad;
    ctx.lineWidth = 2;
    ctx.stroke();

    const lastVal = flightLatencies[flightLatencies.length - 1];
    const lastY = h - (Math.min(420, Math.max(20, lastVal)) / 420) * (h - 12) - 6;
    ctx.fillStyle = '#10B981';
    ctx.beginPath();
    ctx.arc(w - 2, lastY, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }
  drawCanvas();

  // -------------------------------------------------------------
  // -------------------------------------------------------------
  // Dynamic Typing Engine Bridge Resolver
  // Routes OS keystrokes to the local laptop daemon (port 5050 or Cloudflare Tunnel)
  // -------------------------------------------------------------
  let TYPING_API_BASE = '';
  let bridgeResolved = false;

  async function resolveTypingBackend() {
    const host = window.location.hostname;
    // Direct local access or Cloudflare tunnel access: relative path is already the local daemon!
    if (host === 'localhost' || host === '127.0.0.1' || host.includes('trycloudflare.com')) {
      TYPING_API_BASE = '';
      bridgeResolved = true;
      logTerminal(`[Bridge] 💻 Modo Local Activo: Conexión directa a hardware de tipeo.`);
      return;
    }

    // Running on Vercel or custom public domain:
    logTerminal(`[Bridge] 🌐 Modo Nube: Enlazando con el motor de tipeo en tu laptop...`);

    // Probe order:
    // 1. Direct local port 5050 (fastest)
    // 2. Loopback localhost:5050
    // 3. Cloudflare Tunnel (HTTPS -> HTTPS, no mixed-content or private network blocks)
    const candidates = [
      'http://127.0.0.1:5050',
      'http://localhost:5050',
      'https://previous-developers-responding-warrant.trycloudflare.com'
    ];

    for (const base of candidates) {
      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 1200);
        const res = await fetch(`${base}/api/health`, {
          signal: ctrl.signal,
          mode: 'cors'
        });
        clearTimeout(tid);
        if (res.ok) {
          TYPING_API_BASE = base;
          bridgeResolved = true;
          logTerminal(`[Bridge] ⚡ Conectado con éxito a tu laptop (${base}).`);
          logTerminal(`[Bridge] ✅ ¡Tipeo en Google Docs / Word listo para usar!`);
          return;
        }
      } catch (err) {}
    }

    // Default to tunnel URL which is reachable via HTTPS
    TYPING_API_BASE = 'https://previous-developers-responding-warrant.trycloudflare.com';
    bridgeResolved = true;
    logTerminal(`[Bridge] 🛡️ Enrutado mediante Túnel Seguro Cloudflare.`);
  }

  resolveTypingBackend();

  // -------------------------------------------------------------
  // Real OS System Typing Trigger & Telemetry Synchronization
  // -------------------------------------------------------------
  async function startSystemTyping() {
    if (!currentEssay || !currentEssay.trim()) {
      alert('Por favor pega o carga un ensayo antes de iniciar.');
      return;
    }

    if (!bridgeResolved) {
      await resolveTypingBackend();
    }

    const payload = {
      text: currentEssay,
      wpm: parseInt(wpmSlider.value, 10),
      accuracy: parseFloat(accSlider.value),
      start_delay: parseInt(delaySlider.value, 10),
      use_burst: burstCheck.checked,
      use_fragments: fragmentsCheck.checked,
      use_shift_enter: setShiftEnter ? setShiftEnter.checked : false,
      remove_asterisks: setStripMarkdown ? setStripMarkdown.checked : true,
      remove_emojis: setStripEmojis ? setStripEmojis.checked : false
    };

    startBtn.disabled = true;
    startBtn.innerHTML = '<span>TYPING...</span>';
    pauseBtn.disabled = false;
    stopBtn.disabled = false;
    isTyping = true;

    try {
      const resp = await fetch(`${TYPING_API_BASE}/api/type/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      logTerminal(`[Control] ▶ ${data.message}`);
      
      // Begin fast polling for live telemetry from backend typing worker
      if (statusPollTimer) clearInterval(statusPollTimer);
      statusPollTimer = setInterval(pollTypingStatus, 90);
    } catch (err) {
      logTerminal(`[Error] Fallo al iniciar tipeo: ${err.message}`);
      resetTypingUi();
    }
  }

  async function pollTypingStatus() {
    try {
      const resp = await fetch(`${TYPING_API_BASE}/api/type/status`);
      const data = await resp.json();

      if (data.status) {
        statusLabel.textContent = data.status;
        statusLabel.style.color = data.is_typing ? (data.is_paused ? 'var(--c-orange)' : 'var(--c-green)') : 'var(--c-green)';
      }
      if (data.telemetry) telemetryLabel.textContent = data.telemetry;
      if (data.wpm_measured) wpmHugeDisplay.textContent = data.wpm_measured;
      if (data.last_key_ms !== undefined) valLastKey.textContent = `${data.last_key_ms} ms`;
      if (data.keystrokes !== undefined) valKeystrokes.textContent = data.keystrokes;
      if (data.typos_fixed !== undefined) valTypos.textContent = data.typos_fixed;
      if (data.recent_latencies && data.recent_latencies.length > 0) {
        flightLatencies = data.recent_latencies;
        drawCanvas();
      }
      if (data.new_terminal_logs && data.new_terminal_logs.length > 0) {
        data.new_terminal_logs.forEach(msg => logTerminal(msg));
      }

      if (data.is_typing) {
        pauseBtn.disabled = false;
        stopBtn.disabled = false;
        pauseBtn.innerHTML = data.is_paused ? '<span>▶ RESUME (F8)</span>' : '<span>⏸  PAUSE (F8)</span>';
      } else {
        resetTypingUi();
      }
    } catch (e) {
      // ignore transient poll failure
    }
  }

  function resetTypingUi() {
    isTyping = false;
    startBtn.disabled = false;
    startBtn.innerHTML = '<span>▶ START (F9)</span>';
    pauseBtn.disabled = true;
    stopBtn.disabled = true;
    if (statusPollTimer) {
      clearInterval(statusPollTimer);
      statusPollTimer = null;
    }
  }

  async function togglePause() {
    try {
      const resp = await fetch(`${TYPING_API_BASE}/api/type/pause`, { method: 'POST' });
      const data = await resp.json();
      logTerminal(`[Control] ${data.status === 'paused' ? '⏸ Pausado' : '▶ Reanudado'}`);
    } catch (e) {}
  }

  async function stopTyping() {
    try {
      await fetch(`${TYPING_API_BASE}/api/type/stop`, { method: 'POST' });
      logTerminal(`[Control] ⏹ Tipeo detenido por el usuario.`);
      resetTypingUi();
    } catch (e) {}
  }

  startBtn.addEventListener('click', startSystemTyping);
  pauseBtn.addEventListener('click', togglePause);
  stopBtn.addEventListener('click', stopTyping);

  // Global hotkeys (F8 pause, F9 start/stop, F10 abort)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F9' || (e.ctrlKey && e.key === 'Enter')) {
      e.preventDefault();
      if (!isTyping) startSystemTyping();
      else stopTyping();
    } else if (e.key === 'F8') {
      e.preventDefault();
      togglePause();
    } else if (e.key === 'F10' || e.key === 'Escape') {
      if (isTyping) {
        e.preventDefault();
        stopTyping();
      }
    }
  });

  // -------------------------------------------------------------
  // Clipboard Essay Loader
  // -------------------------------------------------------------
  pasteEssayBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && text.trim()) {
        currentEssay = text.trim();
        const words = currentEssay.split(/\s+/).length;
        statusLabel.textContent = `● Ensayo listo: ${words} palabras`;
        statusLabel.style.color = "var(--c-green)";
        telemetryLabel.textContent = `> essay ready: ${words} words in clipboard`;
        logTerminal(`[Essay] ✅ Ensayo detectado: ${words} palabras (${currentEssay.length} caracteres).`);
        logTerminal(`[Essay] Presiona ▶ START (F9) para escribirlo, o 🧪 PLAYGROUND para inspeccionarlo.`);
      } else {
        logTerminal("[Essay] ⚠️ El portapapeles está vacío. Copia tu texto primero (Ctrl+C).");
        statusLabel.textContent = "● Portapapeles vacío (Copia texto)";
        statusLabel.style.color = "var(--c-orange)";
      }
    } catch (e) {
      const fallback = prompt("Pega aquí tu ensayo (Ctrl+V):", currentEssay);
      if (fallback) {
        currentEssay = fallback.trim();
        const words = currentEssay.split(/\s+/).length;
        statusLabel.textContent = `● Ensayo listo: ${words} palabras`;
        statusLabel.style.color = "var(--c-green)";
        telemetryLabel.textContent = `> essay ready: ${words} words in clipboard`;
        logTerminal(`[Essay] ✅ Ensayo cargado: ${words} palabras.`);
      }
    }
  });

  // -------------------------------------------------------------
  // Playground Functions
  // -------------------------------------------------------------
  function isSpanish(text) {
    const sample = text.toLowerCase();
    const esWords = ['de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'se', 'del', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este', 'sí', 'porque', 'esta', 'son', 'entre', 'está', 'cuando', 'muy', 'sin', 'sobre', 'ser', 'tiene', 'también', 'me', 'hasta', 'hay', 'donde', 'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'sea', 'poco', 'ella', 'estar', 'haber', 'estas', 'estaba', 'estamos', 'algunas', 'algo', 'nosotros'];
    const words = sample.split(/\s+/);
    let count = 0;
    words.forEach(w => { if (esWords.includes(w)) count++; });
    return (count / Math.max(1, words.length)) > 0.08 || /[áéíóúñ¿¡]/.test(sample);
  }

  function updateAnalytics() {
    const in_t = pgInputText.value.trim();
    const out_t = pgOutputText.value.trim();

    const in_words = in_t ? in_t.match(/\b\w+\b/g) || [] : [];
    const out_words = out_t ? out_t.match(/\b\w+\b/g) || [] : [];

    cardInWords.textContent = `${in_words.length} words • ${in_t.length} chars`;
    cardOutWords.textContent = `${out_words.length} words • ${out_t.length} chars`;

    if (in_words.length > 0 && out_words.length > 0) {
      let diffCount = Math.abs(out_words.length - in_words.length);
      const minLen = Math.min(in_words.length, out_words.length);
      for (let i = 0; i < minLen; i++) {
        if (in_words[i].toLowerCase() !== out_words[i].toLowerCase()) diffCount++;
      }
      cardDiff.textContent = `${diffCount} words modified`;
    } else if (!in_words.length && !out_words.length) {
      cardDiff.textContent = "0 words modified";
    } else {
      cardDiff.textContent = `${Math.abs(out_words.length - in_words.length)} words diff`;
    }

    if (in_t || out_t) {
      cardLang.textContent = isSpanish(in_t || out_t) ? "🇪🇸 Español" : "🇺🇸 English";
    } else {
      cardLang.textContent = "—";
    }

    const currentWpm = Math.max(20, parseInt(wpmSlider.value, 10));
    const wordCount = out_words.length > 0 ? out_words.length : in_words.length;
    const estSeconds = wordCount > 0 ? Math.floor((wordCount / currentWpm) * 60) : 0;
    const mins = Math.floor(estSeconds / 60);
    const secs = String(estSeconds % 60).padStart(2, '0');
    cardTiming.textContent = `${mins}m ${secs}s @ ${currentWpm} WPM`;
  }

  pgInputText.addEventListener('input', updateAnalytics);

  pgSampleEnBtn.addEventListener('click', () => {
    pgInputText.value = SAMPLE_TEXT_EN;
    updateAnalytics();
    executePlaygroundHumanize();
  });

  pgSampleEsBtn.addEventListener('click', () => {
    pgInputText.value = SAMPLE_TEXT_ES;
    updateAnalytics();
    executePlaygroundHumanize();
  });

  pgPasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && text.trim()) {
        pgInputText.value = text;
        updateAnalytics();
        executePlaygroundHumanize();
        logTerminal(`[Playground] ✅ Pegado: ${text.trim().split(/\s+/).length} palabras (${text.length} caracteres).`);
      }
    } catch (e) {
      const fallback = prompt("Pega aquí tu ensayo (Ctrl+V):", pgInputText.value);
      if (fallback) {
        pgInputText.value = fallback;
        updateAnalytics();
        executePlaygroundHumanize();
      }
    }
  });

  pgClearBtn.addEventListener('click', () => {
    pgInputText.value = '';
    pgOutputText.value = '';
    updateAnalytics();
  });

  async function executePlaygroundHumanize() {
    const raw = pgInputText.value.trim();
    if (!raw) {
      updateAnalytics();
      return;
    }

    pgRunBtn.disabled = true;
    pgRunBtn.textContent = '⏳ HUMANIZING...';
    logTerminal(`[Playground] ⚡ Ejecutando humanizador con motor "${pgEngineSelect.value}"...`);

    try {
      const resp = await fetch('/api/humanize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: raw,
          engine: pgEngineSelect.value,
          casual_mode: pgCasualCheck.checked
        })
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Humanization failed');
      }

      const data = await resp.json();
      pgOutputText.value = data.humanized_text;
      updateAnalytics();

      const words = data.humanized_text.split(/\s+/).length;
      logTerminal(`[Playground] ✅ Humanizado exitoso: ${words} palabras listas.`);
    } catch (err) {
      logTerminal(`[Playground Error] ${err.message}`);
      alert(`Error al humanizar: ${err.message}`);
    } finally {
      pgRunBtn.disabled = false;
      pgRunBtn.textContent = '⚡ RUN HUMANIZER';
    }
  }

  pgRunBtn.addEventListener('click', executePlaygroundHumanize);

  if (pgCleanMarkdownBtn) {
    pgCleanMarkdownBtn.addEventListener('click', async () => {
      const targetArea = pgOutputText.value.trim() ? pgOutputText : pgInputText;
      const text = targetArea.value;
      if (!text || !text.trim()) {
        alert('Escribe o pega texto primero para limpiar el Markdown.');
        return;
      }
      pgCleanMarkdownBtn.disabled = true;
      pgCleanMarkdownBtn.textContent = '🧹 CLEANING...';
      try {
        const resp = await fetch('/api/clean-markdown', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text })
        });
        const data = await resp.json();
        targetArea.value = data.cleaned_text;
        updateAnalytics();
        pgCleanMarkdownBtn.textContent = '✓ CLEANED!';
        logTerminal(`[Playground] 🧹 Markdown depurado con éxito (-${data.chars_diff} caracteres residuales eliminados).`);
        setTimeout(() => { pgCleanMarkdownBtn.textContent = '🧹 CLEAN MARKDOWN'; }, 1500);
      } catch (e) {
        logTerminal(`[Error] Fallo al limpiar Markdown: ${e.message}`);
        pgCleanMarkdownBtn.textContent = '🧹 CLEAN MARKDOWN';
      } finally {
        pgCleanMarkdownBtn.disabled = false;
      }
    });
  }

  pgCopyBtn.addEventListener('click', () => {
    const out = pgOutputText.value.trim() || pgInputText.value.trim();
    if (out) {
      navigator.clipboard.writeText(out);
      pgCopyBtn.textContent = "✓ COPIED!";
      setTimeout(() => { pgCopyBtn.textContent = "📋 COPY"; }, 1500);
    }
  });

  pgUseAutotyperBtn.addEventListener('click', () => {
    const out = pgOutputText.value.trim() || pgInputText.value.trim();
    if (out) {
      currentEssay = out;
      navigator.clipboard.writeText(out);
      pgUseAutotyperBtn.textContent = "✓ READY!";
      const words = currentEssay.split(/\s+/).length;
      statusLabel.textContent = `● Ensayo listo: ${words} palabras`;
      statusLabel.style.color = "var(--c-green)";
      telemetryLabel.textContent = `> essay ready: ${words} words restored`;
      logTerminal(`[Playground] 🚀 Cargadas ${words} palabras. Listo para escribir con START (F9)!`);
      setTimeout(() => {
        pgUseAutotyperBtn.textContent = "🚀 USE IN AUTOTYPER";
        playgroundModal.classList.remove('open');
      }, 700);
    }
  });

  // -------------------------------------------------------------
  // Universal Bookmarklet
  // -------------------------------------------------------------
  function setupBookmarklet() {
    const code = `javascript:(function(){
      if(document.getElementById('hn-floating-widget')){
        document.getElementById('hn-floating-widget').remove();
        return;
      }
      var w=document.createElement('div');
      w.id='hn-floating-widget';
      w.style.position='fixed';
      w.style.bottom='20px';
      w.style.right='20px';
      w.style.zIndex='99999999';
      w.style.width='330px';
      w.style.background='#151922';
      w.style.color='#F1F5F9';
      w.style.border='1px solid #1E2433';
      w.style.borderRadius='6px';
      w.style.boxShadow='0 12px 40px rgba(0,0,0,0.8)';
      w.style.fontFamily='Consolas, monospace';
      w.style.padding='12px';
      w.style.boxSizing='border-box';
      
      w.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
        +'<strong style="color:#06B6D4;font-size:12px;">HumanNature v3.6.0</strong>'
        +'<button id="hn-close" style="background:none;border:none;color:#94A3B8;cursor:pointer;font-size:14px;">×</button>'
        +'</div>'
        +'<textarea id="hn-text" placeholder="Pega tu texto aquí..." style="width:100%;height:75px;background:#0F121A;color:#FFF;border:1px solid #1E2433;border-radius:3px;padding:6px;font-size:11px;box-sizing:border-box;resize:none;margin-bottom:8px;"></textarea>'
        +'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:11px;">'
        +'<span style="color:#94A3B8;">Velocidad:</span>'
        +'<input type="range" id="hn-wpm" min="30" max="140" value="72" style="width:130px;">'
        +'<span id="hn-wpm-val" style="color:#06B6D4;font-weight:bold;">72 WPM</span>'
        +'</div>'
        +'<button id="hn-start" style="width:100%;background:#0E7490;color:#FFF;border:none;border-radius:3px;padding:7px;font-weight:bold;cursor:pointer;font-size:11px;">▶ START TYPING (3s DELAY)</button>'
        +'<div id="hn-status" style="font-size:9px;color:#94A3B8;margin-top:6px;text-align:center;">Haz clic en el documento donde escribir.</div>';
      
      document.body.appendChild(w);
      
      var closeBtn=document.getElementById('hn-close');
      closeBtn.onclick=function(){ w.remove(); };
      
      var wpmSlider=document.getElementById('hn-wpm');
      var wpmVal=document.getElementById('hn-wpm-val');
      wpmSlider.oninput=function(){ wpmVal.innerText=wpmSlider.value+' WPM'; };
      
      var startBtn=document.getElementById('hn-start');
      var statusDiv=document.getElementById('hn-status');
      
      startBtn.onclick=function(){
        var text=document.getElementById('hn-text').value;
        if(!text){ alert('Pega texto en el cuadro de HumanNature.'); return; }
        var wpm=parseInt(wpmSlider.value);
        var baseDelay=(60/(wpm*5))*1000;
        var count=3;
        startBtn.disabled=true;
        var timer=setInterval(function(){
          statusDiv.innerText='Escribiendo en '+count+'s... Haz clic en tu documento!';
          count--;
          if(count<0){
            clearInterval(timer);
            statusDiv.innerText='Escribiendo con ritmo humano...';
            var idx=0;
            function typeChar(){
              if(idx>=text.length){
                statusDiv.innerText='¡Completado 100%! Caracteres: '+text.length;
                startBtn.disabled=false;
                return;
              }
              var c=text[idx];
              document.execCommand('insertText', false, c);
              idx++;
              var jitter=baseDelay*(0.72+Math.random()*0.56);
              if(['.','!','?'].includes(c)) jitter+=250;
              setTimeout(typeChar, jitter);
            }
            typeChar();
          }
        }, 1000);
      };
    })();`;

    pgBookmarkletLink.href = code.replace(/\s+/g, ' ');
  }
  setupBookmarklet();

  logTerminal(`[Init] Todos los subsistemas conectados: Pro, Academic, GhostWriter, Natural Flow.`);
});
