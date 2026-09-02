# hp-prime-kit — herramientas y documentación para programar la HP Prime en serio

Cinco herramientas en Python para trabajar desde el PC con la **HP Prime**, y
la documentación que a la calculadora le falta.

| | |
|---|---|
| **`scripts/lint_ppl.py`** | caza antes de compilar los errores que el compilador de la Prime no sabe explicar |
| **`scripts/hpprgm.py`** | lee y escribe `.hpprgm`, el formato binario de los programas |
| **`scripts/pplrun.py`** | **ejecuta PPL en el PC**, para probar el fichero que se instala |
| **`scripts/mkapp.py`** | construye y verifica una app (`.hpappdir`), con sus envoltorios binarios |
| **`scripts/hpreal.py`** | el **formato de número interno**, descifrado: lee y escribe `.hpmat` |

Sin dependencias: Python 3.7+ y nada más.

## La documentación

La Prime está mal documentada, y de Python en la Prime **no hay documentación
oficial ninguna**. Estos cinco documentos son lo que está **medido en una G2**,
con la evidencia al lado y marcando lo que no está confirmado:

| | |
|---|---|
| [`references/ppl.md`](references/ppl.md) | el lenguaje: los límites que rompen, y **cuatro hipótesis que parecen razonables y son falsas** |
| [`references/apps.md`](references/apps.md) | apps: la `.hpappdir`, los ganchos, y el byte que hace que la app abra donde no toca |
| [`references/micropython.md`](references/micropython.md) | Python en la calculadora: el puente a PPL, y la llamada que **cierra la app** |
| [`references/interfaz.md`](references/interfaz.md) | pantalla, teclado y táctil: `INPUT`, códigos de tecla, el toque que llega dos veces |
| [`references/formato-hpprgm.md`](references/formato-hpprgm.md) | el contenedor binario, verificado por reconstrucción byte a byte |

## El problema que resuelven

PPL está mal documentado y su compilador dice `syntax error` señalando una
línea, sin decir qué sobra. Todo se acaba comprobando a mano en el emulador:
pegar, compilar, mirar, repetir. Un límite no documentado —el máximo de
variables por sentencia `LOCAL`— costó **cinco rondas** de ese ciclo en el
proyecto donde nació esto, porque el error no se movía y cada hipótesis
parecía plausible.

Lo que faltaba no era paciencia: era **poder comprobar cosas sin la
calculadora**.

## Qué hace cada una

### Linter

```bash
python scripts/lint_ppl.py mi_programa.hpprgm
python scripts/lint_ppl.py ppl/ --quiet          # solo errores
python scripts/lint_ppl.py A.txt B.txt --set     # + choques de nombres entre ficheros
```

Nueve reglas, todas sacadas de errores reales medidos en una G2: pasarse de
variables en un `LOCAL`, indexar el retorno de una llamada, `ENDIF`, comparar
con `=`, índice 0, `LOCAL` a media función, bloques sin cerrar, `EXPR` sin
guarda, nombres exportados duplicados. Sale con código 1 si hay errores, así
que sirve de puerta en cualquier script.

Igual de importante es lo que **no** marca: hay cuatro hipótesis que parecen
razonables y son falsas —`RETURN` dentro de un `FOR` es legal, los locales
tipo `L12` o `r2` son legales— y están anotadas para que nadie las vuelva a
«arreglar». Las pruebas comprueban las dos direcciones.

### Leer y escribir `.hpprgm`

```bash
python scripts/hpprgm.py read  PROG.hpprgm -o fuente.txt
python scripts/hpprgm.py write fuente.txt -t plantilla.hpprgm -o PROG.hpprgm
python scripts/hpprgm.py check PROG.hpprgm
python scripts/hpprgm.py plantillas "…/HP Connectivity Kit/Calculators"
```

El `.hpprgm` es un contenedor TLV anidado con el fuente dentro **literal, en
UTF-16LE**. Está documentado en
[`references/formato-hpprgm.md`](references/formato-hpprgm.md) y verificado
reconstruyendo programas byte a byte, incluido uno de 1 MB con datos
compilados.

Sirve para dos cosas: **generar el binario** en vez de crear el programa a
mano y pegar el texto dentro —el último paso sigue siendo arrastrarlo dentro
de la ventana del Connectivity Kit, ver abajo—, y **comparar lo instalado con
el repositorio** para ver si la calculadora se ha quedado atrás.

Está **validado contra hardware**: un programa generado desde Python se
instaló en una HP Prime y se ejecutó allí dando el resultado correcto, con el
fuente y los acentos intactos.

Lo generado se instala **arrastrándolo a la calculadora** en la ventana del
CK.

