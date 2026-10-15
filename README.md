# Ministerios Elim

Aplicación Django y Wagtail para administrar contenido doctrinal, iglesias,
perfiles de pastores y miembros, foros y gráficos interactivos.
Usa SQLite por defecto y no requiere un servidor de base de datos externo.

## Inicio rápido en Windows, Linux y macOS

### 1. Descargar el proyecto

Instala Git y Python **3.12**, y ejecuta:

```bash
git clone https://github.com/OmarGonD/ministerios-elim.git
cd ministerios-elim
```

### 2. Preparar e iniciar el sitio

Instala Python **3.12** y Git. Cada sistema debe crear su propio entorno virtual;
no copies ni uses las carpetas `venv-ministerioselim` de otra máquina.
El lanzador crea `.venv`, instala las dependencias y prepara SQLite sin necesidad
de activar el entorno ni cambiar la política de ejecución de PowerShell.

**Windows (PowerShell o CMD):**

```powershell
py -3.12 dev.py setup --demo
py -3.12 dev.py run
```

**Linux y macOS:**

```bash
python3.12 dev.py setup --demo
python3.12 dev.py run
```

En Debian/Ubuntu, si Python indica que falta `venv`, instala el paquete
`python3.12-venv`. En macOS puedes instalar Python 3.12 desde python.org o
mediante tu gestor de paquetes. El comando `setup` requiere acceso a internet.

### 3. Abrir el sitio

Abre **http://127.0.0.1:8000/**. Mantén la terminal abierta mientras usas el sitio;
para detenerlo, pulsa **Ctrl+C**. En las siguientes ocasiones basta con ejecutar
`dev.py run` usando el comando correspondiente a tu sistema.

Omite `--demo` para una instalación sin contenido de demostración.

### Otros comandos

Usa el mismo lanzador para administrar el proyecto:

```bash
python3.12 dev.py manage createsuperuser
python3.12 dev.py manage demo_seed --refresh-images
```

En Windows sustituye `python3.12` por `py -3.12`. Si `.venv` se copió desde otro
sistema, renómbralo o elimínalo y repite `setup`; tus datos están en `db.sqlite3`
y `media/`, fuera del entorno. Las carpetas virtuales nuevas están excluidas de
Git; los entornos antiguos que ya estaban versionados deben retirarse del índice.

### Entorno Linux existente

Desde la raíz del proyecto, el entorno Linux existente permite arrancar así:

```bash
venv-ministerioselim/bin/python manage.py runserver 127.0.0.1:8000
```

También puedes usar `python manage.py ...`: si el Python global no tiene
Django, `manage.py` vuelve a ejecutarse automáticamente con `.venv` o con
`venv-ministerioselim` cuando alguno de esos entornos existe.

Abre http://127.0.0.1:8000/. El panel de Wagtail está en `/admin/` y
el de Django en `/django-admin/`.

## Instalación desde cero

Usa Python 3.12, como en el Dockerfile. Los entornos virtuales son locales
a cada máquina: el entorno de Windows no sirve en Linux.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py replace_homepage
python manage.py runserver 127.0.0.1:8000
```

Para crear un administrador en una instalación nueva:

```bash
python manage.py createsuperuser
```

La configuración local es `ministerios_elim.settings.dev`. Los correos se
imprimen en la consola. El acceso con Google requiere configurar credenciales
OAuth válidas; el acceso con usuario y contraseña funciona por separado.

Si aparece «Welcome to your new Wagtail site!», configura la portada:

```bash
venv-ministerioselim/bin/python manage.py replace_homepage
```

Este comando conserva las páginas existentes y puede repetirse sin duplicar
la portada.

## Datos de demostración

Para completar todas las secciones con contenido ficticio:

```bash
venv-ministerioselim/bin/python manage.py seed_demo
```

Incluye «Quiénes somos», tres niveles de doctrina con seis lecciones, dos
gráficos interactivos, tres iglesias en Perú y España, eventos, materiales
descargables, foros y perfiles. Conserva el contenido existente y puede
repetirse sin duplicar los datos ni restablecer las contraseñas.

`demo_seed` es un alias del mismo comando:

```bash
python manage.py demo_seed
```

Las imágenes fuente de las secciones están en `static/img/demo/`; las de
las lecciones están en `home/fixtures/doctrina/`. Incluye ambas carpetas al
subir el proyecto a GitHub. El comando importa esos archivos a Wagtail y
los copia a `media/` en cada instalación nueva. No necesita generar imágenes,
descargarlas de internet ni guardar `media/` en Git. El logo original se
conserva en `static/img/logo-elim.png`.

Para aplicar las imágenes a los datos demo existentes:

```bash
python manage.py demo_seed --refresh-images
```

Esta opción actualiza imágenes; conserva los textos y las contraseñas.

Puedes iniciar sesión en `/login/` con `demo_apostol`, `demo_supervisor`,
`demo_pastor_lima`, `demo_pastor_arequipa`, `demo_pastor_madrid`,
`demo_miembro` o `demo_visitante`. La contraseña inicial es `ElimDemo2026!`.
Para elegir otra al crear las cuentas, usa `seed_demo --password 'tu-contraseña'`.

Las entradas de doctrina usan lorem ipsum e imágenes temáticas por título.
Para aplicar esas portadas y textos a las entradas demo ya cargadas:

```bash
venv-ministerioselim/bin/python manage.py seed_demo --refresh-doctrina
```

Esta opción reemplaza el texto y la portada solo de las entradas de ejemplo
creadas por `demo_apostol`. La ejecución habitual conserva las ediciones.

## Verificación

Con el entorno Linux existente:

```bash
venv-ministerioselim/bin/python manage.py check
venv-ministerioselim/bin/python manage.py migrate --check
venv-ministerioselim/bin/python manage.py test --noinput
```

Las pruebas crean una base de datos temporal.

## Preparación para producción

Copia `.env.example` a un archivo de variables seguro fuera del repositorio y
define, como mínimo, `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y
`WAGTAILADMIN_BASE_URL`. La configuración de producción exige HTTPS, cookies
seguras, HSTS y una clave secreta explícita.

Comprueba la configuración antes de desplegar:

```bash
python manage.py check --deploy --settings=ministerios_elim.settings.production
```

El sitio publica `/sitemap.xml`, `/robots.txt` y `/privacidad/`. La medición de
uso es interna y agregada: cuenta búsquedas, consultas de iglesias y lecciones
completadas sin almacenar usuarios, direcciones IP ni identificadores de
dispositivo.
