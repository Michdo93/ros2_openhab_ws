from glob import glob

from setuptools import find_packages, setup

package_name = "openhab_examples"

setup(
    name=package_name,
    version="2.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Michael Christian Dörflinger",
    maintainer_email="michdo93@users.noreply.github.com",
    description="Examples for the openHAB bridge",
    license="MIT",
    tests_require=["pytest"],
    entry_points={"console_scripts": [
        "state_listener = openhab_examples.state_listener:main",
        "presence_light = openhab_examples.presence_light:main",
    ]},
)