> Dos avisos, los dos aprendidos por las malas: la carpeta
> `Calculators\<tu calculadora>\` **no es un buzón** —es un espejo que el CK
> sobrescribe—, y si el arrastre sale con el cursor de prohibido, mira si el
> CK está puesto para ejecutarse **como administrador**: Windows no deja
> arrastrar de un proceso sin elevar a uno elevado. Detalle en
> [`references/formato-hpprgm.md`](references/formato-hpprgm.md).

### Ejecutar PPL en el PC

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
teclado no se dibuja: se anota y devuelve un valor neutro, para que el cálculo
corra sin interfaz.

Lo que no está cubierto **da error**, nunca un resultado inventado.

### Construir una app

```bash
python scripts/mkapp.py MIAPP src/*.py --icon icon.png    # app de Python
python scripts/mkapp.py MIAPP app.txt --ppl -t plantilla.hpprgm
python scripts/mkapp.py --check MIAPP.hpappdir src/*.py
```

Una app es una carpeta con tres envoltorios binarios y los ficheros que se
lleva. Los envoltorios **no llevan el nombre de la app dentro**, así que un
juego vale para todas: el kit trae dos, sacados de apps que arrancan en una G2.

Lo que resuelve de verdad es un fallo que sólo se ve al abrir la app:

> Al salir, **la calculadora reescribe los tres envoltorios** para guardar su
> estado, incluida la vista en la que estabas. Si esa carpeta vuelve al PC, el
> repositorio se queda con un `.hpapp` que hace que la app abra **la consola de
> Python** en vez de su pantalla.

Por eso se rehacen en cada construcción, y por eso `--check` sale con código 1
cuando la carpeta ha dejado de ser la que generarías. De paso avisa de los
`import` que MicroPython en la Prime no tiene —`time`, el primero— que si no se
manifiestan como **la app cerrándose al arrancar, sin decir nada**.

### El número interno, y meter datos sin pegarlos

```bash
python scripts/hpreal.py read  M1.hpmat -o datos.csv
python scripts/hpreal.py write datos.csv -o M0.hpmat
python scripts/hpreal.py nums  PROG.hpprgm      # mirar dentro de un bloque
```

El formato de número de la Prime —el que llena el bloque compilado y los
ficheros `.hpmat`— estaba sin documentar. Son **8 bytes**: exponente decimal de
12 bits, 12 dígitos BCD de mantisa, y el signo en el nibble de arriba (0 o 9).

Se descifró con una **piedra de Rosetta**, no adivinando: un programa de datos
lleva el bloque compilado *delante* del fuente, y el fuente son los mismos
números escritos en decimal. Un solo fichero da 44.718 parejas (bytes, valor)
que nadie ha elegido.

| | |
|---|---|
| Números decodificados y comparados con el fuente | **44.718, exactos** |
| Vueltos a codificar y comparados **byte a byte** | **44.718 de 44.718** |
| Negativos dentro de la comparación | **1.616** |
| Ficheros `.hpmat` reales leídos y reescritos idénticos | **9 de 9** |

Los negativos son los que valieron: el primer intento puso un `1` en el nibble
de signo y falló en exactamente los 1.482 negativos de la muestra. Es un `9`.

**Lo que abre**: una matriz entera se lleva a la calculadora **como fichero**,
sin pegar nada. **Lo que no**: generar el bloque compilado entero, que además
de números lleva registros de símbolo. Lo que se sabe de esa estructura queda
documentado, que es la mitad del trabajo para quien siga.

## Para qué sirve de verdad el intérprete

Si tienes el mismo cálculo escrito dos veces —en PPL para la calculadora y en
Python para desarrollar— ninguna prueba normal puede decirte si divergen: cada
implementación es coherente consigo misma y las dos pasan sus propios tests.
Ejecutando el PPL de verdad y comparando, la divergencia sale sola.

En el primer proyecto donde se usó, un barrido de 2.162 comparaciones sacadas
de los propios datos dio **2.060 coincidencias y 102 fallos, todos la misma
causa**: la búsqueda inversa por presión no contemplaba la región
supercrítica, mientras que la de (P,T) sí. En la calculadora eso significaba
que el agua a 25 MPa se podía consultar por (P,T) pero no por (P,h) ni por
(P,s) —que es justo la expansión isentrópica de un ciclo Rankine
supercrítico—. Tres bancadas de pruebas, 1.599 comprobaciones, y ninguna podía
verlo.

El barrido está en [`examples/conformidad.py`](examples/conformidad.py) como
plantilla para adaptar.

## Probar

```bash
python tests/test_lint.py      # 16: que caza, y que no da falsas alarmas
python tests/test_pplrun.py    # 58: el subconjunto, y que falla donde debe
python tests/test_hpprgm.py    # round-trip sobre TUS binarios del CK
python tests/test_mkapp.py     # 29: la app se construye, y --check ve
python tests/test_hpreal.py    # el numero interno, contra 44.718 casos reales
```

`test_hpprgm.py`, `test_mkapp.py` y `test_hpreal.py` buscan la carpeta del
Connectivity Kit y se saltan lo que no encuentren, así que en una máquina sin
calculadora no fallan: avisan y siguen.

## Usarlo como skill de Claude Code

El repositorio **es** una skill: tiene `SKILL.md` en la raíz. Clonándolo
dentro de `~/.claude/skills/` queda activo, y cualquier sesión que toque
ficheros `.hpprgm` o código PPL tiene delante las reglas medidas en vez de
improvisar sintaxis.

```bash
git clone <url> ~/.claude/skills/hp-prime
```

## Lo que no hace

- **No genera el bloque compilado entero** de un programa de datos, así que los
  programas con matrices grandes se siguen pegando una vez a mano. No estorba:
  los datos no cambian, el código sí. Lo que **sí** está resuelto es el formato
  de sus números; lo que falta es la gramática de los registros de símbolo que
  van entre matriz y matriz, y lo que se sabe de ella está escrito.
- **No dibuja la interfaz.** `INPUT`, `CHOOSE`, `TEXTOUT_P` y compañía se
  anotan pero no se pintan: eso sigue necesitando ojos en el emulador. Lo que
  sí se puede sacar del dibujo —selección, ventana, qué hace cada tecla, y que
  cada texto quepa en su columna— se prueba en el PC, y cómo hacerlo está en
  [`references/interfaz.md`](references/interfaz.md).
- **No ejecuta MicroPython.** El puente `hpprime.eval` sólo existe en la
  calculadora. Lo que se puede hacer es escribir el motor de forma que el
  fichero que calcula sea **el mismo** en los dos sitios, con una sola capa
  sustituible debajo — ver
  [`references/micropython.md`](references/micropython.md).
- **No genera el `.hpapp` desde cero.** Se copia el de una app que funcione, y
  el kit trae dos. Su gramática interna no está descifrada más allá del byte de
  la vista de arranque, y no hace falta que lo esté.
- **No sustituye a probar en la calculadora.** Reduce mucho las vueltas, pero
  el último paso sigue siendo una G2 de verdad.

### Y lo que falta a propósito

No por no poder, sino porque meterlo a ojo sería peor que no tenerlo:

- **Las funciones de cadena del intérprete** (`LEFT`, `MID`, `INSTRING`,
  `SORT`…). Sus detalles de borde no están medidos, y una semántica inventada
  daría un número donde la calculadora da otro — la divergencia exacta que este
  kit existe para cazar. Mídelas y añádelas con su caso en las pruebas.
- **Una regla de linter para indexar un global declarado en otro programa.** Es
  un error de compilación real y está documentado, pero no se puede decidir
  mirando un fichero: `TS1(1)` y `TPT(3,350)` se escriben igual. Marcarlo daría
  una falsa alarma por cada llamada entre programas.
- **`.hplist`, las matrices complejas y la gramática del `.hpapp`.** Se sabe
  dónde empiezan y en qué se diferencian; nadie los ha necesitado todavía.

## Lo que sigue sin estar medido

Lo honesto, para que nadie se apoye en ello:

| | |
|---|---|
| La velocidad de PPL en la calculadora | un solo ancla: 60 iteraciones de bisección «por debajo del segundo» |
| La velocidad de MicroPython | sin medir. Del puente sí: **0,2 ms** por cruce |
| Una app de **PPL** construida entera por `mkapp.py` | sus piezas están validadas por separado; la combinación no se ha abierto en hardware |
| El límite de memoria de una app de Python | sin medir |
| **G1** | todo esto es de una **G2**. El firmware es el mismo; el hardware, no |

## Método

Lo que resuelve los problemas de PPL no es razonar sobre la sintaxis: es
**medir programas que ya funcionan en esa misma calculadora** y comparar
métricas. Un error que no se mueve después de un arreglo significa que la
hipótesis es falsa, no que el arreglo fuera insuficiente.

Cuando aparezca un límite nuevo, va a [`references/ppl.md`](references/ppl.md)
**con la evidencia** —qué programa, qué firmware— y con su regla en el linter
y su caso en las pruebas. Lo que no está medido no se apunta como cierto.

Firmware de referencia: **G2, 2.4 revisión 15515 (2025-09-15)**.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
