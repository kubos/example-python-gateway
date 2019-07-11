import time
import random
import asyncio


class DemoTelemetry:
    def __init__(self, name):
        self.name = name
        self.battery_voltage = 3.9 # starting
        self.alerted = False

    async def nominal(self, duration, major_tom):
        timeout = time.time() + duration
        while time.time() < timeout:
            self.battery_voltage = self.__telemetry_stepper(
                current_value=self.battery_voltage,step=0.01,minimum=3.0,maximum=4.2)
            metrics = [{
                "system": self.name,
                "subsystem": "battery",
                "metric": "voltage",
                "value": self.battery_voltage,
                "timestamp": int(time.time() * 1000)
            }]
            asyncio.ensure_future(major_tom.transmit_metrics(metrics = metrics))
            await asyncio.sleep(1)

    async def error(self, duration, major_tom):
        timeout = time.time() + duration
        self.battery_voltage = 2.0
        while time.time() < timeout:
            self.battery_voltage = self.__telemetry_stepper(
                current_value=self.battery_voltage,step=0.01,minimum=3.2,maximum=4.2)
            metrics = [{
                "system": self.name,
                "subsystem": "battery",
                "metric": "voltage",
                "value": self.battery_voltage,
                "timestamp": int(time.time() * 1000)
            }]
            asyncio.ensure_future(major_tom.transmit_metrics(metrics = metrics))
            if not self.alerted and self.battery_voltage <= 2.1:
                event = {
                    "system": self.name,
                    "type": "Telemetry Alert",
                    "debug": {
                        "subsystem": "battery",
                        "metric": "voltage",
                        "value": self.battery_voltage,
                        "timestamp": int(time.time() * 1000)
                    },
                    "level": "warning",
                    "message": "Battery level below critical threshold",
                    "timestamp": int(time.time() * 1000)
                }
                asyncio.ensure_future(major_tom.transmit_events(events = [event]))
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
                    "message": "Battery level back to nominal",
                    "timestamp": int(time.time() * 1000)
                }
                asyncio.ensure_future(major_tom.transmit_events(events = [event]))
                self.alerted = False

            await asyncio.sleep(1)

    def __telemetry_stepper(self,current_value,step,minimum,maximum):
        if current_value <= minimum:
            return current_value + step
        elif current_value >= maximum:
            return current_value - step
        else:
            return current_value + self.__random_sign(step)
        print(1)

    def __random_sign(self,number):
        if random.random() < 0.5:
            return -1.0*number
        else:
            return number
        print(2)
