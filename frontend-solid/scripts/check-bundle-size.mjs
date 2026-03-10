import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { gzipSync } from "node:zlib";

const distAssetsDir = path.resolve("dist/assets");
const initialBudgetKb = 200;

const toKb = (bytes) => Math.round((bytes / 1024) * 10) / 10;

try {
  const files = await readdir(distAssetsDir, { withFileTypes: true });
  const jsFiles = files
    .filter((entry) => entry.isFile() && entry.name.endsWith(".js"))
    .map((entry) => entry.name);

  if (jsFiles.length === 0) {
    console.error("No JS bundle found in dist/assets. Run npm run build first.");
    process.exit(1);
  }

  const bundles = await Promise.all(
    jsFiles.map(async (fileName) => {
      const fullPath = path.join(distAssetsDir, fileName);
      const buffer = await readFile(fullPath);
      const gzipBytes = gzipSync(buffer).length;
      return { fileName, gzipBytes };
    }),
  );

  const initialBundle = bundles.sort((a, b) => b.gzipBytes - a.gzipBytes)[0];
  const budgetBytes = initialBudgetKb * 1024;

  console.log(`Largest initial candidate: ${initialBundle.fileName} (${toKb(initialBundle.gzipBytes)} KB gzip)`);
  console.log(`Budget: ${initialBudgetKb} KB gzip`);

  if (initialBundle.gzipBytes > budgetBytes) {
    console.error("Bundle budget exceeded.");
    process.exit(1);
  }

  console.log("Bundle budget check passed.");
} catch (error) {
  console.error("Unable to evaluate bundle size.", error);
  process.exit(1);
}
