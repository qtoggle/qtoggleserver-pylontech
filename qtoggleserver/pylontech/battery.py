import logging
import re
import time

from typing import Any, Optional, Union

from pylontech import Pylontech

from qtoggleserver.core import ports as core_ports
from qtoggleserver.lib import polled


class ImprovedPylontech(Pylontech):
    CHUNK_SIZE = 1024

    def __init__(self, *args, **kwargs) -> None:
        self._buffer: bytes = b''
        super().__init__(*args, **kwargs)

    def read_line(self) -> bytes:
        parts = re.split(rb'[\r\n]', self._buffer, maxsplit=1)
        if len(parts) > 1:
            line, self._buffer = parts
            return line.strip(b'\xff') + b'\n'

        data = self.s.read(self.CHUNK_SIZE)
        parts = re.split(rb'[\r\n]', data, maxsplit=1)
        if len(parts) > 1:
            line, rest = parts
            self._buffer += rest
            return line.strip(b'\xff') + b'\n'
        else:
            self._buffer += data
            return b''

    def read_frame(self) -> Any:
        raw_frame = self.read_line()
        f = self._decode_hw_frame(raw_frame=raw_frame)
        parsed = self._decode_frame(f)
        return parsed


class Battery(polled.PolledPeripheral):
    DEFAULT_POLL_INTERVAL = 60
    DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'
    DEFAULT_SERIAL_BAUD = 115200
    READ_RETRY_COUNT = 3

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        *,
        dev_ids: list[int],
        serial_port: str = DEFAULT_SERIAL_PORT,
        serial_baud: int = DEFAULT_SERIAL_BAUD,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._serial_port: str = serial_port
        self._serial_baud: int = serial_baud
        self._dev_ids: list[int] = dev_ids
        self._statuses_by_dev_id: dict[int, dict[str, Any]] = {}

    async def make_port_args(self) -> list[Union[dict[str, Any], type[core_ports.BasePort]]]:
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
        pylontech = ImprovedPylontech(self._serial_port, self._serial_baud)
        try:
            for dev_id in self._dev_ids:
                status = await self.run_threaded(self._poll_dev, pylontech, dev_id)
                self._statuses_by_dev_id[dev_id] = status
        finally:
            pylontech.s.close()

    def _poll_dev(self, pylontech: Pylontech, dev_id: int) -> dict:
        values = None
        for count in range(self.READ_RETRY_COUNT):
            try:
                values = pylontech.get_values_single(dev_id)
            except Exception:
                if count >= self.READ_RETRY_COUNT - 1:
                    raise
                else:
                    continue

        return {
            'timestamp': int(time.time()),
            'soc': values.StateOfCharge,
            'temperature': values.AverageBMSTemperature,
            'current': values.Current,
            'voltage': values.Voltage,
            'power': values.Power,
            'cycles': values.CycleNumber,
        }

    def get_aggregated_status(self) -> Optional[dict[str, Any]]:
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
