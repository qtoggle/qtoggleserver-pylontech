## About

This is an addon for [qToggleServer](https://github.com/qtoggle/qtoggleserver).

It provides Pylontech batteries support for qToggleServer.

Currently, only status reading is supported. No changes to the inverter configuration can be done via this add-on.


## Install

Install using pip:

    pip install qtoggleserver-pylontech


## Usage

##### `qtoggleserver.conf:`
``` ini
...
peripherals = [
    ...
    {
        driver = "qtoggleserver.pylontech.Battery"
        name = "mybattery"              # an optional name of your choice
        serial_port = "/dev/ttyUSB0"    # this is the default
        serial_baud = 115200            # this is the default
        dev_ids = [2, 3]                # list of battery ids installed
    }
    ...
]
...
```
