# AURA-X5 RDK X5 BPU Models Manifest

Large compiled `.bin` / `.hbm` neural network binaries are **not** committed to Git. All models run natively on the **D-Robotics RDK X5 10-TOPS Bayes BPU** via `hbm_runtime` (`1.24.5` / HBRT `3.15.55.0`).

| Role | Model File | Default Path on RDK X5 | Input Shape | Source |
|---|---|---|---|---|
| **Stage 1/3 Baseline (Pre-installed on RDK OS)** | `mobilenetv2_224x224_nv12.bin` | `/app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/mobilenetv2_224x224_nv12.bin` | `[1, 3, 224, 224]` (`uint8`) | Official RDK X5 OS Image |
| **Stage 3 Object / UI Detection (Optional Upgrade)** | `yolov8s_detect_bayese_640x640_nv12.bin` | `/opt/aura_x5/models/yolov8s_detect_bayese_640x640_nv12.bin` | `[1, 3, 640, 640]` (`nv12`) | [D-Robotics/rdk_model_zoo](https://github.com/D-Robotics/rdk_model_zoo) |
| **Stage 3 Tiled Desktop OCR (Optional Upgrade)** | `ppocrv5_det_640x640.hbm` + `ppocrv5_rec.hbm` | `/opt/aura_x5/models/` | `640×640` tiles (`stride=512`) | [D-Robotics/rdk_model_zoo](https://github.com/D-Robotics/rdk_model_zoo) |

## Verify Models on RDK X5
```bash
ls -lh /app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/
```
