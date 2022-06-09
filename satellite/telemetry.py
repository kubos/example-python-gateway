import time
import random


class FakeTelemetry:
    def __init__(self, name, extra_panels=0):
        self.name = name
        self.alerted = False
        self.safemode = False
        self.start_time = time.time()  # For calculating uptime
        self.telemetry = {
            "battery": {
                "voltage": {
                    "value": 3.9,  # Volts, starting
                    "step": 0.01,
                    "max": 4.2,
                    "min": 3.0
                },
                "temperature": {
                    "value": 20,  # Celsius, starting
                    "step": 0.1,
                    "max": 35,
                    "min": 5
                }
            },
            "panels": {
                "temperature_x": {
                    "value": 25,  # Celsius, starting
                    "step": 0.1,
                    "max": 35,
                    "min": 20
                },
                "temperature_y": {
                    "value": 25.5,  # Celsius, starting
                    "step": 0.1,
                    "max": 35,
                    "min": 20
                },
                "temperature_z": {
                    "value": 24.5,  # Celsius, starting
                    "step": 0.1,
                    "max": 35,
                    "min": 20
                }
            }
        }
        for i in range(extra_panels): 
            k = "temperature_{}".format(i)
            x = i * 0.001
            self.telemetry["panels"][k] = {
                "value": x + 24.5,  # Celsius, starting
                "step": x + 0.1,
                "max": 35,
                "min": 20
            }


    def uptime(self, timestamp_ms):
        return timestamp_ms/1000.0 - self.start_time

    # Returns metrics, [list of errors]
    def generate_telemetry(self, mode="NOMINAL", timestamp_ms=None):
        if mode == "NOMINAL":
            self.__nominal()
        elif mode == "ERROR":
            self.telemetry['battery']['voltage']['value'] = 2.0
            self.__error()
        else:
            raise(ValueError(f'Telemetry mode must be NOMINAL or ERROR, not {mode}'))

        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)

        if self.safemode == True:
            event = {
                "system": self.name,
                "type": "Telemetry Alert",
                "level": "warning",
                "message": "Stopping Telemetry beacon, entering safemode.",
                "timestamp": timestamp_ms
            }
            return None, [event]
        
        metrics = []
        for subsystem in self.telemetry:
            for metric in self.telemetry[subsystem]:
                metrics.append({
                    "system": self.name,
                    "subsystem": subsystem,
                    "metric": metric,
                    "value": self.telemetry[subsystem][metric]["value"],
                    "timestamp": timestamp_ms
                })
        metrics.append({
            "system": self.name,
            "subsystem": "obc",
            "metric": "uptime",
            "value": self.uptime(timestamp_ms),
            "timestamp": timestamp_ms
        })
        return metrics, []

    def __nominal(self):
        for subsystem in self.telemetry:
            for metric in self.telemetry[subsystem]:
                self.telemetry[subsystem][metric]["value"] = self.__telemetry_stepper(
                    current_value=self.telemetry[subsystem][metric]["value"],
                    step=self.telemetry[subsystem][metric]["step"],
                    min=self.telemetry[subsystem][metric]["min"],
                    max=self.telemetry[subsystem][metric]["max"])

    def __error(self, gateway):
        for subsystem in self.telemetry:
            for metric in self.telemetry[subsystem]:
                self.telemetry[subsystem][metric]["value"] = self.__telemetry_stepper(
                    current_value=self.telemetry[subsystem][metric]["value"],
                    step=self.telemetry[subsystem][metric]["step"],
                    min=self.telemetry[subsystem][metric]["min"],
                    max=self.telemetry[subsystem][metric]["max"])

        if not self.alerted and self.telemetry['battery']['voltage']['value'] <= 2.5:
            event = {
                "system": self.name,
                "type": "Telemetry Alert",
                "debug": {
                    "subsystem": "battery",
                    "metric": "voltage",
                    "value": self.telemetry['battery']['voltage']['value'],
                    "timestamp": int(time.time() * 1000)
                },
                "level": "error",
                "message": f"Battery level below critical threshold: {self.telemetry['battery']['voltage']['value']}",
                "timestamp": int(time.time() * 1000)
            }
            self.alerted = True
            return None, [event]
        elif self.alerted and self.telemetry['battery']['voltage']['value'] >= 3.2:
            event = {
                "system": self.name,
                "type": "Telemetry Alert",
                "level": "nominal",
                "message": f"Battery level back to nominal: {self.telemetry['battery']['voltage']['value']}",
                "timestamp": int(time.time() * 1000)
            }
            return None, [event]
            self.alerted = False

    def __telemetry_stepper(self, current_value, step, min, max):
        if current_value <= min:
            return current_value + step
        elif current_value >= max:
            return current_value - step
        return current_value + self.__random_sign(step)

    def __random_sign(self, number):
        if random.random() < 0.5:
            return -1.0*number
        return number
