/**
 * paste, write. — Universal Input Typist (v1.0)
 * Pega cualquier cosa. Escríbelo según le digas.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements: Workspace
  const textInput = document.getElementById('pwTextInput');
  const pasteBtn = document.getElementById('pwPasteBtn');
  const clearBtn = document.getElementById('pwClearBtn');
  const charCount = document.getElementById('pwCharCount');
  const wordCount = document.getElementById('pwWordCount');
  const lineCount = document.getElementById('pwLineCount');
  const estimateTime = document.getElementById('pwEstimateTime');

  // Elements: Samples
  const sampleEssayBtn = document.getElementById('sampleEssayBtn');
  const sampleCodeBtn = document.getElementById('sampleCodeBtn');
  const sampleChatBtn = document.getElementById('sampleChatBtn');
  const sampleMarkdownBtn = document.getElementById('sampleMarkdownBtn');

  // Elements: Instruction & Format
  const directiveChips = document.querySelectorAll('.pw-directive-chips .pw-chip');
  const customInstruction = document.getElementById('pwCustomInstruction');
  const applyInstructionBtn = document.getElementById('pwApplyInstructionBtn');

  // Elements: Typist Controls
  const modeButtons = document.querySelectorAll('.pw-mode-btn');
  const wpmSlider = document.getElementById('pwWpmSlider');
  const wpmDisplay = document.getElementById('pwWpmDisplay');
  const accSlider = document.getElementById('pwAccSlider');
  const accDisplay = document.getElementById('pwAccDisplay');
  const delaySlider = document.getElementById('pwDelaySlider');
  const delayDisplay = document.getElementById('pwDelayDisplay');
  
  const shiftEnterCheck = document.getElementById('pwShiftEnterCheck');
  const stripMarkdownCheck = document.getElementById('pwStripMarkdownCheck');
  const punctuationPauses = document.getElementById('pwPunctuationPauses');

  // Elements: Execution & Telemetry
  const startBtn = document.getElementById('pwStartBtn');
  const pauseBtn = document.getElementById('pwPauseBtn');
  const stopBtn = document.getElementById('pwStopBtn');
  const statusLabel = document.getElementById('pwStatusLabel');
  const progressPercent = document.getElementById('pwProgressPercent');
  const progressFill = document.getElementById('pwProgressFill');
  const telemetrySub = document.getElementById('pwTelemetrySub');
  const liveWpmLabel = document.getElementById('pwLiveWpmLabel');
  const analogCanvas = document.getElementById('pwAnalogCanvas');
  const terminal = document.getElementById('pwTerminal');
  const bridgeStatusBadge = document.getElementById('bridgeStatusBadge');
  const liveClock = document.getElementById('liveClock');

  const ctx = analogCanvas.getContext('2d');
  let flightLatencies = new Array(50).fill(160);
  let statusPollTimer = null;
  let isTyping = false;
  let currentMode = 'human';
  let currentDirective = 'verbatim';

  // Live Clock
  function updateLiveClock() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    const hoursStr = String(hours).padStart(2, '0');
    liveClock.textContent = `${hoursStr}:${minutes} ${ampm}`;
  }
  setInterval(updateLiveClock, 1000);
  updateLiveClock();

  // Terminal Logger
  function logTerm(msg) {
    const line = document.createElement('div');
    line.className = 'pw-term-line';
    line.textContent = `> ${msg}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
    while (terminal.children.length > 20) {
      terminal.removeChild(terminal.firstChild);
    }
  }

  // -------------------------------------------------------------
  // Dynamic Typing Engine Bridge Resolver
  // Connects cloud/external frontend to the local laptop typist daemon
  // -------------------------------------------------------------
  let TYPING_API_BASE = '';
  let bridgeResolved = false;

  async function resolveTypingBackend() {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1' || host.includes('trycloudflare.com')) {
      TYPING_API_BASE = '';
      bridgeResolved = true;
      bridgeStatusBadge.textContent = '● LOCAL NATIVE';
      bridgeStatusBadge.style.color = 'var(--pw-green)';
      logTerm('[Bridge] Modo Local Directo conectado al hardware de tu laptop.');
      return;
    }

    bridgeStatusBadge.textContent = '⏳ ENLAZANDO...';
    bridgeStatusBadge.style.color = 'var(--pw-amber)';
    logTerm(`[Bridge] Conectando desde la nube (${host}) a tu laptop...`);

    const candidates = [
      'http://127.0.0.1:5050',
      'http://localhost:5050'
    ];

    // Try to get active tunnel URL if available
    try {
      const tunRes = await fetch('/api/tunnel');
      if (tunRes.ok) {
        const tunData = await tunRes.json();
        if (tunData.tunnel_url) {
          candidates.push(tunData.tunnel_url);
        }
      }
    } catch (e) {}

    candidates.push('https://feed-dee-spoke-resist.trycloudflare.com');

    for (const base of candidates) {
      try {
        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), 1300);
        const res = await fetch(`${base}/api/health`, {
          signal: ctrl.signal,
          mode: 'cors'
        });
        clearTimeout(tid);
        if (res.ok) {
          TYPING_API_BASE = base;
          bridgeResolved = true;
          bridgeStatusBadge.textContent = '● BRIDGE ACTIVO';
          bridgeStatusBadge.style.color = 'var(--pw-cyan)';
          logTerm(`[Bridge] Enlace establecido con éxito (${base}). Tipeo físico activado.`);
          return;
        }
      } catch (err) {}
    }

    TYPING_API_BASE = 'https://feed-dee-spoke-resist.trycloudflare.com';
    bridgeResolved = true;
    bridgeStatusBadge.textContent = '🛡️ TUNNEL BRIDGE';
    bridgeStatusBadge.style.color = 'var(--pw-green)';
    logTerm(`[Bridge] Conectado a través del túnel seguro Cloudflare.`);
  }

  resolveTypingBackend();

  // -------------------------------------------------------------
  // Text Statistics & Estimation
  // -------------------------------------------------------------
  function updateTextStats() {
    const raw = textInput.value;
    const chars = raw.length;
    const words = raw.trim() ? raw.trim().split(/\s+/).length : 0;
    const lines = raw.length ? raw.split('\n').length : 0;

    charCount.textContent = `${chars.toLocaleString()} caracteres`;
    wordCount.textContent = `${words.toLocaleString()} palabras`;
    lineCount.textContent = `${lines} ${lines === 1 ? 'línea' : 'líneas'}`;

    const currentWpm = parseInt(wpmSlider.value, 10) || 72;
    if (words === 0) {
      estimateTime.textContent = `⏱ ~0s @ ${currentWpm} WPM`;
    } else {
      const totalSecs = Math.max(1, Math.round((words / currentWpm) * 60));
      if (totalSecs < 60) {
        estimateTime.textContent = `⏱ ~${totalSecs}s @ ${currentWpm} WPM`;
      } else {
        const mins = Math.floor(totalSecs / 60);
        const remSecs = totalSecs % 60;
        estimateTime.textContent = `⏱ ~${mins}m ${remSecs}s @ ${currentWpm} WPM`;
      }
    }
  }

  textInput.addEventListener('input', updateTextStats);

  // -------------------------------------------------------------
  // Clipboard Paste & Clear
  // -------------------------------------------------------------
  pasteBtn.addEventListener('click', async () => {
    try {
      const clipText = await navigator.clipboard.readText();
      if (clipText && clipText.trim()) {
        textInput.value = clipText;
        updateTextStats();
        logTerm(`[Portapapeles] ✅ Pegado: ${clipText.length} caracteres detectados.`);
        pasteBtn.textContent = '✓ Pegado!';
        setTimeout(() => { pasteBtn.textContent = '📋 Pegar (Ctrl+V)'; }, 1500);
      } else {
        logTerm('[Portapapeles] ⚠️ El portapapeles está vacío.');
        alert('El portapapeles está vacío. Copia algo primero (Ctrl+C).');
      }
    } catch (e) {
      const fallback = prompt('Pega tu texto aquí (Ctrl+V):', textInput.value);
      if (fallback) {
        textInput.value = fallback;
        updateTextStats();
        logTerm(`[Portapapeles] ✅ Texto cargado manualmente.`);
      }
    }
  });

  clearBtn.addEventListener('click', () => {
    textInput.value = '';
    updateTextStats();
    logTerm('[Editor] Lienzo limpiado.');
  });

  // -------------------------------------------------------------
  // Sample Buttons
  // -------------------------------------------------------------
  sampleEssayBtn.addEventListener('click', () => {
    textInput.value = 
      "La inteligencia artificial contemporánea representa una de las transformaciones técnicas más profundas de nuestro tiempo.\n\n" +
      "A diferencia de las herramientas computacionales previas, estos sistemas no solo procesan datos de forma algorítmica, sino que modulan patrones de lenguaje y razonamiento.\n\n" +
      "Es fundamental analizar el impacto que este paradigma genera en la educación superior y en la producción académica moderna.";
    updateTextStats();
    setMode('human');
    setDirective('formal');
    logTerm('[Muestra] Cargado: Ensayo Académico en español.');
  });

  sampleCodeBtn.addEventListener('click', () => {
    textInput.value = 
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
    updateTextStats();
    setMode('code');
    setDirective('code');
    logTerm('[Muestra] Cargado: Código Python (Modo Coder).');
  });

  sampleChatBtn.addEventListener('click', () => {
    textInput.value = "Hola, ya revisé el reporte y quedó perfecto. En un momento te comparto los últimos ajustes por aquí!";
    updateTextStats();
    shiftEnterCheck.checked = true;
    setMode('human');
    setDirective('casual');
    logTerm('[Muestra] Cargado: Mensaje de Chat (Shift+Enter activado).');
  });

  sampleMarkdownBtn.addEventListener('click', () => {
    textInput.value = 
      "### Introducción al Proyecto\n" +
      "Este documento contiene **información crítica** sobre el lanzamiento:\n" +
      "* Primera etapa: depuración de `código` y validación.\n" +
      "* Segunda etapa: despliegue continuo sin asteriscos ni alertas.\n" +
      "> Nota importante: todo el texto se tipea con ritmo humano.";
    updateTextStats();
    setMode('human');
    setDirective('stealth');
    logTerm('[Muestra] Cargado: Texto con Markdown (Modo Stealth).');
  });

  // -------------------------------------------------------------
  // "Según Yo Le Diga": Instruction Directives
  // -------------------------------------------------------------
  function setDirective(dir) {
    currentDirective = dir;
    directiveChips.forEach(chip => {
      chip.classList.toggle('active', chip.dataset.directive === dir);
    });

    if (dir === 'code') {
      setMode('code');
      stripMarkdownCheck.checked = false;
    } else if (dir === 'verbatim') {
      setMode('verbatim');
      stripMarkdownCheck.checked = false;
    } else if (dir === 'stealth' || dir === 'clean_markdown') {
      stripMarkdownCheck.checked = true;
    }
  }

  directiveChips.forEach(chip => {
    chip.addEventListener('click', () => {
      setDirective(chip.dataset.directive);
      logTerm(`[Instrucción] Directriz seleccionada: "${chip.textContent.trim()}".`);
    });
  });

  applyInstructionBtn.addEventListener('click', async () => {
    const raw = textInput.value;
    if (!raw.trim()) {
      alert('Pega o escribe texto primero en el lienzo.');
      return;
    }

    const inst = customInstruction.value.trim() || currentDirective;
    applyInstructionBtn.disabled = true;
    applyInstructionBtn.textContent = '⏳ Transformando...';
    logTerm(`[Instrucción] Aplicando directriz "${inst}" al texto...`);

    try {
      const resp = await fetch('/api/pastewrite/transform', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: raw, instruction: inst })
      });
      const data = await resp.json();
      if (data.success && data.transformed_text) {
        textInput.value = data.transformed_text;
        updateTextStats();
        logTerm(`[Instrucción] ✅ Texto transformado según la directriz (${data.directive}).`);
        applyInstructionBtn.textContent = '✓ Aplicado!';
        setTimeout(() => { applyInstructionBtn.textContent = '⚡ Aplicar al Texto'; }, 1500);
      }
    } catch (e) {
      logTerm(`[Error] Fallo al transformar texto: ${e.message}`);
      applyInstructionBtn.textContent = '⚡ Aplicar al Texto';
    } finally {
      applyInstructionBtn.disabled = false;
    }
  });

  // -------------------------------------------------------------
  // Rhythm Mode Selection
  // -------------------------------------------------------------
  function setMode(mode) {
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
      punctuationPauses.checked = true;
    } else if (mode === 'verbatim') {
      wpmSlider.value = 85;
      wpmDisplay.textContent = '85 WPM';
      accSlider.value = 100;
      accDisplay.textContent = '100% (Sin Errores)';
      stripMarkdownCheck.checked = false;
      punctuationPauses.checked = false;
    } else if (mode === 'code') {
      wpmSlider.value = 90;
      wpmDisplay.textContent = '90 WPM';
      accSlider.value = 100;
      accDisplay.textContent = '100% (Exacto)';
      stripMarkdownCheck.checked = false;
      punctuationPauses.checked = false;
    } else if (mode === 'turbo') {
      wpmSlider.value = 150;
      wpmDisplay.textContent = '150 WPM';
      accSlider.value = 100;
      accDisplay.textContent = '100% (Turbo)';
      stripMarkdownCheck.checked = false;
      punctuationPauses.checked = false;
    }
    updateTextStats();
  }

  modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      setMode(btn.dataset.mode);
      logTerm(`[Modo] Modo de ritmo cambiado a: ${btn.textContent.trim()}.`);
    });
  });

  // -------------------------------------------------------------
  // Sliders
  // -------------------------------------------------------------
  wpmSlider.addEventListener('input', (e) => {
    wpmDisplay.textContent = `${e.target.value} WPM`;
    updateTextStats();
  });

  accSlider.addEventListener('input', (e) => {
    const v = parseFloat(e.target.value);
    accDisplay.textContent = v >= 100 ? '100% (Sin Errores)' : `${v.toFixed(1)}%`;
  });

  delaySlider.addEventListener('input', (e) => {
    delayDisplay.textContent = `${e.target.value}s`;
  });

  // -------------------------------------------------------------
  // Canvas Waveform Oscilloscope
  // -------------------------------------------------------------
  function drawWaveform() {
    const w = analogCanvas.width;
    const h = analogCanvas.height;
    ctx.clearRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = '#141A26';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 30) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }

    // Baseline
    ctx.strokeStyle = 'rgba(6, 182, 212, 0.25)';
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();

    // Pulse curve
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

  // -------------------------------------------------------------
  // Start / Pause / Stop Execution
  // -------------------------------------------------------------
  async function startTyping() {
    const text = textInput.value;
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

    startBtn.disabled = true;
    startBtn.innerHTML = '<span>ESCRIBIENDO...</span>';
    pauseBtn.disabled = false;
    stopBtn.disabled = false;
    isTyping = true;

    try {
      const url = `${TYPING_API_BASE}/api/type/start`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await resp.json();
      logTerm(`[paste, write.] ▶ ${data.message || 'Proceso de tipeo iniciado.'}`);

      if (statusPollTimer) clearInterval(statusPollTimer);
      statusPollTimer = setInterval(pollTypingStatus, 90);
    } catch (err) {
      logTerm(`[Error] Fallo al iniciar: ${err.message}`);
      resetUi();
    }
  }

  async function pollTypingStatus() {
    try {
      const resp = await fetch(`${TYPING_API_BASE}/api/type/status`);
      const data = await resp.json();

      if (data.status) {
        statusLabel.textContent = data.status;
        statusLabel.style.color = data.is_typing ? (data.is_paused ? 'var(--pw-amber)' : 'var(--pw-green)') : 'var(--pw-green)';
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
        data.new_terminal_logs.forEach(msg => logTerm(msg));
      }

      if (data.is_typing) {
        pauseBtn.disabled = false;
        stopBtn.disabled = false;
        pauseBtn.innerHTML = data.is_paused ? '<span>▶ REANUDAR (F8)</span>' : '<span>⏸ PAUSA (F8)</span>';
      } else {
        resetUi();
      }
    } catch (e) {}
  }

  function resetUi() {
    isTyping = false;
    startBtn.disabled = false;
    startBtn.innerHTML = '<span>▶ ESCRIBIR AHORA (F9)</span>';
    pauseBtn.disabled = true;
    stopBtn.disabled = true;
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
      logTerm(`[Control] ${data.status === 'paused' ? '⏸ En Pausa' : '▶ Reanudado'}`);
    } catch (e) {}
  }

  async function stopTyping() {
    try {
      await fetch(`${TYPING_API_BASE}/api/type/stop`, { method: 'POST' });
      logTerm('[Control] ⏹ Tipeo detenido por el usuario.');
      resetUi();
    } catch (e) {}
  }

  startBtn.addEventListener('click', startTyping);
  pauseBtn.addEventListener('click', togglePause);
  stopBtn.addEventListener('click', stopTyping);

  // Global hotkeys
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
  updateTextStats();
});
