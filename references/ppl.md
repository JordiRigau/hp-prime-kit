# PPL: lo que está medido

Firmware de referencia: **G2, 2.4 revisión 15515 (2025-09-15)**. Sus notas de
versión sólo mencionan aritmética exacta con fracciones y multiplicación
implícita: ningún cambio de sintaxis.

Todo lo que hay aquí está comprobado en una calculadora real. Lo que no, se
marca como no confirmado.

---

## 1. Los límites que de verdad rompen

| Lo que no compila | Por qué | Forma correcta |
|---|---|---|
| **`LOCAL` con demasiadas variables** | límite de **7-8 por sentencia**. Da *syntax error* señalando la línea del `LOCAL`, sin decir qué sobra | varias sentencias `LOCAL` seguidas, en grupos de 6 |
| `n := SIZE(M)(1);` | no se puede indexar el resultado de una llamada | `d := DIM(M);` y luego `d(1)` |
| `EXPORT A:=1, B:=2, …;` | falló con 7 variables inicializadas en una línea | una declaración por línea |
| `LOCAL` a media función | todos los locales van juntos al principio del `BEGIN` | declararlos arriba |
| `ENDIF`, `ENDFOR`, `ENDWHILE` | no existen | `END` para todo |

**Evidencia del límite de `LOCAL`**, medida sobre programas que compilan en
esa misma calculadora: `TRAFOS` declara **8** y compila; `Cargas Trifásicas`,
`FPefectivo` y `Etec_4_LINIES` se quedan en **7**. Las funciones que fallaban
declaraban **13, 16 y 18**.

## 2. Hipótesis que resultaron FALSAS

No las repitas: cada una costó una ronda de compilación.

| Hipótesis | Por qué es falsa |
|---|---|
| «`RETURN` dentro de un `FOR`/`REPEAT` no vale» | `INTERP.hpprgm`, que funciona, tiene **2** |
| «letra + dígito está reservado (`r2`, `y1`)» | `Etec_4_LINIES` usa `L12, L13, L14, L15…` como locales |
| «`LOCAL m` choca con las matrices `M0..M9`» | correlación casual: lo que fallaba era el número de locales |
| «varios locales con valor inicial en una línea» | el tutorial de E. Shore usa `local x1:=160, x2:=299, x3:=21` |

Sin confirmar: `i` (unidad imaginaria) y `e` (número de Euler) como nombres de
local. Prefijar los locales (`zm`, `zres`…) sale gratis y evita la duda.

## 3. Sintaxis, lo justo

```ppl
// comentario de línea

EXPORT VAR1, VAR2;              // globales, persisten entre usos
EXPORT MIDATO:=[[1,2],[3,4]];

EXPORT FUNC(a, b)
BEGIN
  LOCAL x, y;                   // TODOS los locales, al principio
  x := a + b;
  RETURN x;
END;                            // el ; del END es obligatorio
```

- `EXPORT` hace visible la función desde otros programas y desde Home; sin él
  es privada del fichero.
- **Todo es 1-based.** Es el error más común al portar desde Python.
- Igualdad `==`, asignación `:=`, distinto `<>`. Lógicos `AND`, `OR`, `NOT`.
- **Hay trampa de errores, pero no excepciones propias.**
  `IFERR sentencias THEN sentencias [ELSE sentencias] END;` atrapa un error
  del sistema y deja su código en `Ans` (`STRINGFROMID` lo convierte en
  mensaje). Lo que **no** hay es forma de lanzar un error propio con un
  valor dentro, así que para una API que devuelve resultados sigue haciendo
  falta un convenio: por ejemplo una región `-1` con el motivo, y `{}` en las
  funciones que devuelven listas. `IFERR` sirve para blindar una llamada
  concreta, no para propagar errores.

| Necesidad | PPL |
|---|---|
| tamaño de lista o cadena | `SIZE(L)` |
| dimensiones de matriz | `d := DIM(M);` → `d(1)`, `d(2)` |
| añadir al final de una lista | `L(SIZE(L)+1) := v;` |
| número → cadena / cadena → número | `STRING(x)` / `EXPR(s)` |
| tipo de una variable | `TYPE(v)` (0 real, 2 cadena, 3 matriz, 6 lista) |

