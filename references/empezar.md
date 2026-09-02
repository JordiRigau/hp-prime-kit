# Empezar de cero

Si nunca has programado una HP Prime, empieza aquí. Los demás documentos son
**referencia**: están ordenados por lo que se ha medido, no por lo que hace
falta saber primero, y leerlos sin contexto es desconcertante.

Esto no es un tutorial del lenguaje. Es el mapa: qué es cada cosa, en qué
orden se hacen, y qué se te va a romper el primer día.

---

## 1. Qué es esto que vas a programar

La **HP Prime** es una calculadora gráfica con pantalla táctil de 320 × 240,
que además es un ordenador pequeño en el que puedes escribir programas. Hay dos
generaciones, **G1** y **G2**; comparten firmware, pero la G2 es más rápida y
tiene más memoria. Todo lo que hay en este kit está medido en una **G2**.

Se programa en **dos lenguajes**, y conviene elegir a conciencia:

| | **PPL** | **Python** |
|---|---|---|
| Qué es | el lenguaje propio de la calculadora | MicroPython, un Python reducido |
| Desde cuándo | siempre | firmware de 2021 en adelante |
| Se parece a | Pascal / BASIC | Python, con menos librería |
| Bueno para | cálculo, librerías que otros programas usan | interfaces, lógica larga, reaprovechar código del PC |
| Documentación oficial | escasa | **ninguna** |

**No hay que elegir uno.** Desde Python se puede ejecutar PPL y recibir el
resultado, así que lo normal es tener el cálculo pesado o los datos en PPL y la
interfaz en Python — o todo en PPL, si es pequeño.

Si vienes de programar en un PC, hay una diferencia que lo cambia todo:

> **No hay depurador, no hay mensajes de error útiles y no hay consola.** El
> compilador de PPL dice `syntax error` y te señala una línea, sin decir qué
> sobra. Una app de Python que hace algo que no le gusta **se cierra sola, sin
> decir nada**.

Ése es el problema que resuelve este kit: **comprobar cosas sin la
calculadora**, para no depender de ese ciclo de pegar-compilar-mirar-repetir.

## 2. Programa o app: qué es cada cosa

| | **Programa** | **App** |
|---|---|---|
| Qué es | un fichero con funciones | una carpeta con icono propio |
| Dónde vive | el catálogo de programas | la tecla `[Apps]` |
| Cómo se abre | `[Shift][Program]`, navegar, `[Enter]` | `[Apps]` y tocar el icono: **dos pulsaciones** |
| El fichero | `MIPROG.hpprgm` | `MIAPP.hpappdir/`, una carpeta |

Una app no calcula mejor: sólo se abre antes y tiene sitio donde guardar sus
cosas. **Empieza siempre como programa** y envuélvelo como app al final, cuando
ya funcione. Iterar sobre un programa es mucho más rápido, y convertirlo
después es empaquetar, no reescribir.

## 3. Qué necesitas instalado

| | |
|---|---|
| **HP Connectivity Kit** (CK) | el programa de PC que habla con la calculadora — <https://hpcalcs.com/download/> |
| **HP Virtual Calculator** | una Prime dentro del PC; sirve para probar sin tener la física delante. Viene con el CK |
| **Python 3.7 o más nuevo** | para las herramientas de este kit. No hace falta nada más: ni pip, ni librerías |

Con eso ya puedes trabajar. La calculadora física no es imprescindible para
empezar: el Virtual Calculator se comporta igual para casi todo.

## 4. El vocabulario mínimo

Los otros documentos usan estas palabras sin explicarlas. Son diez:

