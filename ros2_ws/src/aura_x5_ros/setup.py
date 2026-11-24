from glob import glob
import os
from setuptools import find_packages, setup

package_name = "aura_x5_ros"

setup(
    name=package_name,
    version="1.2.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="AURA-X5 Maintainers",
    maintainer_email="developer@example.com",
    description="ROS 2 Humble / TogetherROS nodes for AURA-X5 on D-Robotics RDK X5",
    license="MIT",
    entry_points={
        "console_scripts": [
            "sensor_node = aura_x5_ros.sensor_node:main",
            "bpu_perception_node = aura_x5_ros.bpu_perception_node:main",
            "safety_gate_node = aura_x5_ros.safety_gate_node:main",
            "actuator_ui_bridge_node = aura_x5_ros.actuator_ui_bridge_node:main",
        ],
    },
)
