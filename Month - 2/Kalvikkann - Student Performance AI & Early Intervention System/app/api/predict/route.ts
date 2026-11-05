import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // 1. Try connecting to the running Flask ML API on port 5000
    const flaskUrl = process.env.FLASK_API_URL || 'http://127.0.0.1:5000';
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1200);

      const flaskRes = await fetch(`${flaskUrl}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (flaskRes.ok) {
        const mlData = await flaskRes.json();
        return NextResponse.json({
          ...mlData,
          source: 'Flask ML API (Port 5000)',
        });
      }
    } catch {
      // Flask server not actively responding, fall through to Python child process or local ML engine
    }

    // 2. Direct Python process bridge to trained model_early.pkl
    const rootDir = process.cwd();
    const appPyPath = path.join(rootDir, 'app.py');
    const modelPath = path.join(rootDir, 'model_early.pkl');
    const metaPath = path.join(rootDir, 'meta_early.json');

    if (fs.existsSync(appPyPath) && fs.existsSync(modelPath) && fs.existsSync(metaPath)) {
      try {
        const pythonResult = await new Promise<any>((resolve, reject) => {
          const inputJson = JSON.stringify(body);
          const pyScript = `
import json, sys
import app

data = json.loads(sys.stdin.read())
with app.app.test_request_context(method='POST', path='/predict', json=data):
    res = app.predict()
    print(res.get_data(as_text=True))
`;
          const pyProc = spawn('python', ['-c', pyScript], { cwd: rootDir });
          let stdout = '';
          let stderr = '';

          pyProc.stdout.on('data', (d) => { stdout += d.toString(); });
          pyProc.stderr.on('data', (d) => { stderr += d.toString(); });

          pyProc.on('close', (code) => {
            if (code === 0) {
              try {
                // Find JSON output in stdout
                const lines = stdout.trim().split('\n');
                const lastLine = lines[lines.length - 1];
                resolve(JSON.parse(lastLine));
              } catch (e) {
                reject(new Error(`Failed to parse Python output: ${stdout}`));
              }
            } else {
              reject(new Error(`Python process exited with code ${code}: ${stderr}`));
            }
          });

          pyProc.stdin.write(inputJson);
          pyProc.stdin.end();
        });

        return NextResponse.json({
          ...pythonResult,
          source: 'Direct Scikit-Learn Model (Embedded Python)',
        });
      } catch (err: any) {
        console.warn('Python spawn bridge failed, using fallback formula:', err.message);
      }
    }

    // 3. Mathematical fallback if Python is unavailable
    const att = Number(body.attendance_percentage ?? body.attendance ?? 80);
    const prev = Number(body.previous_semester_percentage ?? body.previousScore ?? 75);
    const internal = Number(body.internal_exam_1 ?? body.assessmentScore ?? 72);
    const score = Math.round(prev * 0.45 + internal * 0.35 + att * 0.20);
    const pred = score >= 75 ? 'High' : score >= 55 ? 'Average' : 'Low';
    const risk = pred === 'High' ? 'LOW' : pred === 'Average' ? 'MEDIUM' : 'HIGH';

    return NextResponse.json({
      prediction: pred,
      riskLevel: risk,
      confidence: 0.85,
      probabilities: {
        High: pred === 'High' ? 0.75 : 0.15,
        Average: pred === 'Average' ? 0.70 : 0.20,
        Low: pred === 'Low' ? 0.75 : 0.10,
      },
      modelUsed: 'Kalvikkan Ensemble Formula (Fallback)',
      source: 'Fallback Engine',
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message || 'Prediction failed' }, { status: 500 });
  }
}

export async function GET() {
  const rootDir = process.cwd();
  const metaPath = path.join(rootDir, 'meta_early.json');
  let meta: any = null;
  if (fs.existsSync(metaPath)) {
    try {
      meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
    } catch {}
  }

  return NextResponse.json({
    status: 'ok',
    meta: meta,
    endpoints: {
      predict: 'POST /api/predict',
      schema: 'GET /api/predict',
      flaskUrl: 'http://127.0.0.1:5000/predict',
    },
  });
}
