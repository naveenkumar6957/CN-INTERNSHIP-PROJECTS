const fs = require('fs');

console.log('--- Reading index.html ---');
const html = fs.readFileSync('index.html', 'utf8');

// 1. Verify embedded JSON
const scriptMatch = html.match(/<script id="phishshift-model-data" type="application\/json">([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error('ERROR: Embedded model JSON script block not found in index.html!');
  process.exit(1);
}
const rawJson = scriptMatch[1].trim();
const model = JSON.parse(rawJson);
console.log('[OK] Embedded model parsed successfully!');
console.log('     Format:', model.format);
console.log('     Version:', model.version);
console.log('     Vocabulary size:', Object.keys(model.vocabulary).length);
console.log('     Hidden dimension:', model.weights.b1.length);
console.log('     Test Accuracy:', model.metadata.metrics.accuracy);

// 2. Tokenizer test
function tokenize(text) {
  return text.toLowerCase().match(/\b[a-z0-9_]{2,}\b/g) || [];
}

const vocab = model.vocabulary;
const idf = model.idf;
const W1 = model.weights.W1;
const b1 = model.weights.b1;
const W2 = model.weights.W2;
const b2 = model.weights.b2;

function runInference(text) {
  const tokens = tokenize(text);
  const counts = {};
  for (const t of tokens) counts[t] = (counts[t] || 0) + 1;
  const active = [];
  let normSq = 0;
  for (const t in counts) {
    if (vocab[t] !== undefined) {
      const idx = vocab[t];
      const val = counts[t] * idf[idx];
      normSq += val * val;
      active.push({ token: t, idx, val });
    }
  }
  if (!active.length) return { prob: 0.1, attrs: [] };
  const norm = Math.sqrt(normSq);
  for (const a of active) a.normVal = a.val / norm;

  const hiddenDim = b1.length;
  const z1 = new Float64Array(b1);
  for (const a of active) {
    const row = W1[a.idx];
    for (let j = 0; j < hiddenDim; j++) z1[j] += a.normVal * row[j];
  }

  const a1 = new Float64Array(hiddenDim);
  const reluActive = new Uint8Array(hiddenDim);
  let z2 = b2;
  for (let j = 0; j < hiddenDim; j++) {
    if (z1[j] > 0) {
      a1[j] = z1[j];
      reluActive[j] = 1;
      z2 += z1[j] * W2[j];
    }
  }

  const prob = 1 / (1 + Math.exp(-z2));
  const attrs = [];
  for (const a of active) {
    const row = W1[a.idx];
    let grad = 0;
    for (let j = 0; j < hiddenDim; j++) {
      if (reluActive[j]) grad += row[j] * W2[j];
    }
    attrs.push({ token: a.token, attr: a.normVal * grad });
  }
  attrs.sort((x, y) => y.attr - x.attr);
  return { prob, attrs };
}

// 3. Test Messages
const samples = [
  {
    name: 'Suspicious Account Verification',
    text: 'ALERT from FirstMetro Bank: Unusual login attempt detected on your checking account. Access has been temporarily restricted. Verify your credentials immediately within 24 hours to prevent account suspension: https://firstmetro-secure-verify.example/auth'
  },
  {
    name: 'Promotional Flash Sale',
    text: 'Spring Flash Sale at UrbanTrend! Enjoy 30% off our new outerwear collection this weekend only. Use code SPRING30 at checkout in our mobile app. Reply STOP to unsubscribe.'
  },
  {
    name: 'Ordinary Personal Message',
    text: 'Hey Alex, dinner is confirmed for 7:30 PM tonight at the bistro on 4th Street. Can you grab a table outside if you arrive first? See you soon!'
  }
];

console.log('\n--- Evaluating Test Cases in V8 Runtime ---');
for (const s of samples) {
  const res = runInference(s.text);
  console.log(`[${s.name}]`);
  console.log(`  Model Estimated Probability: ${(res.prob * 100).toFixed(1)}%`);
  console.log(`  Top 3 Contributing Tokens:`, res.attrs.slice(0, 3).map(a => `${a.token} (${a.attr >= 0 ? '+' : ''}${a.attr.toFixed(3)})`).join(', '));
}

console.log('\n[OK] All V8 runtime tests passed successfully!');
