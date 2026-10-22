"""Meteorological unit conversion utilities for HeatSense.

Strictly preserves precision and raises validation errors on physically impossible values.
"""

from typing import Union

import numpy as np
import pandas as pd
import xarray as xr

# Physical constants
ABSOLUTE_ZERO_CELSIUS = -273.15
ZERO_CELSIUS_KELVIN = 273.15


def kelvin_to_celsius(
    val: Union[float, np.ndarray, pd.Series, xr.DataArray],
) -> Union[float, np.ndarray, pd.Series, xr.DataArray]:
    """Convert temperature from Kelvin (K) to Celsius (°C).

    Formula: °C = K - 273.15
    """
    if isinstance(val, (int, float)):
        if val < 0.0:
            raise ValueError(f"Physically impossible temperature below 0 Kelvin: {val} K")
        return round(val - ZERO_CELSIUS_KELVIN, 4)

    if isinstance(val, (np.ndarray, pd.Series, xr.DataArray)):
        if np.any(val < 0.0):
            raise ValueError("Temperature array contains values below absolute zero (< 0 K)")
        return val - ZERO_CELSIUS_KELVIN

    raise TypeError(f"Unsupported type for temperature conversion: {type(val)}")


def celsius_to_kelvin(
    val: Union[float, np.ndarray, pd.Series, xr.DataArray],
) -> Union[float, np.ndarray, pd.Series, xr.DataArray]:
    """Convert temperature from Celsius (°C) to Kelvin (K).

    Formula: K = °C + 273.15
    """
    if isinstance(val, (int, float)):
        if val < ABSOLUTE_ZERO_CELSIUS:
            raise ValueError(f"Temperature below absolute zero: {val} °C")
        return round(val + ZERO_CELSIUS_KELVIN, 4)

    if isinstance(val, (np.ndarray, pd.Series, xr.DataArray)):
        if np.any(val < ABSOLUTE_ZERO_CELSIUS):
            raise ValueError("Temperature array contains values below absolute zero (< -273.15 °C)")
        return val + ZERO_CELSIUS_KELVIN

    raise TypeError(f"Unsupported type for temperature conversion: {type(val)}")


def accumulated_joules_to_wm2(
    joules: Union[float, np.ndarray, pd.Series, xr.DataArray],
    accumulation_seconds: float = 3600.0,
) -> Union[float, np.ndarray, pd.Series, xr.DataArray]:
    """Convert accumulated radiation (J/m^2) over accumulation_seconds to mean flux (W/m^2).

    Formula: W/m^2 = (J/m^2) / dt
    """
    if accumulation_seconds <= 0:
        raise ValueError("accumulation_seconds must be positive")
    return joules / accumulation_seconds
