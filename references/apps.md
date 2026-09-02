# Apps de la HP Prime

Un programa suelto vive en el catálogo y se abre con `[Shift][Program]` +
navegar + `[Enter]`. Una **app** tiene icono en `[Apps]`, así que abrirla son
**dos pulsaciones**. Bajo presión de examen esa es toda la diferencia, y es
casi la única razón para envolver algo como app.

Lo demás que aporta —vistas propias, variables que persisten, ganchos de
arranque— sale gratis o no sale, según cómo la montes. Este documento dice qué
hay dentro de una app, qué se puede generar desde el PC y qué trampas tiene,
medido sobre apps que funcionan en una G2.

> **Regla que se paga sola**: desarrolla como **programa** y envuélvelo como
> app al final. El motor y la interfaz son idénticos en los dos casos, la
> `.hpappdir` es sólo un contenedor, y iterar sobre un programa en el emulador
> es mucho más rápido.

---

## 1. Qué hay dentro de una `.hpappdir`

Una app es una **carpeta** cuyo nombre acaba en `.hpappdir`. El nombre de la
app sale del nombre de la carpeta y de los ficheros de dentro: **ninguno de los
tres envoltorios lleva el nombre escrito**. Por eso los mismos tres, byte a
byte, sirven para cualquier app: se copian y se renombran.

```
MIAPP.hpappdir/
   MIAPP.hpapp        ajustes de la app y la VISTA DE ARRANQUE
   MIAPP.hpappnote    la nota  (2 bytes cuando esta vacia: 00 00)
   MIAPP.hpappprgm    el programa PPL de la app -- mismo formato que .hpprgm
   icon.png           el icono (opcional)
   *.py               los modulos, si es una app de Python
   *.png              cualquier otro fichero que la app quiera llevarse
```

Medido sobre las apps instaladas en una G2 real:

| App | `.hpapp` | `.hpappprgm` | Qué es |
|---|---|---|---|
| `&Python` (de fábrica) | 180 B | 1152 B | app de Python, programa vacío |
| `&Function` (de fábrica) | 1699 B | 1152 B | app de fábrica con base propia |
| `Bode Plot` (de usuario) | 1344 B | 1152 B | copia de una app de fábrica |
| `TAULES` (de usuario) | **124 B** | 27322 B | app **en blanco** con programa PPL |
| `MarkdownViewer` | 188 B | 1152 B | app de Python |

Dos lecturas de esa tabla:

- **`.hpappprgm` de 1152 bytes** es la firma de *«programa vacío»*: sólo la
  tabla de símbolos con un `Main` y nada de fuente. Todas las apps de Python lo
  llevan así, porque su código está en los `.py`.
- **El `.hpapp` pequeño (124 B) es el de una app con base *None*.** Las que
  heredan de una app de fábrica arrastran los ajustes de aquélla y pesan diez
  veces más.

`Gallery`, que es de HP, mete además tres PNG sueltos de hasta 300 KB. O sea
que **la carpeta admite ficheros arbitrarios**: es el mecanismo por el que una
app de Python se lleva sus módulos.

## 2. El byte de la vista de arranque

El fallo más desconcertante de una app de Python: la abres y sale **la consola
de Python** —una lista de `>import …` de los arranques anteriores— en vez de tu
pantalla.

No es el código. Es el `.hpapp`, y está en sus **últimos cuatro bytes**:

```
esqueleto que funciona  ...  08 00 00 00   85 06 C9 00   01 00 00 00
&Python de fabrica      ...  08 00 00 00   85 06 C9 00   03 00 00 00
                                longitud     etiqueta       vista
```

`01` es la vista propia de la app; `03` es la Vista Numérica, que en una app de
Python **es la consola**. La app de fábrica `&Python` lleva `03` porque su
pantalla *es* el terminal — así que el valor no está mal, está copiado de donde
no tocaba.

**Cómo llega ahí solo**: al salir de la app, la calculadora **reescribe los
tres envoltorios** para guardar el estado, incluida la vista en la que estabas.
Si después el Connectivity Kit se trae la carpeta al PC, ese estado entra en el
repositorio y a partir de ahí la app arranca donde la dejaste.

Pasó exactamente así en CiclesHP: el `.hpapp` volvió con `03` y la app dejó de
abrir su pantalla.

