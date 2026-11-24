"""Test 8-bit SPI (ILI9486/ST7796/ILI9488) @ 4MHz on RDK X5 spidev1.0."""
import time
import Hobot.GPIO as GPIO
import spidev

PIN_DC = 18
PIN_RST = 22

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN_DC, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PIN_RST, GPIO.OUT, initial=GPIO.HIGH)

spi = spidev.SpiDev()
spi.open(1, 0)
spi.mode = 0
spi.max_speed_hz = 4_000_000

def cmd(c):
    GPIO.output(PIN_DC, GPIO.LOW)
    spi.writebytes([c & 0xFF])

def data(*vals):
    GPIO.output(PIN_DC, GPIO.HIGH)
    spi.writebytes([v & 0xFF for v in vals])

GPIO.output(PIN_RST, GPIO.HIGH); time.sleep(0.05)
GPIO.output(PIN_RST, GPIO.LOW);  time.sleep(0.10)
GPIO.output(PIN_RST, GPIO.HIGH); time.sleep(0.15)

cmd(0x01); time.sleep(0.15)  # Software Reset
cmd(0x11); time.sleep(0.15)  # Sleep Out
cmd(0x3A); data(0x55)        # 16-bit RGB565 (or 0x66 for ILI9488 18-bit)
cmd(0x36); data(0x28)
cmd(0x21)                    # Display Inversion ON (common on IPS/TFT)
cmd(0x29); time.sleep(0.10)

cmd(0x2A); data(0x00, 0x00, 0x01, 0xDF)
cmd(0x2B); data(0x00, 0x00, 0x01, 0x3F)
cmd(0x2C)
GPIO.output(PIN_DC, GPIO.HIGH)
row = bytes([0x00, 0x1F] * 480)  # Solid BLUE
for _ in range(320):
    spi.writebytes2(row)
print("8-bit SPI Solid BLUE pushed @ 4MHz.")
spi.close()
