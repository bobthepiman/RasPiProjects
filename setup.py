from setuptools import setup, find_packages
setup(
    name = "RasPiProjects",
    version = "0.2.1",
    author='Josh Walawender',
    packages = find_packages(),
    entry_points = {
        'console_scripts': [
            'measurehumidity = HumidityMonitor:main',
            'plothumidity = HumidityMonitor:plot',
        ]
    }
)
