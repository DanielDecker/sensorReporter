# Sensors that Use GPIO and GPIO Pin Actuator

This module contains:
* [gpio.dht_sensor.DhtSensor](#gpiodht_sensordhtsensor)
* [gpio.rpi_gpio.RpiGpioSensor](#gpiorpi_gpiorpigpiosensor)
* [gpio.rpi_gpio.RpiGpioActuator](#gpiorpi_gpiorpigpioactuator)
* [gpio.gpio_led.GpioColorLED](#gpiogpio_ledgpiocolorled)

## `gpio.dht_sensor.DhtSensor`

A polling sensor that reads temperature and humidity from a DHT11, DHT22, or AM2302 sensor wired to the GPIO pins.

### Dependencies

This sensor uses the [adaFruit CircuitPython libraries](https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup) (adafruit-blinka, adafruit-circuitpython-dht), RPI.GPIO and libgpiod2.

```bash
cd /srv/sensorReporter
sudo ./install_dependencies.sh gpio
```

### Parameters

| Parameter     | Required | Restrictions                  | Purpose                                                                                                                                                                                    |
|---------------|----------|-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Class`       | X        | `gpio.dht_sensor.DhtSensor`   |                                                                                                                                                                                            |
| `Connections` | X        | Dictionary of connectors      | Defines where to publish the sensor status for each connection. This sensor has 2 outputs, see below. Look at connection readme's for 'Actuator / sensor relevant parameters' for details. |
| `Level`       |          | DEBUG, INFO, WARNING, ERROR   | Override the global log level and use another one for this sensor.                                                                                                                         |
| `Poll`        | X        | Positive number               | Refresh interval for the sensor in seconds.                                                                                                                                                |
| `Sensor`      | X        | `DHT11`, `DHT22`, or `AM2302` | The type of the sensor.                                                                                                                                                                    |
| `Pin`         | X        |                               | GPIO data pin in BMC numbering.                                                                                                                                                            |
| `TempUnit`    |          | `F` or `C`                    | Temperature unit to use: (F)ahrenheit or (C)elsius, defaults to `C`.                                                                                                                       |
| `Smoothing`   |          | Boolean, positive integer     | If `True` or value >= 2 publishes the average of the last readings instead of each individual reading. Larger values result in slower converging readings. True = 3. Default is `False`.   |

### Outputs

The DhtSensor has 2 outputs which can be configured within the 'Connections' section (Look at connection readme's for 'Actuator / sensor relevant parameters' for details).

| Output        | Purpose                                                                                                  |
|---------------|----------------------------------------------------------------------------------------------------------|
| `Temperature` | Where to publish the temperature. When using with the openHAB connection configure a number/string Item. |
| `Humidity`    | Where to publish the humidity. When using with the openHAB connection configure a number/string Item.    |

### Configuration Example

```yaml
Logging:
    Syslog: yes
    Level: INFO

Connection1:
    Class: openhab_rest.rest_conn.OpenhabREST
    Name: openHAB
    URL: http://localhost:8080
    RefreshItem: Test_Refresh

SensorOutdoorClima:
    Class: gpio.dht_sensor.DhtSensor
    Connections:
        openHAB:
            Temperature:
                Item: temperature
            Humidity:
                Item: humidity
    Poll: 2
    Sensor: AM2302
    Pin: 7
    TempUnit: F
    Smoothing: False
    Level: DEBUG
```

## `gpio.rpi_gpio.RpiGpioSensor`

A sensor that can behave as either a polling sensor or a background sensor that reports the HIGH/LOW status of a GPIO pin.
Additionally, the sensor can detect toggle events and report the time of the event to different locations depending on the event duration.

### Dependencies

Depends on `lgpio` Python library.
The user running sensor_reporter must be in the `gpio` group to have GPIO access.
The user will also need read/write access to the sensorReporter root folder, the setup.sh will set these permissions.

```bash
cd /srv/sensorReporter
sudo ./install_dependencies.sh gpio
```

#### For Debian 11 (bullseye) - Raspberry Pi OS (Legacy)

Older OS (with `ldd --version` < glibc 2.33) need to manually install the `lgpio` Python library.
If the 'install_dependencies.sh' script was called with the 'gpio' parameter, manual removal of the incompatible lgpio version is required:

```bash
cd /srv/sensorReporter
bin/python -m pip uninstall lgpio
```

Then follow the installation instructions (Prerequisites and Download&Install) at: [https://abyz.me.uk/lg/download.html](https://abyz.me.uk/lg/download.html)

### Basic parameters

| Parameter        | Required | Restrictions                        | Purpose                                                                                                                                                                                                                                   |
|------------------|----------|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Class`          | X        | `gpio.rpi_gpio.RpiGpioSensor`       |                                                                                                                                                                                                                                           |
| `Connections`    | X        | Dictionary of connectors            | Defines where to publish the sensor status for each connection. This sensor has 3 outputs, see below. Look at connection readme's for 'Actuator / sensor relevant parameters' for details.                                                |
| `GpioChip`       | X        | Positive integer                    | Sets the GPIO-Chip to use. Use for Raspberry Pi 1 to 4 `GpioChip: 0` and for Raspberry Pi 5 `GpioChip: 4`. To list GPIOs and Chips write in console: `cat /sys/kernel/debug/gpio`                                                         |
| `Pin`            | X        | GPIO pin                            | Pin to use as sensor input, using the Broadcom pin numbering (GPIO Number).                                                                                                                                                               |
| `Level`          |          | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Override the global log level and use another one for this sensor.                                                                                                                                                                        |
| `Poll`           |          | Positive decimal number             | The interval in seconds to check for a change of the pin state. If the new state is present for a shorter time then the specified time noting is reported. Can be used as debounce. When not defined `EventDetection` must be configured. |
| `EventDetection` |          | BOTH                                | When defined, Poll is ignored. Indicates which GPIO event to listen for in the background.                                                                                                                                                |
| `PUD`            |          | UP / DOWN                           | Sets the input pin to use either the pull-up or pull-down resistor. Defaults to "DOWN"                                                                                                                                                    |

### Advanced parameters

For a valid configuration the basic parameters marked as required are necessary, all advanced parameters are optional.

| Parameter               | Required | Restrictions                  | Purpose                                                                                                                                                                                                                                                                                                                                                                                 |
|-------------------------|----------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Values`                |          | List of strings or dictionary | Values to replace the default state message of the `Switch` output (default is OPEN, CLOSED). For details see below.                                                                                                                                                                                                                                                                    |
| `Short_Press-Threshold` |          | Decimal number                | Defines the lower bound of short button press event in seconds and the debounce when using event detection. Debounce will wait for a signal to be stable for half the time specified here. If the duration of the button press was shorter than this value no update will be send. Useful to ignore false detection of button press due to electrical interferences. (default is 0.002) |
| `Long_Press-Threshold`  |          | Decimal number                | Defines the lower bound of long button press event in seconds, if the duration of the button press was shorter a short button event will be triggered. Can be determinded via the sensor-reporter log when set on info level. If not defined all button press events will be treated as short press.                                                                                    |
| `Btn_Pressed_State`     |          | LOW or HIGH                   | Sets the expected input level for short and long button press events. Set it to `LOW` if the input pin is connected to ground while the button is pressed (default is determined via PUD config value: `PUD = UP` will assume `Btn_Pressed_State: LOW`)                                                                                                                                 |

#### Values parameter

With this parameter the default state messages of the `Switch` output can be overwritten.
Two different layouts are possible.
To override the state message for all defined connections, configure a list of two string items:

```yaml
Values:
    - 'ON'
    - 'OFF'
```

The fist string will be send if the input is HIGH, the second on LOW.

If separate state messages for each connection are desired, configure a dictionary of connection names containing the string Item list:

```yaml
Values:
    <connection_name>:
        - 'ON'
        - 'OFF'
    <connection_name2>:
        - 'high'
        - 'low'
```

If a configured connection is not present in the Values parameter it will use the sensor default state messages (OPEN, CLOSED).

### Outputs

The RpiGpioSensor has 3 outputs which can be configured within the `Connections` section (Look at connection readme's for 'Actuator / sensor relevant parameters' for details).

| Output             | Purpose                                                                                                                                                                                                                                                                                                                                                                                               |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Switch`           | Where the OPEN/CLOSED messages are published. When using with the openHAB connection configure a contact/string Item.                                                                                                                                                                                                                                                                                 |
| `ShortButtonPress` | Location to publish an update after a short button press happened. Which are two changes of the logic level at the selected pin (eg. LOW, HIGH, LOW) and the duration of the button press is between Short_Press-Threshold and Long_Press-Threshold. For the recommended setup see example config at the bottom of the page. When using with the openHAB connection configure a datetime/string Item. |
| `LongButtonPress`  | Location to publish an update after a long button press happened, requires `Long_Press-Threshold`. When using with the openHAB connection configure a datetime/string Item.                                                                                                                                                                                                                           |

### Configuration Example

```yaml
Logging:
    Syslog: yes
    Level: INFO

Connection1:
    Class: openhab_rest.rest_conn.OpenhabREST
    Name: openHAB
    URL: http://localhost:8080
    RefreshItem: Test_Refresh

SensorBackDoor:
    Class: gpio.rpi_gpio.RpiGpioSensor
    Connections: 
        openHAB:
            Switch:
                Item: back_door
            ShortButtonPress:
                Item: back_door_short
            LongButtonPress:
                Item: back_door_long
    GpioChip: 0
    Pin: 17
    PUD: UP
    EventDetection: BOTH
    Long_Press-Threshold: 1.2

SensorFrontDoor:
    Class: gpio.rpi_gpio.RpiGpioSensor
    Connections:
        openHAB:
            Switch:
                Items: front_door
    Poll: 1
    GpioChip: 0
    Pin: 18
    PUD: UP
    Values:
        openHAB:
            - 'ON'
            - 'OFF'
    Level: DEBUG
```

## `gpio.rpi_gpio.RpiGpioActuator`

Commands a GPIO pin to go high, low, or if configured with SimulateButton it goes high for half a second and then goes to low.
A received command will be sent back on all configured connections to the configured return topic, to keep them up to date.

### Dependencies

Depends on `lgpio` Python library.
The user running sensor_reporter must be in the `gpio` group to have GPIO access.
The user will also need read/write access to the sensorReporter root folder, the setup.sh will set these permissions.

```bash
cd /srv/sensorReporter
sudo ./install_dependencies.sh gpio
```

#### For Debian 11 (bullseye) - Raspberry Pi OS (Legacy)

Older OS (with `ldd --version` < glibc 2.33) need to manually install the `lgpio` Python library.
If the 'install_dependencies.sh' script was called with the 'gpio' parameter, manual removal of the incompatible lgpio version is required:

```bash
cd /srv/sensorReporter
bin/python -m pip uninstall lgpio
```

Then follow the installation instructions (Prerequisites and Download&Install) at: [https://abyz.me.uk/lg/download.html](https://abyz.me.uk/lg/download.html)

### Parameters

| Parameter        | Required | Restrictions                    | Purpose                                                                                                                                                                           |
|------------------|----------|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Class`          | X        | `gpio.rpi_gpio.RpiGpioActuator` |                                                                                                                                                                                   |
| `Connections`    | X        | Dictionary of connectors        | Defines where to subscribe for messages and where to publish the status for each connection. Look at connection readme's for 'Actuator / sensor relevant parameters' for details. |
| `GpioChip`       | X        | Positive integer                | Sets the GPIO-Chip to use. Use for Raspberry Pi 1 to 4 `GpioChip: 0` and for Raspberry Pi 5 `GpioChip: 4`. To list GPIOs and Chips write in console: `cat /sys/kernel/debug/gpio` |
| `Pin`            | X        | GPIO pin                        | Pin to use as actuator output, using the Broadcom pin numbering (GPIO Number).                                                                                                    |
| `Level`          |          | DEBUG, INFO, WARNING, ERROR     | Override the global log level and use another one for this sensor.                                                                                                                |
| `ToggleDebounce` |          | Decimal number                  | The interval in seconds during which repeated toggle commands are ignored (default 0.15 seconds)                                                                                  |
| `InitialState`   |          | HIGH / LOW, (ON / OFF)          | Optional, initializes the pin to the given state. Ignores InvertOut. (ON = HIGH, default LOW)                                                                                     |
| `SimulateButton` |          | Boolean                         | When `True` simulates a button press by setting the pin to HIGH for half a second and then back to LOW. In case of `InitalState` ON it will toggle the other way around.          |
| `InvertOut`      |          | Boolean                         | Inverts the output when set to `True`. When inverted sending `ON` to the actuator will set the output to LOW, `OFF` will set the output to HIGH.                                  |

### Outputs / Inputs

The RpiGpioActuator has only one output and input.
The input expects ON, OFF, TOGGLE or a datetime string as command.
While ON, OFF set the GPIO pin accordingly, TOGGLE and a datetime string will toggle the pin.
Can be connected directly to a RpiGpioSensor ShortButtonPress / LongButtonPress output.
The output will send the pin state as ON / OFF after a change.
When using with the openHAB connection configure a switch/string Item.

### Configuration Examples

```yaml
DEFAULT:
    PinNumbering: BOARD

Logging:
    Syslog: yes
    Level: INFO

Connection1:
    Class: openhab_rest.rest_conn.OpenhabREST
    Name: openHAB
    URL: http://localhost:8080
    RefreshItem: Test_Refresh

ActuatorGarageDoor:
    Class: gpio.rpi_gpio.RpiGpioActuator
    Connections:
        openHAB:
            Item: GarageDoorCmd
    GpioChip: 0
    Pin: 35
    InitialState: ON
    SimulateButton: True
    Level: DEBUG
```

Using a local connection to toggle an actuator, which is also connected to openHAB.
The actuator shows always the correct status in openHAB, even if it is toggled locally.

```yaml
Logging:
    Syslog: yes
    Level: INFO

Connection_openHAB:
    Class: openhab_rest.rest_conn.OpenhabREST
    Name: openHAB
    URL: http://localhost:8080
    RefreshItem: Test_Refresh

Connection0:
    Class: local.local_conn.LocalConnection
    Name: local

SensorLightSwitch:
    Class: gpio.rpi_gpio.RpiGpioSensor
    Connections:
        local:
            ShortButtonPress:
                StateDest: toggle_garage_light
    GpioChip: 0
    Pin: 17
    PUD: UP
    EventDetection: BOTH
    Btn_Pressed_State: HIGH

ActuatorGarageLight:
    Class: gpio.rpi_gpio.RpiGpioActuator
    Connections:
        local:
            CommandSrc: toggle_garage_light
        openHAB:
            Item: garage_light
    GpioChip: 0
    Pin: 19
```

Circuit diagram

![example2](circuit_diagram/example2_circuit.png)

## `gpio.gpio_led.GpioColorLED`

Commands 1, 3 or 4 GPIO pins to control a white, RGB or RGBW LED via software PWM.
A received command will be sent back on all configured connections to the configured return topic, to keep them up to date.

### Dependencies

Depends on `lgpio` Python library.
The user running sensor_reporter must be in the `gpio` group to have GPIO access.
The user will also need read/write access to the sensorReporter root folder, the setup.sh will set these permissions.

```bash
cd /srv/sensorReporter
sudo ./install_dependencies.sh gpio
```

#### For Debian 11 (bullseye) - Raspberry Pi OS (Legacy)

Older OS (with `ldd --version` < glibc 2.33) need to manually install the `lgpio` Python library.
If the 'install_dependencies.sh' script was called with the 'gpio' parameter, manual removal of the incompatible lgpio version is required:

```bash
cd /srv/sensorReporter
bin/python -m pip uninstall lgpio
```

Then follow the installation instructions (Prerequisites and Download&Install) at: [https://abyz.me.uk/lg/download.html](https://abyz.me.uk/lg/download.html)

### Parameters

| Parameter       | Required | Restrictions                 | Purpose																																														 |
|-----------------|----------|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Class`         | X        | `gpio.gpio_led.GpioColorLED` |																																																 |
| `Connections`   | X        | Dictionary of connectors     | Defines where to subscribe for messages and where to publish the status for each connection. Look at connection readme's for 'Actuator / sensor relevant parameters' for details.				 |
| `GpioChip`      | X        | Positive integer             | Sets the GPIO-Chip to use. Use for Raspberry Pi 1 to 4 `GpioChip: 0` and for Raspberry Pi 5 `GpioChip: 4`. To list GPIOs and Chips write in console: `cat /sys/kernel/debug/gpio`              |
| `Pin`           | X        | Dictionary of GPIO pin's     | Pin to use as PWM output. Use sub parameter `Red`, `Green`, `Blue`, `White`, using the Broadcom pin numbering (GPIO Number). It is not necessary to define pin's for all colors. 				 |
| `Level`         |          | DEBUG, INFO, WARNING, ERROR  | When provided, sets the logging level for the sensor.																																			 |
| `InitialState`  |          | Dictionary of values 0-100   | Optional, will set the PWM duty cycle for the color (0 = off, 100 = on, full brightness). Use the sub parameter `Red`, `Green`, `Blue`, `White` (default RGBW = 0)							 |
| `InvertOut`     |          | Boolean                      | Use `True` for common anode LED (default setting). Otherwise use `False`																													     |
| `PWM-Frequency` |			 | Number						| Sets the PWM frequency in Hz (default 100 Hz)																																					 |
| `ToggleDebounce`|          | Decimal number               | The interval in seconds during which repeated toggle commands are ignored. (default 0.15 seconds)                                                                                              |

### Outputs / Inputs
The GpioColorLED has only one output and input.
The input expects 3 comma separated values as command. 
The values will set the LED color in HSV color space `h,s,v`, e.g. 240,100,100.
If the white pin is configured and the second value (saturation) = 0 then only the white LED will shine.
If only the white channel is configured one value (0-100) is sufficient as input.
The output will replay the LED color state in the same format.

The GpioColorLED also accepts ON, OFF, TOGGLE or a datetime string as a command.
While ON, OFF will set the brightness to 100% or 0% respectively, TOGGLE and a datetime string will toggle the brightness to the last state.

Can be connected directly to a RpiGpioSensor ShortButtonPress / LongButtonPress output.
When using with the openHAB connection configure a color item.
If only the white channel is configured use a dimmer item in openHAB.

### Example Config
```yaml
Logging:
    Syslog: yes
    Level: INFO

Connection_openHAB:
    Class: openhab_rest.rest_conn.OpenhabREST
    Name: openHAB
    URL: http://localhost:8080
    RefreshItem: Test_Refresh
    
ActuatorRgbLED:
    Class: gpio.gpio_led.GpioColorLED
    GpioChip: 0
    Pin:
        Red: 5
        Blue: 13
        Green: 6
        White: 7
    InitialState:
        White: 100
    Connections:
        openHAB:
            Item: eg_w_color_led
    Level: DEBUG
```
