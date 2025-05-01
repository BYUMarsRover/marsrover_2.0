from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'coug_localization'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Nelson Durrant',
    maintainer_email='snelsondurrant@gmail.com',
    description='Localization capabilities for the CougUV',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sync_origin = coug_localization.sync_origin:main',
            'dvl_odom = coug_localization.dvl_odom:main',
            'gps_fix = coug_localization.gps_fix:main',
        ],
    },
)
