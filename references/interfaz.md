# Interfaces en la HP Prime

320 × 240 píxeles, un teclado con códigos que no son ASCII, una pantalla táctil
y ningún gestor de ventanas. La documentación oficial describe los comandos uno
a uno y no dice nada de cómo se combinan, así que casi todo lo que hay aquí sale
de **medirlo en una G2** o de **leer apps que funcionan en ella**.

Vale para los dos lados: desde PPL se llama directamente, y desde Python se
llama lo mismo cruzando el puente `hpprime.eval` (ver
[`micropython.md`](micropython.md)). Los ejemplos alternan según de dónde salió
la medida.

---

## 1. La geometría

| | |
|---|---|
| Pantalla | **320 × 240** |
| Zona de la app | y de **0 a 212** |
| Fila de teclas de pantalla | y de **213 a 239** |
| Ancho de cada tecla de pantalla | ~**53 px** (320 / 6) |

Esas dos últimas están medidas sobre `SkeletonApp`, y son las que convierten un
toque en un botón:

```python
def menu_de_toc(x, y):
    """Que tecla de pantalla se ha tocado, o 0 si el toque no cae ahi."""
    if y < 213:
        return 0
    n = int(x / 53) + 1
    return n if 1 <= n <= 6 else 0
```

Un reparto que sale bien para una lista: cabecera de 20 px, siete filas de 24,
y la fila de ayuda debajo.

## 2. Los ladrillos que da la plataforma

| Necesidad | Comando |
|---|---|
| Borrar la pantalla | `RECT()` · desde Python, `fillrect(0,0,0,320,240,col,col)` |
| Rectángulo | `fillrect(gr, x, y, w, h, borde, relleno)` |
| Texto | `TEXTOUT_P(txt, G0, x, y, fuente, color [, ancho])` |
| Fila de seis botones | `DRAWMENU("a","b","c","d","e","f")` |
| Formulario | `INPUT(campos, titulo, etiquetas, ayudas)` |
| Menú emergente | `CHOOSE(var, titulo, "op1", "op2", …)` |
| Aviso modal | `MSGBOX("mensaje")` |
| Tecla pendiente | `GETKEY` |
| Toque | `MOUSE` |
| Dibujo sin parpadeo | `DIMGROB_P` a un grob fuera de pantalla y `BLIT_P` a `G0` |

Fuentes de `TEXTOUT_P`: 1 pequeña, 2 normal, 3 grande (hasta 7). Colores con
`RGB(r,g,b)` en PPL, enteros `0xRRGGBB` desde Python.

## 3. `TEXTOUT_P` recorta — y si no se lo pides, se derrama

El séptimo argumento de `TEXTOUT_P` es la **anchura máxima en píxeles**. Sin él,
un texto largo se escribe por encima de la columna vecina y sigue hasta salirse
de la pantalla.

Y aquí está lo que lo hace peligroso:

> **Un texto que no cabe no da ningún error.** La calculadora lo corta o lo
> pinta encima de otra cosa, y te quedas sin saber qué decía.

Dos capturas de la calculadora enseñaron el mismo fallo por dos sitios:

```
eta      -    buit=isentropica, -1=in...      <- 30 caracteres en 70 pixeles
1 taula  2 gas ...                            <- etiqueta de INPUT recortada
```

Tres cosas lo cierran:

1. **Pasar siempre la anchura.** Con ella, un texto largo como mucho se queda a
   medias, pero dentro de su columna.
2. **La ayuda larga, a su propia línea**, con los 320 píxeles enteros y
   cambiando según la celda donde estés. Una tercera columna tiene 70.
3. **Un módulo de geometría sin un solo `import`**, con todas las `x` de todas
   las columnas, para que una prueba del PC pueda leerlo y comprobar pantalla
   por pantalla que cada texto cabe donde va.

Las anchuras de letra de esa prueba son **estimaciones prudentes**: se toma el
carácter más ancho, así que si dice que cabe, cabe seguro; al revés no. Encontró
siete textos pasados a la primera, dos de ellos aún no vistos en pantalla.

