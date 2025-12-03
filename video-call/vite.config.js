import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: '0.0.0.0',
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'uncascaded-charleigh-insistent.ngrok-free.dev',
      'eluvial-partnerless-vickey.ngrok-free.dev', // new tunnel
    ],
    port: 5173,
  },
});