| Palabra | Qué significa |
|---|---|
| **PPL** | el lenguaje propio de la Prime (*Prime Programming Language*) |
| **CK** | el Connectivity Kit, el programa de PC |
| **`.hpprgm`** | el fichero de un programa. Es **binario**, pero con el código de texto dentro |
| **`.hpappdir`** | la **carpeta** de una app |
| **plantilla** | un `.hpprgm` que ya existe y del que se copia la cabecera para fabricar otro. Hace falta porque el formato no se genera desde cero |
| **bloque compilado** | trozo que la calculadora añade delante del código con los números ya en su formato interno. Hace que el fichero pese más y que abra al instante |
| **el espejo** | la carpeta `Documentos\HP Connectivity Kit\Calculators\<tu calculadora>\`. **No es un buzón**: es una copia que el CK escribe *desde* la calculadora |
| **exportar** | `EXPORT` delante de una función la hace visible desde fuera del fichero. Sin él, es privada |
| **grob** | una imagen en memoria sobre la que se dibuja. `G0` es la pantalla |
| **tecla de pantalla** | los seis botones de la fila de abajo, cuyo texto lo pone tu programa |

## 5. Tu primer programa, de principio a fin

Vamos a escribir algo, comprobarlo en el PC y meterlo en la calculadora.

### Paso 1 — escribirlo, en un `.txt` normal

Un programa PPL es texto. Guárdalo como `saluda.txt`:

```ppl
// Suma los cuadrados de 1 a n.
EXPORT CUADRADOS(n)
BEGIN
  LOCAL zi, zs;          // TODOS los locales, juntos y al principio
  zs := 0;               // asignar es :=  (comparar es ==)
  FOR zi FROM 1 TO n DO
    zs := zs + zi * zi;
  END;                   // END para todo: no existe ENDFOR
  RETURN zs;