Si algún día hace falta medir de verdad, la forma es la del Markdown Viewer:
`TEXTOUT_P` **devuelve la `x` donde acaba**, así que pintando sobre un grob
fuera de pantalla se tiene la anchura exacta.

```python
def textw(txt, fnt=2):
    dimgrob(9, 512, 22, 0)
    return eval('textout_p("' + txt + '",G9,0,0,0,0)')
```

## 4. `INPUT`: lo que hay que saber antes de diseñar con él

```ppl
zok := INPUT(
  { {TCUR, TNAMS, {22, 72, 0}},                    // desplegable
    {TD1, TPROP, {22, 30, 1}}, {TV1, [0], {58, 37, 1}},   // dos campos, una fila
    {TD2, TPROP, {22, 30, 2}}, {TV2, [0], {58, 37, 2}} },
  "TERMO - quines dues coneixes?",
  {"Sust", "Dada 1", "=", "Dada 2", "="},
  {"substancia", "1a magnitud coneguda", "valor, en la unitat del desplegable",
   "2a magnitud coneguda", "valor, en la unitat del desplegable"});
```

Devuelve **1 si se acepta, 0 si se cancela**. Lo medido:

| | |
|---|---|
| **Posición de un campo** | `{x%, ancho%, fila}`, en **porcentaje** de la pantalla |
| **La etiqueta va a la izquierda del campo** | con `x=5` las etiquetas salían recortadas a un punto; con `x=22` caben |
| **Tipo de campo** | `[0]` es real: se teclea el número tal cual, **sin comillas** |
| **Un campo de texto exige comillas** | teclear `"0.2"` en un examen es un impuesto por cada dato |
| **Es modal y construye sus etiquetas una sola vez** | una etiqueta que dependa de otro campo del mismo formulario **no se puede refrescar** |
| **Las variables tienen que existir y tener ya el tipo correcto** | |

Ese detalle de las comillas decidió una interfaz entera. En TermoHP se probaron
tres formas de decir *«qué dos propiedades conozco»*:

| | Menú `CHOOSE` de pares | Formulario con campos en blanco | **Dos desplegables + dos números** |
|---|---|---|---|
| Hay que decidir antes | sí | no | no |
| Campo vacío = desconocido | — | sí, pero exige campos de **texto** | no hace falta |
| Comillas al teclear | no | **sí** | no |
| Unidad a la vista | no | no | **sí, y cambia con la sustancia** |

Ganaron los desplegables: dicen **qué** conoces, los campos numéricos **cuánto**,
y de paso enseñan la unidad. El formulario con huecos parecía mejor sobre el
papel y era peor en la máquina.

### Un `INPUT` de un campo, no un formulario de diez

Desde Python, y por dos razones que no se ven hasta que se usa:

```python
def demana(titol, etiqueta, valor):
    """Un solo campo. Devuelve el nuevo valor, o None si se cancelo."""
    ev('CX:=%s' % repr(float(valor)))
    r = ev('INPUT(CX,"%s","%s","")' % (titol, etiqueta))
    if not r:
        return None
    return ev('CX')
```

- Se puede **corregir un dato suelto** sin repasar los otros nueve.
- Las etiquetas **pueden depender del contexto** —la unidad del fluido de esa
  fila, por ejemplo—, que con un `INPUT` grande no se puede, porque las
  construye una sola vez.

## 5. El teclado

### `GETKEY` devuelve una posición, no un carácter

Es lo primero que descoloca: el código de `[Enter]` es **30**, no 13. Y el mismo
código significa una cosa u otra según el modo — el 42 es `1` en modo normal y
`y` en modo alfa.

Códigos, con de dónde sale cada uno:

| Tecla | Código | Confianza |
|---|---|---|
| `Enter` | **30** | **medido** en la calculadora con un programa de diagnóstico |
| `Esc` | 4 | dos apps que funcionan coinciden |
| ▲ ▼ ◄ ► | 2, 12, 7, 8 | dos apps que funcionan coinciden |
| Retroceso | 19 | ídem |
| `ON` | 46 | ídem |
| Teclas de pantalla 1..6 | 0, 5, 10, 1, 6, 11 | ídem, y en uso |
| Dígitos 1..9 | 42, 43, 44, 37, 38, 39, 32, 33, 34 | ídem, y en uso |
| `Help` | 3 | **deducido** del mapa de posiciones |
| `View` | 9 | **deducido** |