**El arreglo estructural, no el parche**: guarda los tres envoltorios buenos
aparte y **rehazlos en cada construcción**. Eso hace [`mkapp.py`](../scripts/mkapp.py),
y su modo `--check` avisa de que la carpeta ha dejado de coincidir con la
plantilla — o sea, de que la calculadora los ha reescrito — antes de que te
enteres por la app.

## 3. El icono

`icon.png` dentro de la carpeta. Medido:

| Fichero | Tamaño |
|---|---|
| `Gallery.hpappdir/icon.png` (de HP) | **73 × 74**, RGBA |
| `TAULES.hpappdir/icon.png`, después de pasar por la calculadora | **37 × 38**, RGBA |

O sea: se entrega a 73 × 74 y la calculadora se queda una copia a la mitad. Las
dos medidas son de ficheros reales, no de la documentación —que no lo dice—.
Dibújalo a 4× y redúcelo: a 73 px, una curva sin supermuestreo sale dentada.

Sin `icon.png` la app aparece igual, con el icono genérico.

## 4. Las dos clases de app

| | App de **PPL** | App de **Python** |
|---|---|---|
| Dónde vive el código | dentro del `.hpappprgm` | en los `.py` de la carpeta |
| `.hpappprgm` | el programa, con su fuente | vacío (1152 B), con un `Main` |
| Se genera desde el PC | `hpprgm.py write` | copiar los `.py`, y ya |
| Se edita en la calculadora | sí, con su editor | sí, con el editor de Python |
| Llama al otro lado | `PYTHON("script")` | `hpprime.eval("…")` |

La de Python es **mucho más cómoda de generar**: los módulos son ficheros de
texto que se copian tal cual, sin formato binario de por medio. La de PPL
necesita meter el fuente dentro del contenedor, que es lo que hace
[`hpprgm.py`](../scripts/hpprgm.py).

Para el puente entre los dos lados, [`micropython.md`](micropython.md).

## 5. App de PPL: los ganchos, y la trampa de la app en blanco

El programa de la app puede exportar funciones con nombres reservados que la
calculadora llama sola:

```ppl
EXPORT START()      // al abrir la app
BEGIN  MIPROGRAMA();  END;

EXPORT Num()        // la tecla [Num]: la mas grande y facil de encontrar
BEGIN  MIPROGRAMA();  END;

EXPORT Info()       // [Shift][Apps]. Solo admite PRINT
BEGIN  PRINT("que hace esta app");  END;

EXPORT RESET()      // deja los globales como al principio
BEGIN  MIVAR := 1;  END;
```

Y aquí está la trampa, medida en TermoHP:

> Una app creada con **Base App: None** no tiene ninguna vista donde reposar.
>
> - Si `START()` **devuelve** el control, la calculadora cae a Home, y entonces
>   `[Num]` y `[View]` ya no llegan a la app.
> - Si `START()` **no devuelve** el control (se queda en un bucle), retiene el
>   teclado y esas teclas tampoco responden.
>
> Las dos cosas no pueden darse a la vez.

Así que **no cuentes con las teclas de vista para navegar**. La salida es
dibujar el menú en la pantalla y leer las teclas tú: la pantalla de resultados
de TermoHP lleva en el pie `tecla=formulario  View=menu  Help=ayuda  Esc=surt`,
y el propio programa decide qué hace cada una. Ver [`interfaz.md`](interfaz.md).

### El patrón lanzador

TermoHP hace algo que conviene copiar: **la app es sólo un lanzador**. El motor
(`TERMOLIB`) y la interfaz (`TERMO`) siguen siendo programas del catálogo, y la
app se limita a llamarlos.

Dos razones, las dos prácticas:

1. **Lo exportado desde el programa de una app queda ligado a esa app.** Si el
   motor tiene que ser reutilizable desde otra app o desde Home, tiene que
   vivir en un programa del catálogo.
2. **Los nombres globales chocan.** Por eso la app se llama `TAULES` y la
   interfaz `TERMO`: dos símbolos globales con el mismo nombre no pueden
   coexistir.

El coste de partirlo en tres elementos es que hay que instalar tres cosas. El
beneficio es que el bloque que no cambia nunca —los datos, 309 KB— no se toca
al arreglar la interfaz.

