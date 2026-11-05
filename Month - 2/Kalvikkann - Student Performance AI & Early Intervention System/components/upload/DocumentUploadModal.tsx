'use client';

import React, { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Student, StudentDocument } from '@/types';
import { parseUploadedDocument, ExtractedExtractionResult } from '@/lib/documentExtractor';
import { useKalvikkanStore } from '@/lib/store';
import {
  Upload,
  FileText,
  Image as ImageIcon,
  CheckCircle2,
  Sparkles,
  FileSpreadsheet,
  AlertCircle,
  X,
  Layers,
  Award
} from 'lucide-react';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  student?: Student | null;
  isBatchFacultyMode?: boolean;
  onSuccessToast?: (msg: string) => void;
}

interface ParsedFileEntry {
  file: File;
  result: ExtractedExtractionResult;
}

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  student: propStudent,
  isBatchFacultyMode = false,
  onSuccessToast,
}) => {
  const { students, uploadMultipleStudentDocuments, batchUpdateStudents } = useKalvikkanStore();

  const [selectedStudentId, setSelectedStudentId] = useState<string>(
    propStudent?.id || (students.length > 0 ? students[0].id : '')
  );

  const [parsedEntries, setParsedEntries] = useState<ParsedFileEntry[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [manualText, setManualText] = useState('');

  if (!isOpen) return null;

  const currentStudent = propStudent || students.find((s) => s.id === selectedStudentId) || students[0];

  const handleFilesChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    setIsExtracting(true);
    const newEntries: ParsedFileEntry[] = [];

    try {
      for (const file of files) {
        const result = await parseUploadedDocument(file, undefined, currentStudent?.name);
        newEntries.push({ file, result });
      }
      setParsedEntries((prev) => [...prev, ...newEntries]);
    } catch (err) {
      console.error('Extraction error:', err);
    } finally {
      setIsExtracting(false);
      // Reset input value
      e.target.value = '';
    }
  };

  const handleRemoveEntry = (idx: number) => {
    setParsedEntries((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleManualTextExtract = async () => {
    if (!manualText.trim()) return;
    setIsExtracting(true);
    const mockFile = new File([manualText], 'manual_transcript.txt', { type: 'text/plain' });
    const result = await parseUploadedDocument(mockFile, manualText, currentStudent?.name);
    setParsedEntries((prev) => [...prev, { file: mockFile, result }]);
    setManualText('');
    setIsExtracting(false);
  };

  const handleSubmit = () => {
    if (!parsedEntries.length) return;

    if (isBatchFacultyMode) {
      // Check for CSV parsed rows
      const allRows: Partial<Student>[] = [];
      parsedEntries.forEach((entry) => {
        if (entry.result.parsedRows) {
          allRows.push(...entry.result.parsedRows);
        }
      });

      if (allRows.length > 0) {
        batchUpdateStudents(allRows);
        if (onSuccessToast) {
          onSuccessToast(`Batch updated ${allRows.length} student records from uploaded files!`);
        }
      }
    }

    if (currentStudent) {
      const documentsToAdd: StudentDocument[] = parsedEntries.map((entry, idx) => ({
        id: `DOC-${currentStudent.id}-${Date.now().toString().slice(-4)}-${idx}`,
        studentId: currentStudent.id,
        title: entry.result.title,
        category: entry.result.category,
        fileType: entry.result.fileType,
        uploadDate: new Date().toISOString().split('T')[0],
        extractedMetrics: entry.result.extractedMetrics,
        status: 'Verified',
        fileName: entry.file.name,
        fileUrl: entry.result.fileUrl,
        issuer: entry.result.issuer,
        issueDate: entry.result.issueDate,
        credentialId: entry.result.credentialId || `CERT-${Date.now().toString().slice(-5)}`,
        skills: entry.result.skills,
        gradeOrScore: entry.result.gradeOrScore,
        description: entry.result.description,
      }));

      uploadMultipleStudentDocuments(currentStudent.id, documentsToAdd);

      if (onSuccessToast) {
        onSuccessToast(
          `Successfully uploaded ${documentsToAdd.length} credential(s) to ${currentStudent.name}'s gallery & recalculated prediction!`
        );
      }
    }

    handleClose();
  };

  const handleClose = () => {
    setParsedEntries([]);
    setManualText('');
    onClose();
  };

  const totalBonus = parsedEntries.reduce(
    (acc, e) => acc + (e.result.extractedMetrics.certificateBonus || 0),
    0
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={
        isBatchFacultyMode
          ? 'Batch Upload Student Credentials, Marksheets & Activities'
          : `Upload Student Credentials & Gallery Documents • ${currentStudent?.name || ''}`
      }
      maxWidth="max-w-2xl"
    >
      <div className="space-y-4 text-slate-800 dark:text-slate-100">
        {/* Banner */}
        <div className="p-3 bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-900 rounded-xl text-xs text-indigo-900 dark:text-indigo-300">
          <p className="font-bold flex items-center gap-1.5 mb-1">
            <Sparkles className="w-4 h-4 text-amber-500" /> Multimodal Gallery &amp; AI Prediction Engine
          </p>
          Upload single or multiple images/documents (certificates, marksheets, attendance slips, hackathon medals). Every certificate uploaded is instantly saved to the student&apos;s achievement gallery, boosts prediction scores, and notifies the faculty!
        </div>

        {/* If Faculty Mode without preselected student, allow selecting target student */}
        {!propStudent && (
          <div>
            <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
              Select Target Student Portfolio
            </label>
            <select
              value={selectedStudentId}
              onChange={(e) => setSelectedStudentId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-blue-500 font-semibold"
            >
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.department} • EMIS: {s.emis} • Curr Score: {s.predictedScore}%)
                </option>
              ))}
            </select>
          </div>
        )}

        {/* File Dropzone - MULTIPLE FILES */}
        <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-6 text-center hover:border-blue-500 transition-colors bg-slate-50 dark:bg-slate-900/50">
          <input
            type="file"
            id="doc-files-upload"
            multiple={true}
            accept=".png,.jpg,.jpeg,.webp,.csv,.txt"
            onChange={handleFilesChange}
            className="hidden"
          />
          <label htmlFor="doc-files-upload" className="cursor-pointer block">
            <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 mx-auto flex items-center justify-center mb-2">
              <Upload className="w-6 h-6" />
            </div>
            <span className="font-bold text-sm text-slate-900 dark:text-white block">
              Click to Upload Single or Multiple Images / Documents
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 block mt-1">
              Supports PNG, JPG, JPEG, CSV marksheets, or TXT transcripts • Select multiple files at once
            </span>
          </label>
        </div>

        {/* Text Transcript Box Option */}
        <div>
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
            Or Paste Assessment Slip / Transcript
          </label>
          <div className="flex gap-2">
            <textarea
              rows={2}
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder="e.g. Attendance: 92%, Score: 86%, Python NPTEL Elite Certification"
              className="flex-1 px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <Button variant="outline" size="sm" onClick={handleManualTextExtract}>
              Extract
            </Button>
          </div>
        </div>

        {/* Loading Indicator */}
        {isExtracting && (
          <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 text-xs font-bold animate-pulse flex items-center gap-2">
            <Sparkles className="w-4 h-4 animate-spin" /> Processing file(s) through OCR Vision &amp; Prediction Extractor...
          </div>
        )}

        {/* Extracted Files List Preview */}
        {parsedEntries.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold">
              <span className="text-slate-900 dark:text-white flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-blue-600" /> Extracted Documents ({parsedEntries.length})
              </span>
              <span className="text-emerald-600 font-black">
                Total Gallery Impact: +{totalBonus}% AI Bonus
              </span>
            </div>

            <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
              {parsedEntries.map((entry, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-900 text-white border border-slate-800 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {/* Thumbnail preview */}
                    {entry.result.fileUrl ? (
                      <img
                        src={entry.result.fileUrl}
                        alt="preview"
                        className="w-12 h-9 object-cover rounded-md border border-slate-700 shrink-0"
                      />
                    ) : (
                      <div className="w-12 h-9 rounded-md bg-slate-800 flex items-center justify-center shrink-0">
                        <Award className="w-5 h-5 text-amber-400" />
                      </div>
                    )}

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white truncate block">{entry.result.title}</span>
                        <span className="px-1.5 py-0.5 rounded bg-blue-900 text-blue-200 text-[10px] font-bold uppercase shrink-0">
                          {entry.result.category}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 block truncate">
                        {entry.result.issuer} • Score: {entry.result.extractedMetrics.score || 82}% • Att: {entry.result.extractedMetrics.attendance || 88}%
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="font-bold text-emerald-400 text-xs">
                      +{entry.result.extractedMetrics.certificateBonus || 3}%
                    </span>
                    <button
                      onClick={() => handleRemoveEntry(idx)}
                      className="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-slate-800"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modal Buttons */}
        <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={parsedEntries.length === 0}
            onClick={handleSubmit}
            className="gap-1.5 font-bold shadow-md shadow-blue-600/20"
          >
            <CheckCircle2 className="w-4 h-4" /> Save to Gallery &amp; Update AI Predictions ({parsedEntries.length})
          </Button>
        </div>
      </div>
    </Modal>
  );
};
