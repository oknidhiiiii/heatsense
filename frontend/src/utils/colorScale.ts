/**
 * Meteorological color ramp utilities for HeatSense.
 * Maps temperatures in Celsius to accessible color hex codes and Cesium Color values.
 */

export interface ColorStop {
  temp: number;
  hex: string;
  r: number;
  g: number;
  b: number;
}

// Thermal palette from cool blue (15°C) -> cyan (20°C) -> yellow (28°C) -> orange (34°C) -> deep red (42°C)
export const COLOR_STOPS: ColorStop[] = [
  { temp: 15.0, hex: '#3182ce', r: 49, g: 130, b: 206 },
  { temp: 22.0, hex: '#38b2ac', r: 56, g: 178, b: 172 },
  { temp: 28.0, hex: '#ecc94b', r: 236, g: 201, b: 75 },
  { temp: 34.0, hex: '#ed8936', r: 237, g: 137, b: 54 },
  { temp: 42.0, hex: '#e53e3e', r: 229, g: 62, b: 62 },
];

export function getTemperatureHex(tempC: number): string {
  if (tempC <= COLOR_STOPS[0].temp) {
    return COLOR_STOPS[0].hex;
  }
  const last = COLOR_STOPS[COLOR_STOPS.length - 1];
  if (tempC >= last.temp) {
    return last.hex;
  }

  // Linear interpolation between color stops
  for (let i = 0; i < COLOR_STOPS.length - 1; i++) {
    const s1 = COLOR_STOPS[i];
    const s2 = COLOR_STOPS[i + 1];
    if (tempC >= s1.temp && tempC <= s2.temp) {
      const factor = (tempC - s1.temp) / (s2.temp - s1.temp);
      const r = Math.round(s1.r + factor * (s2.r - s1.r));
      const g = Math.round(s1.g + factor * (s2.g - s1.g));
      const b = Math.round(s1.b + factor * (s2.b - s1.b));
      return `rgb(${r}, ${g}, ${b})`;
    }
  }
  return COLOR_STOPS[2].hex;
}
