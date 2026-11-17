from glob import glob

from setuptools import find_packages, setup

package_name = "openhab_bridge"

setup(
    name=package_name,
    version="2.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools", "python-openhab-rest-client>=21.4.1"],
    zip_safe=True,
    maintainer="Michael Christian Dörflinger",
    maintainer_email="michdo93@users.noreply.github.com",
    description="Bridge between openHAB and ROS 2",
    license="MIT",
    tests_require=["pytest"],
    entry_points={"console_scripts": [
        "openhab_bridge = openhab_bridge.bridge_node:main",
    ]},
)
