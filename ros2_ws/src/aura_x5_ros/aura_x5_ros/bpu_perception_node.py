"""ROS 2 Continuous BPU Perception Node (/aura_bpu_perception_node) for AURA-X5 on RDK X5.
Runs real hbm_runtime inference on the 10-TOPS Bayes BPU; never falls back to CPU silently.
"""
import base64
from collections import deque
import io
from pathlib import Path
import time
import numpy as np
from PIL import Image
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from aura_x5_ros.contracts import (
    TOPIC_BPU_METRICS,
    TOPIC_DESKTOP_FRAME,
    TOPIC_PERCEPTION_RESULT,
    decode_json,
    encode_json,
    ensure_firmware_on_path,
    read_soc_temp_c,
)

ensure_firmware_on_path()
from bpu_vision import BPUUnavailableError, RDKX5BPUService  # type: ignore


class AuraBPUPerceptionNode(Node):
    def __init__(self):
        super().__init__("aura_bpu_perception_node")
        self.declare_parameter(
            "bpu_model_path",
            "/app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/mobilenetv2_224x224_nv12.bin",
        )
        self.declare_parameter("bpu_continuous_hz", 15.0)
        self.declare_parameter("bpu_metrics_hz", 2.0)

        self.pub_result = self.create_publisher(String, TOPIC_PERCEPTION_RESULT, 5)
        self.pub_metrics = self.create_publisher(String, TOPIC_BPU_METRICS, 5)
        self.sub_frame = self.create_subscription(String, TOPIC_DESKTOP_FRAME, self._on_desktop_frame, 2)

        model_path = Path(self.get_parameter("bpu_model_path").get_parameter_value().string_value)
        self.bpu = None
        self.bpu_error = None
        try:
            self.bpu = RDKX5BPUService(model_path)
            self.get_logger().info(
                f"BPU ready: {self.bpu.model_name} shape={self.bpu.input_shape} ({model_path})"
            )
        except BPUUnavailableError as exc:
            self.bpu_error = str(exc)
            self.get_logger().error(f"BPU_UNAVAILABLE (no CPU fallback): {exc}")

        self._latest_tensor = None
        self._latest_frame_id = "continuous-idle"
        self._latencies_ms = deque(maxlen=100)
        self._frame_times = deque(maxlen=100)

        infer_hz = float(self.get_parameter("bpu_continuous_hz").value)
        metrics_hz = float(self.get_parameter("bpu_metrics_hz").value)
        self.create_timer(1.0 / max(1.0, infer_hz), self._run_continuous_step)
        self.create_timer(1.0 / max(0.5, metrics_hz), self._publish_metrics)

    def _on_desktop_frame(self, msg: String):
        data = decode_json(msg.data)
        b64_jpg = data.get("thumb_b64")
        if not b64_jpg:
            return
        raw = base64.b64decode(b64_jpg)
        img = Image.open(io.BytesIO(raw)).convert("RGB").resize((224, 224))
        arr = np.asarray(img, dtype=np.uint8).transpose(2, 0, 1)[None, ...]
        self._latest_tensor = np.ascontiguousarray(arr)
        self._latest_frame_id = str(data.get("frame_id", "desktop-frame"))

    def _run_continuous_step(self):
        if self.bpu is None:
            return
        if self._latest_tensor is None:
            self._latest_tensor = np.zeros(self.bpu.input_shape, dtype=np.uint8)
        res = self.bpu.infer_chw_uint8(self._latest_tensor)
        now = time.perf_counter()
        self._latencies_ms.append(res.latency_ms)
        self._frame_times.append(now)

        payload = {
            "ts_ns": self.get_clock().now().nanoseconds,
            "frame_id": self._latest_frame_id,
            "model_name": res.model_name,
            "bpu_core": res.bpu_core,
            "latency_ms": res.latency_ms,
            "top_class_idx": res.top_class_idx,
            "top_score": res.top_score,
        }
        self.pub_result.publish(String(data=encode_json(payload)))

    def _publish_metrics(self):
        fps = 0.0
        avg_ms = None
        p95_ms = None
        if len(self._frame_times) >= 2:
            span = self._frame_times[-1] - self._frame_times[0]
            if span > 0:
                fps = round((len(self._frame_times) - 1) / span, 2)
        if self._latencies_ms:
            arr = np.asarray(self._latencies_ms, dtype=np.float64)
            avg_ms = round(float(arr.mean()), 2)
            p95_ms = round(float(np.percentile(arr, 95)), 2)

        payload = {
            "ts_ns": self.get_clock().now().nanoseconds,
            "bpu_ready": self.bpu is not None,
            "status": "BPU_ONLINE" if self.bpu is not None else "BPU_UNAVAILABLE",
            "error": self.bpu_error,
            "model_name": self.bpu.model_name if self.bpu is not None else None,
            "fps": fps,
            "avg_ms": avg_ms,
            "p95_ms": p95_ms,
            "soc_temp_c": read_soc_temp_c(),
        }
        self.pub_metrics.publish(String(data=encode_json(payload)))


def main(args=None):
    rclpy.init(args=args)
    node = AuraBPUPerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
