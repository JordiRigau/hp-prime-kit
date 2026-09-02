# Python en la HP Prime

> **Antes que esto**: [`empezar.md`](empezar.md) explica los dos lenguajes de la
> Prime y cuándo conviene cada uno. Si vas a escribir Python para la
> calculadora, lee al menos su §1 y §2.

La Prime lleva **MicroPython** desde el firmware de 2021, y con él un módulo
propio, `hpprime`, que da dibujo directo y —lo que de verdad importa— una
función `eval()` que **ejecuta PPL arbitrario y devuelve el resultado**.

Eso convierte a Python en la vía práctica para escribir la interfaz y la lógica
de una app, apoyándose en PPL sólo para lo que la calculadora no expone de otra
manera. Y tiene una consecuencia que vale más que todo lo demás:

> El fichero que calcula puede ser **exactamente el mismo** en el PC y en la
> calculadora. Lo único que cambia debajo es el módulo que consulta los datos.
> Con eso, las pruebas del PC dicen algo real sobre lo que corre en la G2.

**No hay documentación oficial de HP para esto.** Lo que sigue está medido en
una G2 con firmware 2.4 revisión 15515, o leído de apps que corren en ella;
cada cosa dice de dónde viene.

---

## 1. Qué hay y qué no

Lo confirmado ejecutando en la calculadora:

| | |
|---|---|
| `math` | **sí** — es toda la dependencia de librería que necesita un motor de cálculo |
| `hpprime` | **sí** — el puente y el dibujo |
| `micropython` (`const`) | sí |
| **`time`** | **NO existe.** Las apps que lo necesitan se traen su propio `time.py` construido sobre `eval('ticks()')` |
| `__future__` | no |
| `os`, `sys` | no de la misma manera que en CPython: no cuentes con ellos |
| NumPy | no. Para álgebra lineal, la vía es `linalg` de la Prime *(comunidad, no medido aquí)* |

Que falte `time` fue **el primer error de diagnóstico del puerto de CiclesHP**:
`import time` falló, se concluyó que el puente a Python no servía y la rama se
dio por cerrada. Se reabrió al leer el código del **Markdown Viewer**, una app
de Python que corre en esa misma calculadora y que empieza literalmente por
`from hpprime import eval, fillrect`. No fallaba el puente: faltaba un módulo
de la biblioteca estándar.

**Lección de método**: cuando algo falla en una plataforma mal documentada,
busca código que ya funcione *en esa misma máquina* antes de concluir nada.

