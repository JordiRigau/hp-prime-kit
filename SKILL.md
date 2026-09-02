---
name: hp-prime
description: Escribir, revisar y desplegar programas, apps e interfaces para calculadoras HP Prime (G1/G2), en PPL o en MicroPython. Usar siempre que aparezcan ficheros .hpprgm, .hpappdir, .hpapp o .hpappprgm, código PPL (EXPORT/BEGIN/END, LOCAL, TEXTOUT_P, INPUT, CHOOSE, DRAWMENU, GETKEY), Python de la Prime (import hpprime, hpprime.eval, fillrect), el HP Connectivity Kit o el Virtual Calculator, o cuando haya que meter datos, cálculo o una interfaz en una HP Prime.
---

# HP Prime: PPL sin ir a ciegas

PPL está mal documentado y su compilador solo dice «syntax error» señalando una
línea. Esta skill quita las dos fuentes de pérdida de tiempo: **adivinar la
sintaxis** y **el ritual de copiar y pegar en el Connectivity Kit**.

## Antes de escribir código

Lee `references/ppl.md`. No es un tutorial: son los límites y trampas medidos
en una G2 real, incluidas **cuatro hipótesis que parecen razonables y son
falsas**. Escribir PPL de memoria lleva a inventarse restricciones que no
existen y a saltarse la única que importa.

Y según lo que toque, uno de los otros cinco. Todos son lo mismo: **lo que está
medido en una G2**, con la evidencia al lado.

| Documento | Cuándo |
|---|---|
| [`references/empezar.md`](references/empezar.md) | si quien pregunta **no ha programado nunca una Prime**: el mapa, el vocabulario y el primer programa de principio a fin. Enlázale aquí antes que a nada |
| [`references/ppl.md`](references/ppl.md) | **siempre**: el lenguaje, sus límites y las hipótesis falsas |
| [`references/apps.md`](references/apps.md) | envolver algo como app: la `.hpappdir`, los ganchos, el byte que hace que abra donde no toca |
| [`references/micropython.md`](references/micropython.md) | escribirlo en Python: el puente a PPL, y la llamada que cierra la app |
| [`references/interfaz.md`](references/interfaz.md) | pantalla, teclado, táctil: `INPUT`, códigos de tecla, el toque que llega dos veces |
| [`references/formato-hpprgm.md`](references/formato-hpprgm.md) | el binario, y cómo se instala de verdad |

## Antes de compilar: pasar el linter

```bash
python scripts/lint_ppl.py mi_programa.hpprgm
```

Caza sin tocar la calculadora lo que el compilador no sabe explicar: pasarse
de variables en un `LOCAL`, indexar el retorno de una llamada, `ENDIF`,
comparar con `=`, índice 0, `LOCAL` a media función, bloques sin cerrar.
Sale 1 si hay errores, así que sirve de puerta en cualquier script.

Para los ficheros que van juntos a la calculadora, añade `--set` y además
avisa de nombres exportados que chocarían entre ellos.

**Regla:** si el linter da errores, arreglarlos antes de compilar. Si el
programa falla al compilar y el linter está limpio, es un caso nuevo — mídelo
contra programas que ya funcionen en esa misma calculadora y añade la regla.

## Ejecutar el PPL en el PC

`scripts/pplrun.py` interpreta PPL en Python, así que se puede **probar el
fichero que se instala**, no una reimplementación de lo que hace:

```bash
python scripts/pplrun.py MOTOR.hpprgm DATOS.hpprgm --call "MIFUNC(3,350)"
```

```python
import pplrun
m = pplrun.Maquina()
m.carga_fichero('ppl/TERMOLIB.hpprgm')
r = m.llama('TPT', 3.0, 350.0)
```

Cubre el subconjunto de cálculo: números, cadenas, listas, matrices
**1-based**, `IF`/`CASE`/`FOR`/`WHILE`/`REPEAT`/`IFERR`, funciones `EXPORT`,
globales y locales, el paso de matrices **por valor**, y el álgebra
matricial nativa —`MAKEMAT`, `MAKELIST`, `RREF`, `TRN`, `DET`, `INVERSE`—
para que apoyarse en ella no cueste perder las pruebas. Lo de pantalla y
teclado (`TEXTOUT_P`, `RECT`, `INPUT`, `CHOOSE`, `WAIT`, `MSGBOX`) no se
dibuja: se anota en `maquina.io` y devuelve un valor neutro, para que el
cálculo corra sin interfaz.

Lo que no está cubierto **da error**, nunca un resultado inventado. Si hace
falta un comando nuevo, añádelo a `BUILTINS` con su caso en
`tests/test_pplrun.py`.

**Para qué sirve de verdad**: si tienes un motor de referencia en Python,
compara los dos sobre casos sacados de los propios datos — hay una plantilla
lista para adaptar en `examples/conformidad.py`. Ahí aparecen las
divergencias entre lo que calcula el PC y lo que calcula la calculadora, que
es justo lo que ninguna prueba escrita a mano ve — porque las dos
implementaciones suelen ser coherentes cada una consigo misma.

