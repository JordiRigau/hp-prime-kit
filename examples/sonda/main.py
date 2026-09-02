# La sonda: lo primero que conviene meter en una calculadora antes de
# escribir la app de verdad.
#
#     python scripts/mkapp.py SONDA examples/sonda/main.py
#     y arrastrar SONDA.hpappdir encima de la calculadora en el CK
#
# Se llama main.py porque ES el punto de entrada: en las tres apps de Python
# que se han leido -CICLES, PROVA y el MarkdownViewer- el fichero se llama
# asi y su codigo esta a nivel de modulo, o sea que corre al importarse.
#
# Contesta de una pasada las preguntas que deciden como se escribe todo lo
# demas, y que NO se pueden contestar desde el PC:
#
#   - el puente hpprime.eval responde?
#   - ve las funciones de tus programas de PPL?
#   - que devuelve GETKEY con cada tecla?
#   - llega el tactil a Python, y con que coordenadas?
#
# POR QUE VA EN ORDEN DE RIESGO CRECIENTE
#
# Porque una llamada mala CIERRA LA APP, sin mensaje y sin traza. Poniendo lo
# peligroso al final, el punto donde muere ya identifica la causa. Y cada paso
# deja rastro en una variable global de PPL, que sobrevive al cierre:
#
#     si la app se cierra -> ve a Home, escribe  PZ  y pulsa Enter.
#
# Asi se localizo en una sola pasada la trampa que mas cuesta: una lista con
# un TEXTO dentro cierra la app. Todo lo que cruce el puente tiene que ser un
# numero o una lista plana de numeros.

from hpprime import eval as ev, fillrect

BLANCO = 0xFFFFFF
NEGRO = 0x000000
VERDE = 0x008000
ROJO = 0xC00000
AZUL = 0x1A5FB4


def txt(y, s, col=NEGRO):
    # Las comillas se limpian: una comilla dentro de la expresion de PPL la
    # rompe.
    s = str(s).replace('"', "'")[:46]
    ev('TEXTOUT_P("%s",G0,3,%d,2,RGB(%d,%d,%d))'
       % (s, y, (col >> 16) & 255, (col >> 8) & 255, col & 255))


def marca(t):
    """Deja rastro en una global de PPL. Es lo unico que sobrevive si la app
    se cierra: despues, en Home, PZ dice hasta donde llego."""
    try:
        ev('PZ:="' + t + '"')
    except Exception:
        pass


def prueba(y, etiqueta, expresion):
    """Una comprobacion. Si revienta, lo dice en vez de llevarse la app."""
    marca('antes: ' + etiqueta)
    try:
        r = ev(expresion)
        txt(y, '%s = %s' % (etiqueta, r), VERDE)
        marca('ok: ' + etiqueta)
        return r
    except Exception as e:
        txt(y, '%s FALLA: %s' % (etiqueta, str(e)[:20]), ROJO)
        marca('EXCEPCION: ' + etiqueta)
        return None


# El envoltorio del tactil: MOUSE devuelve listas dentro de listas, y eso no
# puede cruzar el puente. Se saca x, y y el tipo, y punto.
MOUSE = ('LOCAL zm:=MOUSE; LOCAL zp:=zm(1);'
         ' IFTE(SIZE(zp)==0,{-1,-1,-1},{zp(1),zp(2),zp(5)})')

fillrect(0, 0, 0, 320, 240, BLANCO, BLANCO)
txt(2, 'SONDA', AZUL)

prueba(22, '1+1', '1+1')                     # responde el puente?
prueba(40, 'lista de numeros', '{1,2,3}')    # pasa una lista plana?
prueba(58, 'ticks', 'ticks()')               # el reloj, que no viene en time
prueba(76, 'envoltorio del tactil', MOUSE)

# Aqui es donde se pondria una llamada a TU libreria de PPL, la ultima porque
# es la que puede matar:
#   prueba(94, 'MILIB', 'LOCAL zr:=MIFUNC(3,350); {zr(1),zr(2)}')

txt(112, 'toca la pantalla o pulsa teclas.', AZUL)
txt(130, 'ESC para salir.', AZUL)
ev('DRAWMENU("1","2","3","4","5","6")')

marca('bucle')
n = 0
while True:
    try:
        k = ev('GETKEY()')
    except Exception:
        k = -1
    if k == 4:                                # 4 = Esc
        break
    if k is not None and k >= 0:
        fillrect(0, 0, 150, 320, 20, BLANCO, BLANCO)
        txt(150, 'tecla: codigo %d' % k, VERDE)
        marca('tecla %d' % k)
    try:
        m = ev(MOUSE)
    except Exception:
        m = None
    if isinstance(m, list) and len(m) >= 3 and m[0] >= 0:
        n = n + 1
        fillrect(0, 0, 170, 320, 40, BLANCO, BLANCO)
        txt(170, 'toque %d:  x=%d  y=%d  tipo=%d' % (n, m[0], m[1], m[2]),
            VERDE)
        # La fila de teclas de pantalla empieza en y=213, y cada una mide 53.
        boton = int(m[0] / 53) + 1 if m[1] >= 213 else 0
        txt(188, 'zona: ' + ('boton %d' % boton if boton else 'lista'), AZUL)
        marca('toque %d' % n)

fillrect(0, 0, 0, 320, 240, BLANCO, BLANCO)
txt(2, 'FIN. toques detectados: %d' % n, VERDE if n else ROJO)
if not n:
    txt(24, 'Ninguno: el tactil no llega a Python.', ROJO)
    txt(42, 'Hazlo todo con teclas.', NEGRO)
marca('fin, toques=%d' % n)
