# TECLA AMB MIDI

# Importem les llibreries necessaries
import time
import random
import board
import usb_midi
import digitalio
import analogio
import math
import busio  # Comunicación I2C
import displayio  # Gestión de elementos gráficos
import terminalio  # Fuente de texto predeterminada
import vectorio  # Creación de formas geométricas
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
from adafruit_midi.control_change import ControlChange
from adafruit_display_text import label  # Texto en pantalla
import adafruit_displayio_ssd1306  # Control específico de pantalla OLED

# Configurem el port MIDI
midi = MIDI(midi_out=usb_midi.ports[1], out_channel=0)
displayio.release_displays()  # Libera recursos de displays anteriores

# Configuración comunicación I2C con la pantalla
i2c = busio.I2C(board.GP21, board.GP20, frequency=400_000)  # Frecuencia 400kHz
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)  # Dirección común SSD1306
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)  # Inicialización

# Grupo contenedor para elementos gráficos
splash = displayio.Group()
display.root_group = splash  # Asignamos el grupo como raíz

# Paleta de colores (1 color: blanco)
obj_palette = displayio.Palette(1)
obj_palette[0] = 0xFFFFFF  # Código de color en hexadecimal

# Configurem l'octava i les notes, l'octava anirà de la -1 a la 8
octava = 0
kidmos = 0
caos = 0
notes = [i for i in range(12)]  # Notes de C a B (0-11)
# Añade estas variables globales al inicio del código
nota_actual = -1  # Track de la nota que está sonando

# Definim els pins dels 16 botons i els 3 potenciòmetres
digital_pins = [
    board.GP1, board.GP0, board.GP3, board.GP2, board.GP5, board.GP4, board.GP7, board.GP6,
    board.GP9, board.GP8, board.GP11, board.GP10, board.GP13, board.GP12, board.GP15, board.GP14
]
pot_pins = [board.A1, board.A0, board.A2]

# Configurem els botons i els potenciòmetres
buttons = []
for pin in digital_pins:
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.DOWN
    buttons.append(btn)

potes = [analogio.AnalogIn(pin) for pin in pot_pins]

#Output Visual Test de Botons i Potenciometres

modo="null"

text_area = label.Label(terminalio.FONT, text=""".-. .-. .-. .   .-. 
 |  |-  |   |   |-| 
 '  `-' `-' `-' ` ' 
"""
, color=0xFFFFFF, x=10, y=10)
splash.append(text_area)

# Creació del cercle 1
objeto = vectorio.Circle(
    radius=10,  # Radio inicial
    x=6,       # Centro X
    y=32,       # Centro Y
    pixel_shader=obj_palette
)
# Creació del cercle 2
objeto2 = vectorio.Circle(
    radius=5,  # Radio inicial
    x=120,       # Centro X
    y=32,       # Centro Y
    pixel_shader=obj_palette
)
# Creació del cercle 3
objeto3 = vectorio.Circle(
    radius=15,  # Radio inicial
    x=64,       # Centro X
    y=32,       # Centro Y
    pixel_shader=obj_palette
)
#codi_part1.HolaBonaTarda()

#splash.append(objeto)  # Añadir a la pantalla el cercle 1
#splash.append(objeto2)  # Añadir a la pantalla el cercle 2
#splash.append(objeto3)  # Añadir a la pantalla el cercle 3

state_harmony = {
    'previous_note': 60,
    'last_profile': 0,
    'last_tension': 0,
    'initialized': False
}

state = {
    'last_note_time': 0,
    'arp_index': 0,
    'chord_index': 0,
    'current_progression': [],
    'active_notes': set(),
    'initialized': False,
    'current_scale': []
}


# Variables de configuració dels potenciòmetres
pot_min, pot_max = 0.0, 3.3
step = (pot_max - pot_min) / 127.0
step_melo = (pot_max - pot_min) / 10.0
step_control = (pot_max - pot_min) / 50.0
step_nota = (pot_max - pot_min) / 23.0
step_ritme = (pot_max - pot_min) / 36.0

# Funcions per als potenciòmetres
def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def steps(voltage):
    return round((voltage - pot_min) / step)

def steps_melo(voltage):
    return round((voltage - pot_min) / step_melo)

def steps_control(voltage):
    return round((voltage - pot_min) / step_control)

def steps_nota(voltage):
    return round((voltage - pot_min) / step_nota)

def steps_ritme(voltage):
    return round((voltage - pot_min) / step_ritme)

