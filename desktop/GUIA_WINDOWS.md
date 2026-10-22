# 🪟 Guía Completa de Instalación y Uso en Windows
### HumanNature × paste, write. (Desktop Edition)

Esta guía paso a paso te explica cómo instalar y poner a funcionar la aplicación en cualquier computadora con **Windows 10 u 11**, desde cero.

---

## 📥 Paso 1: Instalar Python 3

Para que la aplicación funcione, necesitas tener Python instalado en tu computadora:

1. Ve a la página oficial de Python:  
   👉 **[https://www.python.org/downloads/](https://www.python.org/downloads/)**
2. Haz clic en el botón amarillo grande: **"Download Python 3.12.x"** (o la versión más reciente).
3. Abre el archivo instalador que se descargó (`python-3.x.x-amd64.exe`).
4. ⚠️ **EL PASO MÁS IMPORTANTE:**  
   En la primera ventana del instalador, **marca la casilla que está abajo del todo**:
   ```
   [✔] Add python.exe to PATH
   ```
   *(Si no marcas esta casilla, Windows no sabrá dónde encontrar Python).*
5. Luego haz clic en el botón superior: **"Install Now"**.
6. Espera que termine y haz clic en **"Close"**.

---

## 📂 Paso 2: Descargar la Aplicación

Tienes dos formas de descargarla (elige la que te sea más fácil):

### Opción A: Descarga directa en ZIP (Recomendada si no tienes Git)
1. Entra al repositorio en GitHub:  
   👉 **[https://github.com/drylexx3/HumanNatureWeb](https://github.com/drylexx3/HumanNatureWeb)**
2. Haz clic en el botón verde que dice **`<> Code`**.
3. En el menú desplegable, haz clic en **`Download ZIP`**.
4. Ve a tu carpeta de Descargas, haz clic derecho sobre el archivo `HumanNatureWeb-main.zip` y selecciona **"Extraer todo..."** (o con WinRAR / 7-Zip).
5. Abre la carpeta que se extrajo.

### Opción B: Mediante Git (Si ya usas terminal)
Abre tu consola (`cmd` o `PowerShell`) y ejecuta:
```cmd
git clone https://github.com/drylexx3/HumanNatureWeb.git
```

---

## 🚀 Paso 3: Iniciar la Aplicación (1 Solo Clic)

1. Abre la carpeta del proyecto y entra a la subcarpeta **`desktop`**:
   ```
   HumanNatureWeb \ desktop
   ```
2. Busca el archivo llamado:
   ```
   run.bat
   ```
3. Haz **doble clic en `run.bat`**.

> **¿Qué hace `run.bat` automáticamente por ti?**
> - Detecta tu instalación de Python.
> - Descarga e instala en segundos las dos librerías que necesita la app (`pynput` y `pyperclip`).
> - Lanza la ventana de la aplicación de inmediato con interfaz oscura y panel cyber-dark.
> 
> *(Si Windows SmartScreen te muestra un aviso azul de "Windows protegió su PC", haz clic en **"Más información"** y luego en **"Ejecutar de todas formas"**).*

---

## ⌨️ Paso 4: Cómo Usar la Suite

La aplicación tiene dos herramientas unificadas en pestañas:

### 1. Pestaña: `paste, write.` (Mecanografiado Físico Real)
Esta herramienta escribe automáticamente en cualquier programa (Google Docs, Word, Discord, Bloc de Notas) simulando los pulsos reales de un teclado físico para que sea 100% indetectable:

1. **Pega tu texto:** Escríbelo en la caja o haz clic en **"📋 Pegar portapapeles"**.
2. **Selecciona la directriz de estilo:**
   - `🎯 Tal cual (Exacto)`: Escribe el texto idéntico carácter por carácter.
   - `🛡️ Google Docs Stealth`: Previene ventanas emergentes de markdown en Docs y cuida los acentos.
   - `🧹 Sin Markdown`: Quita asteriscos (`*`) y hashes (`#`).
3. **Ajusta la velocidad y cuenta atrás:**
   - **WPM:** Velocidad de palabras por minuto (recomendado entre 60 y 85 WPM).
   - **Cuenta atrás:** Tiempo en segundos (por ejemplo 5s) para darte tiempo de cambiar a la ventana de Word o Google Docs y colocar el cursor donde quieres que empiece a escribir.
4. **Inicia la escritura:**
   - Haz clic en **"🚀 Iniciar Escritura"** o presiona la tecla **`F9`**.
   - Haz clic en tu documento donde quieras que escriba y espera que termine la cuenta atrás.

#### Atajos de Teclado Globales (funcionan en cualquier ventana):
- **`F9`**: Iniciar escritura / Reanudar.
- **`F8`**: Pausar la escritura momentáneamente.
- **`F10`**: Cancelar / Detener de emergencia inmediatamente.

---

### 2. Pestaña: `HumanNature Studio` (Humanizador y Métricas)
- Pega ensayos o textos generados por IA para reescribirlos y humanizarlos con algoritmos de estilo natural.
- Permite seleccionar presets y analizar métricas de detección antes de mecanografiarlos.

---

## ❓ Preguntas Frecuentes y Solución de Problemas

- **Al abrir `run.bat` dice que "No se encontró Python":**  
  Significa que instalaste Python pero olvidaste marcar la casilla *"Add python.exe to PATH"*. Desinstala Python, vuelve a ejecutar el instalador y asegúrate de marcar esa casilla al inicio.
- **¿Puedo usarlo sin instalar nada?**  
  Sí, puedes usar la versión web directamente en tu navegador entrando a:  
  👉 **[https://humannature-web.vercel.app/paste-write](https://humannature-web.vercel.app/paste-write)**
