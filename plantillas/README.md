# Los envoltorios de una app

Una `.hpappdir` no son sólo los `.py` o el programa PPL. Lleva **tres ficheros
binarios** que la calculadora usa para saber que la carpeta es una app y **con
qué vista arranca**.

Ninguno lleva el nombre de la app dentro — el nombre sale del nombre de la
carpeta y del de los ficheros. Por eso estos sirven tal cual para cualquier
app: [`scripts/mkapp.py`](../scripts/mkapp.py) los copia y los renombra.

| Fichero | | Qué es | De dónde sale |
|---|---|---|---|
| `app-python.hpapp` | 188 B | descriptor de una app **basada en la de Python** | del **MarkdownViewer**, que arranca bien en una G2 |
| `app-blanca.hpapp` | 124 B | descriptor de una app creada con **Base App: None**, que es la forma de una app de PPL | de **TAULES**, que funciona en esa misma calculadora |
| `app.hpappnote` | 2 B | la nota, vacía | ídem |
| `app.hpappprgm` | 1152 B | el programa PPL, con un `Main` vacío | ídem |

Los dos descriptores se han comprobado: **no llevan ningún texto dentro**, así
que no arrastran nada de la app de la que salieron más allá de sus ajustes.

## Por qué están aquí y no se generan

Porque **la calculadora los reescribe**. Al salir de la app guarda su estado
—entre otras cosas, en qué vista estabas— y si el Connectivity Kit vuelve a
traerse la carpeta al PC, ese estado se cuela en el repositorio.

Pasó: un `.hpapp` acabó con un `03` donde el bueno lleva un `01`, y la app
empezó a abrirse en la **consola de Python** —la Vista Numérica— en vez de en
su pantalla. Se veía el registro de los `>import` de los arranques anteriores y
ni un píxel de la app.

Están en los **últimos cuatro bytes** del `.hpapp`:

```
app-python.hpapp   ...  08 00 00 00   85 06 C9 00   01 00 00 00
&Python de fabrica ...  08 00 00 00   85 06 C9 00   03 00 00 00
                            longitud     etiqueta      vista
```

`mkapp.py` los rehace desde aquí en cada construcción, así que ese estado no
sobrevive a una reconstrucción; y `mkapp.py --check` avisa de que la carpeta ha
dejado de coincidir, que es la forma de enterarse antes de abrir la app.

La regla de fondo, la misma de todo el kit: ante una duda de plataforma,
**copiar algo que ya funciona en esa máquina** en vez de razonar desde los
síntomas.

Detalle completo en [`references/apps.md`](../references/apps.md).
