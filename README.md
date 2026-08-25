# hp-prime-kit — herramientas para programar la HP Prime en serio

Tres herramientas en Python para trabajar con **HP PPL**, el lenguaje de las
calculadoras HP Prime, desde el PC:

| | |
|---|---|
| **`scripts/lint_ppl.py`** | caza antes de compilar los errores que el compilador de la Prime no sabe explicar |
| **`scripts/hpprgm.py`** | lee y escribe `.hpprgm`, el formato binario de los programas |
| **`scripts/pplrun.py`** | **ejecuta PPL en el PC**, para probar el fichero que se instala |

Sin dependencias: Python 3.7+ y nada más.

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
```

El `.hpprgm` es un contenedor TLV anidado con el fuente dentro **literal, en
UTF-16LE**. Está documentado en
[`references/formato-hpprgm.md`](references/formato-hpprgm.md) y verificado
reconstruyendo programas byte a byte, incluido uno de 1 MB con datos
compilados.

Sirve para dos cosas: **desplegar copiando un fichero** en vez de crear el
programa a mano y pegar el texto, y **comparar lo instalado con el
repositorio** para ver si la calculadora se ha quedado atrás.

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
globales y locales, y el paso de matrices **por valor**. Lo de pantalla y
teclado no se dibuja: se anota y devuelve un valor neutro, para que el cálculo
corra sin interfaz.

Lo que no está cubierto **da error**, nunca un resultado inventado.

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
python tests/test_pplrun.py    # 39: el subconjunto, y que falla donde debe
python tests/test_hpprgm.py    # round-trip sobre TUS binarios del CK
```

`test_hpprgm.py` busca la carpeta del Connectivity Kit y se salta lo que no
encuentre, así que en una máquina sin calculadora no falla: avisa y sale.

## Usarlo como skill de Claude Code

El repositorio **es** una skill: tiene `SKILL.md` en la raíz. Clonándolo
dentro de `~/.claude/skills/` queda activo, y cualquier sesión que toque
ficheros `.hpprgm` o código PPL tiene delante las reglas medidas en vez de
improvisar sintaxis.

```bash
git clone <url> ~/.claude/skills/hp-prime
```

## Lo que no hace

- **No genera el bloque compilado** de un programa de datos, así que los
  programas con matrices grandes se siguen pegando una vez a mano. No estorba:
  los datos no cambian, el código sí.
- **No dibuja la interfaz.** `INPUT`, `CHOOSE`, `TEXTOUT_P` y compañía se
  anotan pero no se pintan: eso sigue necesitando ojos en el emulador.
- **No sustituye a probar en la calculadora.** Reduce mucho las vueltas, pero
  el último paso sigue siendo una G2 de verdad.

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