Las dos apps que coinciden son `CHOOSE_R` y el **Markdown Viewer**, escritas por
gente distinta y que corren las dos en esta calculadora.

**Diseña para fallar sin ruido**: en TermoHP, una tecla con código equivocado
cae en el caso por defecto, que es volver al formulario. Y un programa de tres
líneas dice el código de la tecla que pulses:

```ppl
EXPORT TKEY()
BEGIN
  LOCAL zk;
  RECT(); TEXTOUT_P("Prem una tecla...", 4, 40, 3);
  zk := TPAUSE();
  RECT(); TEXTOUT_P("codi = " + STRING(zk), 4, 40, 4);
  TPAUSE();
  RETURN zk;
END;
```

### Esperar una tecla: vaciar el buffer primero

Esto tiene una contradicción medida que conviene conocer antes de elegir:

> **En TermoHP, `WAIT(-1)` no esperó.** La pantalla de resultados pasaba de
> largo y volvía el formulario al instante. Parecía que esperaba porque, al
> acabar el programa, la pantalla se quedaba dibujada hasta que se pulsaba algo;
> en cuanto se metió el bucle, se vio que no.
>
> **En `SkeletonApp` y `CHOOSE_R`, `WAIT(-1)` es el bucle de eventos**: devuelve
> un número (tecla) o una lista (toque), y devuelve −1 cada 60 s.

La explicación más probable —**hipótesis, no medida**— es que había una tecla
pendiente en el buffer: la que acababa de aceptar el `INPUT`. Sea o no eso, la
forma que **sí funciona** en esta calculadora es vaciar y luego esperar:

```ppl
EXPORT TPAUSE()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;    // vaciar lo pendiente
  REPEAT zk := GETKEY; UNTIL zk >= 0;   // y ahora si, esperar
  RETURN zk;
END;
```

Desde Python, el mismo principio con `keyboard()` + `GETKEY()`, que es lo que
hace el Markdown Viewer:

```python
if keyboard():
    k = ev('GETKEY()')
```

`WAIT(-1)` gastaría menos batería y daría los toques en el mismo sitio. Si lo
usas, **compruébalo tú**: aquí se eligió lo comprobado sobre lo elegante.

## 6. El táctil, y el toque que llega dos veces

`MOUSE` devuelve **listas dentro de listas**: `{{x1,y1,x0,y0,tipo}, …}`. Desde
Python hay que aplanarlo antes de que cruce el puente, porque una lista que no
sean sólo números **cierra la app** (ver [`micropython.md`](micropython.md)):

```python
_MOUSE = ('LOCAL zm:=MOUSE; LOCAL zp:=zm(1);'
          ' IFTE(SIZE(zp)==0,{-1,-1,-1},{zp(1),zp(2),zp(5)})')
```

### El fallo que no se ve leyendo el código

Entrabas cuántos estados tiene el ciclo, tocabas **OK**… y la app soltaba *«El
montaje no cuadra: no hay ningún componente»*. Correcto —aún no habías puesto
ninguna caja— pero **nadie había pulsado `RESOL`**.

Lo había pulsado el dedo:

> Los diálogos de la Prime (`INPUT`, y los avisos) se aceptan con un botón **OK
> que cae justo encima de la fila de teclas de pantalla, en la posición de la
> F6**. Si el dedo sigue ahí cuando el diálogo se cierra, **el mismo toque llega
> otra vez** a la pantalla de debajo, como si hubieras pulsado su F6.

El arreglo es un antirrebote **con memoria**, y está en el módulo de lógica pura
—no en el de píxeles— justamente para poder probarlo en el PC:

```python
class Debot(object):
    """Un toque = una accion."""
    def __init__(self):
        self.tocat = True

    def purga(self):
        """Da por tocado: el toque que cierra una cosa no cuenta en la siguiente."""
        self.tocat = True

    def passa(self, hi_ha_toc):
        """Cierto solo en el primer contacto de un toque nuevo."""
        if not hi_ha_toc:
            self.tocat = False
            return False
        if self.tocat:
            return False
        self.tocat = True
        return True
```

