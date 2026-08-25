# El formato `.hpprgm`

Lo que la HP Prime guarda cuando escribes un programa. No está documentado por
HP; esto es lo que se dedujo midiendo ficheros reales escritos por el
Connectivity Kit y verificándolo por reconstrucción byte a byte.

**La conclusión práctica**: el fuente PPL va dentro **literal**, en UTF-16LE.
Ni comprimido ni cifrado. Se puede leer y se puede escribir desde el PC, así
que desplegar deja de ser «crear el programa a mano y pegar el texto» y pasa a
ser copiar un fichero.

## Estructura

Contenedor TLV anidado, todo little-endian:

```
offset  contenido
------  ----------------------------------------------------------
0       7C 61 8A B2                       magic
4       FE FF FF FF   00 00 00 00         preámbulo
12      [u32 longitud][longitud bytes]    registros, anidados
...     (opcional) bloque compilado
...     [u32 longitud][u32 etiqueta][fuente UTF-16LE][NUL]
...     cola
```

Cada registro es una longitud de 4 bytes seguida de esos bytes. Dentro del
payload, unos registros llevan una etiqueta de 4 bytes antes de sus hijos y
otros no — por eso descender por el árbol «cogiendo el último hijo» **no
funciona**, y es el error que costó una ronda aquí.

## Cómo se localiza el fuente

La forma del registro del fuente sí es firme:

```
[u32 longitud][u32 etiqueta][texto UTF-16LE][NUL]
```

Así que se busca por ahí: recorrer los offsets, quedarse con los que dan un
bloque que decodifica como UTF-16LE, acaba en NUL y es casi todo ASCII
imprimible, y coger el mayor. Los registros que hay que reajustar al cambiar
el texto son **los que terminan exactamente donde él**.

Dos detalles que parecen menores y no lo son:

- **El barrido es byte a byte, no de 4 en 4.** Cuando delante del fuente hay
  un bloque compilado, su tamaño no es múltiplo de 4 y el registro del fuente
  queda desalineado. En el fichero de datos de TermoHP empieza en el offset
  367.557, que es impar.
- **La cola no mide siempre 1008 bytes.** Lo mide en todo lo que escribe el
  Connectivity Kit, y suponerlo funciona… hasta que se prueba con las apps de
  fábrica de la calculadora, que lo desmienten. No hay que darlo por supuesto:
  lo que va detrás del fuente se conserva tal cual.

## Saltos de línea

El Connectivity Kit guarda **el buffer del editor**: saltos **LF** y **sin
salto final**. Un fichero de texto normal del PC sí lleva salto final, así que
al generar hay que quitar uno para que salga byte a byte lo mismo que
escribiría el CK. Las apps de fábrica de HP, en cambio, llevan **CRLF**
dentro: el contenedor acepta las dos cosas.

## El bloque compilado

Un programa que sólo tiene código es cabecera + fuente + cola. Uno que declara
matrices grandes lleva además un bloque **antes** del fuente con los números
ya en formato interno de la calculadora.

Se nota en el tamaño. En TermoHP:

| Programa | Fuente | Fichero | Bloque compilado |
|---|---|---|---|
| `TERMOLIB` (código) | 36 KB | 37 KB | — |
| `TDAT` (43.796 números) | 632 KB | 1.001 KB | 367 KB |

Ese bloque es lo que hace que un programa de datos abra **al instante** en la
calculadora que lo recibe, sin esperar compilación. Generarlo no está resuelto:
`hpprgm.py` rechaza usar como plantilla un programa que lo lleve, porque
cambiarle el fuente lo dejaría descuadrado. En la práctica no estorba — los
datos se pegan una vez y no cambian nunca; el código, que sí cambia, se
despliega por fichero.

## Apps

Una app es una carpeta `.hpappdir` con:

```
X.hpapp        ajustes
X.hpappprgm    el programa de la app -- mismo formato que un .hpprgm
X.hpappnote    la nota
icon.png       el icono
```

El `.hpappprgm` se lee y se escribe igual que cualquier otro programa.

## Cómo está verificado

No basta con que el round-trip cuadre: leer y escribir con el **mismo** error
da un round-trip perfecto y un resultado equivocado. Eso pasó aquí — la
primera versión arrastraba 88 bytes de cabecera como si fueran fuente y el
round-trip salía idéntico igualmente.

Lo que lo verifica de verdad es reconstruir un programa **desde la plantilla
de otro de distinto tamaño**, y comparar con lo que escribió el Connectivity
Kit:

| Prueba | Resultado |
|---|---|
| Round-trip de un programa de código (37 KB) | idéntico |
| Round-trip de un programa de datos (1 MB, con bloque compilado) | idéntico |
| Round-trip de un `.hpappprgm` | idéntico |
| Round-trip de las apps de fábrica (con CRLF) | idéntico |
| App de 11.918 caracteres reconstruida desde una plantilla de 18.007 | **byte a byte igual al fichero del CK** |
| App de fábrica de 579 caracteres desde la misma plantilla | **byte a byte igual** |

Las dos últimas son las que valen: cambian el tamaño, así que ejercitan la
aritmética de longitudes.

`tests/test_hpprgm.py` lo repite sobre los binarios que tengas en tu máquina.

## Qué se puede hacer con esto

```bash
# sacar el fuente de un programa instalado
python scripts/hpprgm.py read PROG.hpprgm -o fuente.txt

# ver si la calculadora se ha quedado atras respecto al repositorio
diff fuente.txt ppl/PROG.txt

# generar el binario desde el fuente
python scripts/hpprgm.py write fuente.txt -t plantilla.hpprgm -o PROG.hpprgm
```

La plantilla es cualquier `.hpprgm` de código que haya escrito el Connectivity
Kit; están en `Documentos\HP Connectivity Kit\Calculators\<tu calculadora>\`.
Se copia una vez y sirve para siempre.

Lo de comparar con el repositorio no es teórico: es lo que destapó que la app
instalada en la calculadora llevaba semanas dos commits por detrás del código
que se daba por bueno.
