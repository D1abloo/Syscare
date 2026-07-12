# SysCare

SysCare es una aplicacion grafica para Linux y macOS orientada a mantenimiento de usuario:

- Limpieza de temporales, caches, logs, papelera local y cookies conocidas.
- En macOS limpia tambien Quick Look, diagnosticos, estados guardados y `~/.Trash`.
- Optimizacion con cache DNS, cache de fuentes, limpieza de paquetes, journal y revision de entradas invalidas.
- Mantenimiento adicional para pip, npm, Docker, Quick Look, Xcode DerivedData y caches de gestores Linux cuando existan.
- Optimizacion de memoria RAM mediante la herramienta nativa disponible (`purge` en macOS con autorizacion del sistema).
- Deteccion de equivalentes Linux/macOS a entradas invalidas del registro: enlaces rotos, `.desktop` sin destino, LaunchAgents obsoletos y archivos grandes.
- Busqueda y recuperacion de archivos borrados que aun estan en papeleras accesibles del usuario o de volumenes montados.
- Recuperacion propia por papelera local, por carpeta original y por papeleras de discos/volumenes sin servicios de terceros.
- Panel de rendimiento con CPU, memoria, disco, bateria y temperaturas disponibles.
- En macOS muestra estado termico mediante `pmset` cuando no hay sensores de temperatura accesibles.
- Indicador en barra superior/bandeja del sistema con memoria y temperatura, y menu para mostrar/ocultar, limpiar o buscar actualizaciones.
- Buscador de aplicaciones instaladas.
- Instalador y desinstalador de paquetes mediante Homebrew, MacPorts, apt, dnf, yum, zypper, pacman, snap o flatpak.
- Desinstalacion de apps `.app` en macOS moviendolas a la papelera.
- Compresion y descompresion de carpetas/archivos.
- Comprobacion de actualizaciones desde GitHub Releases o ultimo commit de GitHub.
- Panel de ayuda integrado con estado de actualizaciones.
- Interfaz clara profesional con navegacion en header y animacion de apertura.

## Requisitos

- Python 3.10 o superior.
- Linux o macOS.
- Dependencias Python definidas en `requirements.txt`.
- Para instalar/desinstalar paquetes en Linux: un gestor instalado (`apt`, `dnf`, `yum`, `zypper`, `pacman`, `snap` o `flatpak`) y permisos mediante `pkexec` o `sudo` cuando aplique.
- Para macOS: Homebrew (`brew`) o MacPorts (`port`) si quieres instalar paquetes desde SysCare.

## Instalacion en Linux

### Ubuntu 22.04/24.04, Debian 12, Linux Mint

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-pyqt6 pkexec
./scripts/install-dev.sh
./scripts/create-linux-launcher.sh
```

### Fedora 39/40/41, RHEL compatible

```bash
sudo dnf install -y python3 python3-pip python3-virtualenv polkit
./scripts/install-dev.sh
./scripts/create-linux-launcher.sh
```

### Arch Linux, Manjaro, EndeavourOS

```bash
sudo pacman -S --needed python python-pip python-virtualenv polkit
./scripts/install-dev.sh
./scripts/create-linux-launcher.sh
```

### openSUSE Tumbleweed/Leap

```bash
sudo zypper install python3 python3-pip python3-virtualenv polkit
./scripts/install-dev.sh
./scripts/create-linux-launcher.sh
```

## Instalacion en macOS

Compatible con macOS 13 Ventura, macOS 14 Sonoma y macOS 15 Sequoia si tienes Python 3.10+.

### Con Homebrew

```bash
brew install python
./scripts/install-dev.sh
```

### Sin Homebrew

Instala Python 3 desde <https://www.python.org/downloads/macos/> y ejecuta:

```bash
./scripts/install-dev.sh
```

Para abrirla como app desde Finder puedes usar Automator, Platypus o generar un binario con PyInstaller.
Tambien puedes crear un lanzador local en `~/Applications` con icono nativo `.icns`:

```bash
./scripts/create-macos-launcher.sh
open ~/Applications/SysCare.app
```

## Instalacion de desarrollo

```bash
./scripts/install-dev.sh
```

El instalador puede ejecutarse desde la raiz del proyecto o desde `scripts/`. Si el entorno no puede instalar el paquete editable por falta de `setuptools` o red, crea un enlace local de desarrollo para que `syscare` siga funcionando con las dependencias presentes.

## Lanzamiento

```bash
syscare
```

Tambien puedes lanzarla sin instalar el script:

```bash
python -m syscare_app
```

O usar:

```bash
./scripts/run.sh
```

## Actualizaciones

El boton de actualizaciones consulta GitHub. Primero comprueba Releases y, si no hay releases, compara el ultimo commit de `main`.

Para consultar un repositorio concreto sin Git local:

```bash
export SYSCARE_REPO_URL="https://github.com/usuario/repositorio"
syscare
```

Si el repositorio tiene GitHub Releases, SysCare compara la version local con la ultima release.

El panel Ayuda muestra si hay actualizaciones pendientes. Si se instala una actualizacion mediante Git, reinicia SysCare para ver los cambios nuevos.

## Empaquetado opcional

Para generar un binario local con PyInstaller:

```bash
source .venv/bin/activate
pip install pyinstaller
pyinstaller packaging/syscare.spec
```

El resultado queda en `dist/SysCare`.

## Seguridad

La limpieza esta limitada a rutas de usuario y temporales conocidos. En directorios compartidos como `/tmp`, SysCare solo procesa elementos propiedad del usuario actual. Las cookies y papelera se marcan como categorias sensibles porque pueden cerrar sesiones o eliminar contenido que no se recupera facilmente.

Linux y macOS no tienen registro de Windows. Por eso SysCare trata como "entradas invalidas" los accesos y metadatos equivalentes: enlaces rotos, launch agents obsoletos, accesos `.desktop` invalidos y referencias a apps eliminadas.

La recuperacion propia funciona si el archivo sigue dentro de una papelera accesible del usuario o de un volumen montado.
La recuperacion de disco completo se limita a papeleras accesibles del usuario y volumenes montados. macOS/APFS no permite recuperar sectores borrados permanentemente desde una app normal sin herramientas forenses y permisos especiales.
