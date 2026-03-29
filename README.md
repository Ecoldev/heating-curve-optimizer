# Heating Curve Optimizer

Tool for optimizing underfloor heating settings based on real weather data.

## Problem

Manual adjustment of heating curves is inefficient and often based on guesswork.
This tool uses weather data (historical + forecast) to recommend optimal settings.

## Features

* Open-Meteo integration
* IMGW integration (Poland)
* Heating curve recommendation engine
* Two modes:

  * simple (trend-based)
  * advanced (weather factors + charts)

## Usage

### Simple mode

python main.py

### Advanced mode

python main.py advanced

## Requirements

pip install -r requirements.txt

## Data sources

* Open-Meteo API
* IMGW API

## Roadmap

* [ ] CLI arguments (lat/lon)
* [ ] config file
* [ ] JSON output (history)
* [ ] Home Assistant integration

## Author

DevOps / automation project