END;
```

Cinco cosas que ya están usadas ahí y que conviene fijar desde el principio:
`EXPORT` para que se vea desde fuera, los `LOCAL` juntos arriba, `:=` para
asignar, `END` para cerrar cualquier bloque, y el `;` final obligatorio.

### Paso 2 — pasar el linter, antes de compilar nada

```bash
python scripts/lint_ppl.py saluda.txt
```

Caza lo que el compilador de la Prime no sabe explicar. Si dice algo,
arréglalo ahora: en la calculadora te habría costado una vuelta entera.

### Paso 3 — ejecutarlo en el PC

```bash
python scripts/pplrun.py saluda.txt --call "CUADRADOS(10)"
```

Debe dar `385`. Esto ejecuta **el mismo fichero** que vas a instalar, no una
reimplementación, así que lo que veas aquí es lo que hará allí.

### Paso 4 — convertirlo en un `.hpprgm`

Necesitas una **plantilla**: un `.hpprgm` de código que haya escrito el CK.

```bash
python scripts/hpprgm.py plantillas "…/Documentos/HP Connectivity Kit/Calculators"
```

Si no encuentra ninguna —es lo normal, y el porqué está en
[`formato-hpprgm.md`](formato-hpprgm.md)— fabrícala: abre el CK, **clic derecho
→ Nuevo** sobre *Program*, escribe dos líneas que compilen, y **copia ese
fichero fuera de la carpeta antes de enviarlo a la calculadora**. Guárdalo como
`plantilla_codigo.hpprgm` en la raíz del kit y las herramientas lo cogen solas.

```bash
python scripts/hpprgm.py write saluda.txt -t plantilla_codigo.hpprgm -o CUADRADOS.hpprgm
```

### Paso 5 — meterlo en la calculadora

1. Conecta la calculadora (o abre el Virtual Calculator) y abre el **CK**.
2. **Arrastra `CUADRADOS.hpprgm` desde el explorador encima de la calculadora**,
   en la ventana del CK.

> **No lo copies a la carpeta del espejo.** Es el error que todo el mundo comete
> una vez: parece un buzón y no lo es. Al conectar, el CK la sobrescribe con lo
> que haya en la calculadora y tu fichero desaparece.

Si al arrastrar sale el **cursor de prohibido** y no pasa nada, no es el
fichero: mira si el CK está puesto para ejecutarse **como administrador**, en
las propiedades del acceso directo. Windows no deja arrastrar de un proceso sin
elevar a uno elevado.

### Paso 6 — ejecutarlo allí

En la pantalla **Home**, escribe el nombre de la función y sus argumentos:

```
CUADRADOS(10)
```

y `[Enter]`. Debe salir `385`.

### Paso 7 — comprobar que has instalado lo que creías

Merece la pena, y cuesta un comando:

```bash
python scripts/hpprgm.py read "…/Calculators/HP Prime/CUADRADOS.hpprgm" -o instalado.txt
diff instalado.txt saluda.txt
```

Suena paranoico hasta el día que descubres que la calculadora llevaba semanas
con una versión vieja. Pasó.

## 6. Lo que se te va a romper el primer día

Todo esto está medido, y cada uno cuesta al menos una vuelta:

| Lo que haces | Lo que pasa | Lo correcto |
|---|---|---|
| `LOCAL a,b,c,d,e,f,g,h,i,j;` | *syntax error* señalando esa línea | máximo **7-8** por sentencia; ponlos en grupos de 6 |
| `L(0)` | error en ejecución | **todo empieza en 1**, no en 0 |
| `IF x = 1 THEN` | no compara, o compara mal | `==` para comparar, `:=` para asignar |
| `ENDIF`, `ENDFOR` | *syntax error* | `END` para todo |
| `n := SIZE(M)(1);` | *syntax error* | `d := DIM(M);` y luego `d(1)` |
| declarar un `LOCAL` a media función | *syntax error* | todos arriba, juntos |
| copiar el fichero al espejo | no se instala nada | arrastrarlo en la ventana del CK |
| pasar una matriz grande a una función | va lentísimo | se copia **por valor**: usa una global |

Y una regla de orden que sorprende: **un programa sólo ve las funciones de otro
si se compiló después.** Si tienes datos, motor y app, instálalos en ese orden.

## 7. Cuando algo no cuadra: el método

Es lo más útil de todo el kit, y no es una herramienta:

> **No razones sobre la sintaxis: mide programas que ya funcionen en esa misma
> calculadora, y compara.**

El límite de variables por `LOCAL` costó **cinco rondas** de compilar y probar,
porque el error no se movía y cada hipótesis parecía razonable. Lo resolvió
tabular los programas que sí compilaban y contar sus locales.

Dos corolarios que ahorran días:

- **Un error que no se mueve después de un arreglo significa que tu hipótesis
  es falsa**, no que el arreglo fuera insuficiente.
- **Descarga el programa de otro y léelo.** [hpcalc.org](https://www.hpcalc.org/prime/)
  está lleno de código que corre en calculadoras reales. De ahí salen el bucle
  de eventos, los códigos de tecla y la geometría del menú que hay en este kit.
  Una rama entera de un proyecto se dio por muerta —«`import hpprime` falla»—
  hasta que se leyó una app de Python que corría en esa misma calculadora: no
  fallaba el puente, faltaba el módulo `time`.

## 8. Por dónde seguir

Ya con contexto, los documentos de referencia se leen bien. En este orden:

| | Cuándo te hará falta |
|---|---|
| [`ppl.md`](ppl.md) | **el siguiente**: el lenguaje entero, sus límites reales y cuatro hipótesis que parecen razonables y son falsas |
| [`interfaz.md`](interfaz.md) | cuando tu programa tenga que pedir datos o dibujar algo |
| [`apps.md`](apps.md) | cuando quieras que tenga icono propio |
| [`micropython.md`](micropython.md) | si lo vas a escribir en Python, o si quieres llamar a PPL desde Python |
| [`formato-hpprgm.md`](formato-hpprgm.md) | cuando te pique la curiosidad por el binario, o cuando necesites meter muchos datos |

Y una advertencia sobre el tono de todos ellos: **están escritos para no
mentir**. Cuando algo está medido, dicen dónde y con qué firmware; cuando no,
lo dicen también. Si algo aparece sin evidencia, desconfía — y si lo mides,
añádelo con la suya.