# Función del ritmo euclidiano
def generar_ritmo_euclideo(pulsos, pasos):
    if pulsos > pasos:
        pulsos = pasos
    grupos = [[1] for _ in range(pulsos)] + [[0] for _ in range(pasos - pulsos)]
    while len(grupos) > 1:
        nuevos_grupos = []
        for i in range(0, len(grupos) // 2):
            nuevos_grupos.append(grupos[i] + grupos[-(i + 1)])
        if len(grupos) % 2 == 1:
            nuevos_grupos.append(grupos[len(grupos) // 2])
        grupos = nuevos_grupos
    return [item for sublist in grupos for item in sublist]

# Altres variables
playing_notes = set()
loop_mode = 0
iteration = 0
iteration_saw = 0
canvi = 0
patro = 0

#variables melodia
melodia = [0] * 36
posicio = 0

#loop escala
nota_escala = 0
escalada = 0
escalo = 0
pas = 0

# Inicialización de las coordenadas x e y para el ruido Perlin
x = 0.0  # Valor inicial de x
y = 0.0  # Valor inicial de y
offsetx = 0.01
offsety = 0.01
octava = 0
position = 0  # Inicializamos la posición actual

# Inicialización de la semilla aleatoria (aunque se actualizará en la función de ruido)
random.seed(0)

# Funcions d'ajuda
def mandelbrot_to_midi(cx, cy, max_iter=200):
    x, y = 0.0, 0.0
    iteration = 0
    while x*x + y*y <= 4 and iteration < max_iter:
        x_new = x*x - y*y + cx
        y = 2*x*y + cy
        x = x_new
        iteration += 1
    return iteration % 60 + 32

# Funció sinusoidal que oscil·la entre 0 i 127
def sinusoidal_value(iteration, vairable, ampli):
    # Configurar el rang de la funció sinusoidal
    min_value = 0
    max_value = 127
    amplitude = ampli / 2
    offset = (max_value + min_value) / 2
    
    # Calcular el valor sinusoidal
    value = amplitude * math.sin(iteration) + offset
    return max(min(round(value), max_value), min_value)

def sinusoidal_value_2(iteration, ampli, base_frequency):
    # Parámetros base
    min_value = 0
    max_value = 127
    variable =63
    #base_frequency = 0.1   Frecuencia base de oscilación
    
    # Amplitud controlada solo por 'ampli' (0-127)
    amplitude = ampli / 2  # Rango efectivo: 0-63.5
    
    # Offset para centrar en rango MIDI
    offset = (max_value + min_value) / 2  # 63.5
    
    # Modulación de fase usando 'variable' (afecta velocidad/frecuencia)
    modulated_frequency = base_frequency * (1 + variable/255)  # Frecuencia variable
    phase = iteration * modulated_frequency
    
    # Cálculo del valor con amplitud fija y fase modulada
    value = amplitude * math.sin(phase) + offset
    
    # Asegurar rango MIDI
    return max(min(round(value), max_value), min_value)


def map_value(value, in_min, in_max, out_min, out_max):
    return out_min + (float(value - in_min) * (out_max - out_min) / (in_max - in_min))

# Función para generar el Perlin Noise sin usar numpy
def perlin_noise(x, y, grad_size=256*2):
    """
    Calcula el valor de Perlin Noise en las coordenadas (x, y)
    """
    xi = int(x) % grad_size
    yi = int(y) % grad_size
    
    # Semillas aleatorias para los gradientes
    random.seed(xi + yi)
    gradient_x = random.uniform(-1, 1)
    gradient_y = random.uniform(-1, 1)
    
    # Calcular la distancia entre el punto y los puntos de la cuadrícula
    dx = x - int(x)
    dy = y - int(y)
    
    # Función de suavizado (fade)
    def fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    u = fade(dx)
    v = fade(dy)
    
    # Producto escalar entre el gradiente y el vector de desplazamiento
    def dot_product(gx, gy, dx, dy):
        return gx * dx + gy * dy
    
    grad_dot = dot_product(gradient_x, gradient_y, dx, dy)
    
    # Interpolación final
    return grad_dot * (1 - u) * (1 - v)

def midi_newton_iterations(input_value):
    """
    Calcula una salida MIDI (0-127) basada en el número de iteraciones
    del método de Newton-Raphson para encontrar la raíz de una función.

    Parámetros:
    - input_value: Un valor entero entre 0 y 127 que se usará como parámetro inicial.

    Retorna:
    - Un valor entero entre 0 y 127, correspondiente al número de iteraciones
      normalizado al rango MIDI.
    """
    # Asegurar que el valor esté en el rango 0-127
    if not (0 <= input_value <= 127):
        raise ValueError("El parámetro de entrada debe estar entre 0 y 127.")

    # Escalar el valor de entrada a un rango más razonable para cálculos (0-100)
    x0 = input_value / 127  # Escalar a un rango de 0-100

    # Función objetivo y su derivada
    f = lambda x: x**2 - 2  # Queremos resolver x^2 - 2 = 0
    df = lambda x: 2 * x    # Derivada: 2x

    # Parámetros del método de Newton-Raphson
    tolerance = 1e-6
    max_iterations = 127  # Limitar las iteraciones al rango MIDI
    iterations = 0

    # Newton-Raphson
    while iterations < max_iterations:
        iterations += 1
        if df(x0) == 0:
            break  # Evitar división por cero
        x1 = x0 - f(x0) / df(x0)  # Método de Newton
        if abs(x1 - x0) < tolerance:  # Convergencia
            break
        x0 = x1

    # Normalizar las iteraciones al rango MIDI (0-127)
    midi_output = int((iterations / max_iterations) * 127)
    return midi_output

# Función para mapear el valor generado por Perlin Noise al rango de notas MIDI (0-127)
def perlin_to_midi(x, y):
    """
    Mapea el valor de Perlin Noise a un rango de notas MIDI (0-127)
    """
    noise_value = perlin_noise(x, y)
    # Mapear de [-1, 1] a [0, 127]
    midi_note = int((noise_value + 1) * 63.5)  # El rango de MIDI es de 0 a 127
    return midi_note

def transpose_melody(melody, octava):
    return [note + (12 * octava) for note in melody]

def play_note(note, velocity=100):
    midi.send(NoteOn(note, velocity))
    playing_notes.add(note)
    time.sleep(0.01)
    
def stop_note(nota_actual):
    midi.send(NoteOff(nota_actual, 100))

def play_note_full(note, play, octava, periode):
    if play == 0:
        
        midi.send(NoteOn(note, 0))
        playing_notes.add(note)
        time.sleep(periode/50)
        midi.send(NoteOff(note, 0))
    else:
        midi.send(NoteOn(note, 100))
        playing_notes.add(note)
        time.sleep(periode/50)
        midi.send(NoteOff(note, 100))

def stop_all_notes():
    for note in playing_notes:
        midi.send(NoteOff(note, 0))
    playing_notes.clear()

def scale_with_randomness(input_value):
    """
    Escala un valor entre 0 y 20 al rango 0-127, con un poco de aleatoriedad,
    asegurando que la salida nunca esté fuera del rango 0-127.

    Parámetros:
    - input_value (int): Un valor entero entre 0 y 20.

    Retorna:
    - Un valor entero entre 0 y 127.
    """
    # Validar que la entrada esté en el rango permitido
    if not (0 <= input_value <= 15):
        input_value = 10

    # Escalar el valor al rango 0-127
    scaled_value = (input_value / 15) * 127

    # Añadir aleatoriedad entre 0 y 10 (puede ser positivo o negativo)
    random_adjustment = random.uniform(-10, 10)
    adjusted_value = scaled_value + random_adjustment

    # Asegurarse de que el valor esté entre 0 y 127
    final_value = max(0, min(127, int(adjusted_value)))

    return final_value


def sawtooth_value(fase, frequencia, maxim, x):
    """
    Genera un valor de diente de sierra con control de fase.
    
    Parámetros:
    - fase: Desplazamiento de fase (0-127)
    - frequencia: Velocidad de incremento
    - maxim: Valor máximo de la onda
    - x: Tiempo/iteración actual
    
    Retorna:
    - Valor de la onda entre 0 y maxim
    """
    # Aplicar desplazamiento de fase
    x_con_fase = x + int((fase / 10) * maxim)  # Convertir fase 0-10 a 0-maxim
    
    # Calcular valor con wrap-around
    valor = (x_con_fase * frequencia) % maxim
    
    # Asegurar rango válido MIDI
    return max(0, min(valor, maxim))

# Función de diente de sierra que oscil·la entre 0 i 127
def sawtooth_value_2(offset, frequencia, maxim, x):
    """
    Genera un valor de diente de sierra que oscila como diente de sierra.

    Parámetros:
    - offset: El valor minim.
    - frequency (float): quan creix la señal de rapid.
    - ampli (float): Maxim de la señal (rango 50 a 127).

    Retorna:
    - Un valor entre 0 y 127 que representa la señal de diente de sierra.
    """
    # Configurar el rango de la función de diente de sierra
    min_value = offset
    max_value = maxim
    
    valor = min_value + x + frequencia
    if valor >= max_value:
        valor = 0
    
    # Asegurarse de que el valor esté entre el rango de 0 a 127
    return valor


# Función Gaussiana adaptada
def calcular_nota_gauss(pas_valor, rango):
    mu = rango // 2  # Centro
    sigma = rango // 6  # 83 para rango 500
    
    # Límites precalculados para 10 intervalos
    limites = [0, 83, 125, 167, 208, 250, 292, 333, 375, 417, 500]
    
    # Ajustar límites al rango actual
    if rango != 500:
        limites = [int(x*(rango/500)) for x in limites]
    
    # Determinar intervalo
    if pas_valor < limites[1]:
        return -6
    elif limites[1] <= pas_valor < limites[2]:
        return -4
    elif limites[2] <= pas_valor < limites[3]:
        return -3
    elif limites[3] <= pas_valor < limites[4]:
        return -2
    elif limites[4] <= pas_valor < limites[5]:
        return -1
    elif limites[5] <= pas_valor < limites[6]:
        return 1
    elif limites[6] <= pas_valor < limites[7]:
        return 2
    elif limites[7] <= pas_valor < limites[8]:
        return 3
    elif limites[8] <= pas_valor < limites[9]:
        return 4
    else:
        return 6

def harmonic_next_note(x, y, previous_note=0):
    # Sistema de 24 intervalos (6 perfiles x 4 niveles)
    intervals = {
        # Perfiles de 0 a 5 (6 total)
        0: [3, 4, 7, 12],      # Consonantes básicas
        1: [2, 5, 9, 16],      # Intervalos justos extendidos
        2: [1, 6, 11, 19],     # Tensiones moderadas
        3: [8, 14, 17, 23],    # Intervalos compuestos
        4: [10, 15, 20, 24],   # Tensiones fuertes
        5: [13, 18, 21, 22]    # Cromatismos y clusters
    }
    
    # Cálculo seguro de índices (x:0-127 -> 0-5)
    harmonic_profile = min(x // 21, 5)  # 21.16 ≈ 127/6
    tension = min(y // 32, 3)          # 4 niveles fijos
    
    selected_interval = intervals[harmonic_profile][tension]
    
    # Dirección basada en paridad de la suma
    direction = 1 if (x ^ y) % 2 else -1  # XOR para más variación
    
    # Cálculo de nota base
    base_note = previous_note + (direction * selected_interval)
    
    # Variación armónica no lineal
    harmonic_variation = int((x % 16) - (y % 16))  # -15 a +15
    final_note = (base_note + harmonic_variation) % 128
    
    # Sistema de seguridad MIDI
    return max(0, min(final_note, 127))
    

# Loop principal
while True:
    
    pot_values = [get_voltage(pote) for pote in potes]
    z, x, y = pot_values
    
    #Refresh screen
    if loop_mode == 0:
        text_area.text= """.-. .-. .-. .   .-. 
 |  |-  |   |   |-| 
 '  `-' `-' `-' ` ' 
"""

        display.refresh()
    if loop_mode !=0:
        text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
        display.refresh()
    
    ritmo = generar_ritmo_euclideo(steps_ritme(y), steps_ritme(z)+1)
    to = random.randint(0,1)
    if to == 0:
        size_val = x*15  # Tamaño 0-100%
    if to == 1:
        size_val = x*20  # Tamaño 0-100%
    # Lectura y conversión de valores
    
    x_val = y*10     # Posición X 0-100%
    y_val = z*10     # Posición Y 0-100%

    # Cálculos para el círculo (modificación)
#     new_radius = 1 + int(size_val * 0.2)  # Radio entre 5-25 píxeles
    
#     max_x = 128 - (new_radius * 2)  # Límite horizontal
#     max_y = 64 - (new_radius * 2)   # Límite vertical
    
#     new_x = int(x_val * max_x / 100) + new_radius  # Centro X
    #new_y = int(y_val * max_y / 100) + new_radius  # Centro Y
    
    # Actualización del objeto (cambiar a círculo)
    #objeto.radius = new_radius  # Propiedad específica de Circle
    #objeto.x = new_x
    #objeto.y = new_y
    #objeto2.radius = new_radius*2  # Propiedad específica de Circle
    #objeto2.x = 128-new_x
    #objeto2.y = 64 -new_y

    # Gestionem els botons
    if buttons[1].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 1
            print(f"Mode de loop canviat a mandelbrot")
            modo="Mandelbrot"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
            stop_all_notes()
            time.sleep(0.01)

    if buttons[0].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 4
            print(f"Loop Harmonia activat")
            modo="Loop Harmonia"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
            stop_all_notes()
        time.sleep(0.01)

    if buttons[3].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 6
            print(f"Loop Newton-Raphson")
            modo="Newton-Raphson"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)

    if buttons[2].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 5
            print(f"Loop personalitzat activat")
            modo="LOOP"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)

    if buttons[5].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 3
            print(f"Loop sinusoidal activat")
            modo="Sinus"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)

    if buttons[4].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 7
            print(f"Loop Dent de Serra")
            modo="Serra"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)

    if buttons[7].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 2
            stop_all_notes()
            print(f"Mode de loop canviat a random")
            modo="Random"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)
        
    if buttons[6].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 13
            print("◆ Iniciando modo matemático ◆")
            modo="◆Matemàtic◆"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)
        
    if buttons[9].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 8
            print(f"Loop Batec")
            modo="♥Batec♥"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)

    if buttons[8].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 10
            print(f"Loop riu")
            modo="Riu"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)
        
    if buttons[11].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 11
            print(f"Loop tormenta")
            modo="Tormenta"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)

    if buttons[10].value:
        if loop_mode == 12:
            loop_mode = 12
        if loop_mode == 14:
            loop_mode = 14
        else:
            loop_mode = 9
            print(f"Loop escala")
            modo="Escala"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
        time.sleep(0.01)

    if buttons[13].value:
        if loop_mode == 12:
            loop_mode = 14
            print(f"Modo Sequenciador | Octava: {octava}")
            modo="Sequenciador"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
            time.sleep(0.1)
        else:
            loop_mode = 12
            print(f"Modo teclado activado | Octava: {octava}")
            modo="Teclat"
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
            time.sleep(0.1)

    if buttons[15].value:  # Si se presiona el botón para subir
        if octava < 8:     # Limita la octava máxima a 9
            octava += 1
            
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
            
            
            print(f"Octava subida a {octava}")
            time.sleep(0.1)
            kidmos = 0
            caos = 0
        else:
            print(f"Ya estás en la octava máxima (9).{kidmos} {caos}")
            kidmos +=1
            if kidmos >= 5:
                caos = 0
                kidmos = 0
            elif kidmos >= 3:
                caos = 1
            time.sleep(0.1)  # Previene múltiples activaciones rápidas
            
    # Botón para bajar la octava (buttons[13])
    if buttons[12].value:  # Si se presiona el botón para bajar
        if octava > 0:     # Limita la octava mínima a 0
            octava -= 1
            
            #Refresh screen
            text_area.text= f"	  TECLA\nA:"+str(round(x,2))+" B:"+str(round(y,2))+" C:"+str(round(z,2))+" \nOct:"+str(octava)+"\n MODO:"+modo
            display.refresh()
            
            print(f"Octava bajada a {octava}")
            time.sleep(0.1)
            kidmos = 0
            caos = 0
        else:
            print(f"Ya estás en la octava mínima (0). {kidmos} {caos}")
            kidmos +=1
            if kidmos >= 5:
                caos = 0
                kidmos = 0
            elif kidmos >= 3:
                caos = 1
        time.sleep(0.1)  # Previene múltiples activaciones rápidas
        
    if buttons[14].value:
        loop_mode = 0
        stop_all_notes()
        print(f"ATURAA")
        iteration = 0
        time.sleep(0.1)
        
        """
        if buttons[9].value:
                if canvi == 1:
                    canvi = 2
                    melodia[steps_melo(y)] = int(steps_nota(z))
                    print(f"Nota {steps_melo(y)} de melodia cambiada a:{steps_nota(z)}")
                    time.sleep(0.01)
                if canvi == 0:
                    canvi = 1
                    time.sleep(0.1)
                else:
                    canvi = 0
                    time.sleep(0.1)

            # Botón para ritmos eucledianos
            if buttons[12].value:  # Si se presiona el botón para bajar
                ritmo = generar_ritmo_euclideo(steps_ritme(y), steps_ritme(z)+1)
                print(f"Patrón rítmico generado: {ritmo}")
                print("-----------------------------------")
                posición_max = steps_ritme(z)+1
                # Avanzar a la siguiente posición
        """  

    cx = map_value(potes[2].value, 0, 65535, -1.5, 1.5)
    cy = map_value(potes[0].value, 0, 65535, -1.5, 1.5)

    if loop_mode == 1:
        note = mandelbrot_to_midi(cx, cy)
        if caos == 0:
            play_note(note)
            print(f"Nota fractal: {note}, cx:{cx:.2f}, cy:{cy:.2f}")
            time.sleep(steps_melo(x) / 50)
            midi.send(NoteOff(note, 100))
            iteration = 0
            
        elif caos == 1:
            play_note_full(note, to, octava, steps_melo(x))
            print(f"Nota fractal: {note}, cx:{cx:.2f}, cy:{cy:.2f}   | CAOS : {to}")

    elif loop_mode == 2:
        if steps(z) > steps(y):
            random_note = random.randint(0, 127)
        else:
            random_note = random.randint(steps(z), steps(y))
        
        if caos == 0:
            play_note(random_note)
            print(f"Nota aleatoria: {random_note}")
            time.sleep(steps_melo(x) / 50)
            midi.send(NoteOff(random_note, 100))
            iteration = 0
        elif caos == 1:
            play_note_full(random_note, to, octava, steps_melo(x))
            print(f"Nota aleatoria: {random_note}   | CAOS : {to}")
            
        # Cálculos para el círculo (modificación)
        new_radius = 1 + int(random_note * 0.2)  # Radio entre 5-25 píxeles
        
        max_x = 128 - (new_radius * 2)  # Límite horizontal
        max_y = 64 - (new_radius * 2)   # Límite vertical
        
        new_x = int(x_val * max_x / 100) + new_radius  # Centro X
        new_y = int(y_val * max_y / 100) + new_radius  # Centro Y
        
        # Actualización del objeto (cambiar a círculo)
        objeto.radius = new_radius  # Propiedad específica de Circle
        objeto.x = new_x
        objeto.y = new_y
        objeto2.radius = new_radius*2  # Propiedad específica de Circle
        objeto2.x = 128-new_x
        objeto2.y = 64 -new_y
        
    elif loop_mode == 3:
        sinusoidal_val = sinusoidal_value_2(iteration, steps(z),steps(y)*2/100)  # Obtenir el valor sinusoidal
        note = int(sinusoidal_val)  # Convertim el valor sinusoidal a una nota MIDI
        if caos == 0:
            midi.send(NoteOn(note, 100))  # Enviar la nota MIDI
            print(f"Nota sinusoidal: {note}, ampli = {steps(z)} | freq base = {steps(y)*2/100} | iteració: {iteration}")
            iteration += 1  # Incrementar la iteració per a la següent execució
            if iteration >= 60000:
                iteration = 0
            time.sleep(steps_melo(x) / 50)
            #time.sleep(0.01)
            midi.send(NoteOff(note, 100))
            
        if caos == 1:
            play_note_full(note, to, octava, steps_melo(x))
            print(f"Nota sinusoidal: {note}, ampli = {steps(z)} | freq base = {steps(y)*2/100} | iteració: {iteration}   | CAOS : {to}")
            iteration += 1  # Incrementar la iteració per a la següent execució
            if iteration >= 60000:
                iteration = 0
                # Cálculos para el círculo (modificación)
                
                
        new_radius = 1 + int(steps(x) * 0.2)  # Radio entre 5-25 píxeles
        
        max_x = 124  # Límite horizontal
        max_y = 64   # Límite vertical
        
        new_x = int(sinusoidal_val * max_x / 200)  # Centro X
        new_y = 32  # Centro Y
        
        # Actualización del objeto (cambiar valores)
        objeto3.radius = new_radius  # Propiedad específica de Circle
        objeto3.x = new_x+25
        objeto3.y = new_y
        objeto2.radius = new_radius  # Propiedad específica de Circle
        objeto2.x = 0
        objeto2.y = new_x-5
        objeto.radius = new_radius  # Propiedad específica de Circle
        objeto.x = 124
        objeto.y = 69-new_x

        
    elif loop_mode == 4:
        # Inicialización única
        if not state_harmony['initialized']:
            state_harmony.update({
                'previous_note': 60,
                'last_profile': 0,
                'last_tension': 0,
                'initialized': True
            })
        
        # Parámetros dinámicos
        x_param = steps_melo(y) % 128
        y_param = steps_melo(z) % 128
        
        # Generación de nota
        new_note = harmonic_next_note(x_param, y_param, state_harmony['previous_note'])
        
        # Actualizar estado
        state_harmony.update({
            'previous_note': new_note,
            'last_profile': min(x_param // 21, 5),
            'last_tension': min(y_param // 32, 3)
        })
        
        # Lógica de reproducción
        if caos == 0:
            play_note(new_note)
            print(f"🎼 Nota: {new_note} | X: {x_param} | Y: {y_param}")
            time.sleep(steps_melo(x) / 50)
            midi.send(NoteOff(new_note, 100))
        elif caos == 1:
            play_note_full(new_note, to, octava, steps_melo(x))
            print(f"🎼🔥 CAOS | Nota: {new_note} | Var: {x_param + y_param}")
            time.sleep(steps_melo(x) / 50)
        
        # Reset manual
        if any(btn.value for btn in buttons):
            state_harmony.update({
                'previous_note': 60,
                'last_profile': 0,
                'last_tension': 0
            })
            stop_all_notes()
        
    elif loop_mode == 40:
        x = steps_melo(y)/100# Coordinar x (puedes cambiar esta lógica)
        y = steps_melo(z) /100# Coordinar y (puedes cambiar esta lógica)
        note = perlin_to_midi(x, y)  # Obtener la nota MIDI a partir de Perlin Noise
        if note == 58:
            note = random.randint(0, 20)
        elif note == 59:
            note = random.randint(20, 40)
        elif note == 60:
            note = random.randint(40, 57)
        elif note == 61:
            note = random.randint(64, 80)
        elif note == 62:
            note = random.randint(80, 100)
        elif note == 63:
            note = random.randint(100, 120)
            
        if caos == 0:
            play_note(note)  # Enviar la nota MIDI
            print(f"Nota Perlin enviada: {note}, valor 1:{x}, valor 2: {y}")  # Imprimir la nota para monitoreo
            time.sleep(steps_melo(x) / 50)
            midi.send(NoteOff(note, 100))
        if caos == 1:
            play_note_full(note, to, octava, steps_melo(x))
            print(f"Nota Perlin enviada: {note}, valor 1:{x}, valor 2: {y}   | CAOS : {to}")  # Imprimir la nota para monitoreo
            time.sleep(steps_melo(x) / 50)
        
    elif loop_mode == 5:
        if position >= steps_ritme(z):
            position = 0
            ritmo = generar_ritmo_euclideo(steps_ritme(y), steps_ritme(z)+1)
            nota = melodia[position]
            to = ritmo[position]
            nota = 0 + (octava * 12)
            play_note_full(nota, to, octava, steps_melo(x))
            print(f"nota tocada: {nota}, Activada: {to}, Posició: {position}, Longitud: {len(ritmo)}, Freqüencia: {steps_melo(x)} \n patro tocat: {ritmo}")
        else:
            ritmo = generar_ritmo_euclideo(steps_ritme(y), steps_ritme(z)+1)
            nota = melodia[position]
            to = ritmo[position]
            nota = 0 + (octava * 12) + random.randint(-3,3)
            if nota <= 0:
                nota = 0
            play_note_full(nota, to, octava, steps_melo(x))
            position = position + 1
            print(f"nota tocada: {nota}, Activada: {to}, Posició: {position}, Longitud: {len(ritmo)}, Freqüencia: {steps_melo(x)} \n patro tocat: {ritmo}")
            

    elif loop_mode == 6:
        input_value = random.uniform(min(cx, cy), max(cx, cy))
        input_value = max(0, min(127, input_value))  # Limitar al rango MIDI
        salida = midi_newton_iterations(input_value)
        escalada_newton = scale_with_randomness(salida)
        if caos == 0:
            play_note(escalada_newton)
            print(f"Nota Newton-Raphson_ {escalada_newton}, ValorX: {cx}, ValorY: {cy}")
            time.sleep(steps_melo(x) / 50)
            midi.send(NoteOff(escalada_newton, 100))
        elif caos == 1:
            play_note_full(escalada_newton, to, octava, steps_melo(x))
            print(f"Nota Newton-Raphson_ {escalada_newton}   |   CAOS : {to}")

    elif loop_mode == 7:  # Modo Sawtooth con control de fase
        iteration_saw += 1
        
        # Control principal de fase usando steps_melo(z) en rango 0-10
        fase_actual = steps_melo(z)
        
        # Generar nota con fase dinámica
        nota_saw = sawtooth_value(
            fase=fase_actual,
            frequencia=steps_control(y),
            maxim=127,
            x=iteration_saw
        )
        
        # Lógica de reset mejorada
        if iteration_saw >= 127 or nota_saw >= 125:
            iteration_saw = 0
            #print("🔄 Reseteo de onda")
        
        # Sistema de reproducción
        if caos == 0:
            play_note(nota_saw)
            print(f"🔊 Nota: {nota_saw} | Iter: {iteration_saw} | Fase: {fase_actual}/10")
            time.sleep(steps_melo(x) / 50)
            midi.send(NoteOff(nota_saw, 100))
        elif caos == 1:
            play_note_full(nota_saw, to, octava, steps_melo(x))
            print(f"🎛️ Nota Caótica: {nota_saw} | Fase: {fase_actual} | Iter: {iteration_saw}")

    elif loop_mode == 70:
        iteration_saw = iteration_saw+1   # Iteración o tiempo de la señal
                
        # Generar el valor de la señal de diente de sierra
        nota_saw = sawtooth_value(steps_melo(z), steps_control(y), 127, iteration_saw)
        if iteration_saw >= 127 or nota_saw >= 125:
            iteration_saw = 0
        if caos == 0:
            play_note(nota_saw)
            print(f"Valor de diente de sierra: {nota_saw} en iteracio: {iteration_saw}")
            time.sleep(steps_melo(x) / 50)
            midi.send(NoteOff(nota_saw, 100))
        elif caos == 1:
            play_note_full(nota_saw, to, octava, steps_melo(x))
        
        
    elif loop_mode == 8:
        # Configuración parámetros cardíacos
        base_bpm = steps_melo(x) /50  # BPM base controlado por el input
        lub_note = steps_melo(y) + (octava * 12) # C2 - sonido grave (lub)
        dub_note = 12- steps_melo(z) + (octava * 12)  # C5 - sonido agudo (dub)
        
        # Cálculo intervalo basado en BPM (60,000 ms / BPM)
        heartbeat_interval = 1.2/(steps_melo(x)+1)  # Convertir a segundos
        
        # Patrón temporal típico de latido (relación 1:3)
        lub_duration = heartbeat_interval * 0.15  # 15% del intervalo total
        dub_duration = heartbeat_interval * 0.10  # 10% del intervalo total
        pause_duration = heartbeat_interval * 0.75  # 75% del intervalo total
        
        # Primer latido (LUB) - más fuerte y largo
        play_note(lub_note, velocity=110)
        time.sleep(lub_duration/50)
        midi.send(NoteOff(lub_note, 100))
        
        # Pequeña pausa entre latidos
        
        # Segundo latido (DUB) - más corto y suave
        play_note(dub_note, velocity=80)
        time.sleep(dub_duration)
        midi.send(NoteOff(dub_note, 100))
        
        
        print(f"{dub_note}   ❤️{lub_note}  |  BPM: {base_bpm*600} | Intervalo: {heartbeat_interval:.2f}s")
        
        

    elif loop_mode == 9:
        escalada = steps_control(y)  # 0-50
        escalo = steps_melo(z)       # 0-10
        
        boulder = random.randint(0, escalo)
        agafada = random.randint(0, escalada)
        
        pas = boulder * agafada + escalada
        RANGO = escalada*escalo # Rango máximo teórico (50*10)
        
        # Aplicar modificación
        progres = calcular_nota_gauss(pas, RANGO)
        nota_escala += calcular_nota_gauss(pas, RANGO)
        
        # Asegurar rango MIDI y tocar nota
        nota_escala = max(0, min(127, nota_escala))
        play_note(nota_escala)
        time.sleep(steps_melo(x) / 50)
        midi.send(NoteOff(nota_escala, 100))
        print(f"NOTA TOCADA = {nota_escala} | PROGRES: {progres} | PAS = {pas} (Base: {escalada*escalo})")
            
    elif loop_mode == 10:  # Modo "Río"
        # Parámetros de control
        corriente = steps_control(y) / 25  # Intensidad de la corriente (0-2)
        turbulencia = steps(z)        # Fuerza del meandro (0-10)
        
        # Variables de estado persistentes (deberían ser globales/inicializadas fuera del loop)
        if 'rio_base' not in globals():
            rio_base = 64  # Nota central inicial
        rio_time = time.time()  # Tiempo para variaciones suaves
        
        # Simulación de movimiento fluvial
        rio_base += corriente  # La corriente modifica la posición base
        rio_base = rio_base % 127  # Wrap-around en los límites MIDI
        
        # Cálculo de variaciones con ruido suavizado (Perlin noise sería ideal)
        wave = math.sin(rio_time * 0.8) * (corriente * 0.5)
        ripple = math.cos(rio_time * 2.2) * (turbulencia * 0.3)
        random_offset = random.uniform(-corriente*0.2, turbulencia*0.2)
        
        nota_rio = rio_base + wave + ripple - random_offset * 2
        
        
        # Ajuste final y clamping
        nota_rio = int(max(0, min(127, nota_rio)))
        
        # Tocar nota con dinámica variable
        play_note(nota_rio, 100)
        
        time.sleep(steps_melo(x) / 50)
        
        midi.send(NoteOff(nota_rio, 100))
        print(f"Nota: {nota_rio} | Corriente: {corriente:.1f} | Turbulencia: {turbulencia}")

    elif loop_mode == 11:  # Modo "Tormenta Dinámica con Octavas"
        volumen_fijo = 100
        escala_tormenta = [0, 3, 5, 7, 10]
        
        fuerza_viento = steps(x)
        intensidad_lluvia = steps_control(y)
        frecuencia_rayos = steps_melo(z)
        
        # Sistema de viento cósmico con límites
        efecto_viento = max(0, min(63, int(fuerza_viento * 0.5)))  # Aseguramos 0-63
        resonancia_espectral = 1 + (fuerza_viento / 42.0)
        
        # Nota base con protección de octava
        octava = max(0, min(10, octava))  # Asegurar octava válida (0-10)
        nota_base = 12 * octava + int(intensidad_lluvia * 0.48)
        nota_base = max(0, min(127, nota_base))
        
        # Modulación armónica con protección de intervalos
        escalas_fantasma = []
        if efecto_viento > 30:
            escala_tormenta = [max(0, min(24, int(i * resonancia_espectral))) for i in escala_tormenta]  # Límite de intervalo
            escalas_fantasma = [[max(-12, min(12, n + 7)), max(-12, min(12, n - 5))] for n in escala_tormenta]  # Fantasmas acotados
        
        if random.randint(0, 1000) < (frecuencia_rayos * 100):
            direccion = 1 if random.random() > 0.3 else -1
            for i, intervalo in enumerate(escala_tormenta[::direccion]):
                # Cálculo seguro de relámpago
                multiplicador = max(1, min(3, (i+1)))  # Limitar multiplicador
                nota_relampago = nota_base + (intervalo * direccion * multiplicador)
                nota_relampago = max(0, min(127, nota_relampago))
                
                # Efecto de viento con protección doble
                if efecto_viento > 20 and escalas_fantasma:
                    for fantasma in random.choice(escalas_fantasma):
                        nota_fantasma = max(0, min(127, nota_relampago + fantasma))
                        vol_fantasma = max(10, min(127, volumen_fijo - efecto_viento))
                        play_note(nota_fantasma, vol_fantasma)
                
                play_note(nota_relampago, volumen_fijo)
                time.sleep(max(0.01, 0.05 - (frecuencia_rayos * 0.003)))
                midi.send(NoteOff(nota_relampago, volumen_fijo))
            
            print(f"⚡ Rayo con viento {fuerza_viento} | Oct {octava}")
        else:
            # Lluvia fractal con protección mejorada
            variacion_lluvia = random.randint(-2 + frecuencia_rayos, 2 + frecuencia_rayos)
            nota_lluvia = max(0, min(127, nota_base + variacion_lluvia))
            
            # Generación fractal segura
            fractal = []
            for i in range(1 + efecto_viento // 30):
                offset = ((i % 3) * efecto_viento // 18)
                nota_fractal = max(0, min(127, nota_lluvia + offset))
                fractal.append(nota_fractal)
            
            for nota_fractal in fractal:
                play_note(nota_fractal, volumen_fijo)
                time.sleep(max(0.01, 0.05 * (1 - (fuerza_viento/127))))
                midi.send(NoteOff(nota_fractal, volumen_fijo))
            
            densidad = (intensidad_lluvia / 50) * 0.9 + 0.1
            tiempo_base = 0.3 * (1.0 - densidad)
            tiempo_gota = random.uniform(tiempo_base * 0.5, tiempo_base * 1.5)
            
            play_note(nota_lluvia, volumen_fijo)
            time.sleep(max(0.01, tiempo_gota * 0.1))
            midi.send(NoteOff(nota_lluvia, volumen_fijo))
            time.sleep(max(0.01, tiempo_gota * 0.9))

        print(f"🌪️ Tormenta: Viento {fuerza_viento} | Oct {octava} | Base {nota_base}")
    
    
    
    
    elif loop_mode == 12:
        # Sistema de notas superpuestas con vibrato
        notas_activas = set()  # Nuevo: track de múltiples notas
        vibrato = random.randint(0, steps_control(y))
        repla = random.randint(0, steps_control(z))
        
        # Calcular vibra para todas las notas
        if vibrato >= 35:
            vibra = random.randint(-3,3)
        elif vibrato >= 30:
            vibra = random.randint(-2,2)
        elif vibrato >= 20:
            vibra = random.randint(-1,1)
        else:
            vibra = 0
            
        # Calcular vibra para todas las notas
        
        if repla >= 40:
            time.sleep(max(0.01, steps_melo(x) / 10))
           # print(f"SWING MAXIMO")
        elif repla >= 35:
            time.sleep(max(0.01, steps_melo(x) / 25))
           # print(f"SWING ECLECTICO")
        elif repla >= 25:
            time.sleep(max(0.01, steps_melo(x) / 50))
           # print(f"SWING")
        else:
            repla = 0
        
        # Procesar todos los botones pulsados
        for btn in range(13):
            nota_base = (octava * 12) + btn
            nota_actual = max(0, min(127, nota_base + vibra))
            
            if buttons[btn].value:
                if nota_actual not in notas_activas:
                    midi.send(NoteOn(nota_actual, 100))
                    notas_activas.add(nota_actual)
                    time.sleep(max(0.01, steps_melo(x) / 50))  # Mínimo 10ms
                    midi.send(NoteOff(nota_actual, 100))
                    #print(f"NoteOn: {nota_actual}")
            else:
                if nota_actual in notas_activas:
                    midi.send(NoteOff(nota_actual, 100))
                    notas_activas.remove(nota_actual)
                    #print(f"NoteOff: {nota_actual}")

        # Control de tiempo dinámico común para todas las notas
        midi.send(NoteOff(nota_actual, 100))
        time.sleep(max(0.01, steps_melo(x) / 50))  # Mínimo 10ms
        
        # Control de octavas con polyfonía

        
        # Botón 15 con limpieza polifónica
        if buttons[15].value:
            for nota in notas_activas:
                midi.send(NoteOff(nota, 100))
            notas_activas.clear()
            
            loop_mode = 0
            #print("Modo teclado desactivado")
            time.sleep(0.2)
       
    elif loop_mode == 42:
        # Reproducir notas con botones 0-12 (versión modificada)
        nota_anterior = nota_actual  # Nueva variable para control de repetición
        vibrato = random.randint(0, steps_control(y))
        vibra = 0
        if vibrato >= 20:
            vibra = random.randint(-1,1)
        elif vibrato >= 30:
            vibra = random.randint(-2,2)
        elif vibrato >= 35:
            vibra = random.randint(-3,3)
        else:
            vibra = 0
        
        for btn in range(13):
            if buttons[btn].value:
                nueva_nota = (octava * 12) + btn + vibra
                nueva_nota = max(0, min(127, nueva_nota))
                
                # Siempre envía NoteOff antes de nueva nota
                if nota_actual != -1:
                    midi.send(NoteOff(nota_actual, 100))
                
                midi.send(NoteOn(nueva_nota, 100))
                nota_actual = nueva_nota
                #print(f"Nota: {nueva_nota}")
                
                # Control de tiempo dinámico
                time.sleep(steps_melo(x) / 50)  # steps_melo definida externamente
                break
        else:
            if nota_actual != -1:
                midi.send(NoteOff(nota_actual, 100))
                nota_actual = -1

        # Control de octavas con delay dinámico
        if buttons[13].value and octava < 8:
            octava += 1
            print(f"Octava subida: {octava}")
            time.sleep(steps_melo(x) / 50) # Originalmente 0.2
        
        if buttons[14].value and octava > 0:
            octava -= 1
            print(f"Octava bajada: {octava}")
            time.sleep(steps_melo(x) / 50)  # Originalmente 0.2
        
        # Botón 15 con delay dinámico
        if buttons[15].value:
            if nota_actual != -1:
                midi.send(NoteOff(nota_actual, 100))
            loop_mode = 0
            nota_actual = -1
            print("Modo teclado desactivado")
            time.sleep(steps_melo(x) / 50)  # Originalmente 0.2
       
    elif loop_mode == 13:  # Loop Matemático Armónico Pro
        # Configuración de estado mejorada
        
        try:
            # Inicialización mejorada
            if not state['initialized']:
                state.update({
                    'current_progression': [],
                    'active_notes': set(),
                    'arp_index': 0,
                    'chord_index': 0,
                    'current_scale': [],
                    'initialized': True
                })
            
            # Salida responsiva
            if any(btn.value for btn in buttons):
                raise KeyboardInterrupt
            
            # Parámetros dinámicos con validación
            x_val = steps_melo(get_voltage(potes[0]))
            velocidad = max(0.02, x_val / 45)  # Rango más musical
            octava_actual = octava * 12
            tipo_acorde = steps_nota(get_voltage(potes[1])) % 5
            progresion_pattern = steps_ritme(get_voltage(potes[2])) % 4
            direccion_arpegio = -1 if (get_voltage(potes[2]) > 2.0) else 1
            
            # Escalas musicales predefinidas (0: Mayor, 1: Menor, etc.)
            escalas = [
                [0, 2, 4, 5, 7, 9, 11],  # Mayor
                [0, 2, 3, 5, 7, 8, 10]   # Menor natural
            ]
            escala_actual = escalas[progresion_pattern % 2]
            
            # Generación de progresión armónica mejorada
            if not state['current_progression'] or (time.monotonic() - state['last_note_time'] > velocidad * 4):
                patrones_progresion = [
                    [0, 4, 5, 3],  # I-V-vi-IV
                    [0, 5, 3, 4],  # I-vi-IV-V
                    [0, 2, 3, 5],  # I-ii-iii-V
                    [0, 5, 7, 4]   # Progresión experimental
                ]
                
                progression = patrones_progresion[progresion_pattern]
                state['current_progression'] = [
                    octava_actual + escala_actual[g % len(escala_actual)] + 12 * (g // len(escala_actual))
                    for g in progression
                ]
                state['chord_index'] = 0
                state['arp_index'] = 0
            
            # Lógica de ejecución temporal optimizada
            elapsed_time = time.monotonic() - state['last_note_time']
            if elapsed_time >= velocidad:
                # Configuración de acorde con Fibonacci dinámico
                acordes = [
                    [0, 4, 7],    # Mayor
                    [0, 3, 7],    # Menor
                    [0, 5, 7],     # Sus4
                    [0, 3, 6],     # Disminuido
                    [0, 4, 8]      # Aumentado
                ]
                
                # Cálculo de offset Fibonacci modular
                fib_sequence = (0, 1, 1, 2, 3, 5, 8, 13, 21)
                fib_offset = fib_sequence[state['arp_index'] % 9] % 12
                
                # Generación de notas del acorde
                nota_base = state['current_progression'][state['chord_index']]
                notas_acorde = [max(0, min(127, nota_base + n + fib_offset)) for n in acordes[tipo_acorde]]
                
                # Ordenamiento direccional
                notas_ordenadas = notas_acorde[::direccion_arpegio]
                nota_actual = notas_ordenadas[state['arp_index'] % len(notas_ordenadas)]
                
                # Ejecución de notas con gestión de overlaps
                play_note(nota_actual)
                state['active_notes'].add(nota_actual)
                
                # Transición suave entre notas
                time.sleep(max(0.01, velocidad * 0.3))
                
                # Actualización de índices mejorada
                state['arp_index'] += 1
                if state['arp_index'] >= len(notas_ordenadas) * 2:
                    state['chord_index'] = (state['chord_index'] + 1) % len(state['current_progression'])
                    state['arp_index'] = 0
                    # Limpieza de notas al cambiar de acorde
                    for n in state['active_notes']:
                        stop_note(n)
                    state['active_notes'].clear()
                
                state['last_note_time'] = time.monotonic()
                
                # Feedback mejorado
                note_name = nota_actual  # Asume función de conversión MIDI a nombre
                print(f"🎵 {note_name} | Type: {['Mayor','Menor','Sus4','Disminuido','Aumentado'][tipo_acorde]} | Prog: {['I-V-vi-IV','I-vi-IV-V','I-ii-iii-V','Experimental'][progresion_pattern]} | Dir: {'⬆' if direccion_arpegio==1 else '⬇'} | BPM: {int(60/(velocidad*len(notas_ordenadas)))} | Volt: {get_voltage(potes[2]):.2f}v")

        except KeyboardInterrupt:
            for n in state['active_notes']:
                stop_note(n)
            state.update({
                'initialized': False,
                'active_notes': set(),
                'current_progression': []
            })

    elif loop_mode == 14:  # Modo Secuendiador
        sequence = [60] * 12
        current_step = 0
        last_step_time = time.monotonic()
        bpm = 120
        note_duration = 0.5
        last_clock = time.monotonic()
        current_time = time.monotonic()
        #Iniciar Secuenciador
        
        if current_time - last_step_time >= (60/bpm):
            midi.send(NoteOn(sequence[current_play_step], 100))
            time.sleep(0.05)  # Nota proporcional al tempo
            midi.send(NoteOff(sequence[current_play_step], 100))

            # Avanzar paso
            current_play_step = (current_play_step + 1) % 12
            last_step_time = current_time  # <--- Actualiza el timer
        
        # 1. Seleccionar paso con botones 1-12
        for i in range(12):
            if buttons[i].value:
                current_step = i
                print(f"Paso {current_step} seleccionado | Nota actual: {sequence[current_step]}")

        # 2. Pot X: Cambiar nota del paso actual (0-127)
        sequence[current_step] = int(steps_nota(x))  # Usa steps_nota() como en otros modos
    
        # 3. Pot Z: Ajustar BPM (40-270)
        bpm = 40 + (230 * (z / 3.3))  # 40 + (0..100*2.3)
    
        # 4. Pot Y: Control complementario (ej: duración)
        note_duration = 0.1 + (0.8 * (y / 3.3))  # 10%-100% del paso
    
        # Reproducción automática de la secuencia
        if time.monotonic() - last_step_time > (60 / bpm):
            # Toca la nota actual
            midi.send(NoteOn(sequence[current_play_step], 100))
            time.sleep((60 / bpm) * note_duration)
            midi.send(NoteOff(sequence[current_play_step], 100))
        
            # Avanza al siguiente paso
            current_play_step = (current_play_step + 1) % 12
            last_step_time = time.monotonic()

    elif loop_mode == 23:  # Loop Matemático Armónico
        # Variables de estado
        state = {
            'last_note_time': 0,
            'arp_index': 0,
            'chord_index': 0,
            'current_notes': [],
            'current_progression': [],
            'initialized': False
        }
        
        try:
            # Inicialización
            if not state['initialized']:
                state['current_progression'] = []
                state['current_notes'] = []
                state['arp_index'] = 0
                state['chord_index'] = 0
                state['initialized'] = True
                
            
            # Control de salida inmediata
            if any(btn.value for btn in buttons):
                raise KeyboardInterrupt
            
            # Actualizar parámetros
            x_val = steps_melo(get_voltage(potes[0]))
            velocidad = max(0.01, x_val / 50)  # Velocidad mínima de 10ms
            raiz = 0 + (octava * 12)
            tipo_acorde = steps_nota(get_voltage(potes[1])) % 5
            progresion_pattern = steps_ritme(get_voltage(potes[2])) % 4
            
            # Generar nueva progresión si es necesario
            if not state['current_progression'] or time.monotonic() - state['last_note_time'] > velocidad:
                progression = [
                    [0,5,7,4], [0,3,4,7], [0,2,4,5], [0,7,4,2]
                ][progresion_pattern]
                state['current_progression'] = [raiz + (12 * (g // 7)) + (g % 7) for g in progression]
                state['chord_index'] = 0
                state['arp_index'] = 0
            
            # Lógica de ejecución temporal
            if time.monotonic() - state['last_note_time'] >= velocidad:
                # Calcular nota actual
                chord = state['current_progression'][state['chord_index']]
                fib_offset = (0,1,1,2,3,5,8,13,21)[state['arp_index'] % 9] % 12
                acorde = [[0,4,7],[0,3,7],[0,5,7],[0,3,6],[0,4,8]][tipo_acorde]
                notas = [max(0, min(127, chord + n + fib_offset)) for n in acorde]
                
                # Determinar dirección
                direccion = -1 if (get_voltage(potes[2]) > 2.0) else 1
                nota_idx = state['arp_index'] % len(notas)
                nota_actual = notas[::direccion][nota_idx]
                
                # Tocar nota
                play_note(nota_actual)
                time.sleep(steps_melo(x) / 50)
                
                # Actualizar estado
                state['arp_index'] += 1
                if state['arp_index'] >= len(notas) * 2:
                    state['chord_index'] = (state['chord_index'] + 1) % len(state['current_progression'])
                    state['arp_index'] = 0
                
                state['last_note_time'] = time.monotonic()


                print(f"▶ Nota: {nota_actual} | Arpegio: {state['arp_index'] + 1}/{len(notas)*2} | Acorde: }")

                # Pequeña pausa no bloqueante
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            stop_all_notes()
            state['initialized'] = False




     
