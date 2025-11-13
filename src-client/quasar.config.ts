// Configuration for your app
// https://v2.quasar.dev/quasar-cli-vite/quasar-config-file

import { defineConfig } from '#q-app/wrappers';

export default defineConfig((/* ctx */) => {
  return {
    // ... (boot, css, extras, build... tudo como está) ...
    boot: ['axios', 'apexcharts'],

    css: ['app.scss'],

    extras: ['roboto-font', 'material-icons'],

    build: {
      target: {
        browser: ['es2022', 'firefox115', 'chrome115', 'safari14'],
        node: 'node20',
      },
      typescript: {
        strict: true,
        vueShim: true,
      },
      vueRouterMode: 'hash',
      vitePlugins: [
        [
          'vite-plugin-checker',
          {
            vueTsc: true,
            eslint: {
              lintCommand:
                'eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"',
              useFlatConfig: true,
            },
          },
          { server: false },
        ],
      ],
    },

    // Full list of options: https://v2.quasar.dev/quasar-cli-vite/quasar-config-file#devserver
    devServer: {
      // https: true,
      open: true, // opens browser window automatically

      // --- CORREÇÃO AQUI ---
      // Remova o bloco 'proxy' que adicionamos.
      // proxy: {
      //   '/api': {
      //     target: 'http://localhost:8000',
      //     changeOrigin: true,
      //   },
      // },
      // --- FIM DA CORREÇÃO ---
    },

    // https://v2.quasar.dev/quasar-cli-vite/quasar-config-file#framework
    framework: {
      config: {},
      plugins: ['Notify', 'Dialog'],
    },

    // ... (animations, ssr, pwa, cordova, capacitor, electron, bex... tudo como está) ...
    animations: [],

    ssr: {
      prodPort: 3000,
      middlewares: ['render'],
      pwa: false,
    },

    pwa: {
      workboxMode: 'GenerateSW',
    },

    capacitor: {
      hideSplashscreen: true,
    },

    electron: {
      preloadScripts: ['electron-preload'],
      inspectPort: 5858,
      bundler: 'packager',
      builder: {
        appId: 'trucar',
      },
    },

    bex: {
      extraScripts: [],
    },
  };
});