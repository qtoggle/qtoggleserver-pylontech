import time

from typing import Any, Dict, Optional, List, Type, Union

from pylontech import Pylontech

from qtoggleserver.core import ports as core_ports
from qtoggleserver.lib import polled


class Battery(polled.PolledPeripheral):
    DEFAULT_POLL_INTERVAL = 60
    DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'
    DEFAULT_SERIAL_BAUD = 115200

    def __init__(
        self,
        *,
        dev_ids: List[int],
        serial_port: str = DEFAULT_SERIAL_PORT,
        serial_baud: int = DEFAULT_SERIAL_BAUD,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._serial_port: str = serial_port
        self._serial_baud: int = serial_baud
        self._dev_ids: List[int] = dev_ids
        self._statuses_by_dev_id: Dict[int, Dict[str, Any]] = {}

    async def make_port_args(self) -> List[Union[Dict[str, Any], Type[core_ports.BasePort]]]:
        from .ports import SocPort, TemperaturePort, CurrentPort, VoltagePort, PowerPort, CyclesPort

        status_port_drivers = [SocPort, TemperaturePort, CurrentPort, VoltagePort, PowerPort, CyclesPort]
        port_args = [
            {
                'driver': driver,
                'id': driver.get_property(),
            }
            for driver in status_port_drivers
        ]

        return port_args

    async def poll(self) -> None:
        pylontech = Pylontech(self._serial_port, self._serial_baud)
        try:
            for dev_id in self._dev_ids:
                status = await self.run_threaded(self._poll_dev, pylontech, dev_id)
                self._statuses_by_dev_id[dev_id] = status
        finally:
            pylontech.s.close()

    def _poll_dev(self, pylontech: Pylontech, dev_id: int) -> dict:
        values = pylontech.get_values_single(dev_id)
        return {
            'timestamp': int(time.time()),
            'soc': values.StateOfCharge,
            'temperature': values.AverageBMSTemperature,
            'current': values.Current,
            'voltage': values.Voltage,
            'power': values.Power,
            'cycles': values.CycleNumber,
        }

    def get_aggregated_status(self) -> Optional[Dict[str, Any]]:
        if not self._statuses_by_dev_id:
            return None

        statuses = list(self._statuses_by_dev_id.values())
        agg_status = dict(statuses[0])

        for status in statuses[1:]:
            agg_status['timestamp'] = min(agg_status['timestamp'], status['timestamp'])
            agg_status['soc'] = min(agg_status['soc'], status['soc'])
            agg_status['temperature'] = max(agg_status['temperature'], status['temperature'])
            agg_status['current'] += status['current']
            agg_status['voltage'] += status['voltage']
            agg_status['power'] += status['power']
            agg_status['cycles'] = max(agg_status['cycles'], status['cycles'])

        agg_status['voltage'] /= len(statuses)

        return agg_status
