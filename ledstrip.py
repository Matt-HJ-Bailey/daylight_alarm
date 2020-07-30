import rpi_ws281x as ws
import random
import time
from collections import defaultdict
from pyowm.owm import OWM
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)
 
def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)
 
def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return ws.Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return ws.Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return ws.Color(0, pos * 3, 255 - pos * 3)
 
def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)
 
def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)
 
def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def dither_fade(strip, new_color, leds_to_switch=None, dither_time=1):
    # Dither in to a new color by randomly switching group_size
    # at a time.
    
    start_time = time.time()
    if leds_to_switch is None:
        leds_to_switch = [i for i in range(strip.numPixels())]
    random.shuffle(leds_to_switch)
    
    num_leds = len(leds_to_switch)
    # As a rough rule of thumb, it takes 0.005 seconds to switch an LED and render an
    # update. Calculate the group size dynamically to fit into our time budget.
    
    min_update_time = 0.005
    switches_in_time = int(round(dither_time / min_update_time))
    batch_size = int(round((strip.numPixels() / switches_in_time) + 0.5))
    if batch_size != 1:
        num_batches = int(round((strip.numPixels() / batch_size)))
        batch_size = int(round((strip.numPixels() / num_batches)))


    while leds_to_switch:
        these_leds = [leds_to_switch.pop() for _ in range(batch_size) if leds_to_switch]
        for this_led in these_leds:
            strip.setPixelColor(this_led, new_color)
        time.sleep(dither_time / (batch_size * num_leds))
        strip.show()

    # Sometimes we go too fast with the switching, as
    # the batching approximation is horrible. If we
    # do, just chill here before moving on
    end_time = time.time()
    time_diff = end_time - start_time
    if time_diff < dither_time:
        time.sleep(dither_time - time_diff)


def sunrise_animation(strip, total_time=3600, reverse=False):
    steps = 256
    dither_time = total_time / 2
    brightening_time = total_time - dither_time

    for step in range(steps):
        frac = step / steps
        if reverse:
            frac = 1.0 - frac
        SKYBLUE = ws.Color( max(int(135 * frac), 1),
                            max(int(206 * frac), 1),
                            max(int(235 * frac), 1))
        SUNRISE = ws.Color( max(int(255 * frac), 1), 
                            max(int(191 * frac), 1),
                            max(int(39 * frac), 1))
        sunrise_width = int(strip.numPixels() * 0.1)
        sunrise_start = int(frac * strip.numPixels())
        sunrise_end = sunrise_start + sunrise_width
        sky_pixels = [i for i in range(strip.numPixels())]
        for pixel in range(sunrise_start, sunrise_end):
            if pixel in sky_pixels:
                sky_pixels.remove(pixel)
            strip.setPixelColor(pixel, SUNRISE)
        t_1 = time.time()
        dither_fade(strip, SKYBLUE, sky_pixels, (brightening_time - 1) / steps)
        t_2 = time.time()
        time_diff = t_2 - t_1
        if time_diff < brightening_time / steps:
            time.sleep((brightening_time / steps) - time_diff)

WEATHER_ANIMATIONS = defaultdict(lambda: sunrise_animation)

def main(strip):
    print(f"Good morning! Waking up at {time.time()}")
    owm = OWM(WEATHER_API_KEY)
    
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place('Oxford,GB')  # the observation object is a box containing a weather object
    weather = observation.weather.status
    print(f"The current weather is {weather}")
    
    start_time = time.time()
    strip.begin()
    dither_fade(strip, ws.Color(0, 1, 1), leds_to_switch=None, dither_time=RUNTIME * 0.5)
    WEATHER_ANIMATIONS[weather](strip, RUNTIME)
    time.sleep(10 * 60)
    WEATHER_ANIMATIONS[weather](strip, RUNTIME, reverse=True)
    dither_fade(strip, ws.Color(0, 0, 0), leds_to_switch=None, dither_time=RUNTIME * 0.5)
    end_time = time.time()
    print(f"I hope you're awake! Closing down at {time.time()}. We spent {(end_time - start_time) // 60} minutes.")

def read_api_keys(filename):
    """
    Read api keys from a filename for usage in this program.

    The file should have keys in the format 'name=api key', each on a new line. Don't add that file to git!

    :param filename: the filename of the file containing api keys
    :return: a dictionary keyed by api name, with api keys as values.
    """
    key_dict={}
    with open(filename) as fi:
        for line in fi:
            key, val = [item.strip() for item in line.split("=")]
            key_dict[key] = val
    return key_dict

if __name__ == "__main__":
    WEATHER_API_KEY = read_api_keys("./.apikey")["openweathermap"]
    NUM_LEDS = 150
    LED_PIN = 18
    RUNTIME = 20 * 60
    strip = ws.PixelStrip(NUM_LEDS, LED_PIN)
    try:
        main(strip)
    except KeyboardInterrupt:
        for pixel in range(strip.numPixels()):
            strip.setPixelColor(pixel, ws.Color(0, 0, 0))
        strip.show()
        raise KeyboardInterrupt

