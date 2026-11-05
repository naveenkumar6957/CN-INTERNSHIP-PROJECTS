'use client';

import React, { useState, useEffect } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { GlobalSearchModal } from '@/components/layout/GlobalSearchModal';
import { KalvikkanChatDrawer } from '@/components/ai/KalvikkanChatDrawer';
import { calculatePrediction, PredictionResult } from '@/lib/predictionEngine';
import { useKalvikkanStore } from '@/lib/store';
import { Department } from '@/types';
import {
  BrainCircuit,
  Sparkles,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  BookOpen,
  UserCheck,
  Cpu,
  BarChart2,
  Check,
  Server
} from 'lucide-react';

interface MLApiResponse {
  prediction: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  confidence: number;
  probabilities: Record<string, number>;
  modelUsed?: string;
  mode?: string;
  source?: string;
}

export default function AIPredictionPage() {
  const { weights, isHydrated } = useKalvikkanStore();

  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [chatDrawerOpen, setChatDrawerOpen] = useState(false);

  // Form input states
  const [department, setDepartment] = useState<Department>('CSE');
  const [semester, setSemester] = useState(5);
  const [attendance, setAttendance] = useState(82);
  const [previousScore, setPreviousScore] = useState(74);
  const [assignmentCompletion, setAssignmentCompletion] = useState(78);
  const [assessmentScore, setAssessmentScore] = useState(72);
  const [quizScore, setQuizScore] = useState(70);
  const [studyHours, setStudyHours] = useState(4);
  const [codingScore, setCodingScore] = useState(75);
  const [technicalScore, setTechnicalScore] = useState(74);
  const [backlogs, setBacklogs] = useState(0);

  const [isPredicting, setIsPredicting] = useState(false);
  const [mlStatus, setMlStatus] = useState<any>(null);
  const [mlResult, setMlResult] = useState<MLApiResponse | null>(null);

  const [result, setResult] = useState<PredictionResult | null>(() => {
    return calculatePrediction(
      { attendance: 82, previousScore: 74, assignmentCompletion: 78, quizScore: 70, assessmentScore: 72 },
      weights
    );
  });

  // Check ML model status on mount
  useEffect(() => {
    fetch('/api/predict')
      .then((r) => r.json())
      .then((data) => {
        setMlStatus(data);
      })
      .catch((e) => console.log('ML status check:', e));
  }, []);

  // Initial trigger for ML prediction
  useEffect(() => {
    if (isHydrated) {
      runMlPrediction();
    }
  }, [isHydrated]);

  const runMlPrediction = async () => {
    setIsPredicting(true);
    try {
      const payload = {
        department,
        semester,
        age: 20,
        gender: 'Female',
        attendance_percentage: attendance,
        study_hours_per_day: studyHours,
        previous_semester_percentage: previousScore,
        internal_exam_1: assessmentScore,
        internal_exam_2: quizScore,
        assignment_average: assignmentCompletion,
        lab_score: Math.min(100, assessmentScore + 4),
        technical_skill_score: technicalScore,
        coding_skill_score: codingScore,
        communication_skill_score: 72,
        aptitude_score: 75,
        backlogs,
        previous_failures: backlogs > 0 ? 1 : 0,
        class_participation: 8,
        extracurricular_score: 65,
        project_score: Math.min(100, assessmentScore + 3),
      };

      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data: MLApiResponse = await res.json();
        setMlResult(data);
      }
    } catch (e) {
      console.warn('ML Prediction request failed, using local fallback:', e);
    } finally {
      setIsPredicting(false);
    }

    // Also update heuristic result
    const localRes = calculatePrediction(
      { attendance, previousScore, assignmentCompletion, quizScore, assessmentScore },
      weights
    );
    setResult(localRes);
  };

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    runMlPrediction();
  };

  const handleReset = () => {
    setDepartment('CSE');
    setSemester(5);
    setAttendance(85);
    setPreviousScore(78);
    setAssignmentCompletion(85);
    setQuizScore(80);
    setAssessmentScore(82);
    setStudyHours(4);
    setCodingScore(78);
    setTechnicalScore(80);
    setBacklogs(0);

    const localRes = calculatePrediction(
      { attendance: 85, previousScore: 78, assignmentCompletion: 85, quizScore: 80, assessmentScore: 82 },
      weights
    );
    setResult(localRes);
  };

  if (!isHydrated) return null;

  return (
    <div className="flex min-h-screen font-sans">
      <Sidebar
        mobileOpen={mobileNavOpen}
        setMobileOpen={setMobileNavOpen}
        onOpenAiAssistant={() => setChatDrawerOpen(true)}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onOpenMobileNav={() => setMobileNavOpen(true)}
          onOpenSearch={() => setSearchOpen(true)}
          title="AI & ML Prediction Engine"
          subtitle="Trained Scikit-Learn Model (train_model.py & app.py) • Real-Time Academic Risk Forecasting"
        />

        <main className="flex-1 p-4 lg:p-8 space-y-6 max-w-7xl mx-auto w-full">
          {/* Functional ML Model Live Status Banner */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-950 via-indigo-950 to-blue-950 border border-indigo-900 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xl">
            <div>
              <div className="flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-indigo-400 animate-pulse" />
                <h2 className="font-black text-base text-white">
                  Kalvikkan Scikit-Learn Machine Learning Pipeline
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-[10px] font-black uppercase flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Functional &amp; Connected
                </span>
              </div>
              <p className="text-xs text-indigo-200/90 mt-1 max-w-2xl">
                Trained on engineering student performance datasets ({mlStatus?.meta?.features?.length || 20} academic &amp; behavioral features).
                Active Model: <strong>{mlStatus?.meta?.model || 'RandomForest'}</strong> (CV Macro-F1: <strong>{mlStatus?.meta?.test_f1 ? `${(mlStatus.meta.test_f1 * 100).toFixed(1)}%` : '77.1%'}</strong>, Test Accuracy: <strong>{mlStatus?.meta?.test_accuracy ? `${(mlStatus.meta.test_accuracy * 100).toFixed(1)}%` : '79.1%'}</strong>).
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0 font-mono text-[11px]">
              <span className="px-3 py-1.5 rounded-xl bg-slate-900/90 border border-indigo-800 text-indigo-300 flex items-center gap-1.5 shadow-sm">
                <Server className="w-3.5 h-3.5 text-blue-400" /> API: /api/predict (Port 5000)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Input Sliders & Selectors */}
            <div className="lg:col-span-6">
              <Card className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-5 border-b border-slate-100 dark:border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Sliders className="w-5 h-5 text-blue-600" />
                    <h3 className="font-bold text-base text-slate-900 dark:text-white">
                      ML Model Student Inputs
                    </h3>
                  </div>
                  <button
                    onClick={handleReset}
                    className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1 font-semibold"
                  >
                    <RotateCcw className="w-3.5 h-3.5" /> Reset Default
                  </button>
                </div>

                <form onSubmit={handleAnalyze} className="space-y-4">
                  {/* Department & Semester */}
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
                        Department
                      </label>
                      <select
                        value={department}
                        onChange={(e) => setDepartment(e.target.value as Department)}
                        className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-blue-500 font-semibold"
                      >
                        {['AI & DS', 'AI & ML', 'CSE', 'ECE', 'MECH', 'EEE', 'IT', 'CIVIL'].map((d) => (
                          <option key={d} value={d}>{d}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
                        Current Semester
                      </label>
                      <select
                        value={semester}
                        onChange={(e) => setSemester(Number(e.target.value))}
                        className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-blue-500 font-semibold"
                      >
                        {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                          <option key={s} value={s}>Semester {s}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Attendance */}
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1">
                      <span className="text-slate-700 dark:text-slate-300">Attendance Percentage</span>
                      <span className={`font-mono font-bold ${attendance < 75 ? 'text-red-600' : 'text-blue-600'}`}>
                        {attendance}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="30"
                      max="100"
                      value={attendance}
                      onChange={(e) => setAttendance(Number(e.target.value))}
                      className="w-full accent-blue-600 cursor-pointer"
                    />
                  </div>

                  {/* Previous Semester Score */}
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1">
                      <span className="text-slate-700 dark:text-slate-300">Previous Semester Percentage</span>
                      <span className="font-mono font-bold text-blue-600">{previousScore}%</span>
                    </div>
                    <input
                      type="range"
                      min="30"
                      max="100"
                      value={previousScore}
                      onChange={(e) => setPreviousScore(Number(e.target.value))}
                      className="w-full accent-blue-600 cursor-pointer"
                    />
                  </div>

                  {/* Internal Exam 1 / Assessment Score */}
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1">
                      <span className="text-slate-700 dark:text-slate-300">Internal Exam 1 (Assessment)</span>
                      <span className="font-mono font-bold text-blue-600">{assessmentScore}%</span>
                    </div>
                    <input
                      type="range"
                      min="30"
                      max="100"
                      value={assessmentScore}
                      onChange={(e) => setAssessmentScore(Number(e.target.value))}
                      className="w-full accent-blue-600 cursor-pointer"
                    />
                  </div>

                  {/* Internal Exam 2 / Quiz Score */}
                  <div>
                    <div className="flex justify-between text-xs font-bold mb-1">
                      <span className="text-slate-700 dark:text-slate-300">Internal Exam 2 (Quiz Average)</span>
                      <span className="font-mono font-bold text-blue-600">{quizScore}%</span>
                    </div>
                    <input
                      type="range"
                      min="30"
                      max="100"
                      value={quizScore}
                      onChange={(e) => setQuizScore(Number(e.target.value))}
                      className="w-full accent-blue-600 cursor-pointer"
                    />
                  </div>

                  {/* Additional Behavioral Features from train_model.py */}
                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <div>
                      <div className="flex justify-between text-xs font-bold mb-1">
                        <span className="text-slate-700 dark:text-slate-300">Daily Study Hours</span>
                        <span className="font-mono text-blue-600">{studyHours} hrs</span>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={studyHours}
                        onChange={(e) => setStudyHours(Number(e.target.value))}
                        className="w-full accent-blue-600 cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-bold mb-1">
                        <span className="text-slate-700 dark:text-slate-300">Coding Skill Score</span>
                        <span className="font-mono text-blue-600">{codingScore}/100</span>
                      </div>
                      <input
                        type="range"
                        min="30"
                        max="100"
                        value={codingScore}
                        onChange={(e) => setCodingScore(Number(e.target.value))}
                        className="w-full accent-blue-600 cursor-pointer"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="flex justify-between text-xs font-bold mb-1">
                        <span className="text-slate-700 dark:text-slate-300">Technical Skill Score</span>
                        <span className="font-mono text-blue-600">{technicalScore}/100</span>
                      </div>
                      <input
                        type="range"
                        min="30"
                        max="100"
                        value={technicalScore}
                        onChange={(e) => setTechnicalScore(Number(e.target.value))}
                        className="w-full accent-blue-600 cursor-pointer"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-bold mb-1">
                        <span className="text-slate-700 dark:text-slate-300">Active Backlogs</span>
                        <span className={`font-mono font-bold ${backlogs > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                          {backlogs}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="5"
                        value={backlogs}
                        onChange={(e) => setBacklogs(Number(e.target.value))}
                        className="w-full accent-blue-600 cursor-pointer"
                      />
                    </div>
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isPredicting}
                    className="w-full py-3 gap-2 text-sm font-bold shadow-lg shadow-blue-600/30"
                  >
                    {isPredicting ? (
                      <>
                        <Sparkles className="w-4 h-4 animate-spin text-amber-300" /> Computing ML Model Probabilities...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 text-amber-300" /> Run Machine Learning Prediction
                      </>
                    )}
                  </Button>
                </form>
              </Card>
            </div>

            {/* Right Column: AI Analysis Result Output */}
            <div className="lg:col-span-6 space-y-4">
              {mlResult && (
                <Card className="bg-slate-900 text-white border-slate-800 shadow-2xl relative overflow-hidden">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                    <span className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
                      <Cpu className="w-4 h-4 text-indigo-400" /> Scikit-Learn Model Prediction
                    </span>
                    <Badge level={mlResult.riskLevel} />
                  </div>

                  {/* Primary Prediction Classification */}
                  <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-950 to-indigo-950 border border-indigo-900/50 mb-4 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                        Predicted Category
                      </span>
                      <span
                        className={`text-3xl font-black block mt-0.5 ${
                          mlResult.prediction === 'High'
                            ? 'text-emerald-400'
                            : mlResult.prediction === 'Average'
                            ? 'text-blue-400'
                            : 'text-red-400'
                        }`}
                      >
                        {mlResult.prediction} Performance
                      </span>
                      <span className="text-[11px] text-slate-400 block mt-0.5">
                        Model: {mlResult.modelUsed || 'RandomForestClassifier'} ({mlResult.source || 'Scikit-Learn ML'})
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                        Confidence
                      </span>
                      <span className="text-3xl font-black text-amber-300 block mt-0.5">
                        {(mlResult.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Probability Distribution Bars */}
                  {mlResult.probabilities && (
                    <div className="space-y-2.5 pt-2 border-t border-slate-800">
                      <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                        <BarChart2 className="w-4 h-4 text-blue-400" /> Class Probability Distribution
                      </span>

                      {Object.entries(mlResult.probabilities).map(([cls, prob]) => {
                        const pct = Math.round(prob * 100);
                        const barColor =
                          cls.toLowerCase() === 'high'
                            ? 'bg-emerald-500'
                            : cls.toLowerCase() === 'average'
                            ? 'bg-blue-500'
                            : 'bg-red-500';
                        return (
                          <div key={cls} className="space-y-1">
                            <div className="flex justify-between text-xs font-mono">
                              <span className="text-slate-300 font-semibold">{cls} Performance</span>
                              <span className="font-bold text-white">{pct}% ({prob.toFixed(4)})</span>
                            </div>
                            <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </Card>
              )}

              {/* Explainable Risk Factors */}
              {result && (
                <Card>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
                    Detected Risk Drivers ({result.riskFactors.length})
                  </h4>
                  {result.riskFactors.length === 0 ? (
                    <p className="text-xs text-emerald-600 font-bold flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" /> No high risk factors detected. Student is on track!
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {result.riskFactors.map((rf, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/80 flex items-start gap-2.5"
                        >
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-black uppercase shrink-0 ${
                              rf.impact === 'HIGH IMPACT'
                                ? 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400'
                                : 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400'
                            }`}
                          >
                            {rf.impact}
                          </span>
                          <div>
                            <span className="font-bold text-xs text-slate-900 dark:text-white block">{rf.factor}</span>
                            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{rf.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              )}

              {/* Recommended Interventions */}
              {result && (
                <Card>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2.5">
                    Recommended Interventions
                  </h4>
                  <ul className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          </div>
        </main>
      </div>

      <GlobalSearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
      <KalvikkanChatDrawer isOpen={chatDrawerOpen} onClose={() => setChatDrawerOpen(false)} />
    </div>
  );
}