`purga()` se llama al cerrar **cualquier** diálogo y al volver de **cualquier**
pantalla, de modo que ningún sitio pueda olvidarse. Y de paso vacía la cola de
`GETKEY()`, que tenía el mismo problema en pequeño.

Dos cosas que hace falta que el antirrebote resuelva y que no son la misma: la
pantalla se lee decenas de veces por segundo mientras el dedo no se levanta, y
el toque que cierra un diálogo sobrevive al diálogo.

## 7. Un solo widget para todo: la lista con ventana

El hallazgo de diseño que más ahorra. Leyendo `CHOOSE_R` aparece una lista con
siete filas visibles, índice superior, barra de desplazamiento, flechas, táctil
y salto por dígito. Y resulta que **todas las pantallas de una app de cálculo
son esa misma lista**:

| Pantalla | Qué es cada fila |
|---|---|
| Los datos | un estado: `3   0.800   26.0   236.0` |
| Las cajas | un componente: `2  BESCAN  2 -> 3` |
| Los resultados | un estado resuelto |
| El diagnóstico | lo que falta: `Estat 7: falten T, h, s` |

Escribirlo una vez y usarlo cuatro es la diferencia entre una interfaz que cabe
en el presupuesto y una que no. Y como es **lógica pura** —selección, ventana,
barra, qué significa cada tecla— se prueba entera en el PC. El módulo de píxeles
se queda con dibujar filas.

Lo que resuelve de paso: **21 filas no caben en 7**, pero con ventana y barra no
hace falta que quepan. El problema del ancho se resuelve por el otro lado:
cuatro columnas visibles y `Enter` abre el detalle completo de una fila.

### Comportamiento que conviene copiar tal cual

Todo esto sale de apps que funcionan, no de inventarlo:

- **Los dígitos saltan a la fila.** Pulsar `7` va a la fila 7 sin bajar siete
  veces. Bajo presión de examen es de lo que más se nota.
- **La selección da la vuelta** en los extremos.
- **Izquierda y derecha cambian de columna** cuando hay varias, y pasan página
  cuando no. Es lo que hace la Vista Numérica de la propia calculadora, así que
  el gesto ya se sabe.
- **Tocar una fila la selecciona; tocarla otra vez entra.** Es como se comportan
  las listas del sistema.
- **`Cancel` y `OK` en las posiciones 5 y 6** del menú de pantalla. Es la
  convención de la plataforma.
- **Redibujado parcial**: al mover la selección se repintan dos filas, no la
  pantalla.
- **Salida automática por inactividad.** En un examen la batería importa.
- **`IFERR` alrededor del bucle de eventos**, y vaciar la cola si falla.
- **Menú de dos páginas** si hacen falta más de seis acciones, en vez de apretar
  seis etiquetas ilegibles.
- **Colores del tema**, para no desentonar en modo oscuro.

Lo que **no** conviene copiar: el marco de eventos completo de `SkeletonApp`,
con arrastres, clic largo y ocho manejadores. Para una app que se maneja con
flechas, `Enter` y seis botones, sobra.

## 8. Una tabla no necesita centinelas; un formulario sí

El primer intento de meter los datos fue un formulario: `Enter` sobre un estado
abría un `INPUT` con cuatro campos. Era rápido y **estaba mal**, por algo que
sólo se ve usándolo:

> Un formulario no sabe decir *«esto no lo sé»*.

Había que inventarse centinelas: `0` significaba vacío, y como `x = 0` es un
dato legítimo, hacía falta un `-1` aparte. Aun así quedaba un agujero: una
temperatura de exactamente 0 no se podía escribir.

Una **tabla editable** no tiene ese problema. Una celda vacía está vacía:

```
  ESTATS                                    4 estats
   #      P        T        x       grau
 +----+--------+--------+--------+--------+
 | 1  | 0.1    |   -    |   -    | 6.36   |
 | 2  | 0.8    |  60    |   -    |   -    |
 | 3  | 0.8    |   -    |   -    | -5.33  |
 | 4  | 0.1    |   -    |   -    |   -    |
 +----+--------+--------+--------+--------+
  1.P  pressio  [MPa]
 [Quants][Fluids][Fluid][Buida][Torna][h s v u]
```

