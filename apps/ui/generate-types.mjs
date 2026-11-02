// Generate src/api/types.ts from openapi.json using openapi-typescript v6.
// The v6 API returns the generated string; we write it to disk ourselves.
import defaultGenerate from "openapi-typescript";
import fs from "node:fs";
import path from "node:path";

const outPath = path.join(process.cwd(), "src", "api", "types.ts");
const generated = await defaultGenerate(path.join(process.cwd(), "openapi.json"));
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, generated);
console.log("types.ts written to", outPath, `(${generated.length} chars)`);
