import time
import random
import asyncio


class DemoTelemetry:
    def __init__(self, name):
        self.name = name
        self.battery_voltage = 3.9  # starting
        self.alerted = False
        self.safemode = False

    async def generate_telemetry(self, duration, major_tom, type="NOMINAL"):

        if type == "ERROR":
            self.battery_voltage = 2.0

        timeout = time.time() + duration
        while time.time() < timeout:
            if type == "NOMINAL":
                self.__nominal()
            elif type == "ERROR":
                self.__error(major_tom=major_tom)
            else:
                raise(ValueError(f'Telemetry type must be NOMINAL or ERROR, not {type}'))

            if self.safemode == True:
                event = {
                    "system": self.name,
                    "type": "Telemetry Alert",
                    "level": "warning",
                    "message": "Stopping Telemetry beacon, entering safemode.",
                    "timestamp": int(time.time() * 1000)
                }
                asyncio.ensure_future(major_tom.transmit_events(events=[event]))
                break
            metrics = [{
                "system": self.name,
                "subsystem": "battery",
                "metric": "voltage",
                "value": self.battery_voltage,
                "timestamp": int(time.time() * 1000)
            }]
            asyncio.ensure_future(major_tom.transmit_metrics(metrics=metrics))
            await asyncio.sleep(1)

    def __nominal(self):
        self.battery_voltage = self.__telemetry_stepper(
            current_value=self.battery_voltage, step=0.01, minimum=3.0, maximum=4.2)

    def __error(self, major_tom):
        self.battery_voltage = self.__telemetry_stepper(
            current_value=self.battery_voltage, step=0.01, minimum=3.2, maximum=4.2)
        if not self.alerted and self.battery_voltage <= 2.5:
            event = {
                "system": self.name,
                "type": "Telemetry Alert",
                "debug": {
                    "subsystem": "battery",
                    "metric": "voltage",
                    "value": self.battery_voltage,
                    "timestamp": int(time.time() * 1000)
                },
                "level": "error",
                "message": f"Battery level below critical threshold: {self.battery_voltage}",
                "timestamp": int(time.time() * 1000)
            }
            asyncio.ensure_future(major_tom.transmit_events(events=[event]))
            self.alerted = True
        elif self.alerted and self.battery_voltage >= 3.2:
            event = {
                "system": self.name,
                "type": "Telemetry Alert",
                "debug": {
                    "subsystem": "battery",
                    "metric": "voltage",
                    "value": self.battery_voltage,
                    "timestamp": int(time.time() * 1000)
                },
                "level": "nominal",
                "message": f"Battery level back to nominal: {self.battery_voltage}",
                "timestamp": int(time.time() * 1000)
            }
            asyncio.ensure_future(major_tom.transmit_events(events=[event]))
            self.alerted = False

    def __telemetry_stepper(self, current_value, step, minimum, maximum):
        if current_value <= minimum:
            return current_value + step
        elif current_value >= maximum:
            return current_value - step
        return current_value + self.__random_sign(step)

    def __random_sign(self, number):
        if random.random() < 0.5:
            return -1.0*number
        return number
