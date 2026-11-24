"""Bit-bang MPI3501 ILI9486 init + 120x120 bright RED box on RDK X5 to confirm LCD response."""
import time
import Hobot.GPIO as GPIO

MOSI, SCLK, CS, DC, RST = 19, 23, 24, 18, 22
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
for p, init in ((MOSI, GPIO.LOW), (SCLK, GPIO.LOW), (CS, GPIO.HIGH), (DC, GPIO.LOW), (RST, GPIO.HIGH)):
    GPIO.setup(p, GPIO.OUT, initial=init)

def write16(val):
    GPIO.output(CS, GPIO.LOW)
    for i in range(15, -1, -1):
        GPIO.output(MOSI, (val >> i) & 1)
        GPIO.output(SCLK, GPIO.HIGH)
        GPIO.output(SCLK, GPIO.LOW)
    GPIO.output(CS, GPIO.HIGH)

def cmd(c):
    GPIO.output(DC, GPIO.LOW)
    write16(c & 0xFF)

def data(*vals):
    GPIO.output(DC, GPIO.HIGH)
    for v in vals:
        write16(v & 0xFF)

GPIO.output(RST, GPIO.HIGH); time.sleep(0.05)
GPIO.output(RST, GPIO.LOW);  time.sleep(0.10)
GPIO.output(RST, GPIO.HIGH); time.sleep(0.15)

cmd(0xB0); data(0x00)
cmd(0x11); time.sleep(0.15)
cmd(0x3A); data(0x55)
cmd(0xC2); data(0x44)
cmd(0xC5); data(0x00, 0x00, 0x00, 0x00)
cmd(0xE0); data(0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00)
cmd(0xE1); data(0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75, 0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00)
cmd(0x36); data(0x28)
cmd(0x29); time.sleep(0.10)

# Draw 120x120 RED box at (100, 100)
cmd(0x2A); data(0x00, 100, 0x00, 219)
cmd(0x2B); data(0x00, 100, 0x00, 219)
cmd(0x2C)
GPIO.output(DC, GPIO.HIGH)
for _ in range(120 * 120):
    write16(0xF800)

print("Bit-bang MPI3501 120x120 RED box complete!")
GPIO.cleanup()
