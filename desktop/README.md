# 📋 paste, write. (Desktop Edition v1.0)
> **Pega cualquier cosa. Escríbelo según le digas.**

Herramienta nativa ultra-rápida para escribir cualquier texto, código o mensaje en cualquier aplicación (Google Docs, Word, Discord, VSCode, terminal, navegadores) simulando pulsaciones reales de teclado a nivel de sistema operativo.

---

## 🌟 Características Principales

- **📋 Pega lo que sea**:
  - Lienzo amplio con conteo en tiempo real de caracteres, palabras, líneas y tiempo estimado de escritura.
  - Botón de 1 clic para pegar desde el portapapeles (`Ctrl + V`).
  - Muestras rápidas: Ensayo Académico, Código Python, Mensajes de Chat y Markdown.
- **🎯 Escríbelo según tú le digas**:
  - **Directrices predeterminadas**:
    - `🎯 Tal cual (Exacto)`: Escribe carácter por carácter sin modificar nada.
    - `💻 Código limpio`: Respeta indentación, llaves, corchetes y comillas sin autocorregir.
    - `🛡️ Google Docs Stealth`: Depura asteriscos y sintaxis para que Google Docs no abra ventanas de advertencia.
    - `🎓 Más formal`: Eleva el registro a nivel académico.
    - `🌊 Más natural`: Flujo conversacional y fluido.
    - `🧹 Sin Markdown`: Limpieza instantánea de formato.
  - **Campo de instrucción libre**: Escribe cualquier directriz personalizada y aplícala con 1 clic al texto.
- **⚡ Control Total del Tipeo**:
  - Velocidad WPM ajustable (25 a 160 WPM).
  - Precisión humana regulable (80% a 100%) con corrección automática de errores tipográficos mediante Backspace.
  - Cuenta atrás configurable (1 a 10 segundos) para cambiar a la ventana destino.
  - Soporte de `Shift + Enter` para chats donde Enter envía el mensaje (Slack, Discord).
- **⌨️ Atajos Globales de Teclado**:
  - `F9` o `Ctrl + Enter`: Iniciar / Detener escritura.
  - `F8`: Pausar / Reanudar en cualquier momento.
  - `F10` o `Esc`: Cancelar inmediatamente.

---

## 🚀 Inicio Rápido

### En Windows 🪟:
1. Asegúrate de tener instalado Python 3 ([python.org](https://www.python.org/downloads/)) con la casilla **"Add python.exe to PATH"** activada.
2. Abre la carpeta `desktop` y haz doble clic en:
   ```cmd
   run.bat
   ```
   *(El script instalará automáticamente las librerías necesarias `pynput` y `pyperclip` e iniciará la aplicación).*

### En Linux 🐧:
```bash
./run.sh
```

---

## 🌐 Versión Web

También disponible en vivo en la versión web en `/paste-write`:
- **Vercel**: [https://humannature-web.vercel.app/paste-write](https://humannature-web.vercel.app/paste-write)
- **Localhost**: [http://localhost:5050/paste-write](http://localhost:5050/paste-write)
