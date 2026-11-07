'use client';

import React, { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Student, StudentDocument } from '@/types';
import { parseUploadedDocument, ExtractedExtractionResult } from '@/lib/documentExtractor';
import { useKalvikkanStore } from '@/lib/store';
import { saveDocumentFile } from '@/lib/documentStorage';
import { Upload, FileText, Image as ImageIcon, CheckCircle2, Sparkles, FileSpreadsheet, AlertCircle } from 'lucide-react';

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  student?: Student | null;
  isBatchFacultyMode?: boolean;
  onSuccessToast?: (msg: string) => void;
}

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  onClose,
  student,
  isBatchFacultyMode = false,
  onSuccessToast,
}) => {
  const { uploadStudentDocuments, batchUpdateStudents } = useKalvikkanStore();

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionResults, setExtractionResults] = useState<ExtractedExtractionResult[]>([]);
  const [manualText, setManualText] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    setSelectedFiles(files);
    setExtractionResults([]);
    setErrorMessage(null);
    setIsExtracting(true);

    try {
      setExtractionResults(await Promise.all(files.map((file) => parseUploadedDocument(file))));
    } catch (err) {
      console.error('Document extraction failed:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Could not process the selected files.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleManualTextExtract = async () => {
    if (!manualText.trim()) return;
    setIsExtracting(true);
    setErrorMessage(null);
    try {
      const mockFile = new File([manualText], 'manual_transcript.txt', { type: 'text/plain' });
      setSelectedFiles([]);
      setExtractionResults([await parseUploadedDocument(mockFile, manualText)]);
    } catch (err) {
      console.error('Transcript extraction failed:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Could not process the transcript.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSubmit = async () => {
    if (!extractionResults.length) return;

    try {
      if (isBatchFacultyMode && extractionResults.some((result) => result.parsedRows)) {
        const parsedRows = extractionResults.flatMap((result) => result.parsedRows || []);
        batchUpdateStudents(parsedRows);
        onSuccessToast?.(`Batch updated ${parsedRows.length} student records from uploaded file(s)!`);
      } else if (student) {
        const documents: StudentDocument[] = [];
        for (const [index, result] of extractionResults.entries()) {
          const file = selectedFiles[index];
          const documentId = `DOC-${crypto.randomUUID()}`;
          if (file) await saveDocumentFile(documentId, file);
          documents.push({
            id: documentId,
            studentId: student.id,
            title: result.title,
            category: result.category,
            fileType: result.fileType,
            uploadDate: new Date().toISOString().split('T')[0],
            extractedMetrics: result.extractedMetrics,
            status: 'Verified',
            fileName: file?.name || 'transcript.txt',
            mimeType: file?.type || 'text/plain',
          });
        }

        uploadStudentDocuments(student.id, documents);
        onSuccessToast?.(`${documents.length} document(s) saved to your gallery and student prediction updated.`);
      }
      onClose();
      setSelectedFiles([]);
      setExtractionResults([]);
      setManualText('');
      setErrorMessage(null);
    } catch (err) {
      console.error('Could not save uploaded documents:', err);
      setErrorMessage(err instanceof Error ? err.message : 'Could not save the selected documents.');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isBatchFacultyMode ? 'Batch Class Dataset & Marksheet Extraction' : `Upload Student Document • ${student?.name || ''}`}
      maxWidth="max-w-xl"
    >
      <div className="space-y-4 text-slate-800 dark:text-slate-100">
        <div className="p-3 bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-900 rounded-xl text-xs text-indigo-900 dark:text-indigo-300">
          <p className="font-bold flex items-center gap-1.5 mb-1">
            <Sparkles className="w-4 h-4 text-amber-500" /> Multimodal Extraction &amp; Auto-Prediction Engine
          </p>
          Upload certificates, marksheets, attendance slips, or CSV rosters in <strong>Image (PNG/JPG)</strong>, <strong>CSV</strong>, or <strong>Text</strong> format. Metrics are extracted to instantly update predictions.
        </div>

        {/* File Dropzone */}
        <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-6 text-center hover:border-blue-500 transition-colors bg-slate-50 dark:bg-slate-900/50">
          <input
            type="file"
            id="doc-file-upload"
            accept=".png,.jpg,.jpeg,.csv,.txt"
            multiple
            onChange={handleFileChange}
            className="hidden"
          />
          <label htmlFor="doc-file-upload" className="cursor-pointer block">
            <div className="w-12 h-12 rounded-2xl bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 mx-auto flex items-center justify-center mb-2">
              <Upload className="w-6 h-6" />
            </div>
            <span className="font-bold text-sm text-slate-900 dark:text-white block">
              {selectedFiles.length ? `${selectedFiles.length} file(s) selected` : 'Click to Browse File (Image, CSV, or Text)'}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400 block mt-1">
              Supports multiple PNG/JPG certificates, CSV marksheets, or TXT transcripts
            </span>
          </label>
        </div>

        {/* Text Transcript Box Option */}
        <div>
          <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">
            Or Paste Text Transcript / Assessment Slip
          </label>
          <div className="flex gap-2">
            <textarea
              rows={2}
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder="e.g. Attendance: 88%, Score: 84%, Mathematics Quiz: 78"
              className="flex-1 px-3 py-2 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs focus:ring-2 focus:ring-blue-500 font-mono"
            />
            <Button variant="outline" size="sm" onClick={handleManualTextExtract}>
              Extract
            </Button>
          </div>
        </div>

        {/* Extraction Results Preview Card */}
        {isExtracting && (
          <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 text-xs font-bold animate-pulse flex items-center gap-2">
            <Sparkles className="w-4 h-4 animate-spin" /> Processing document through OCR Vision &amp; Parser engine...
          </div>
        )}

        {extractionResults.length > 0 && !isExtracting && (
          <div className="p-4 rounded-xl bg-slate-900 text-white border border-slate-800 space-y-2">
            {extractionResults.map((result, index) => (
              <div key={`${result.title}-${index}`} className="border-b border-slate-800 last:border-0 pb-2 last:pb-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> {result.title}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-blue-900 text-blue-200 text-[10px] font-bold uppercase">
                    {result.category}
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-mono mt-1">
                  {result.summaryMessage}
                </p>
              </div>
            ))}
          </div>
        )}

        {errorMessage && (
          <div role="alert" className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" /> {errorMessage}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" disabled={!extractionResults.length || isExtracting} onClick={handleSubmit}>
            Save to Gallery &amp; Recalculate AI Prediction
          </Button>
        </div>
      </div>
    </Modal>
  );
};
