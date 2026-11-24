"""ROS 2 Sensor & Hardware Control Node (/aura_sensor_node) for AURA-X5 on RDK X5.
Publishes real hardware telemetry, mmWave radar presence, DPDT privacy sense,
Kill-Switch interrupts, and EC11 physical inputs without fabricating missing sensors.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String

from aura_x5_ros.contracts import (
    TOPIC_HARDWARE_TELEMETRY,
    TOPIC_KILL_SWITCH,
    TOPIC_PHYSICAL_INPUT,
    TOPIC_PRIVACY_STATE,
    TOPIC_RADAR_PRESENCE,
    encode_json,
    ensure_firmware_on_path,
)

ensure_firmware_on_path()
from hal_devices import HardwareUnavailableError, PrivacyAndControls, parse_ld2410c_frame  # type: ignore
from sensor_hub import probe_connected_hardware  # type: ignore
from sensors_full import INA219Driver, SHT40Driver  # type: ignore


class AuraSensorNode(Node):
    def __init__(self):
        super().__init__("aura_sensor_node")
        self.declare_parameter("telemetry_hz", 2.0)
        self.declare_parameter("radar_hz", 5.0)
        self.declare_parameter("kill_switch_poll_hz", 20.0)
        self.declare_parameter("radar_uart_device", "/dev/ttyS1")
        self.declare_parameter("radar_baud", 256000)

        self.pub_tel = self.create_publisher(String, TOPIC_HARDWARE_TELEMETRY, 5)
        self.pub_radar = self.create_publisher(String, TOPIC_RADAR_PRESENCE, 5)
        self.pub_privacy = self.create_publisher(Bool, TOPIC_PRIVACY_STATE, 5)
        self.pub_kill = self.create_publisher(Bool, TOPIC_KILL_SWITCH, 10)
        self.pub_input = self.create_publisher(String, TOPIC_PHYSICAL_INPUT, 10)

        self.controls = None
        try:
            self.controls = PrivacyAndControls()
            self.get_logger().info("Hobot.GPIO PrivacyAndControls initialized.")
        except HardwareUnavailableError as exc:
            self.get_logger().warn(f"GPIO controls unavailable: {exc}")

        self.radar_serial = None
        uart_dev = self.get_parameter("radar_uart_device").get_parameter_value().string_value
        uart_baud = self.get_parameter("radar_baud").get_parameter_value().integer_value
        try:
            import serial  # type: ignore
            self.radar_serial = serial.Serial(uart_dev, baudrate=uart_baud, timeout=0.05)
            self.get_logger().info(f"HLK-LD2410C UART opened on {uart_dev}@{uart_baud}.")
        except Exception as exc:
            self.get_logger().info(f"HLK-LD2410C UART not attached ({uart_dev}): {exc}")

        self._last_ec11_sw = 1
        self._last_kill = False

        tel_hz = float(self.get_parameter("telemetry_hz").value)
        radar_hz = float(self.get_parameter("radar_hz").value)
        kill_hz = float(self.get_parameter("kill_switch_poll_hz").value)

        self.create_timer(1.0 / max(0.5, tel_hz), self._poll_telemetry)
        self.create_timer(1.0 / max(1.0, radar_hz), self._poll_radar)
        self.create_timer(1.0 / max(5.0, kill_hz), self._poll_fast_gpio)

    def _poll_fast_gpio(self):
        if self.controls is None:
            return
        kill_now = self.controls.is_kill_pressed()
        if kill_now or kill_now != self._last_kill:
            self._last_kill = kill_now
            self.pub_kill.publish(Bool(data=kill_now))

        # Active-low falling edge on EC11 push button -> physical approval
        ec11_sw = int(self.controls.GPIO.input(self.controls.PIN_EC11_SW))
        if self._last_ec11_sw == 1 and ec11_sw == 0:
            payload = {
                "ts_ns": self.get_clock().now().nanoseconds,
                "source": "ec11_press",
                "decision": "approve",
            }
            self.pub_input.publish(String(data=encode_json(payload)))
        self._last_ec11_sw = ec11_sw

    def _poll_radar(self):
        ts_ns = self.get_clock().now().nanoseconds
        if self.radar_serial is None:
            self.pub_radar.publish(String(data=encode_json({
                "ts_ns": ts_ns,
                "connected": False,
                "user_present": None,
            })))
            return
        raw = self.radar_serial.read(64)
        idx = raw.find(b"\xf4\xf3\xf2\xf1")
        reading = parse_ld2410c_frame(raw[idx:idx + 23]) if idx >= 0 else None
        if reading is not None:
            self.pub_radar.publish(String(data=encode_json({
                "ts_ns": ts_ns,
                "connected": True,
                "user_present": reading.user_present,
                "moving_dist_cm": reading.moving_dist_cm,
                "static_dist_cm": reading.static_dist_cm,
                "detect_dist_cm": reading.detect_dist_cm,
            })))

    def _poll_telemetry(self):
        tel = probe_connected_hardware()
        if tel.i2c_sht40:
            try:
                env = SHT40Driver().read()
                tel.ambient_temp_c = env.temp_c
                tel.ambient_rh_pct = env.rh_pct
            except Exception as exc:
                self.get_logger().warn(f"SHT40 read error: {exc}")
        if tel.i2c_ina219:
            try:
                tel.power_mw = round(INA219Driver().read_bus_voltage_v() * 1000.0, 1)
            except Exception as exc:
                self.get_logger().warn(f"INA219 read error: {exc}")

        payload = tel.to_dict()
        payload["ts_ns"] = self.get_clock().now().nanoseconds
        self.pub_tel.publish(String(data=encode_json(payload)))

        if self.controls is not None:
            self.pub_privacy.publish(Bool(data=self.controls.is_privacy_power_on()))


def main(args=None):
    rclpy.init(args=args)
    node = AuraSensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.radar_serial is not None:
            node.radar_serial.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
