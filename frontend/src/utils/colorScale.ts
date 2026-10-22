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

// Vibrant multi-stop thermal palette (Cool Cyan -> Emerald -> Lime -> Yellow -> Orange -> Red -> Magenta)
export const COLOR_STOPS: ColorStop[] = [
  { temp: 18.0, hex: '#06b6d4', r: 6, g: 182, b: 212 },   // Cool Cyan
  { temp: 22.0, hex: '#10b981', r: 16, g: 185, b: 129 },  // Emerald Green
  { temp: 26.0, hex: '#84cc16', r: 132, g: 204, b: 22 },  // Lime
  { temp: 29.0, hex: '#eab308', r: 234, g: 179, b: 8 },   // Amber / Yellow
  { temp: 33.0, hex: '#f97316', r: 249, g: 115, b: 22 },  // Warm Orange
  { temp: 37.0, hex: '#ef4444', r: 239, g: 68, b: 68 },   // Crimson Red
  { temp: 42.0, hex: '#ec4899', r: 236, g: 72, b: 153 },  // Hot Magenta
];

export function getTemperatureHex(
  tempC: number,
  minTemp?: number,
  maxTemp?: number
): string {
  // If min and max are provided and have meaningful variance (> 0.5°C), use dynamic relative normalization
  if (minTemp !== undefined && maxTemp !== undefined && maxTemp - minTemp >= 0.5) {
    const clamped = Math.max(minTemp, Math.min(maxTemp, tempC));
    const factor = (clamped - minTemp) / (maxTemp - minTemp); // 0.0 to 1.0

    // Thermal gradient stops (0.0: Green -> 0.25: Lime -> 0.5: Yellow -> 0.75: Orange -> 1.0: Crimson Red)
    const stops = [
      { r: 16, g: 185, b: 129 },  // Emerald Green
      { r: 132, g: 204, b: 22 },  // Lime
      { r: 234, g: 179, b: 8 },   // Bright Yellow
      { r: 249, g: 115, b: 22 },  // Vibrant Orange
      { r: 239, g: 68, b: 68 },   // Deep Crimson Red
      { r: 217, g: 70, b: 239 },  // Magenta Peak
    ];

    const idx = factor * (stops.length - 1);
    const i = Math.min(Math.floor(idx), stops.length - 2);
    const localFactor = idx - i;

    const s1 = stops[i];
    const s2 = stops[i + 1];
    const r = Math.round(s1.r + localFactor * (s2.r - s1.r));
    const g = Math.round(s1.g + localFactor * (s2.g - s1.g));
    const b = Math.round(s1.b + localFactor * (s2.b - s1.b));
    return `rgb(${r}, ${g}, ${b})`;
  }

  // Fallback to absolute temperature mapping
  if (tempC <= COLOR_STOPS[0].temp) {
    return COLOR_STOPS[0].hex;
  }
  const last = COLOR_STOPS[COLOR_STOPS.length - 1];
  if (tempC >= last.temp) {
    return last.hex;
  }

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
  return COLOR_STOPS[3].hex;
}

export function getTemperatureRgb(
  tempC: number,
  minTemp?: number,
  maxTemp?: number
): [number, number, number] {
  if (minTemp !== undefined && maxTemp !== undefined && maxTemp - minTemp >= 0.5) {
    const clamped = Math.max(minTemp, Math.min(maxTemp, tempC));
    const factor = (clamped - minTemp) / (maxTemp - minTemp);

    const stops = [
      { r: 6, g: 182, b: 212 },   // Cool Cyan (#06b6d4)
      { r: 16, g: 185, b: 129 },  // Emerald Green (#10b981)
      { r: 234, g: 179, b: 8 },   // Bright Amber (#eab308)
      { r: 249, g: 115, b: 22 },  // Vibrant Orange (#f97316)
      { r: 239, g: 68, b: 68 },   // Deep Crimson Red (#ef4444)
      { r: 217, g: 70, b: 239 },  // Magenta Peak (#d946ef)
    ];

    const idx = factor * (stops.length - 1);
    const i = Math.min(Math.floor(idx), stops.length - 2);
    const localFactor = idx - i;

    const s1 = stops[i];
    const s2 = stops[i + 1];
    const r = Math.round(s1.r + localFactor * (s2.r - s1.r));
    const g = Math.round(s1.g + localFactor * (s2.g - s1.g));
    const b = Math.round(s1.b + localFactor * (s2.b - s1.b));
    return [r, g, b];
  }

  // Fallback to absolute temperature mapping
  if (tempC <= COLOR_STOPS[0].temp) {
    const s = COLOR_STOPS[0];
    return [s.r, s.g, s.b];
  }
  const last = COLOR_STOPS[COLOR_STOPS.length - 1];
  if (tempC >= last.temp) {
    return [last.r, last.g, last.b];
  }

  for (let i = 0; i < COLOR_STOPS.length - 1; i++) {
    const s1 = COLOR_STOPS[i];
    const s2 = COLOR_STOPS[i + 1];
    if (tempC >= s1.temp && tempC <= s2.temp) {
      const factor = (tempC - s1.temp) / (s2.temp - s1.temp);
      const r = Math.round(s1.r + factor * (s2.r - s1.r));
      const g = Math.round(s1.g + factor * (s2.g - s1.g));
      const b = Math.round(s1.b + factor * (s2.b - s1.b));
      return [r, g, b];
    }
  }
  return [234, 179, 8];
}
