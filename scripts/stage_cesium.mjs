import { cpSync, mkdirSync } from 'node:fs';

const source = new URL('../node_modules/cesium/Build/Cesium/', import.meta.url);
const target = new URL('../apps/web/public/cesium/', import.meta.url);
mkdirSync(target, { recursive: true });
for (const directory of ['Assets', 'ThirdParty', 'Widgets', 'Workers']) {
  cpSync(new URL(directory, source), new URL(directory, target), { recursive: true });
}
