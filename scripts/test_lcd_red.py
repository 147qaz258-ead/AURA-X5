"""Test MPI3501 16-bit per-word CS-framed SPI @ 4MHz on RDK X5."""
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
    spi.writebytes([0x00, c & 0xFF])

def data(d):
    GPIO.output(PIN_DC, GPIO.HIGH)
    spi.writebytes([0x00, d & 0xFF])

# Hard reset
GPIO.output(PIN_RST, GPIO.HIGH); time.sleep(0.05)
GPIO.output(PIN_RST, GPIO.LOW);  time.sleep(0.10)
GPIO.output(PIN_RST, GPIO.HIGH); time.sleep(0.15)

# Standard Waveshare/MPI3501 ILI9486 init (each byte CS-framed)
cmd(0xB0); data(0x00)
cmd(0x11); time.sleep(0.15)
cmd(0x3A); data(0x55)
cmd(0xC2); data(0x44)
cmd(0xC5); data(0x00); data(0x00); data(0x00); data(0x00)
cmd(0xE0); data(0x0F); data(0x1F); data(0x1C); data(0x0C); data(0x0F); data(0x08); data(0x48); data(0x98); data(0x37); data(0x0A); data(0x13); data(0x04); data(0x11); data(0x0D); data(0x00)
cmd(0xE1); data(0x0F); data(0x32); data(0x2E); data(0x0B); data(0x0D); data(0x05); data(0x47); data(0x75); data(0x37); data(0x06); data(0x10); data(0x03); data(0x24); data(0x20); data(0x00)
cmd(0x36); data(0x28)
cmd(0x29); time.sleep(0.10)

# Set full window 480x320 and fill solid BLACK (0x0000) then RED (0xF800)
cmd(0x2A); data(0x00); data(0x00); data(0x01); data(0xDF)
cmd(0x2B); data(0x00); data(0x00); data(0x01); data(0x3F)
cmd(0x2C)
GPIO.output(PIN_DC, GPIO.HIGH)
# Send fast 4096-byte chunks of 0xF8, 0x00 (RED)
row = bytes([0xF8, 0x00] * 480)
for _ in range(320):
    spi.writebytes2(row)
print("Solid RED pushed @ 4MHz with per-word CS framing.")
spi.close()
