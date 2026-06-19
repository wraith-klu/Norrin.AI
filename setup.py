from setuptools import setup, find_packages


setup(
    name="player-performance-prediction",
    version="0.1.0",
    packages=find_packages(include=["src*", "sports_predictor*", "api*", "dashboard*"]),
)
