import board  # Acceso a los pines de la Raspberry Pi Pico
import busio  # Comunicación I2C
import displayio  # Gestión de elementos gráficos
import terminalio  # Fuente de texto predeterminada
import analogio  # Lectura de potenciómetros
import time  # Control de tiempos
import vectorio  # Creación de formas geométricas
from adafruit_display_text import label  # Texto en pantalla
import adafruit_displayio_ssd1306  # Control específico de pantalla OLED

displayio.release_displays()  # Libera recursos de displays anteriores

# Configuración de los potenciómetros
pot1 = analogio.AnalogIn(board.GP26)  # Tamaño del objeto
pot2 = analogio.AnalogIn(board.GP27)  # Posición horizontal (X)
pot3 = analogio.AnalogIn(board.GP28)  # Posición vertical (Y)

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

# Creació del cercle 1
objeto = vectorio.Circle(
    radius=10,  # Radio inicial
    x=64,       # Centro X
    y=32,       # Centro Y
    pixel_shader=obj_palette
)
# Creació del cercle 2
objeto2 = vectorio.Circle(
    radius=2,  # Radio inicial
    x=24,       # Centro X
    y=32,       # Centro Y
    pixel_shader=obj_palette
)
splash.append(objeto)  # Añadir a la pantalla el cercle 1
splash.append(objeto2)  # Añadir a la pantalla el cercle 2


def map_value(value, in_min=0, in_max=65535, out_min=0, out_max=100):
    # Mapea valores de 0-65535 (16 bits) a un rango personalizado
    return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

while True:
    # Lectura y conversión de valores
    size_val = map_value(pot1.value)  # Tamaño 0-100%
    x_val = map_value(pot2.value)     # Posición X 0-100%
    y_val = map_value(pot3.value)     # Posición Y 0-100%
    
    # Cálculos para el círculo (modificación)
    new_radius = 1 + int(size_val * 0.2)  # Radio entre 5-25 píxeles
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
    


    
    time.sleep(0.05)