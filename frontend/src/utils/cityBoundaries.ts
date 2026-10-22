/**
 * City boundaries and administrative polygon coordinates for HeatSense pilot domain.
 * Supports interactive hovering, outlines, and city-focused heatmaps.
 */

export interface CityData {
  id: string;
  name: string;
  state: string;
  latitude: number;
  longitude: number;
  cameraHeight: number;
  bbox: [number, number, number, number]; // [minLat, minLon, maxLat, maxLon]
  polygonCoordinates: [number, number][]; // Array of [lon, lat] points tracing boundary
  description: string;
}

export const CITIES_DATA: CityData[] = [
  {
    id: 'city_mumbai',
    name: 'Mumbai',
    state: 'Maharashtra',
    latitude: 19.0760,
    longitude: 72.8777,
    cameraHeight: 45000,
    bbox: [18.88, 72.75, 19.30, 72.98],
    description: 'Mumbai Metropolitan Region — Coastal Urban Heat Island',
    polygonCoordinates: [
      // Detailed boundary polygon tracing Mumbai peninsula & suburban coast
      [72.815, 18.895], // Colaba Point
      [72.835, 18.922], // Gateway of India / Fort
      [72.855, 18.960], // Docklands / Sewri
      [72.905, 18.995], // Mahul / Trombay
      [72.935, 19.015], // Trombay Hill
      [72.925, 19.060], // Chembur / Deonar
      [72.945, 19.100], // Vikhroli Mangroves
      [72.960, 19.150], // Bhandup
      [72.965, 19.190], // Mulund East / Thane creek
      [72.930, 19.200], // Sanjay Gandhi National Park East
      [72.890, 19.240], // Borivali East Hills
      [72.850, 19.260], // Dahisar
      [72.805, 19.245], // Gorai Creek
      [72.780, 19.190], // Manori
      [72.795, 19.140], // Madh Island
      [72.810, 19.110], // Juhu Beach
      [72.815, 19.055], // Bandra Bandstand
      [72.810, 19.015], // Worli Sea Face
      [72.795, 18.960], // Malabar Hill / Chowpatty
      [72.815, 18.895], // Close loop
    ],
  },
  {
    id: 'city_pune',
    name: 'Pune',
    state: 'Maharashtra',
    latitude: 18.5204,
    longitude: 73.8567,
    cameraHeight: 50000,
    bbox: [18.42, 73.72, 18.66, 74.00],
    description: 'Pune Metropolitan Area — Deccan Plateau Heat Corridor',
    polygonCoordinates: [
      // Polygon encompassing PMC & PCMC (Pimpri-Chinchwad, Hinjewadi, Hadapsar, Katraj)
      [73.710, 18.590], // Hinjewadi Phase 3
      [73.740, 18.650], // Ravet / Nigdi
      [73.790, 18.660], // Chinchwad / Moshi
      [73.850, 18.640], // Bhosari
      [73.910, 18.620], // Dighi / Charholi
      [73.950, 18.580], // Viman Nagar / Lohegaon
      [73.970, 18.540], // Kharadi / Wagholi
      [73.960, 18.495], // Hadapsar / Magarpatta
      [73.920, 18.450], // Kondhwa / Undri
      [73.860, 18.430], // Katraj Ghat
      [73.805, 18.470], // Warje / Sinhagad Road
      [73.760, 18.505], // Kothrud / Chandani Chowk
      [73.740, 18.550], // Baner / Pashan
      [73.710, 18.590], // Close loop
    ],
  },
  {
    id: 'city_thane',
    name: 'Thane',
    state: 'Maharashtra',
    latitude: 19.2183,
    longitude: 72.9781,
    cameraHeight: 35000,
    bbox: [19.12, 72.92, 19.32, 73.08],
    description: 'Thane Municipal Corporation — Creek & Inland Urban Core',
    polygonCoordinates: [
      [72.940, 19.290], // Gaimukh / Ghodbunder
      [72.975, 19.270], // Kasarvadavali
      [73.010, 19.240], // Majiwada / Balkum
      [73.025, 19.210], // Kalwa / Kharegaon
      [73.035, 19.170], // Mumbra / Retibunder
      [73.000, 19.160], // Diva
      [72.970, 19.175], // Kopri / Mulund boundary
      [72.945, 19.200], // Naupada / Pachpakhadi
      [72.925, 19.225], // Upvan Lake / Wagle Estate
      [72.940, 19.290], // Close loop
    ],
  },
  {
    id: 'city_nashik',
    name: 'Nashik',
    state: 'Maharashtra',
    latitude: 19.9975,
    longitude: 73.7898,
    cameraHeight: 45000,
    bbox: [19.90, 73.70, 20.08, 73.88],
    description: 'Nashik Valley — Northern Maharashtra Plateau',
    polygonCoordinates: [
      [73.740, 20.040], // Gangapur Dam road
      [73.780, 20.060], // Panchavati North / Mhasrul
      [73.840, 20.030], // Adgaon / Mumbai-Agra highway
      [73.860, 19.980], // Nashik Road / Dasak
      [73.840, 19.930], // Deolali Camp
      [73.780, 19.920], // Pathfinder / Ambad South
      [73.725, 19.945], // Ambad MIDC
      [73.715, 19.990], // Satpur Industrial Area
      [73.740, 20.040], // Close loop
    ],
  },
];

export function findCityById(id: string): CityData | undefined {
  return CITIES_DATA.find((c) => c.id === id);
}

export function isCoordInBBox(lat: number, lon: number, bbox: [number, number, number, number]): boolean {
  const [minLat, minLon, maxLat, maxLon] = bbox;
  return lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon;
}

export function getNearestCity(lat: number, lon: number): CityData | null {
  for (const city of CITIES_DATA) {
    if (isCoordInBBox(lat, lon, city.bbox)) {
      return city;
    }
  }
  return null;
}
