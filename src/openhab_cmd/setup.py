from setuptools import setup

package_name = 'openhab_cmd'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/openhab_cmd']),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='openhab_cmd ROS2 package',
    license='MIT',
    entry_points={
        'console_scripts': [],
    },
)