Con dos detalles que salieron de teclear un enunciado de verdad:

- **Después de editar, el cursor baja solo.** En un enunciado los datos vienen
  por columnas —*«el condensador trabaja a 0,8 MPa»* da la P de dos estados de
  golpe—, así que se llena una columna de seguido.
- **Los valores por defecto se proponen.** En un ciclo, la salida de una caja es
  la entrada de la siguiente: proponiéndolo, un ciclo de cuatro cajas se teclea
  **sin escribir ni un número de conexión**.

## 9. Las unidades no se preguntan: se dicen

Pregunta razonable mirando una pantalla de propiedades: *«¿cómo sabe la app si
estoy en °C o en K?»*. La respuesta es que **no debe ser una elección**.

> Preguntarlo al arrancar sería peor que no decir nada: dejaría escribir `25`
> donde la tabla espera `298`, y el resultado saldría **resuelto y mal**, que es
> la peor forma de fallar porque no avisa.

La unidad se deduce del dato —en TaulesHP la fija la sustancia— y aparece en la
etiqueta del `INPUT`, en la línea de ayuda, y en el título de la columna cuando
todo comparte unidad. Cuando no la comparten, el título se queda neutro y la
unidad sale abajo, que sí es de la fila donde estás.

## 10. Qué se puede probar en el PC y qué no

Es la división que ordena todo lo anterior:

| | Se prueba en el PC | Sólo en la calculadora |
|---|---|---|
| Selección, ventana, barra, qué hace cada tecla | ✅ | |
| Qué texto va en cada fila | ✅ | |
| Que cada texto quepa en su columna | ✅ (contra el módulo de geometría) | |
| Dibujar, leer teclas, leer el táctil | | ❌ |
| Que un diálogo se cierre donde crees | | ❌ |
| Cuánto se tarda en rellenar una ficha de verdad | | ❌ — hay que cronometrarlo |
| Si el cálculo de detrás va lo bastante rápido | | ❌ — ver la velocidad en [`ppl.md`](ppl.md) |

Para dimensionar una pantalla antes de dibujarla: con la fuente pequeña caben
del orden de **20 filas de 40 caracteres** — estimación, no medida, así que
sirve para descartar un diseño imposible, no para dar uno por bueno. Para eso
está la prueba que mide cada texto contra el ancho de su columna (§3).

Por eso el módulo de píxeles se hace **tan fino como se pueda**: todo lo que
decide *qué* se ve y *qué* pasa vive fuera de él.

Y el intérprete del kit ([`pplrun.py`](../scripts/pplrun.py)) sigue la misma
regla: `TEXTOUT_P`, `INPUT`, `CHOOSE`, `MSGBOX` y `WAIT` **no se dibujan**; se
anotan en `maquina.io` y devuelven un valor neutro, para que el cálculo corra
sin interfaz.

## 11. De dónde sale esto

Apps de terceros leídas de [hpcalc.org](https://www.hpcalc.org/prime/), todas
corriendo en calculadoras reales:

| Programa | Qué aportó |
|---|---|
| **SkeletonApp** (Andreas Möller) | el bucle de eventos y la geometría del menú de pantalla |
| **CHOOSE_R 1.0** (Jacob Wall) | la lista con ventana, el redibujado parcial, la salida por inactividad |
| **LibMenu 3.0** | el menú de pantalla de dos páginas |
| **ktest** / **WaitLab** | qué devuelve exactamente cada método de entrada |
| **CAC** | el patrón «elige qué resuelves y sólo se te pide lo que hace falta» |
| **Markdown Viewer** | el bucle `keyboard()` + `GETKEY()` desde Python, y medir texto con un grob |
| **PrimeEdit** | la prueba de que en Python cabe una interfaz completa: widgets, menús, iconos, resaltado de sintaxis |

El resto está medido en una **G2 con firmware 2.4 revisión 15515**, en los
proyectos TermoHP y CiclesHP.
