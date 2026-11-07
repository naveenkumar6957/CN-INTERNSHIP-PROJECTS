'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { ArrowDownToLine, FileText, Images, UserRound } from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { Card } from '@/components/ui/Card';
import { GlobalSearchModal } from '@/components/layout/GlobalSearchModal';
import { useKalvikkanStore } from '@/lib/store';
import { getDocumentFile } from '@/lib/documentStorage';
import { StudentDocument } from '@/types';

function StudentGalleryContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { students, role, currentUser, loggedStudentId, isHydrated } = useKalvikkanStore();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [fileUrls, setFileUrls] = useState<Record<string, string>>({});
  const [storageError, setStorageError] = useState<string | null>(null);

  const ownStudentId = currentUser?.studentId || currentUser?.id || loggedStudentId;
  const requestedStudentId = role === 'student' ? ownStudentId : searchParams.get('studentId');
  const selectedStudent =
    students.find((student) => student.id === requestedStudentId) ||
    (role === 'student' ? undefined : students[0]);
  const documents = selectedStudent?.documents || [];

  useEffect(() => {
    let active = true;
    const urls: string[] = [];
    setFileUrls({});
    setStorageError(null);

    void Promise.all(
      documents.map(async (document) => {
        const file = await getDocumentFile(document.id);
        if (!file) return [document.id, ''] as const;
        const url = URL.createObjectURL(file);
        urls.push(url);
        return [document.id, url] as const;
      })
    ).then((entries) => {
      if (active) {
        setFileUrls(Object.fromEntries(entries));
      } else {
        urls.forEach((url) => URL.revokeObjectURL(url));
      }
    }).catch((error: unknown) => {
      if (active) {
        console.error('Could not load student gallery files:', error);
        setStorageError(error instanceof Error ? error.message : 'Could not load gallery files.');
      }
    });

    return () => {
      active = false;
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [selectedStudent?.id, selectedStudent?.documents]);

  if (!isHydrated) return null;

  const openStudentGallery = (studentId: string) => {
    router.replace(`/gallery?studentId=${encodeURIComponent(studentId)}`);
  };

  const renderDocument = (document: StudentDocument) => {
    const url = fileUrls[document.id];
    return (
      <Card key={document.id} className="overflow-hidden p-0 border-slate-200 dark:border-slate-800">
        <div className="aspect-[4/3] bg-slate-100 dark:bg-slate-800 flex items-center justify-center relative">
          {url && document.mimeType?.startsWith('image/') ? (
            <Image
              src={url}
              alt={document.title}
              width={640}
              height={480}
              unoptimized
              className="w-full h-full object-contain"
            />
          ) : (
            <FileText className="w-12 h-12 text-blue-500" />
          )}
        </div>
        <div className="p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white line-clamp-2">{document.title}</h3>
            <span className="shrink-0 rounded-full bg-blue-100 dark:bg-blue-950 px-2 py-0.5 text-[10px] font-bold text-blue-700 dark:text-blue-300">
              {document.category}
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {document.fileName} · Uploaded {document.uploadDate}
          </p>
          {url ? (
            <a
              href={url}
              download={document.fileName}
              target={document.mimeType?.startsWith('image/') ? '_blank' : undefined}
              rel={document.mimeType?.startsWith('image/') ? 'noreferrer' : undefined}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-600 hover:text-blue-800 dark:text-blue-400"
            >
              <ArrowDownToLine className="w-3.5 h-3.5" /> Open / download
            </a>
          ) : (
            <p className="text-xs text-slate-400">File content is unavailable for this older upload.</p>
          )}
        </div>
      </Card>
    );
  };

  return (
    <div className="flex min-h-screen font-sans">
      <Sidebar mobileOpen={mobileNavOpen} setMobileOpen={setMobileNavOpen} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onOpenMobileNav={() => setMobileNavOpen(true)}
          onOpenSearch={() => setSearchOpen(true)}
          title="Student Achievement Gallery"
          subtitle="Browse certificates, marksheets, and other student uploads"
        />
        <main className="flex-1 p-4 lg:p-8 space-y-6 max-w-7xl mx-auto w-full">
          {role !== 'student' && (
            <Card className="flex flex-col sm:flex-row sm:items-center gap-3">
              <label htmlFor="gallery-student" className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                <UserRound className="w-4 h-4 text-blue-600" /> Select student
              </label>
              <select
                id="gallery-student"
                value={selectedStudent?.id || ''}
                onChange={(event) => openStudentGallery(event.target.value)}
                className="sm:ml-auto w-full sm:max-w-sm px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm"
              >
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.name} · {student.emis}
                  </option>
                ))}
              </select>
            </Card>
          )}

          {storageError && (
            <div role="alert" className="p-3 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 text-sm">
              {storageError}
            </div>
          )}

          {selectedStudent ? (
            <>
              <Card className="flex items-center justify-between gap-4 bg-gradient-to-r from-blue-950 to-indigo-950 text-white border-indigo-800">
                <div>
                  <p className="text-xs text-blue-200">Achievement portfolio</p>
                  <h2 className="text-xl font-black">{selectedStudent.name}</h2>
                  <p className="text-xs text-blue-200 mt-1">{selectedStudent.department} · EMIS {selectedStudent.emis}</p>
                </div>
                <div className="rounded-2xl bg-white/10 p-3 text-center min-w-16">
                  <Images className="w-5 h-5 mx-auto text-amber-300" />
                  <span className="block text-lg font-black">{documents.length}</span>
                  <span className="text-[10px] text-blue-100">uploads</span>
                </div>
              </Card>

              {documents.length ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {documents.map(renderDocument)}
                </div>
              ) : (
                <Card className="text-center py-12">
                  <Images className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600" />
                  <h3 className="mt-3 text-sm font-bold text-slate-800 dark:text-slate-200">No uploads yet</h3>
                  <p className="mt-1 text-xs text-slate-500">Certificates and other uploads will appear here.</p>
                </Card>
              )}
            </>
          ) : (
            <Card className="text-center py-12 text-sm text-slate-500">No student gallery is available for this account.</Card>
          )}
        </main>
      </div>
      <GlobalSearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </div>
  );
}

export default function StudentGalleryPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <StudentGalleryContent />
    </Suspense>
  );
}
