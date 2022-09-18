from typing import cast

from qtoggleserver.core import ports as core_ports
from qtoggleserver.core.typing import NullablePortValue
from qtoggleserver.lib import polled

from .battery import Battery


class BatteryStatusPort(polled.PolledPort):
    PROPERTY = ''

    @classmethod
    def get_property(cls) -> str:
        return cls.PROPERTY

    def get_peripheral(self) -> Battery:
        return cast(Battery, super().get_peripheral())

    async def read_value(self) -> NullablePortValue:
        battery = self.get_peripheral()
        status = battery.get_aggregated_status()
        if status is None:
            return None

        return status[self.PROPERTY]


class SocPort(BatteryStatusPort):
    TYPE = core_ports.TYPE_NUMBER
    PROPERTY = 'soc'


class TemperaturePort(BatteryStatusPort):
    TYPE = core_ports.TYPE_NUMBER
    PROPERTY = 'temperature'


class CurrentPort(BatteryStatusPort):
    TYPE = core_ports.TYPE_NUMBER
    PROPERTY = 'current'


class VoltagePort(BatteryStatusPort):
    TYPE = core_ports.TYPE_NUMBER
    PROPERTY = 'voltage'


class PowerPort(BatteryStatusPort):
    TYPE = core_ports.TYPE_NUMBER
    PROPERTY = 'power'


class CyclesPort(BatteryStatusPort):
    TYPE = core_ports.TYPE_NUMBER
    PROPERTY = 'cycles'