## Desplegar sin pegar nada

`.hpprgm` es un contenedor binario, pero el fuente va dentro **literal en
UTF-16LE**. `scripts/hpprgm.py` lo lee y lo escribe:

```bash
python scripts/hpprgm.py read  PROG.hpprgm -o fuente.txt
python scripts/hpprgm.py write fuente.txt -t plantilla.hpprgm -o PROG.hpprgm
python scripts/hpprgm.py check PROG.hpprgm        # round-trip
python scripts/hpprgm.py plantillas "…/HP Connectivity Kit/Calculators"
```

La **plantilla** es un `.hpprgm` de código **escrito por el Connectivity Kit**.
Se copia una vez y vale para cualquier programa: el tamaño se ajusta solo.

Conseguirla tiene truco, y no está en la carpeta que uno diría: en
`Calculators\<tu calculadora>\` todo ha pasado por la calculadora, que le añade
su bloque compilado a lo que guarda. Medido: de **58** contenedores de programa
ahí dentro, **2** servían. La forma fiable es crear un programa **dentro del
propio CK** y copiarlo fuera antes de enviarlo a la calculadora. `write` no se
deja engañar —rechaza las plantillas con bloque compilado—, pero saberlo ahorra
la vuelta.

Guárdala como **`plantilla_codigo.hpprgm` en la raíz**: es la convención que ya
usan `tests/test_hpprgm.py` y `mkapp.py --ppl`, que la cogen solos.

### Cómo se instala lo generado (leer esto)

**Esa carpeta NO es un buzón.** Es un espejo que el Connectivity Kit escribe
*desde* la calculadora. Copiar un fichero dentro con el CK cerrado no instala
nada: al conectar, el CK la sobrescribe con lo que haya en la calculadora, y
tu fichero desaparece. Está comprobado por las malas.

**El escritor está validado contra hardware**: un programa generado desde
Python se instaló en una HP Prime y **se ejecutó dando el resultado correcto**,
con el fuente intacto y los acentos bien.

La entrega es **arrastrar el fichero desde el explorador a la calculadora**
en la ventana del CK. Copiarlo a `Calculators\<calculadora>\` no sirve: esa
carpeta es un espejo y el CK la sobrescribe.

Si el arrastre sale con el **cursor de prohibido** y no pasa nada, no es el
fichero: mira si el CK está puesto para **ejecutarse como administrador** (o
en modo de compatibilidad) en las propiedades del acceso directo o del `.exe`.
Windows no deja arrastrar desde un proceso sin elevar a uno elevado. Para
descartar el fichero en diez segundos, arrastra uno que haya escrito el propio
CK: si también lo rechaza, es el entorno.

Y no te fíes de haber instalado: **compruébalo leyendo el binario de vuelta**,
que es la parte de `hpprgm.py` que nunca falla.

### Dos cosas más

- **Programas con matrices grandes**: llevan un bloque compilado *antes* del
  fuente (los números ya en formato interno; hace que el fichero pese ~3× y
  que al recibirlo no haya que esperar compilación). Ese bloque **no se sabe
  generar entero**, así que `write` rechaza esas plantillas — aunque el
  formato de sus números sí está descifrado, ver abajo.
- **Usa como plantilla un fichero del CK, no uno de la calculadora.** Cuando
  la calculadora guarda un programa le añade su propio bloque compilado,
  también si es sólo código. Los del CK son sólo fuente, que es lo que hay
  que generar.

## Meter datos sin pegarlos: el número interno y `.hpmat`

El formato de número interno de la Prime —el del bloque compilado y el de los
ficheros `.hpmat`— está **descifrado**: 8 bytes, 12 dígitos BCD, exponente de
12 bits, signo 9 para negativo. Detalle y verificación en
[`references/formato-hpprgm.md`](references/formato-hpprgm.md).

Lo que abre en la práctica: **una matriz entera se lleva como fichero**, sin
pegar nada y sin pasar por el fuente de ningún programa.

```bash
python scripts/hpreal.py read  M1.hpmat -o datos.csv
python scripts/hpreal.py write datos.csv -o M0.hpmat
python scripts/hpreal.py nums  PROG.hpprgm     # mirar dentro de un bloque
```

Está verificado con una **piedra de Rosetta**: un programa de datos lleva el
bloque compilado delante del fuente, y el fuente son los mismos números en
decimal. **44.718 de 44.718** decodifican exactos y vuelven a codificar byte a
byte, negativos incluidos.

Lo que **no** abre: generar el bloque compilado entero, porque entre matriz y
matriz lleva registros de símbolo con el nombre en UTF-16LE. Lo que se sabe de
esa estructura está documentado, por si algún día toca seguir.

### Comprobar antes de tocar la calculadora

```bash
python tests/test_hpprgm.py        # round-trip sobre tus binarios reales
python tests/test_lint.py          # que el linter caza y no da falsas alarmas
python tests/test_pplrun.py        # el subconjunto, y que falla donde debe
python tests/test_mkapp.py         # que la app se construye y --check ve
python tests/test_hpreal.py        # el numero interno, contra tus ficheros
```

`test_hpprgm.py`, `test_mkapp.py` y `test_hpreal.py` buscan la carpeta del
Connectivity Kit y se saltan lo que no encuentren. Vale la pena pasarlos en una máquina nueva antes
de fiarse.

## Envolverlo como app

Una app son **dos pulsaciones** para abrirla en vez de cuatro y navegar. Eso es
casi todo lo que aporta, así que **desarrolla como programa y envuélvelo al
final**: la `.hpappdir` es un contenedor, no una reescritura.

```bash
python scripts/mkapp.py MIAPP src/*.py --icon icon.png    # app de Python
python scripts/mkapp.py MIAPP app.txt --ppl -t plantilla.hpprgm
python scripts/mkapp.py --check MIAPP.hpappdir src/*.py
```

Tres cosas que hay que saber antes de montar una, todas en
[`references/apps.md`](references/apps.md):

- **La calculadora reescribe los tres envoltorios** al salir de la app, y con
  ellos la vista de arranque. Si esa carpeta vuelve al PC, el repositorio se
  queda con un `.hpapp` que hace que la app abra **la consola de Python** en vez
  de su pantalla. Por eso se rehacen en cada construcción y por eso existe
  `--check`.
- **Una app en blanco no tiene vista donde reposar**, así que `[Num]` y `[View]`
  no llegan al programa: dibuja el menú y lee las teclas tú.
- **Lo exportado desde el programa de una app queda ligado a esa app.** Si el
  motor tiene que ser reutilizable, déjalo en un programa del catálogo y que la
  app sea sólo un lanzador.

## Si lo escribes en Python

MicroPython está en la Prime y `hpprime.eval` **ejecuta PPL y devuelve el
resultado**, así que se puede tener el motor en Python y la librería de datos en
PPL. Lee [`references/micropython.md`](references/micropython.md) antes de la
primera línea, porque hay una trampa que no perdona:

> **Una lista con un texto dentro cierra la app.** Sin mensaje y sin traza. Todo
> lo que cruce el puente tiene que ser un número o una lista plana de números.

Y una que hace perder una tarde: **`time` no existe**. Si `import time` falla,
no es el puente — es que falta el módulo.

Lo que hace que esto valga la pena es la arquitectura: **el fichero que calcula
puede ser el mismo en el PC y en la calculadora**, con una sola capa de datos
sustituible debajo. Entonces las pruebas del PC dicen algo real sobre lo que
corre en la G2.

## La interfaz

[`references/interfaz.md`](references/interfaz.md). Lo que más veces se paga:

- **`TEXTOUT_P` tiene un séptimo argumento de anchura que recorta.** Sin él, un
  texto que no cabe no da ningún error: se derrama sobre la columna vecina y te
  quedas sin saber qué decía.
- **El `OK` de un diálogo cae encima de la fila de teclas de pantalla**, en la
  posición de la F6. Si el dedo sigue ahí, el mismo toque llega dos veces.
- **`GETKEY` devuelve una posición, no un carácter.** `Enter` es 30.
- **Saca la lógica del dibujo.** Selección, ventana y qué hace cada tecla son
  lógica pura y se prueban en el PC; el módulo de píxeles se queda tan fino como
  se pueda, porque es lo único que no se puede probar.

## Detectar que la calculadora se ha quedado atrás

El fuente se puede extraer del binario instalado, así que se puede **comparar
con el repositorio**:

```bash
python scripts/hpprgm.py read "…/Calculators/HP Prime/MIPROG.hpprgm" -o instalado.txt
diff instalado.txt ppl/MIPROG.txt
```

Merece la pena hacerlo antes de dar por bueno cualquier resultado obtenido en
la calculadora: es fácil arreglar algo en el PC y olvidarse de volver a pegarlo.

## Método, cuando algo no cuadra

Lo que resuelve los problemas de PPL no es razonar sobre la sintaxis: es
**medir programas que ya funcionan en esa misma calculadora** y comparar
métricas (máximo de locales por sentencia, longitud, construcciones usadas).
Un error que no se mueve después de un arreglo significa que la hipótesis es
falsa, no que el arreglo fuera insuficiente.

Cuando aparezca un límite nuevo, añádelo al documento que le toque —`ppl.md`,
`apps.md`, `micropython.md`, `interfaz.md`— **con la evidencia**: qué programa,
qué firmware, qué se vio. Y si se puede cazar desde el PC, con su regla en el
linter y su caso en `tests/test_lint.py`. **Lo que no está medido no se apunta
como cierto**, y lo que viene de fuera se marca como tal.

La otra mitad del método, para una plataforma tan mal documentada como ésta:
**lee código que ya funcione en esa misma máquina**. El bucle de eventos, los
códigos de tecla, la geometría del menú y el puente a Python de este kit salen
de descargar apps de [hpcalc.org](https://www.hpcalc.org/prime/) y leerlas. Y
una rama entera de CiclesHP se dio por muerta —«`import hpprime` falla»— hasta
que se leyó una app de Python que corría en esa misma calculadora: no fallaba el
puente, faltaba el módulo `time`.