> Módulos que la comunidad documenta y que aquí **no** se han medido:
> `cmath`, `array`, `gc`, `sys`, `ucollections`, `uerrno`, `uhashlib`, `uio`,
> `urandom`, `ure`, `ustruct`, `utimeq`, y los módulos `graphic` y `cas`
> (`cas.caseval`). Fuente: [HP Prime Python Libraries](https://udel.edu/~mm/hp/primePython/upython.html).
> La misma fuente avisa de que la Prime implementa **un subconjunto** de
> MicroPython y de que hay más rutinas documentadas que existentes.

## 2. El módulo `hpprime`

```python
from hpprime import eval, fillrect, keyboard
```

Lo que está **usado y funcionando** en apps que corren en esta calculadora:

| Llamada | Qué hace |
|---|---|
| `eval(cadena_ppl)` | ejecuta PPL y devuelve el resultado (§3) |
| `fillrect(gr, x, y, w, h, col_borde, col_relleno)` | rectángulo relleno. `gr=0` es la pantalla |
| `keyboard()` | cierto si hay alguna tecla pulsada |
| `dimgrob(n, w, h, color)` | crea un grob fuera de pantalla (para medir texto) |

Los colores son enteros de 24 bits, `0xRRGGBB`.

> La comunidad documenta bastantes más: `arc`, `blit`, `circle`, `grob`,
> `grobh`, `grobw`, `line`, `mouse`, `pixon`, `rect`, `strblit`, `textout`,
> `get_cartesian`, `set_cartesian`, y una variante `_c` de cada una. Aquí no
> están medidas, y para casi todas hay un equivalente en PPL al que se llega
> por `eval`, que es lo que hacen las apps leídas.

## 3. El puente: `eval()`

El corazón de todo. Se construye una cadena de PPL y se ejecuta:

```python
from hpprime import eval as ev

ev('TEXTOUT_P("hola",G0,10,20,2,RGB(0,0,0))')   # dibuja
n = ev('1+1')                                    # -> 2
t = ev('ticks()')                                # milisegundos
ev('CX:=3.5')                                    # escribe una global de PPL
x = ev('CX')                                     # y la lee
r = ev('TSATP(1.0)')                             # llama a TU libreria de PPL
```

**Devuelve números y listas de números.** Eso es todo lo que hace falta para
llamar a una librería de PPL bien escrita.

### La trampa que cierra la app

Está medida, y no es una precaución: es la diferencia entre que funcione y que
la app desaparezca.

> **Una lista con un texto dentro cierra la app.** Sin excepción, sin mensaje,
> sin traza.

La función `TPT` de TaulesHP devuelve `{T,P,v,u,h,s,x,region,AVISO}`: ocho
números y un aviso de texto al final. Llamarla cruda desde Python **cerraba la
app**. Todo lo que había funcionado hasta entonces devolvía números sueltos.

La solución es no dejar salir nunca la lista cruda: se envuelve la llamada en
PPL y sólo se dejan pasar los números.

```python
def _vuit(crida):
    """Ejecuta una llamada de PPL y saca SOLO los ocho numeros.
    El aviso -el noveno elemento, que es texto- se descarta aqui dentro."""
    return ev('LOCAL zr:=' + crida + '; {zr(1),zr(2),zr(3),zr(4),zr(5),'
              'zr(6),zr(7),zr(8)}')
```

El mismo patrón vale para `MOUSE`, que devuelve **listas dentro de listas**:

```python
_MOUSE = ('LOCAL zm:=MOUSE; LOCAL zp:=zm(1);'
          ' IFTE(SIZE(zp)==0,{-1,-1,-1},{zp(1),zp(2),zp(5)})')
```

**Regla general**: que el envoltorio de PPL devuelva siempre una lista plana de
números, o un número. Si tu librería de PPL va a llamarse desde Python,
diséñala así desde el principio.

### Construir la cadena sin romperla

Dos reglas que salieron de usarlo:

**Las comillas.** Una comilla dentro de la cadena rompe la expresión de PPL. Se
limpian antes de concatenar:

```python
s = str(s).replace('"', "'")
```

**Los números.** Un número que Python escribe en notación científica con signo
`+` —`1e+20`— es lo que el entorno HOME de la Prime interpreta mal *(problema
reportado por la comunidad, no medido aquí; el rodeo que proponen es
`cas.caseval`)*. La práctica que sí está en uso y funciona es pasar los números
con `repr(float(x))`, que en el rango de trabajo normal da una forma que el
parser de PPL entiende:

```python
def _n(x):
    """Un numero hacia texto de PPL, sin notacion que el parser no entienda."""
    return repr(float(x))
```

Si vas a mover magnitudes muy grandes o muy pequeñas, compruébalo con una sonda
antes de fiarte.

### Lo que cuesta

**0,2 ms por cruce**, medido. Un ciclo termodinámico completo hace 30-40
consultas, o sea unos **8 ms**. No hay nada que optimizar: escribe el código
claro y crúzalo tantas veces como haga falta.

## 4. La arquitectura que hace todo esto útil

El puente por sí solo no es gran cosa. Lo que lo convierte en una forma seria de
trabajar es esta división:

```
      PC                                    calculadora
   ---------                             -----------------
   engine.py   \                        /   TERMOLIB (PPL)
                >   taules.py (2 caras) <
                                        \   hpprime.eval
                        |
                     cycle.py     <-- EL MISMO FICHERO en los dos sitios
                        |
                  main / pantalla        <-- solo aqui hay pixeles
```

- **`cycle.py` es el mismo fichero** en el repositorio y en la app. Se copia con
  un comando, y una prueba comprueba que no se han separado
  (`mkapp.py --check`).
- **`taules.py` tiene dos versiones con la misma cara.** Una llama al motor de
  Python, la otra cruza el puente. Es la única pieza duplicada a propósito.
- **Lo que toca píxeles y teclas se aísla en un módulo tan fino como se pueda**,
  porque es lo único que no se puede probar desde el PC.

Esa disciplina ya se ha pagado: la prueba de sincronía destapó que la forma
serializada de un fluido incompresible **no guardaba el volumen específico ni la
unidad de temperatura**. En Python la ida y vuelta colaba porque los valores por
defecto coincidían; el PPL, que no tiene defectos, lo delató a la primera.

### Los `import` de los ficheros compartidos

Un módulo que va a la calculadora sólo puede importar lo que MicroPython tenga.
Merece la pena comprobarlo con una prueba, porque el síntoma en la calculadora
es que **la app se cierra sin decir nada**:

```python
PERMITIDOS = ('math', 'cycle', 'taules', 'llista', 'vistes',
              'pantalla', 'hpprime')
```

Los `import` de dentro de una función no cuentan: sólo los de nivel superior.

Y **borra `__pycache__`** antes de empaquetar: son `.pyc` de CPython que
MicroPython no leería.

## 5. Depurar cuando la app se cierra sola

No hay traza, no hay mensaje y la pantalla se va. La técnica que funciona es
**dejar rastro en una variable global de PPL**, que sobrevive al cierre:

```python
def marca(t):
    try:
        ev('PZ:="' + t + '"')
    except Exception:
        pass

marca('antes del envoltorio')
r = ev(EXPRESION)
marca('OK envoltorio')
```

Si la app se cierra: ve a **Home**, escribe `PZ` y pulsa `Enter`. Dice
exactamente hasta dónde llegó.

Con eso se localizó la trampa del §3 en una sola pasada. La sonda iba probando
**en orden de riesgo creciente** —`{1,2,3}`, luego `{1,"a"}`, luego una lista de
diez números de verdad, luego la llamada recortada, y la cruda la última, porque
era la que mataba— así que el punto exacto en el que moría identificaba la causa
sin más experimentos.

**Empaqueta la sonda como app**, no como script suelto: así se ejecuta por el
mismo camino que la app de verdad y no estás midiendo otra cosa.

Hay una lista para adaptar en [`examples/sonda/`](../examples/sonda/).
Contesta de una pasada lo que no se puede contestar desde el PC —si el puente
responde, si ve tus funciones de PPL, qué devuelve `GETKEY` con cada tecla, si
el táctil llega y con qué coordenadas—, y es lo primero que conviene meter en
una calculadora antes de escribir la app de verdad:

```bash
python scripts/mkapp.py SONDA examples/sonda/main.py
```

## 6. Desde PPL hacia Python

El camino inverso existe: PPL puede ejecutar un script de Python con

```ppl
PYTHON("nombre_del_script", parametros);
```

y el editor de programas admite bloques `#PYTHON … #END` dentro del fuente PPL.

*No está medido en este kit* — no ha hecho falta, porque la dirección útil para
un motor de cálculo es la contraria. Está aquí para que conste que la puerta
existe. Fuente: [HP Prime Programming](https://udel.edu/~mm/hp/primePython/).

## 7. Lo que sigue sin estar medido

- **La velocidad de cálculo puro en Python** frente a la del PPL. El cruce del
  puente sí está medido (§3); lo que tarda un bucle numérico largo dentro de
  MicroPython, no.
- **El límite de memoria** de una app de Python: cuántos módulos y de qué
  tamaño admite antes de quedarse sin sitio.
- **Los `_c` y el resto del módulo `hpprime`**: los que no aparecen en §2 no se
  han ejercitado aquí.
