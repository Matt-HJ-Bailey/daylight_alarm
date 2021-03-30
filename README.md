# daylight_alarm
A python script that runs a WS2812b strip to act as a daylight alarm.

Run with
`sudo -E python3 ./flask_time.py` 
to run a flask-powered webpage serving at your IP address. 
This currently has two boxes that allow you to set a time that the lights will come on every day.

Draws from OpenWeatherMap to get the weather for today, and displays a different image (crudely) depending on the day.

** Details **
Requires a file called `light_coordinates.csv` containing the actual positions of the LEDs.
I calculated this by taking a picture and using ImageJ to label the LED positions.
Then a KDTree is calculated to effectively work as a Voronoi partition, splitting the image space up into regions that are closest to a given pixel.
Then, pick a colour for each pixel using a KMeans cluster to identify the most significant cluster of pixel colours (we can't average or we'll just get brown).

At the scheduled time every day, sample the weather from OWM (requires an API key) and fade in that image on the LEDs to act as a daylight alarm.
After a runtime of 20 minutes, fade the image out again gradually.
This uses a non-linear interpolation (gamma curve with exponent 2.2) and dithers between stages by picking random pixels to change; this prevents it being really bright at the start and allows for a more gradual wakeup.

** Future Work **

Animations -- for example, a rain animation?
Different schedules for the weekday and weekend.
