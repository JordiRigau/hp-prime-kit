---
name: hp-prime
description: Escribir, revisar y desplegar programas y apps en PPL para calculadoras HP Prime (G1/G2). Usar siempre que aparezcan ficheros .hpprgm o .hpappdir, código PPL (EXPORT/BEGIN/END, LOCAL, TEXTOUT_P, INPUT, CHOOSE), el HP Connectivity Kit o el Virtual Calculator, o cuando haya que meter datos o cálculo en una HP Prime.
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

Para el formato binario de los programas, `references/formato-hpprgm.md`.

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
globales y locales, y el paso de matrices **por valor**. Lo de pantalla y
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
```

La **plantilla** es cualquier `.hpprgm` de código que haya escrito el
Connectivity Kit; están en
`Documentos\HP Connectivity Kit\Calculators\<tu calculadora>\`. Se copia una
vez y vale para cualquier programa: el tamaño se ajusta solo.

### Cómo se instala lo generado (leer esto)

**Esa carpeta NO es un buzón.** Es un espejo que el Connectivity Kit escribe
*desde* la calculadora. Copiar un fichero dentro con el CK cerrado no instala
nada: al conectar, el CK la sobrescribe con lo que haya en la calculadora, y
tu fichero desaparece. Está comprobado por las malas.

**El escritor está validado contra hardware**: un programa generado desde
Python acabó cargado y compilado en una HP Prime, con el fuente intacto y los
acentos bien. Se sabe porque la calculadora le añadió su bloque compilado, que
sólo escribe si lo ha entendido.

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
  que al recibirlo no haya que esperar compilación). Ese bloque no se sabe
  generar, así que `write` rechaza esas plantillas.
- **Usa como plantilla un fichero del CK, no uno de la calculadora.** Cuando
  la calculadora guarda un programa le añade su propio bloque compilado,
  también si es sólo código. Los del CK son sólo fuente, que es lo que hay
  que generar.

### Comprobar antes de tocar la calculadora

```bash
python tests/test_hpprgm.py        # round-trip sobre tus binarios reales
python tests/test_lint.py          # que el linter caza y no da falsas alarmas
```

`test_hpprgm.py` busca solo la carpeta del Connectivity Kit y se salta lo que
no encuentre. Vale la pena pasarlo en una máquina nueva antes de fiarse.

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

Cuando aparezca un límite nuevo, añádelo a `references/ppl.md` **con la
evidencia** (qué programa, qué firmware) y una regla en el linter con su caso
en `tests/test_lint.py`. Lo que no está medido no se apunta como cierto.