## 6. App de Python: cómo se monta

### Cómo se crea la primera vez

En la calculadora: `[Apps]` → **Python** → tecla **(Save)** → nombre nuevo. Eso
da una app de Python con tu nombre. A partir de ahí el Connectivity Kit ya
tiene la carpeta y los tres envoltorios buenos, que es lo único que hacía falta
sacar de la calculadora.

Para una app de PPL en blanco: `[Apps]` → **(Save)** → *Base App*: **None** →
nombre.

El kit trae los envoltorios listos en [`plantillas/`](../plantillas/), así que
para empezar no hace falta ni eso. Son **dos descriptores distintos**, porque
no son intercambiables:

| Fichero | | De dónde sale |
|---|---|---|
| `app-python.hpapp` | 188 B | del Markdown Viewer: una app **basada en la de Python** |
| `app-blanca.hpapp` | 124 B | de `TAULES`: una app creada con **Base App: None**, que es la forma de una app de PPL |
| `app.hpappnote` | 2 B | la nota vacía |
| `app.hpappprgm` | 1152 B | el programa vacío, con su `Main` |

`mkapp.py` coge el que toca: el de Python por defecto, el blanco con `--ppl`.
Con `--base` se le pasa otro, incluido un `.hpapp` tuyo.

Ninguno de los dos lleva texto dentro —se ha comprobado— así que no arrastran
nada de la app de la que salieron más allá de sus ajustes.

### El punto de entrada es `main.py`

En las tres apps de Python leídas —`CICLES`, `PROVA` y el **Markdown Viewer**—
el fichero se llama `main.py` y **su código está a nivel de módulo**, no dentro
de un `if __name__`: se ejecuta al importarse. El Markdown Viewer acaba
literalmente así:

```python
try:
    main()
except KeyboardInterrupt:
    clear_screen()
```

`KeyboardInterrupt` es la tecla `[ON]`, que es como se sale de un bucle.

### La estructura que sale bien

De CiclesHP. La regla que la ordena es **separar lo que se puede probar en el
PC de lo que no**:

| Fichero | Qué es | ¿Se prueba en el PC? |
|---|---|---|
| `cycle.py` | el motor de cálculo | **sí** — es el *mismo fichero* que el del PC |
| `projecte.py` | el estado mientras se monta | sí |
| `llista.py` | selección, ventana, teclas: lógica pura | sí |
| `vistes.py` | qué texto va en cada fila | sí |
| `geometria.py` | sólo números: dónde va cada columna | sí, y hay una prueba que lo usa |
| `taules.py` | la capa de propiedades | **no** — es la que cruza el puente |
| `pantalla.py` | píxeles y teclas | **no** — por eso es tan fina como se puede |
| `main.py` | pegarlo todo | no |

El truco que hace que esto funcione: `taules.py` tiene **dos versiones con la
misma cara**, una sobre el motor del PC y otra sobre el puente a PPL. Gracias a
eso `cycle.py` es literalmente el mismo fichero en los dos sitios, y las
comprobaciones que pasa en el PC dicen algo de lo que corre en la calculadora.

### El ensamblado

Copiar a mano garantiza que tarde o temprano los dos ficheros dejen de ser el
mismo. Así que se copian con un comando y **hay una comprobación de que no se
han separado**: `mkapp.py --check`.

Tres detalles que esa herramienta resuelve y que si no se olvidan:

- **rehacer los tres envoltorios** desde la plantilla (§2);
- **borrar `__pycache__`**: son `.pyc` de CPython, que MicroPython no leería, y
  sólo abultan;
- **comprobar los `import`**: un módulo compartido no puede importar nada que
  MicroPython no tenga. `__future__` no existe, ni `os` ni `sys` de la misma
  manera. Es un fallo que no se ve hasta que la app arranca — y entonces se
  cierra sin decir nada.

## 7. Instalar

Lo mismo que un programa, y con las mismas dos trampas:

1. Abre el **Connectivity Kit** con la calculadora conectada (o el Virtual
   Calculator).
2. **Arrastra la carpeta `.hpappdir`** desde el explorador **encima de la
   calculadora**, en la ventana del CK.
3. En la calculadora: `[Apps]` → tu app.

