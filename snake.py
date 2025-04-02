from machine import Pin, I2C
import ssd1306
import time

i2c = I2C(0, scl=Pin(1), sda=Pin(0))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Definim els pins dels 16 botons i els 3 potenciòmetres 
#digital_pins = [
#    board.GP1, board.GP0, board.GP3, board.GP2, board.GP5, board.GP4, board.GP7, board.GP6,
#    board.GP9, board.GP8, board.GP11, board.GP10, board.GP13, board.GP12, board.GP15, board.GP14
#]
#pot_pins = [board.A1, board.A0, board.A2]
#
# Configurem els botons i els potenciòmetres
#buttons = []
#for pin in digital_pins:
#    btn = digitalio.DigitalInOut(pin)
#    btn.direction = digitalio.Direction.INPUT
#    btn.pull = digitalio.Pull.DOWN
#    buttons.append(btn)
#
#potes = [analogio.AnalogIn(pin) for pin in pot_pins]


# Inicialitza el joc
snake = [(64, 32)]
direction = (1, 0)
food = (100, 20)

def draw_snake():
    for x, y in snake:
        oled.pixel(x, y, 1)

def draw_food():
    oled.pixel(food[0], food[1], 1)

def move_snake():
    global snake, direction, food
    head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
    snake.insert(0, head)
    if head == food:
        food = (int(time.time()) % 128, int(time.time()) % 64)
    else:
        snake.pop()

while True:
    oled.fill(0)
    draw_snake()
    draw_food()
    oled.show()
    move_snake()
    time.sleep(0.1)