Control de flujo: `IF … THEN … ELSE … END;` · `FOR i FROM 1 TO n DO … END;`
(`DOWNTO` y `STEP` también) · `WHILE … DO … END;` · `REPEAT … UNTIL c;` ·
`CASE … DEFAULT … END;` · `IFERR … THEN … END;` · `BREAK` · `CONTINUE` ·
`KILL` · `IFTE(c, a, b)` como expresión.

Las palabras clave son **insensibles a mayúsculas** (`local x := 1;` vale);
los nombres de variable, no.

Entrada y salida:

```ppl
INPUT({v1,v2}, "Título", {"Etiq1:","Etiq2:"}, {"ayuda1","ayuda2"});  // 1 = OK
CHOOSE(var, "Título", "op1", "op2");   // var recibe el índice
MSGBOX("mensaje");
RECT();                                  // borra la pantalla (320x240)
TEXTOUT_P("texto", x, y, fuente, RGB(r,g,b));
WAIT(-1);                                // espera tecla, devuelve su código
```

## 4. Trampas de tiempo de ejecución

| Trampa | Detalle |
|---|---|
| **Matrices por valor** | pasar una matriz grande a una función la **copia**. Con datos grandes, accede a globales en vez de pasarlos como argumento |
| **`EXPR("")` falla** | comprueba siempre `SIZE(s) > 0` antes de evaluar el contenido de un campo |
| **Nombres globales** | los exportados comparten espacio con Home: usa prefijos para no chocar |
| **Decimal en el fuente** | siempre `.`, aunque la calculadora muestre `,` |
| **Acceso dinámico** | `EXPR("NOMBRE")` da la variable cuyo nombre se construye al vuelo; hazlo una vez al cargar, nunca por elemento |
| **`INPUT` construye sus etiquetas una sola vez** | es modal: una etiqueta que dependa de otro campo del mismo formulario no se puede refrescar. Ofrece las variantes fijas |
| **`WAIT(-1)`** | devuelve un identificador de posición de tecla, **no el ASCII**. Confírmalo con una prueba: `[Enter]` es 30 |
| **App en blanco** | no tiene vista donde reposar, así que `[View]`/`[Num]` no llegan al programa: dibuja el menú en pantalla y lee las teclas tú |
| **Orden de compilación** | un programa sólo ve las funciones de otro **si se compiló después**. Pega datos → motor → app |
| **Lo exportado desde el programa de una app** | queda ligado a esa app. Si el motor tiene que ser reutilizable, ponlo en un programa del catálogo |

## 5. El formato `.hpprgm`

Contenedor TLV anidado, little-endian, con el fuente dentro **literal en
UTF-16LE** — ni comprimido ni cifrado. Un programa de datos lleva además un
bloque compilado antes del fuente, que es lo que hace que pese ~3x y que abra
al instante en la calculadora que lo recibe.

Se lee y se escribe con `scripts/hpprgm.py`. El formato entero, las dos
trampas que tiene y cómo está verificado, en
[`formato-hpprgm.md`](formato-hpprgm.md).

## 6. Fuentes

| Fuente | Para qué sirve |
|---|---|
| *HP Prime Programming Reference* (HP) | referencia puntual de comandos, no para aprender |
| **hpmuseum.org/forum**, subforo HP Prime | la mejor: código completo y comportamientos reales |
| **en.hpprime.club** (E. Shore / H. Klaver) | tutoriales con ejemplos que funcionan |
| **hpcalc.org** | archivo de programas: busca ahí antes de escribir nada |

Enlaces concretos:
[límites no documentados](https://www.hpmuseum.org/cgi-bin/archv021.cgi?read=254706) ·
[tutorial de E. Shore](https://literature.hpcalc.org/community/hpprime-prog-tutorial.pdf) ·
[firmware G2 2.4.15515](https://www.hpcalc.org/details/7783)