> **No la copies a `Documentos\HP Connectivity Kit\Calculators\<calculadora>\`.**
> Esa carpeta es un **espejo** que el CK escribe *desde* la calculadora: al
> conectar la sobrescribe y tu copia desaparece. Y si el arrastre sale con el
> **cursor de prohibido**, mira si el CK está puesto para ejecutarse **como
> administrador**. Los dos casos, con la evidencia, en
> [`formato-hpprgm.md`](formato-hpprgm.md#como-se-instala-lo-generado).

Una vez instalada, pasarla a otra calculadora es arrastrar la carpeta **dentro**
del CK, de una a otra. La Prime admite además transferencia directa entre
calculadoras por USB OTG.

## 8. Generarla y comprobarla desde el PC

```bash
# crear una app de Python entera: envoltorios + modulos + icono
python scripts/mkapp.py MIAPP src/*.py --icon icon.png

# rehacerla, y avisar si la calculadora ha reescrito los envoltorios
python scripts/mkapp.py --check MIAPP.hpappdir src/*.py

# app de PPL: el fuente entra en el .hpappprgm, y el descriptor es el blanco
python scripts/mkapp.py MIAPP app.txt --ppl -t plantilla.hpprgm
```

`-t` se puede omitir si guardas la plantilla como **`plantilla_codigo.hpprgm`
en la raíz del repositorio**, que es la convención que ya usa
`tests/test_hpprgm.py`.

### Qué está verificado y qué no

| | |
|---|---|
| El `.hpappprgm` generado se relee y da el mismo fuente | **sí**, y `mkapp.py` lo comprueba antes de escribirlo |
| Un programa generado desde Python **se ejecuta en una HP Prime** | **sí** — ver [`formato-hpprgm.md`](formato-hpprgm.md) |
| Los envoltorios de una app de **Python** la arrancan en su pantalla | **sí**: son los del Markdown Viewer, que corre en esta calculadora |
| Una app de **PPL** montada entera por `mkapp.py` | **no probada en hardware.** Sus piezas sí lo están por separado —el descriptor sale de `TAULES`, que funciona, y el escritor de programas está validado— pero la combinación no se ha abierto todavía en una calculadora |

Y lo que de verdad conviene hacer antes de fiarse de un resultado obtenido en
la calculadora: **sacar el fuente de vuelta y compararlo con el repositorio**.

```bash
python scripts/hpprgm.py read "…/Calculators/HP Prime/MIAPP.hpappdir/MIAPP.hpappprgm" -o instalado.txt
diff instalado.txt ppl/MIAPP.txt
```

Eso destapó una vez que la app instalada llevaba semanas dos commits por detrás
del código que se daba por bueno.

## 9. Lo que no está resuelto

- **Generar un `.hpapp` desde cero.** Se copia el de una app que funcione. Su
  gramática interna no está descifrada más allá del byte de la vista, y no hace
  falta: no lleva el nombre dentro, así que uno vale para todas.
- **El `.hpappprgm` vacío no sirve de plantilla para `write`.** No tiene bloque
  de fuente que sustituir — `hpprgm.py` dice *«no se encuentra ningún bloque de
  fuente (programa vacío?)»*.

  Y conseguir una plantilla buena es más difícil de lo que parece, porque
  **la calculadora le añade su bloque compilado a todo lo que guarda**. En la
  máquina donde se escribió esto, de los **58** contenedores de programa que
  hay en la carpeta espejo del CK, **sólo 2 servían de plantilla** — y los dos
  eran `.hpappprgm` de apps, no programas del catálogo. Comprueba antes de
  fiarte:

  ```bash
  python scripts/hpprgm.py read CANDIDATO.hpprgm
  ```

  Si dice *«lleva N bytes de bloque compilado antes del fuente»*, no vale. Lo
  que sí produce una plantilla limpia es **crear el programa dentro del propio
  Connectivity Kit** (clic derecho → Nuevo sobre *Program*) y copiarlo fuera
  **antes** de que pase por la calculadora.
- **El bloque compilado.** La app `TAULES` que vuelve de la calculadora lleva
  2324 bytes de bloque compilado delante del fuente; se lee bien, pero no sirve
  de plantilla. Detalle en [`formato-hpprgm.md`](formato-hpprgm.md).
