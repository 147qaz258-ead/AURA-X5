/* Ultra-fast mmap(/dev/mem) GPIO register driver for MPI3501 16-bit ILI9486 on RDK X5.
 * Uses LSIO GPIO controller at 0x34120000 (base=379, offset 0x00 = SWPORTA_DR).
 * Bit offsets: CS(394)=15, SCLK(395)=16, MOSI(398)=19, DC(402)=23.
 * Compile: gcc -O2 -shared -fPIC ili9486_fast.c -o ili9486_fast.so
 */
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#define GPIO_BASE_ADDR 0x34120000UL
#define BIT_CS   (1U << 15)
#define BIT_SCLK (1U << 16)
#define BIT_MOSI (1U << 19)
#define BIT_DC   (1U << 23)

static int mem_fd = -1;
static volatile uint32_t *gpio_dr = NULL;

static inline void tiny_delay(void) {
    /* ~30-50ns pulse width so 74HC4094/74HC4040 shift registers latch reliably */
    __asm__ volatile("nop; nop; nop; nop; nop; nop; nop; nop;");
}

int lcd_gpio_open(int g_mosi, int g_sclk, int g_cs, int g_dc) {
    (void)g_mosi; (void)g_sclk; (void)g_cs; (void)g_dc;
    if (gpio_dr != NULL) return 0;
    mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
    if (mem_fd < 0) return -1;
    void *map = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, mem_fd, GPIO_BASE_ADDR);
    if (map == MAP_FAILED) {
        close(mem_fd);
        mem_fd = -1;
        return -1;
    }
    gpio_dr = (volatile uint32_t *)map;
    return 0;
}

void lcd_gpio_close(void) {
    if (gpio_dr != NULL) {
        munmap((void *)gpio_dr, 4096);
        gpio_dr = NULL;
    }
    if (mem_fd >= 0) {
        close(mem_fd);
        mem_fd = -1;
    }
}

int push_rgb565_gpio(const uint16_t *pixels, int num_pixels) {
    if (!gpio_dr) return -1;
    uint32_t base = (*gpio_dr & ~(BIT_CS | BIT_SCLK | BIT_MOSI)) | BIT_DC;
    *gpio_dr = base | BIT_CS;
    for (int i = 0; i < num_pixels; i++) {
        uint16_t val = pixels[i];
        uint32_t v = base;  /* CS=0 */
        *gpio_dr = v;
        for (int b = 15; b >= 0; b--) {
            uint32_t w = (val & (1U << b)) ? (v | BIT_MOSI) : v;
            *gpio_dr = w;
            tiny_delay();
            *gpio_dr = w | BIT_SCLK;
            tiny_delay();
            *gpio_dr = w;
        }
        *gpio_dr = v | BIT_CS;
        tiny_delay();
    }
    return 0;
}
