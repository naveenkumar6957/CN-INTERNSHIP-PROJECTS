'use client';

import React, { useState } from 'react';
import { Student, StudentDocument } from '@/types';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { useKalvikkanStore } from '@/lib/store';
import {
  Award,
  Sparkles,
  CheckCircle2,
  Clock,
  Search,
  Upload,
  Download,
  Printer,
  ShieldCheck,
  Eye,
  Trash2,
  ExternalLink,
  Filter,
  Check,
  Calendar,
  Building,
  Tag
} from 'lucide-react';

interface CertificateGalleryProps {
  student: Student;
  onOpenUploadModal?: () => void;
  canVerify?: boolean; // Faculty/Admin can verify certificates
  compact?: boolean;
}

export const CertificateGallery: React.FC<CertificateGalleryProps> = ({
  student,
  onOpenUploadModal,
  canVerify = true,
  compact = false,
}) => {
  const { verifyStudentDocument, deleteStudentDocument, currentUser } = useKalvikkanStore();

  const [activeCategory, setActiveCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<StudentDocument | null>(null);
  const [verificationFeedback, setVerificationFeedback] = useState<string | null>(null);

  const docs = student.documents || [];

  // Filtered documents
  const filteredDocs = docs.filter((doc) => {
    const matchesCategory =
      activeCategory === 'ALL' ||
      doc.category.toLowerCase() === activeCategory.toLowerCase();

    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (doc.issuer && doc.issuer.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (doc.skills && doc.skills.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase())));

    return matchesCategory && matchesSearch;
  });

  const verifiedCount = docs.filter((d) => d.status === 'Verified').length;
  const totalBonus = docs.reduce((acc, d) => acc + (d.extractedMetrics.certificateBonus || 0), 0);

  // Collect unique skills from all certificates
  const allSkills = Array.from(
    new Set(docs.flatMap((d) => d.skills || []))
  );

  const handleVerify = (doc: StudentDocument) => {
    const verifier = currentUser?.name || 'Faculty Mentor';
    verifyStudentDocument(student.id, doc.id, verifier);
    setSelectedDoc({ ...doc, status: 'Verified', verifiedBy: verifier });
    setVerificationFeedback(`Certificate "${doc.title}" verified and endorsed by ${verifier}!`);
    setTimeout(() => setVerificationFeedback(null), 3000);
  };

  const handleDelete = (docId: string) => {
    if (confirm('Are you sure you want to remove this certificate from the gallery?')) {
      deleteStudentDocument(student.id, docId);
      setSelectedDoc(null);
    }
  };

  const handlePrint = (doc: StudentDocument) => {
    const win = window.open('', '_blank');
    if (win) {
      win.document.write(`
        <html>
          <head>
            <title>${doc.title} • ${student.name}</title>
            <style>
              body { margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #000; font-family: sans-serif; }
              img { max-width: 95vw; max-height: 95vh; object-fit: contain; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border-radius: 8px; }
            </style>
          </head>
          <body>
            <img src="${doc.fileUrl || ''}" alt="${doc.title}" />
            <script>window.onload = () => { setTimeout(() => window.print(), 500); }</script>
          </body>
        </html>
      `);
      win.document.close();
    }
  };

  return (
    <div className="space-y-5">
      {/* Gallery Header & Stats */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 border border-slate-800 text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-amber-500/20 text-amber-300">
              <Award className="w-5 h-5" />
            </span>
            <h3 className="text-xl font-black tracking-tight text-white">
              Student Achievement Gallery
            </h3>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300">
              {docs.length} Credential{docs.length === 1 ? '' : 's'}
            </span>
          </div>
          <p className="text-xs text-slate-300 max-w-xl">
            Verified academic credentials, NPTEL certificates, hackathon honors, and workshop awards for{' '}
            <strong className="text-amber-300">{student.name}</strong> ({student.department}, EMIS: {student.emis}).
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {onOpenUploadModal && (
            <Button
              variant="primary"
              size="sm"
              onClick={onOpenUploadModal}
              className="gap-2 shadow-md shadow-blue-600/30 font-bold"
            >
              <Upload className="w-4 h-4" /> Upload Certificate(s)
            </Button>
          )}
        </div>
      </div>

      {/* KPI Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Total Uploads</span>
          <span className="text-2xl font-black text-slate-900 dark:text-white block mt-0.5">{docs.length}</span>
          <span className="text-[10px] text-slate-500 mt-1 block">In official portfolio</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] font-semibold text-emerald-500 uppercase tracking-wider block">Faculty Verified</span>
          <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 block mt-0.5">{verifiedCount}</span>
          <span className="text-[10px] text-slate-500 mt-1 block">Authenticated records</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] font-semibold text-amber-500 uppercase tracking-wider block">AI Prediction Boost</span>
          <span className="text-2xl font-black text-amber-500 block mt-0.5">+{totalBonus}%</span>
          <span className="text-[10px] text-slate-500 mt-1 block">Cumulative score bonus</span>
        </div>
        <div className="p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-[11px] font-semibold text-blue-500 uppercase tracking-wider block">Skills Verified</span>
          <span className="text-2xl font-black text-blue-600 dark:text-blue-400 block mt-0.5">{allSkills.length}</span>
          <span className="text-[10px] text-slate-500 mt-1 block">Engineering competences</span>
        </div>
      </div>

      {/* Search and Category Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
        <div className="flex flex-wrap items-center gap-1.5">
          {['ALL', 'Certificate', 'Achievement', 'Marksheet'].map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                activeCategory === cat
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {cat === 'ALL' ? `All (${docs.length})` : `${cat}s (${docs.filter((d) => d.category === cat).length})`}
            </button>
          ))}
        </div>

        <div className="relative min-w-[220px]">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search certificate or skill..."
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Gallery Grid */}
      {filteredDocs.length === 0 ? (
        <div className="p-12 text-center border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl bg-slate-50 dark:bg-slate-900/30">
          <Award className="w-12 h-12 text-slate-400 mx-auto mb-3 opacity-60" />
          <h4 className="text-base font-bold text-slate-800 dark:text-slate-200">No Certificates Found</h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchQuery
              ? 'No credentials match your filter search. Try searching another skill or category.'
              : 'This student has not uploaded any credentials to their gallery yet.'}
          </p>
          {onOpenUploadModal && (
            <Button variant="outline" size="sm" onClick={onOpenUploadModal} className="mt-4 gap-2">
              <Upload className="w-4 h-4" /> Upload First Certificate
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocs.map((doc) => {
            const isVerified = doc.status === 'Verified';
            return (
              <div
                key={doc.id}
                onClick={() => setSelectedDoc(doc)}
                className="group relative rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-blue-500 dark:hover:border-blue-500 transition-all duration-300 shadow-sm hover:shadow-xl cursor-pointer flex flex-col justify-between"
              >
                {/* Certificate Preview Visual Thumbnail */}
                <div className="relative aspect-[16/10] bg-slate-950 overflow-hidden flex items-center justify-center">
                  {doc.fileUrl ? (
                    <img
                      src={doc.fileUrl}
                      alt={doc.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="p-4 text-center text-slate-400">
                      <Award className="w-10 h-10 mx-auto mb-1 text-amber-400" />
                      <span className="text-xs font-bold block">{doc.title}</span>
                    </div>
                  )}

                  {/* Top Badges Overlay */}
                  <div className="absolute top-2.5 left-2.5 right-2.5 flex items-center justify-between pointer-events-none">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-slate-900/80 backdrop-blur-md text-white border border-slate-700/60 shadow-sm">
                      {doc.category}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase flex items-center gap-1 shadow-sm ${
                        isVerified
                          ? 'bg-emerald-500 text-white'
                          : 'bg-amber-500 text-slate-950'
                      }`}
                    >
                      {isVerified ? (
                        <>
                          <CheckCircle2 className="w-3 h-3" /> Verified
                        </>
                      ) : (
                        <>
                          <Clock className="w-3 h-3" /> Under Review
                        </>
                      )}
                    </span>
                  </div>

                  {/* Hover Inspect Overlay */}
                  <div className="absolute inset-0 bg-blue-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-xs">
                    <span className="px-3 py-1.5 rounded-xl bg-white text-slate-900 font-bold text-xs flex items-center gap-1.5 shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-transform">
                      <Eye className="w-4 h-4 text-blue-600" /> View Certificate
                    </span>
                  </div>
                </div>

                {/* Details Footer */}
                <div className="p-4 space-y-2 flex-1 flex flex-col justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white line-clamp-1 group-hover:text-blue-600 transition-colors">
                      {doc.title}
                    </h4>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1">
                      {doc.issuer || 'Academic Institution'}
                    </p>
                  </div>

                  {/* Skills Tag Pills */}
                  {doc.skills && doc.skills.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {doc.skills.slice(0, 3).map((sk) => (
                        <span
                          key={sk}
                          className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-medium"
                        >
                          {sk}
                        </span>
                      ))}
                      {doc.skills.length > 3 && (
                        <span className="text-[10px] text-slate-400 self-center">
                          +{doc.skills.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 font-mono">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-slate-400" /> {doc.uploadDate || doc.issueDate}
                    </span>
                    <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> +{doc.extractedMetrics.certificateBonus || 3}% Score
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Full-Screen Certificate Viewer & Verification Modal */}
      {selectedDoc && (
        <Modal
          isOpen={!!selectedDoc}
          onClose={() => setSelectedDoc(null)}
          title={`Certificate Credential • ${selectedDoc.title}`}
          maxWidth="max-w-4xl"
        >
          <div className="space-y-4">
            {verificationFeedback && (
              <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                {verificationFeedback}
              </div>
            )}

            {/* High-Resolution Certificate Canvas */}
            <div className="rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 shadow-2xl relative">
              {selectedDoc.fileUrl ? (
                <img
                  src={selectedDoc.fileUrl}
                  alt={selectedDoc.title}
                  className="w-full max-h-[500px] object-contain mx-auto"
                />
              ) : (
                <div className="p-16 text-center text-white">
                  <Award className="w-20 h-20 text-amber-400 mx-auto mb-2" />
                  <h3 className="text-xl font-bold">{selectedDoc.title}</h3>
                </div>
              )}
            </div>

            {/* Metadata and AI Impact Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Student Owner</span>
                <span className="font-bold text-sm text-slate-900 dark:text-white block mt-0.5">{student.name}</span>
                <span className="text-slate-500 font-mono text-[11px] block">{student.department} • EMIS: {student.emis}</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Issuing Authority</span>
                <span className="font-bold text-sm text-slate-900 dark:text-white block mt-0.5">{selectedDoc.issuer || 'NPTEL / College'}</span>
                <span className="text-slate-500 font-mono text-[11px] block">Issued: {selectedDoc.issueDate || selectedDoc.uploadDate}</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Verification Status</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span
                    className={`font-bold text-sm ${
                      selectedDoc.status === 'Verified' ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-500'
                    }`}
                  >
                    {selectedDoc.status}
                  </span>
                  {selectedDoc.verifiedBy && (
                    <span className="text-[10px] text-slate-500 font-mono">(by {selectedDoc.verifiedBy})</span>
                  )}
                </div>
                <span className="text-emerald-600 dark:text-emerald-400 font-bold text-[11px] block mt-0.5">
                  AI Boost: +{selectedDoc.extractedMetrics.certificateBonus || 3}% score bonus
                </span>
              </div>
            </div>

            {/* Credential ID and Skills */}
            <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700 flex flex-wrap items-center justify-between gap-2 text-xs">
              <span className="font-mono text-slate-500">
                CREDENTIAL ID: <strong className="text-slate-800 dark:text-slate-200">{selectedDoc.credentialId || `CERT-${selectedDoc.id}`}</strong>
              </span>

              {selectedDoc.skills && (
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-slate-400 text-[11px]">Skills:</span>
                  {selectedDoc.skills.map((sk) => (
                    <span
                      key={sk}
                      className="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 text-[10px] font-bold"
                    >
                      {sk}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePrint(selectedDoc)}
                  className="gap-1.5 text-xs"
                >
                  <Printer className="w-3.5 h-3.5" /> Print / PDF
                </Button>
                {selectedDoc.fileUrl && (
                  <a
                    href={selectedDoc.fileUrl}
                    download={`${selectedDoc.title.toLowerCase().replace(/[^a-z0-9]/g, '_')}.png`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-300 dark:border-slate-700 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <Download className="w-3.5 h-3.5" /> Download
                  </a>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(selectedDoc.id)}
                  className="gap-1.5 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Remove
                </Button>
              </div>

              <div className="flex items-center gap-2">
                {canVerify && selectedDoc.status !== 'Verified' && (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleVerify(selectedDoc)}
                    className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
                  >
                    <ShieldCheck className="w-4 h-4" /> Verify &amp; Endorse Certificate
                  </Button>
                )}
                <Button variant="secondary" size="sm" onClick={() => setSelectedDoc(null)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
