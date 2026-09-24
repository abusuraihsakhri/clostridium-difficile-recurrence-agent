import assert from "node:assert/strict";
import { evaluateCDI } from "../web/cdiff.mjs";

const wbcBoundary = evaluateCDI({ age: 55, wbcCount: 15, serumCreatinine: 1.1 });
assert.equal(wbcBoundary.severity.grade, "NON_SEVERE");

const creatinineBoundary = evaluateCDI({ age: 55, wbcCount: 10, serumCreatinine: 1.5 });
assert.equal(creatinineBoundary.severity.grade, "SEVERE");

const lactateOnly = evaluateCDI({ age: 55, wbcCount: 10, serumCreatinine: 1.0, lactate: 5.2 });
assert.equal(lactateOnly.severity.grade, "NON_SEVERE");
assert.match(lactateOnly.severity.summary, /not an IDSA\/SHEA fulminant criterion/);

const fulminant = evaluateCDI({ age: 70, wbcCount: 10, serumCreatinine: 1.0, hypotensionOrShock: true });
assert.equal(fulminant.severity.grade, "FULMINANT");

const lowRisk = evaluateCDI({ age: 32, wbcCount: 8, serumCreatinine: 0.8 });
assert.equal(lowRisk.risk.score, 0);
assert.equal(lowRisk.risk.category, "LOW");
assert.match(lowRisk.risk.modelNotice, /not a validated or calibrated/);

const recurrent = evaluateCDI({ age: 71, wbcCount: 12, serumCreatinine: 1.2, priorEpisodes: 2 });
assert.equal(recurrent.treatment.fmtCandidate, true);

const chf = evaluateCDI({ age: 74, wbcCount: 12, serumCreatinine: 1.0, heartFailureHistory: true });
assert.equal(chf.treatment.considerBezlotoxumab, true);
assert.match(chf.treatment.bezlotoxumabWarning, /benefit outweighs risk/);

assert.throws(
  () => evaluateCDI({ age: 17, wbcCount: 10, serumCreatinine: 1.0 }),
  /adult guidance/
);

console.log("browser engine smoke tests passed");
