import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BPMN_VIEWER_CDN =
  'https://unpkg.com/bpmn-js@17.11.1/dist/bpmn-viewer.development.js';

async function renderSvg(page, xml) {
  await page.setContent(
    '<!doctype html><html><head><meta charset="utf-8"><style>html,body,#canvas{margin:0;padding:0;width:100%;height:100%;background:#fff;overflow:hidden;} .djs-container,.diagram-container,.viewport{background:#fff !important;}</style></head><body><div id="canvas"></div></body></html>',
    { waitUntil: 'load' }
  );

  await page.addScriptTag({ url: BPMN_VIEWER_CDN });
  const result = await page.evaluate(async (diagramXml) => {
    const viewer = new window.BpmnJS({ container: '#canvas' });
    await viewer.importXML(diagramXml);
    viewer.get('canvas').zoom('fit-viewport', 'auto');
    const { svg } = await viewer.saveSVG();
    return svg;
  }, xml);

  return result;
}

async function svgToPng(page, svg, outputPath) {
  await page.setViewportSize({ width: 4000, height: 2200 });
  await page.setContent(
    `<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;background:#fff;} #wrap{display:inline-block;padding:24px;background:#fff;}</style></head><body><div id="wrap">${svg}</div></body></html>`,
    { waitUntil: 'load' }
  );

  const wrap = await page.locator('#wrap');
  await wrap.screenshot({ path: outputPath, omitBackground: false });
}

async function main() {
  const files = (await fs.readdir(__dirname))
    .filter((name) => name.toLowerCase().endsWith('.bpmn'))
    .sort();

  if (files.length === 0) {
    console.log('No BPMN files found.');
    return;
  }

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 3600, height: 2000 } });

  try {
    for (const name of files) {
      const fullPath = path.join(__dirname, name);
      const xml = await fs.readFile(fullPath, 'utf8');
      const svg = await renderSvg(page, xml);

      const baseName = name.replace(/\.bpmn$/i, '');
      const svgPath = path.join(__dirname, `${baseName}.svg`);
      const pngPath = path.join(__dirname, `${baseName}.png`);

      await fs.writeFile(svgPath, svg, 'utf8');
      await svgToPng(page, svg, pngPath);

      console.log(`Exported ${name} -> ${path.basename(svgPath)}, ${path.basename(pngPath)}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
