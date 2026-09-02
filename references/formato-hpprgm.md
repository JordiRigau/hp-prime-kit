# El formato `.hpprgm`

Lo que la HP Prime guarda cuando escribes un programa. No está documentado por
HP; esto es lo que se dedujo midiendo ficheros reales escritos por el
Connectivity Kit y verificándolo por reconstrucción byte a byte.

**La conclusión práctica**: el fuente PPL va dentro **literal**, en UTF-16LE.
Ni comprimido ni cifrado. Se puede leer y se puede escribir desde el PC, así
que generar un programa deja de ser «crearlo a mano en el Connectivity Kit y
pegar el texto dentro». Ojo con el último paso, que tiene trampa — ver
[Cómo se instala](#como-se-instala-lo-generado).

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
- **La cola no es constante.** Mide 1008 bytes en casi todo, pero las apps de
  fábrica desmienten hasta eso, y además puede llevar **metadatos dentro**:
  entre dos ficheros con el mismo fuente aparecieron 15 bytes de diferencia
  ahí, con texto UTF-16 (`qt-p…`). No hay que darla por supuesta: lo que va
  detrás del fuente se conserva tal cual al reescribir, y al **generar** se
  copia la de la plantilla. La calculadora acepta el resultado, pero eso
  significa que generar no es byte-exacto para un fichero cualquiera: lo es
  para la cabecera y el fuente, que es lo que el escritor construye.

## Saltos de línea

El Connectivity Kit guarda **el buffer del editor**: saltos **LF** y **sin
salto final**. Un fichero de texto normal del PC sí lleva salto final, así que
al generar hay que quitar uno para que salga byte a byte lo mismo que
escribiría el CK. Las apps de fábrica de HP, en cambio, llevan **CRLF**
dentro: el contenedor acepta las dos cosas.

## El bloque compilado

Un programa que sólo tiene código, **tal como lo escribe el Connectivity
Kit**, es cabecera + fuente + cola, con el fuente empezando en el offset
**152 exacto**. Cualquier cosa por encima de 152 es bloque compilado: ése es
el criterio para saber si un fichero sirve de plantilla. (Un umbral más laxo
deja pasar los bloques pequeños que añade la calculadora — 96, 184, 360
bytes — y entonces lo generado sale justo esos bytes más corto.) Uno que declara matrices grandes lleva
además un bloque **antes** del fuente con los números ya en formato interno de
la calculadora. (La propia calculadora añade ese bloque a todo lo que guarda,
también al código suelto — ver «Quién escribe qué».)

Se nota en el tamaño. En TermoHP, con los ficheros del CK:

| Programa | Fuente | Fichero | Bloque compilado |
|---|---|---|---|
| `TERMOLIB` (código) | 36 KB | 37 KB | — |
| `TDAT` (43.796 números) | 632 KB | 1.001 KB | 367 KB |

Ese bloque es lo que hace que un programa de datos abra **al instante** en la
calculadora que lo recibe, sin esperar compilación. Generarlo no está resuelto:
`hpprgm.py` rechaza usar como plantilla un programa que lo lleve, porque
cambiarle el fuente lo dejaría descuadrado. En la práctica no estorba: los
datos se pegan una vez y no cambian nunca, y el código, que sí cambia, se
genera y se arrastra.

## El número interno, descifrado

Lo de dentro del bloque compilado ya no es opaco. **Un número son 8 bytes**,
little-endian; leídos como un entero de 64 bits:

```
bits  0..11   exponente decimal, complemento a dos de 12 bits
bits 12..59   12 digitos BCD de mantisa, el mas significativo arriba
bits 60..63   signo: 0 positivo, 9 negativo     (el convenio BCD de siempre)

valor = d1.d2d3...d12 x 10^exponente            y el cero es todo ceros
```

Del bloque de `TDAT`:

| Palabra | Signo | Mantisa | Exp | Valor |
|---|---|---|---|---|
| `9760000000000001` | 9 | `760000000000` | 1 | **−76** |
| `0600000000000FFC` | 0 | `600000000000` | −4 | **0,0006** |
| `0205991225000002` | 0 | `205991225000` | 2 | **205,991225** |
| `0915550000000000` | 0 | `915550000000` | 0 | **9,1555** |

### Cómo se descifró, que es lo que lo hace fiable

Con una **piedra de Rosetta**, no adivinando. Un programa de datos lleva el
bloque compilado **delante del fuente**, y el fuente son *los mismos números*
escritos en decimal. O sea que un solo fichero da decenas de miles de parejas
(bytes, valor) que nadie ha elegido:

| | |
|---|---|
| Matrices de `TDAT` localizadas en el bloque | **56 de 56** |
| Números decodificados y comparados con el fuente | **44.718, exactos** |
| Vueltos a codificar y comparados **byte a byte** | **44.718 de 44.718** |
| Negativos dentro de esa comparación | **1.616** |

Los negativos son los que importan: el primer intento puso un `1` en el nibble
de signo, el round-trip falló en exactamente 1.482 números —todos los
negativos— y ahí se vio que es un **9**. Sin negativos en la muestra, el error
habría pasado.

Se rehace sobre tus ficheros con `python tests/test_hpreal.py`.

### Lo que abre: `.hpmat`

Los ficheros `.hpmat` de las matrices `M0`..`M9` son **el mismo formato de
número** con una cabecera de 16 bytes:

```
00  01 00      constante en todos los observados
02  14 80      tipo: 8014 real, 8094 complejo (16 bytes por elemento)
04  u32 = 2    rango: 2 = matriz
08  u32        filas
12  u32        columnas
16  ...        los elementos, fila a fila, 8 bytes cada uno
```

Con eso, una matriz entera se lleva a la calculadora **como fichero**, sin
pegar nada y sin pasar por el fuente de ningún programa:

```bash
python scripts/hpreal.py read  M1.hpmat -o datos.csv
python scripts/hpreal.py write datos.csv -o M0.hpmat
```

El nombre del fichero manda: `M0.hpmat` es la matriz `M0`. Se arrastra a la
calculadora igual que un programa, y desde PPL se copia a donde haga falta con
una línea. Las matrices **complejas** se leen como error explícito, no como
números inventados: no están cubiertas.

Verificado: los nueve `.hpmat` reales de una G2 se leen y se vuelven a escribir
**byte a byte idénticos**, cabecera incluida.

### Lo que NO abre todavía: generar el bloque

El bloque no es sólo números. Entre matriz y matriz lleva registros con el
**nombre del símbolo en UTF-16LE**. Justo después de la primera matriz de
`TDAT` (que ocupa hasta el offset 4504 del bloque) aparece:

```
54 13 00 00   44 00 00 00   8B 01 40 00   41 00 49 00 47 00 55 00 41 00 53 00 50 00
[longitud]    [longitud]    [etiqueta]    A  I  G  U  A  S  P   en UTF-16LE
```

O sea: la misma clase de contenedor TLV que por fuera, con el nombre del global
y luego su matriz. `hpreal.py matrices_de_bloque()` recorre lo que reconoce
—las matrices— y se salta el resto, así que sirve para **mirar dentro**, no
para reescribirlo:

```bash
python scripts/hpreal.py nums TDAT.hpprgm
```

Para generar el bloque faltaría la gramática de esos registros. Ya no es el
número lo que lo impide, que era la parte opaca; es una estructura, y las
estructuras se leen midiendo. Mientras tanto sigue en pie lo de siempre: los
datos se pegan una vez y no cambian nunca.

## Otros ficheros de la calculadora

En la carpeta espejo del CK hay más cosas, y conviene saber cuáles sabe leer
este kit y cuáles no, para no perder el tiempo:

| | Qué es | ¿Lo lee el kit? |
|---|---|---|
| `.hpprgm` | un programa | **sí** — `hpprgm.py` |
| `.hpappdir/` | una app | **sí** — `mkapp.py`, y su `.hpappprgm` con `hpprgm.py` |
| `.hpmat` | una de las matrices `M0`..`M9` | **sí** — `hpreal.py` (las reales) |
| `.hplist` | una de las listas `L0`..`L9` | no: otra cabecera (`FE FF 16 00`) y elementos de tamaño variable con etiqueta de tipo. Una lista vacía son 8 bytes |
| `.hpsettings`, `settings` | ajustes; `settings` lleva el identificador de la calculadora (el número de serie, si es física) | no |
| `.hpexammode` | un modo de examen | no |

Ninguno de éstos empieza por el magic `7C 61 8A B2`: **no son el contenedor
TLV**, así que `hpprgm.py` los rechaza a la primera en vez de inventarse nada.

## Apps

Una app es una carpeta `.hpappdir` con:

```
X.hpapp        ajustes
X.hpappprgm    el programa de la app -- mismo formato que un .hpprgm
X.hpappnote    la nota
icon.png       el icono
```

El `.hpappprgm` se lee y se escribe igual que cualquier otro programa — con una
excepción: en una app de **Python** está **vacío** (1152 bytes, sólo la tabla de
símbolos con un `Main`), y entonces no tiene bloque de fuente, así que `leer`
falla y no sirve de plantilla. El código de esa app está en los `.py` de la
carpeta.

El `.hpapp` no se genera: se copia de una app que funcione. Sus **últimos cuatro
bytes son la vista de arranque**, y es la diferencia entre que la app abra su
pantalla o la consola de Python.

Todo eso —los envoltorios, el icono, los ganchos, cómo se construye una app
desde el PC— está en [`apps.md`](apps.md).

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

## Quién escribe qué, y por qué importa

Hay **dos productores** de ficheros `.hpprgm`, y no escriben lo mismo:

| Lo escribe | Qué mete | Ejemplo (`TERMOLIB`, mismo fuente) |
|---|---|---|
| El **Connectivity Kit** | sólo el fuente | 38.888 B |
| La **calculadora**, al guardar | fuente **+ su bloque compilado** | 42.078 B (3.190 de bloque) |

Es decir: el bloque compilado no aparece sólo en los programas de datos. La
calculadora se lo añade a cualquier programa cuando lo guarda, también si es
puro código. El de datos es llamativo porque el bloque es enorme (367 KB en un
fichero de 1 MB), pero el mecanismo es el mismo.

Los dos se leen igual de bien, y el round-trip es exacto en ambos. Pero **para
generar hay que usar como plantilla uno del Connectivity Kit**: los de la
calculadora llevan un bloque compilado que dejaría de corresponder al fuente
nuevo, y `hpprgm.py write` los rechaza por eso.

<a name="como-se-instala-lo-generado"></a>
## Cómo se instala lo generado

**La carpeta `Calculators\<tu calculadora>\` no es un buzón.** Es un espejo
que el Connectivity Kit escribe *desde* la calculadora. Dejar ahí un fichero
con el CK cerrado no instala nada: al conectar, el CK sobrescribe la carpeta
con lo que haya en la calculadora y el fichero desaparece.

Comprobado por las malas: se copiaron ahí dos binarios corregidos, y al abrir
el emulador seguía la versión vieja. Los ficheros que quedaron en la carpeta
después eran los que había escrito la calculadora, con su bloque compilado.

El manual del CK dice que se arrastra el fichero desde el escritorio al panel
de calculadoras. **En la máquina donde se desarrolló esto, eso no funciona**:
el cursor muestra el símbolo de prohibido y no pasa nada, sin ningún diálogo.

Y no es cosa de los ficheros generados. La comprobación que lo zanja: se sacó
al escritorio un programa **escrito por el propio CK** y se volvió a arrastrar
adentro — mismo rechazo. Así que el generador queda descartado como causa.

Estado real de cada vía, sin adornos:

| Vía | Estado |
|---|---|
| Arrastrar el fichero desde el explorador al CK | **funciona** — es la vía buena |
| Arrastrar entre calculadoras **dentro** del CK | funciona |
| Pegar el texto en el editor del CK | funciona, pero es el camino lento |
| Copiar el fichero a `Calculators\<calculadora>\` | **no instala**: esa carpeta es un espejo y el CK la sobrescribe al conectar |

### Si el arrastre se rechaza con el cursor de prohibido

Síntoma: arrastras el `.hpprgm` sobre la calculadora, sale el símbolo de
prohibido y no pasa nada. Ningún diálogo, ningún error.

**No es el fichero.** La forma de comprobarlo en diez segundos es arrastrar un
programa que haya escrito el propio CK: si también lo rechaza, el problema es
del entorno.

La causa aquí fue que el Connectivity Kit tenía activado, en su pestaña de
compatibilidad, **modo Windows 8 y «ejecutar como administrador»**. Windows
prohíbe el arrastre entre procesos de distinto nivel de integridad (UIPI): el
explorador va sin elevar y no puede soltar nada en una ventana elevada. Al
quitar esas dos casillas, el arrastre funciona.

Dónde mirar: propiedades del acceso directo **y del `.exe`** → *Compatibilidad*.
Ojo con comprobarlo por registro: la marca vive en
`HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers`
con la ruta del ejecutable como nombre del valor, pero si la casilla está
puesta en un acceso directo concreto no aparece ahí — hay que mirar el `.lnk`
que se usa de verdad para arrancarlo, que no tiene por qué ser el del
escritorio.

## El escritor, validado contra hardware

Un programa generado desde Python —cabecera de una plantilla, fuente metido
por `hpprgm.py`, nunca tocado por el CK ni por la calculadora— **acabó
cargado y compilado en una HP Prime**:

| | |
|---|---|
| Lo generado | 3.134 bytes, sin bloque compilado |
| Lo que quedó en la calculadora | 3.406 bytes, con **272 de bloque compilado** |
| El fuente de dentro | idéntico al `.txt` original |
| Los acentos (`àèóç`) | intactos |
| **Ejecutado en la calculadora** | `PESC3()` → **1** |

El bloque compilado lo escribe la calculadora al cargar el programa, así que
su sola presencia ya dice que lo entendió. Pero la prueba de verdad es la
última fila: `PESC3()` comprueba por dentro que el bucle da 385 y que la
cadena con acentos mide 26 caracteres. **El programa generado desde Python
calcula bien en la calculadora.**

El programa de prueba está en `examples/PROVAESC.txt`: se regenera y se
repite el experimento con un comando.

Una pista para saber cuál es tu calculadora cuando hay varias carpetas: el
fichero `settings` de cada una lleva su identificador, y el de la calculadora
física es su número de serie. El nombre de la carpeta es el que muestra el CK
en su árbol.

## Qué se puede hacer con esto

```bash
# sacar el fuente de un programa instalado
python scripts/hpprgm.py read PROG.hpprgm -o fuente.txt

# ver si la calculadora se ha quedado atras respecto al repositorio
diff fuente.txt ppl/PROG.txt

# generar el binario desde el fuente
python scripts/hpprgm.py write fuente.txt -t plantilla.hpprgm -o PROG.hpprgm
```

### Conseguir una plantilla, que no es tan fácil como suena

La plantilla es un `.hpprgm` de código **escrito por el Connectivity Kit**: sin
bloque compilado, con el fuente empezando en el offset 152. Se copia una vez y
sirve para siempre.

Lo que no vale es dar por hecho que los hay en
`Documentos\HP Connectivity Kit\Calculators\<tu calculadora>\`. Esa carpeta es
el **espejo**, o sea que todo lo que hay dentro ha pasado por la calculadora —y
la calculadora le añade su bloque compilado a todo lo que guarda—. Medido en la
máquina donde se escribió esto: de **58** contenedores de programa en el espejo,
**2** servían de plantilla, y los dos eran `.hpappprgm` de apps.

```bash
python scripts/hpprgm.py read CANDIDATO.hpprgm
```

Si dice *«lleva N bytes de bloque compilado antes del fuente»*, no sirve; y
`write` lo rechaza por su cuenta, así que el error no se cuela.

**La forma fiable de fabricar una**: crea un programa nuevo **dentro del propio
Connectivity Kit** (clic derecho → *Nuevo* sobre *Program*), escribe dos líneas
que compilen, y **cópialo fuera de la carpeta espejo antes de enviarlo a la
calculadora**. Ése es un fichero escrito por el CK y nunca tocado por la
calculadora, que es exactamente lo que hace falta.

Lo de comparar con el repositorio no es teórico: es lo que destapó que la app
instalada en la calculadora llevaba semanas dos commits por detrás del código
que se daba por bueno. Y como el fuente se puede sacar también de los ficheros
que escribe la propia calculadora, sirve para confirmar que lo que acabas de
instalar es de verdad lo que querías instalar.
