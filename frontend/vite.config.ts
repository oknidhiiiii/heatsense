import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cesium from 'vite-plugin-cesium';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), cesium()],
  server: {
    port: 5173,
    host: true,
    allowedHosts: [
      '8da0-2401-4900-8924-3d26-cdea-ccc8-bffb-71a9.ngrok-free.app',
      '.ngrok-free.app',
    ],
  },
});
