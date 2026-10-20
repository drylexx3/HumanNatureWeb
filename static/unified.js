/**
 * HumanNature × paste, write. — Unified Master Script
 * Seamless single-app experience combining the AI Humanizer Studio and Universal Typist
 */

document.addEventListener('DOMContentLoaded', () => {

  // =============================================================
  // 1. MASTER TAB NAVIGATION SYSTEM
  // =============================================================
  const navTabs = document.querySelectorAll('.master-nav-tabs .nav-tab-btn');
  const tabPanels = document.querySelectorAll('.tab-content-area .tab-panel');

  function switchTab(tabId) {
    navTabs.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    tabPanels.forEach(panel => {
      panel.classList.toggle('active', panel.id === `tab-${tabId}`);
    });

    // Update location hash without jumping
    history.replaceState(null, null, `#${tabId}`);

    if (tabId === 'pastewrite') {
      drawWaveform();
      updatePwStats();
    } else if (tabId === 'humanizer' || tabId === 'playground') {
      updateHnAnalytics();
    }
  }

  navTabs.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  // Check initial hash or route
  const currentPath = window.location.pathname;
  const currentHash = window.location.hash.replace('#', '');
  if (currentHash && document.getElementById(`tab-${currentHash}`)) {
    switchTab(currentHash);
  } else if (currentPath.includes('paste-write')) {
    switchTab('pastewrite');
  } else {
    switchTab('pastewrite'); // Default directly to the versatile typist
  }

  // Live Clock
  const liveClock = document.getElementById('liveClock');
  function updateClock() {
    const now = new Date();
    let h = now.getHours();
    const m = String(now.getMinutes()).padStart(2, '0');
    const ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    liveClock.textContent = `${String(h).padStart(2, '0')}:${m} ${ampm}`;
  }
  setInterval(updateClock, 1000);
  updateClock();

  // =============================================================
  // 2. DYNAMIC HARDWARE BRIDGE RESOLVER
  // =============================================================
  const bridgeStatusBadge = document.getElementById('bridgeStatusBadge');
  let TYPING_API_BASE = '';
  let bridgeResolved = false;

  async function resolveTypingBackend() {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1' || host.includes('trycloudflare.com')) {
      TYPING_API_BASE = '';
      bridgeResolved = true;
      bridgeStatusBadge.textContent = '● LOCAL NATIVE';
      bridgeStatusBadge.style.color = 'var(--c-green)';
      logPwTerm('[Bridge] Modo Local Directo conectado al hardware de tu laptop.');
      return;
    }

    bridgeStatusBadge.textContent = '⏳ ENLAZANDO...';
    bridgeStatusBadge.style.color = 'var(--c-amber)';
    logPwTerm(`[Bridge] Conectando desde la nube (${host}) a tu laptop...`);

    const candidates = [
      'http://127.0.0.1:5050',
      'http://localhost:5050'
    ];

    try {
      const tunRes = await fetch('/api/tunnel');
      if (tunRes.ok) {
        const tunData = await tunRes.json();
        if (tunData.tunnel_url) candidates.push(tunData.tunnel_url);
      }
    } catch (e) {}

    candidates.push('https://feed-dee-spoke-resist.trycloudflare.com');

    for (const base of candidates) {
      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 1300);
        const res = await fetch(`${base}/api/health`, { signal: ctrl.signal, mode: 'cors' });
        clearTimeout(tid);
        if (res.ok) {
          TYPING_API_BASE = base;
          bridgeResolved = true;
          bridgeStatusBadge.textContent = '● BRIDGE ACTIVO';
          bridgeStatusBadge.style.color = 'var(--c-cyan)';
          logPwTerm(`[Bridge] Enlace establecido con éxito (${base}). Tipeo físico activado.`);
          return;
        }
      } catch (err) {}
    }

    TYPING_API_BASE = 'https://feed-dee-spoke-resist.trycloudflare.com';
    bridgeResolved = true;
    bridgeStatusBadge.textContent = '🛡️ TUNNEL BRIDGE';
    bridgeStatusBadge.style.color = 'var(--c-green)';
    logPwTerm(`[Bridge] Conectado a través del túnel seguro Cloudflare.`);
  }

  resolveTypingBackend();

  // =============================================================
  // 3. TAB 1: PASTE, WRITE. (UNIVERSAL TYPIST) LOGIC
  // =============================================================
  const pwText = document.getElementById('pwTextInput');
  const pwPasteBtn = document.getElementById('pwPasteBtn');
  const pwClearBtn = document.getElementById('pwClearBtn');
  const pwCharCount = document.getElementById('pwCharCount');
  const pwWordCount = document.getElementById('pwWordCount');
  const pwLineCount = document.getElementById('pwLineCount');
  const pwEstimateTime = document.getElementById('pwEstimateTime');

  const directiveChips = document.querySelectorAll('.pw-directive-chips-row .pw-chip-dir');
  const customInstruction = document.getElementById('pwCustomInstruction');
  const applyInstructionBtn = document.getElementById('pwApplyInstructionBtn');

  const modeButtons = document.querySelectorAll('.pw-btn-mode');
  const wpmSlider = document.getElementById('pwWpmSlider');
  const wpmDisplay = document.getElementById('pwWpmDisplay');
  const accSlider = document.getElementById('pwAccSlider');
  const accDisplay = document.getElementById('pwAccDisplay');
  const delaySlider = document.getElementById('pwDelaySlider');
  const delayDisplay = document.getElementById('pwDelayDisplay');

  const shiftEnterCheck = document.getElementById('pwShiftEnterCheck');
  const stripMarkdownCheck = document.getElementById('pwStripMarkdownCheck');

  const pwStartBtn = document.getElementById('pwStartBtn');
  const pwPauseBtn = document.getElementById('pwPauseBtn');
  const pwStopBtn = document.getElementById('pwStopBtn');

  const statusLabel = document.getElementById('pwStatusLabel');
  const progressPercent = document.getElementById('pwProgressPercent');
  const progressFill = document.getElementById('pwProgressFill');
  const telemetrySub = document.getElementById('pwTelemetrySub');
  const liveWpmLabel = document.getElementById('pwLiveWpmLabel');
  const analogCanvas = document.getElementById('pwAnalogCanvas');
  const pwTerminal = document.getElementById('pwTerminal');

  const ctx = analogCanvas.getContext('2d');
  let flightLatencies = new Array(50).fill(160);
  let statusPollTimer = null;
  let isTyping = false;
  let currentMode = 'human';
  let currentDirective = 'verbatim';

  function logPwTerm(msg) {
    const line = document.createElement('div');
    line.className = 'pw-term-line';
    line.textContent = `> ${msg}`;
    pwTerminal.appendChild(line);
    pwTerminal.scrollTop = pwTerminal.scrollHeight;
    while (pwTerminal.children.length > 20) {
      pwTerminal.removeChild(pwTerminal.firstChild);
    }
  }

  function updatePwStats() {
    const raw = pwText.value;
    const chars = raw.length;
    const words = raw.trim() ? raw.trim().split(/\s+/).length : 0;
    const lines = raw.length ? raw.split('\n').length : 0;

    pwCharCount.textContent = `${chars.toLocaleString()} caracteres`;
    pwWordCount.textContent = `${words.toLocaleString()} palabras`;
    pwLineCount.textContent = `${lines} ${lines === 1 ? 'línea' : 'líneas'}`;

    const currentWpm = parseInt(wpmSlider.value, 10) || 72;
    if (words === 0) {
      pwEstimateTime.textContent = `⏱ ~0s @ ${currentWpm} WPM`;
    } else {
      const totalSecs = Math.max(1, Math.round((words / currentWpm) * 60));
      if (totalSecs < 60) {
        pwEstimateTime.textContent = `⏱ ~${totalSecs}s @ ${currentWpm} WPM`;
      } else {
        const mins = Math.floor(totalSecs / 60);
        const remSecs = totalSecs % 60;
        pwEstimateTime.textContent = `⏱ ~${mins}m ${remSecs}s @ ${currentWpm} WPM`;
      }
    }
  }

  pwText.addEventListener('input', updatePwStats);

  // Clipboard Paste & Clear
  pwPasteBtn.addEventListener('click', async () => {
    try {
      const clip = await navigator.clipboard.readText();
      if (clip && clip.trim()) {
        pwText.value = clip;
        updatePwStats();
        logPwTerm(`[Portapapeles] ✅ Pegado: ${clip.length} caracteres detectados.`);
        pwPasteBtn.textContent = '✓ Pegado!';
        setTimeout(() => { pwPasteBtn.textContent = '📋 Pegar (Ctrl+V)'; }, 1500);
      } else {
        alert('El portapapeles está vacío. Copia algo primero (Ctrl+C).');
      }
    } catch (e) {
      const fallback = prompt('Pega tu texto aquí (Ctrl+V):', pwText.value);
      if (fallback) {
        pwText.value = fallback;
        updatePwStats();
      }
    }
  });

  pwClearBtn.addEventListener('click', () => {
    pwText.value = '';
    updatePwStats();
    logPwTerm('[Editor] Lienzo limpiado.');
  });

  // Sample Buttons in Tab 1
  document.getElementById('sampleEssayBtn').addEventListener('click', () => {
    pwText.value = 
      "La inteligencia artificial contemporánea representa una de las transformaciones técnicas más profundas de nuestro tiempo.\n\n" +
      "A diferencia de las herramientas informáticas previas, estos sistemas no solo procesan datos de forma algorítmica, sino que modulan patrones de lenguaje y razonamiento.\n\n" +
      "Es fundamental analizar el impacto que este paradigma genera en la educación superior y en la producción académica moderna.";
    updatePwStats();
    setPwMode('human');
    setPwDirective('formal');
    logPwTerm('[Muestra] Cargado: Ensayo Académico.');
  });

  document.getElementById('sampleCodeBtn').addEventListener('click', () => {
    pwText.value = 
      "def calculate_typing_flight(wpm: int, accuracy: float) -> dict:\n" +
      "    cpm = max(1, wpm * 5)\n" +
      "    base_ms = (60.0 / cpm) * 1000.0\n" +
      "    jitter_range = (base_ms * 0.75, base_ms * 1.25)\n" +
      "    return {\n" +
      "        'target_wpm': wpm,\n" +
      "        'base_delay_ms': round(base_ms, 2),\n" +
      "        'jitter': jitter_range,\n" +
      "        'mode': 'native_keystroke'\n" +
      "    }\n\n" +
      "if __name__ == '__main__':\n" +
      "    print(calculate_typing_flight(72, 96.5))\n";
    updatePwStats();
    setPwMode('code');
    setPwDirective('code');
    logPwTerm('[Muestra] Cargado: Código Python.');
  });

  document.getElementById('sampleChatBtn').addEventListener('click', () => {
    pwText.value = "Hola, ya revisé el reporte y quedó perfecto. En un momento te comparto los últimos ajustes por aquí!";
    updatePwStats();
    shiftEnterCheck.checked = true;
    setPwMode('human');
    setPwDirective('casual');
    logPwTerm('[Muestra] Cargado: Mensaje Chat (Shift+Enter activo).');
  });

  document.getElementById('sampleMarkdownBtn').addEventListener('click', () => {
    pwText.value = 
      "### Introducción al Proyecto\n" +
      "Este documento contiene **información crítica** sobre el lanzamiento:\n" +
      "* Primera etapa: depuración de `código` y validación.\n" +
      "* Segunda etapa: despliegue continuo sin asteriscos ni alertas.\n" +
      "> Nota importante: todo el texto se tipea con ritmo humano.";
    updatePwStats();
    setPwMode('human');
    setPwDirective('stealth');
    logPwTerm('[Muestra] Cargado: Texto con Markdown.');
  });

  // Directives
  function setPwDirective(dir) {
    currentDirective = dir;
    directiveChips.forEach(chip => {
      chip.classList.toggle('active', chip.dataset.directive === dir);
    });

    if (dir === 'code') {
      setPwMode('code');
      stripMarkdownCheck.checked = false;
    } else if (dir === 'verbatim') {
      setPwMode('verbatim');
      stripMarkdownCheck.checked = false;
    } else if (dir === 'stealth' || dir === 'clean_markdown') {
      stripMarkdownCheck.checked = true;
    }
  }

  directiveChips.forEach(chip => {
    chip.addEventListener('click', () => {
      setPwDirective(chip.dataset.directive);
      logPwTerm(`[Directriz] Seleccionada: "${chip.textContent.trim()}".`);
    });
  });

  applyInstructionBtn.addEventListener('click', async () => {
    const raw = pwText.value;
    if (!raw.trim()) {
      alert('Pega o escribe texto primero en el lienzo.');
      return;
    }

    const inst = customInstruction.value.trim() || currentDirective;
    applyInstructionBtn.disabled = true;
    applyInstructionBtn.textContent = '⏳ Aplicando...';
    logPwTerm(`[Instrucción] Aplicando directriz "${inst}" al texto...`);

    try {
      const resp = await fetch('/api/pastewrite/transform', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: raw, instruction: inst })
      });
      const data = await resp.json();
      if (data.success && data.transformed_text) {
        pwText.value = data.transformed_text;
        updatePwStats();
        logPwTerm(`[Instrucción] ✅ Texto transformado (${data.directive}).`);
        applyInstructionBtn.textContent = '✓ Aplicado!';
        setTimeout(() => { applyInstructionBtn.textContent = '⚡ Aplicar al Texto'; }, 1500);
      }
    } catch (e) {
      logPwTerm(`[Error] Fallo al transformar texto: ${e.message}`);
      applyInstructionBtn.textContent = '⚡ Aplicar al Texto';
    } finally {
      applyInstructionBtn.disabled = false;
    }
  });

  // Rhythm Modes
  function setPwMode(mode) {
    currentMode = mode;
    modeButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    if (mode === 'human') {
      wpmSlider.value = 72;
      wpmDisplay.textContent = '72 WPM';
      accSlider.value = 96.5;
      accDisplay.textContent = '96.5%';
      stripMarkdownCheck.checked = true;
    } else if (mode === 'verbatim') {
      wpmSlider.value = 85;
      wpmDisplay.textContent = '85 WPM';
      accSlider.value = 100;
      accDisplay.textContent = '100% (Sin Errores)';
      stripMarkdownCheck.checked = false;
    } else if (mode === 'code') {
      wpmSlider.value = 90;
      wpmDisplay.textContent = '90 WPM';
      accSlider.value = 100;
      accDisplay.textContent = '100% (Exacto)';
      stripMarkdownCheck.checked = false;
    } else if (mode === 'turbo') {
      wpmSlider.value = 150;
      wpmDisplay.textContent = '150 WPM';
      accSlider.value = 100;
      accDisplay.textContent = '100% (Turbo)';
      stripMarkdownCheck.checked = false;
    }
    updatePwStats();
  }

  modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      setPwMode(btn.dataset.mode);
      logPwTerm(`[Modo] Ritmo cambiado a: ${btn.textContent.trim()}.`);
    });
  });

  wpmSlider.addEventListener('input', (e) => {
    wpmDisplay.textContent = `${e.target.value} WPM`;
    updatePwStats();
  });

  accSlider.addEventListener('input', (e) => {
    const v = parseFloat(e.target.value);
    accDisplay.textContent = v >= 100 ? '100% (Sin Errores)' : `${v.toFixed(1)}%`;
  });

  delaySlider.addEventListener('input', (e) => {
    delayDisplay.textContent = `${e.target.value}s`;
  });

  // Canvas Oscilloscope
  function drawWaveform() {
    const w = analogCanvas.width;
    const h = analogCanvas.height;
    ctx.clearRect(0, 0, w, h);

    ctx.strokeStyle = '#141A26';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 30) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }

    ctx.strokeStyle = 'rgba(6, 182, 212, 0.25)';
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.strokeStyle = isTyping ? '#06B6D4' : '#334155';
    ctx.lineWidth = 1.5;

    const slice = w / flightLatencies.length;
    for (let i = 0; i < flightLatencies.length; i++) {
      const val = flightLatencies[i];
      const y = h - Math.min(h - 4, Math.max(4, (val / 380) * h));
      const x = i * slice;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  drawWaveform();

  // Execution
  async function startTyping() {
    const text = pwText.value;
    if (!text || !text.trim()) {
      alert('Pega o escribe algo en el cuadro de texto antes de iniciar.');
      return;
    }

    if (!bridgeResolved) {
      await resolveTypingBackend();
    }

    const payload = {
      text: text,
      wpm: parseInt(wpmSlider.value, 10),
      accuracy: parseFloat(accSlider.value),
      start_delay: parseInt(delaySlider.value, 10),
      use_burst: true,
      use_fragments: currentMode === 'human',
      use_shift_enter: shiftEnterCheck.checked,
      remove_asterisks: stripMarkdownCheck.checked,
      remove_emojis: false,
      mode: currentMode
    };

    pwStartBtn.disabled = true;
    pwStartBtn.innerHTML = '<span>ESCRIBIENDO...</span>';
    pwPauseBtn.disabled = false;
    pwStopBtn.disabled = false;
    isTyping = true;

    try {
      const url = `${TYPING_API_BASE}/api/type/start`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      logPwTerm(`[paste, write.] ▶ ${data.message || 'Proceso de tipeo iniciado.'}`);

      if (statusPollTimer) clearInterval(statusPollTimer);
      statusPollTimer = setInterval(pollTypingStatus, 90);
    } catch (err) {
      logPwTerm(`[Error] Fallo al iniciar: ${err.message}`);
      resetTypingUi();
    }
  }

  async function pollTypingStatus() {
    try {
      const resp = await fetch(`${TYPING_API_BASE}/api/type/status`);
      const data = await resp.json();

      if (data.status) {
        statusLabel.textContent = data.status;
        statusLabel.style.color = data.is_typing ? (data.is_paused ? 'var(--c-amber)' : 'var(--c-green)') : 'var(--c-green)';
      }
      if (data.telemetry) telemetrySub.textContent = data.telemetry;
      if (data.wpm_measured) liveWpmLabel.textContent = `${data.wpm_measured} WPM`;

      if (data.total_chars > 0) {
        const pct = Math.min(100, Math.round((data.current_char / data.total_chars) * 100));
        progressFill.style.width = `${pct}%`;
        progressPercent.textContent = `${pct}% (${data.current_char}/${data.total_chars})`;
      }

      if (data.recent_latencies && data.recent_latencies.length > 0) {
        flightLatencies = data.recent_latencies;
        drawWaveform();
      }

      if (data.new_terminal_logs && data.new_terminal_logs.length > 0) {
        data.new_terminal_logs.forEach(msg => logPwTerm(msg));
      }

      if (data.is_typing) {
        pwPauseBtn.disabled = false;
        pwStopBtn.disabled = false;
        pwPauseBtn.innerHTML = data.is_paused ? '<span>▶ REANUDAR (F8)</span>' : '<span>⏸ PAUSA (F8)</span>';
      } else {
        resetTypingUi();
      }
    } catch (e) {}
  }

  function resetTypingUi() {
    isTyping = false;
    pwStartBtn.disabled = false;
    pwStartBtn.innerHTML = '<span>▶ ESCRIBIR AHORA (F9)</span>';
    pwPauseBtn.disabled = true;
    pwStopBtn.disabled = true;
    if (statusPollTimer) {
      clearInterval(statusPollTimer);
      statusPollTimer = null;
    }
    drawWaveform();
  }

  async function togglePause() {
    try {
      const resp = await fetch(`${TYPING_API_BASE}/api/type/pause`, { method: 'POST' });
      const data = await resp.json();
      logPwTerm(`[Control] ${data.status === 'paused' ? '⏸ En Pausa' : '▶ Reanudado'}`);
    } catch (e) {}
  }

  async function stopTyping() {
    try {
      await fetch(`${TYPING_API_BASE}/api/type/stop`, { method: 'POST' });
      logPwTerm('[Control] ⏹ Tipeo detenido por el usuario.');
      resetTypingUi();
    } catch (e) {}
  }

  pwStartBtn.addEventListener('click', startTyping);
  pwPauseBtn.addEventListener('click', togglePause);
  pwStopBtn.addEventListener('click', stopTyping);

  // =============================================================
  // 4. TAB 2: HUMANIZER AI (ESSAY STUDIO) LOGIC
  // =============================================================
  const hnInputText = document.getElementById('hnInputText');
  const hnOutputText = document.getElementById('hnOutputText');
  const hnEngineSelect = document.getElementById('hnEngineSelect');
  const hnCasualCheck = document.getElementById('hnCasualCheck');
  const hnRunBtn = document.getElementById('hnRunBtn');
  const hnCleanMarkdownBtn = document.getElementById('hnCleanMarkdownBtn');
  const hnCopyBtn = document.getElementById('hnCopyBtn');
  const hnSendToTypistBtn = document.getElementById('hnSendToTypistBtn');

  // Analytics Cards in Tab 3 & 2
  const cardInWords = document.getElementById('cardInWords');
  const cardOutWords = document.getElementById('cardOutWords');
  const cardDiff = document.getElementById('cardDiff');
  const cardLang = document.getElementById('cardLang');
  const cardTiming = document.getElementById('cardTiming');
  const cardPerplexity = document.getElementById('cardPerplexity');
  const buzzwordsCloud = document.getElementById('buzzwordsCloud');

  const SAMPLE_TEXT_ES = 
    "Es crucial destacar que la inteligencia artificial juega un papel fundamental en el vertiginoso mundo actual. " +
    "Asimismo, cabe señalar que para optimizar los procesos debemos sumergirnos en un sinfín de posibilidades " +
    "con el fin de arrojar luz sobre esta materia y desentrañar los misterios de la tecnología.";

  const SAMPLE_TEXT_EN = 
    "Furthermore, it is important to note that utilizing this framework ensures optimal results. " +
    "In order to delve into the realm of artificial intelligence, we must meticulously analyze every aspect " +
    "and take into consideration various factors to revolutionize our workflow.";

  document.getElementById('hnSampleEsBtn').addEventListener('click', () => {
    hnInputText.value = SAMPLE_TEXT_ES;
    updateHnAnalytics();
    executeHumanize();
  });

  document.getElementById('hnSampleEnBtn').addEventListener('click', () => {
    hnInputText.value = SAMPLE_TEXT_EN;
    updateHnAnalytics();
    executeHumanize();
  });

  document.getElementById('hnClearBtn').addEventListener('click', () => {
    hnInputText.value = '';
    hnOutputText.value = '';
    updateHnAnalytics();
  });

  document.getElementById('hnPasteBtn').addEventListener('click', async () => {
    try {
      const clip = await navigator.clipboard.readText();
      if (clip) {
        hnInputText.value = clip;
        updateHnAnalytics();
        executeHumanize();
      }
    } catch (e) {
      const f = prompt('Pega tu texto:', hnInputText.value);
      if (f) {
        hnInputText.value = f;
        updateHnAnalytics();
        executeHumanize();
      }
    }
  });

  // Presets in Humanizer
  const HN_PRESETS = {
    formal: { engine: "🎓 Academic Master", casual: false, wpm: 55 },
    casual: { engine: "🌊 Natural Flow", casual: true, wpm: 85 },
    espanol: { engine: "⚡ HumanizeAI Pro", casual: false, wpm: 72 },
    essay: { engine: "🎓 Academic Master", casual: false, wpm: 65 },
    coder: { engine: "⚡ HumanizeAI Pro", casual: false, wpm: 95 },
    turbo: { engine: "⚡ HumanizeAI Pro", casual: false, wpm: 140 },
    stealth: { engine: "🧠 GhostWriter Ultra", casual: false, wpm: 68 }
  };

  document.querySelectorAll('.hn-preset-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.hn-preset-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const p = HN_PRESETS[btn.dataset.preset];
      if (p) {
        hnEngineSelect.value = p.engine;
        hnCasualCheck.checked = p.casual;
        wpmSlider.value = p.wpm;
        wpmDisplay.textContent = `${p.wpm} WPM`;
        updatePwStats();
      }
    });
  });

  function isSpanish(text) {
    const sample = text.toLowerCase();
    const esWords = ['de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'se', 'del', 'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este', 'sí', 'porque', 'esta', 'son', 'entre', 'está'];
    const words = sample.split(/\s+/);
    let count = 0;
    words.forEach(w => { if (esWords.includes(w)) count++; });
    return (count / Math.max(1, words.length)) > 0.08 || /[áéíóúñ¿¡]/.test(sample);
  }

  function updateHnAnalytics() {
    const in_t = hnInputText.value.trim();
    const out_t = hnOutputText.value.trim();

    const in_words = in_t ? in_t.match(/\b\w+\b/g) || [] : [];
    const out_words = out_t ? out_t.match(/\b\w+\b/g) || [] : [];

    if (cardInWords) cardInWords.textContent = `${in_words.length} palabras • ${in_t.length} chars`;
    if (cardOutWords) cardOutWords.textContent = `${out_words.length} palabras • ${out_t.length} chars`;

    if (cardDiff) {
      if (in_words.length > 0 && out_words.length > 0) {
        let diffCount = Math.abs(out_words.length - in_words.length);
        const minLen = Math.min(in_words.length, out_words.length);
        for (let i = 0; i < minLen; i++) {
          if (in_words[i].toLowerCase() !== out_words[i].toLowerCase()) diffCount++;
        }
        cardDiff.textContent = `${diffCount} palabras modificadas`;
      } else {
        cardDiff.textContent = "0 modificadas";
      }
    }

    if (cardLang) {
      cardLang.textContent = (in_t || out_t) ? (isSpanish(in_t || out_t) ? "🇪🇸 Español" : "🇺🇸 English") : "—";
    }

    if (cardTiming) {
      const curWpm = parseInt(wpmSlider.value, 10) || 72;
      const count = out_words.length || in_words.length;
      const estSecs = count > 0 ? Math.floor((count / curWpm) * 60) : 0;
      cardTiming.textContent = `${Math.floor(estSecs / 60)}m ${String(estSecs % 60).padStart(2, '0')}s @ ${curWpm} WPM`;
    }
  }

  hnInputText.addEventListener('input', updateHnAnalytics);
  hnOutputText.addEventListener('input', updateHnAnalytics);

  async function executeHumanize() {
    const raw = hnInputText.value.trim();
    if (!raw) return;

    hnRunBtn.disabled = true;
    hnRunBtn.textContent = '⏳ HUMANIZANDO...';

    try {
      const resp = await fetch('/api/humanize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: raw,
          engine: hnEngineSelect.value,
          casual_mode: hnCasualCheck.checked
        })
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Fallo al humanizar');
      }

      const data = await resp.json();
      hnOutputText.value = data.humanized_text;
      updateHnAnalytics();

      if (data.analysis_after && cardPerplexity) {
        cardPerplexity.textContent = `${data.analysis_after.verdict} (${data.analysis_after.ai_probability}% AI)`;
      }

      if (data.analysis_before && data.analysis_before.buzzwords_found && buzzwordsCloud) {
        buzzwordsCloud.innerHTML = '';
        if (data.analysis_before.buzzwords_found.length === 0) {
          buzzwordsCloud.innerHTML = '<span style="font-size:10px;color:var(--c-green);">✓ Cero palabras cliché detectadas.</span>';
        } else {
          data.analysis_before.buzzwords_found.forEach(bw => {
            const tag = document.createElement('span');
            tag.className = 'pg-buzz-tag';
            tag.textContent = bw;
            buzzwordsCloud.appendChild(tag);
          });
        }
      }
    } catch (err) {
      alert(`Error al humanizar: ${err.message}`);
    } finally {
      hnRunBtn.disabled = false;
      hnRunBtn.textContent = '⚡ RUN HUMANIZER';
    }
  }

  hnRunBtn.addEventListener('click', executeHumanize);

  hnCleanMarkdownBtn.addEventListener('click', async () => {
    const target = hnOutputText.value.trim() ? hnOutputText : hnInputText;
    const txt = target.value;
    if (!txt.trim()) return;

    hnCleanMarkdownBtn.disabled = true;
    try {
      const resp = await fetch('/api/clean-markdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: txt })
      });
      const data = await resp.json();
      target.value = data.cleaned_text;
      updateHnAnalytics();
      hnCleanMarkdownBtn.textContent = '✓ LIMPIADO!';
      setTimeout(() => { hnCleanMarkdownBtn.textContent = '🧹 LIMPIAR MARKDOWN'; }, 1500);
    } catch (e) {
      hnCleanMarkdownBtn.textContent = '🧹 LIMPIAR MARKDOWN';
    } finally {
      hnCleanMarkdownBtn.disabled = false;
    }
  });

  hnCopyBtn.addEventListener('click', () => {
    const out = hnOutputText.value.trim() || hnInputText.value.trim();
    if (out) {
      navigator.clipboard.writeText(out);
      hnCopyBtn.textContent = '✓ COPIADO!';
      setTimeout(() => { hnCopyBtn.textContent = '📋 COPIAR'; }, 1500);
    }
  });

  // Seamless Transfer to Tab 1 (paste, write.)
  hnSendToTypistBtn.addEventListener('click', () => {
    const textToType = hnOutputText.value.trim() || hnInputText.value.trim();
    if (!textToType) {
      alert('Escribe o humaniza un texto primero.');
      return;
    }

    // Put into paste, write.
    pwText.value = textToType;
    updatePwStats();
    setPwMode('human');
    setPwDirective('formal');

    // Switch to paste, write. tab
    switchTab('pastewrite');
    logPwTerm(`[Humanizer] 🚀 Texto transferido con éxito (${textToType.split(/\s+/).length} palabras). ¡Listo para escribir con START (F9)!`);
    pwStartBtn.focus();
  });

  // =============================================================
  // 5. GLOBAL HOTKEYS
  // =============================================================
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F9' || (e.ctrlKey && e.key === 'Enter')) {
      e.preventDefault();
      if (!isTyping) startTyping();
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

  // Initial stats
  updatePwStats();
  updateHnAnalytics();
});
