"""Bit-bang XPT2046 over Hobot.GPIO Pins 19(MOSI), 21(MISO), 23(SCLK), 26(TP_CS) to verify physical bus."""
import time
import Hobot.GPIO as GPIO

MOSI, MISO, SCLK, CS, IRQ = 19, 21, 23, 26, 11
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(MOSI, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(SCLK, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(CS,   GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(IRQ,  GPIO.IN)

def xfer_xpt(cmd):
    GPIO.output(CS, GPIO.LOW)
    for i in range(7, -1, -1):
        GPIO.output(MOSI, (cmd >> i) & 1)
        GPIO.output(SCLK, GPIO.HIGH)
        GPIO.output(SCLK, GPIO.LOW)
    val = 0
    for i in range(15, -1, -1):
        GPIO.output(SCLK, GPIO.HIGH)
        bit = GPIO.input(MISO)
        GPIO.output(SCLK, GPIO.LOW)
        val = (val << 1) | bit
    GPIO.output(CS, GPIO.HIGH)
    return val >> 3

print("TP_IRQ:", GPIO.input(IRQ))
for c in (0xD0, 0x90, 0xB0, 0xC0):
    print(hex(c), "->", xfer_xpt(c))
GPIO.cleanup()
