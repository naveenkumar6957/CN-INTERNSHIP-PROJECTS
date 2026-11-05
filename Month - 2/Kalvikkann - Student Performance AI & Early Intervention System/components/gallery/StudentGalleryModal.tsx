'use client';

import React from 'react';
import { Student } from '@/types';
import { Modal } from '@/components/ui/Modal';
import { CertificateGallery } from './CertificateGallery';

interface StudentGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  student: Student | null;
  onOpenUploadModal?: () => void;
}

export const StudentGalleryModal: React.FC<StudentGalleryModalProps> = ({
  isOpen,
  onClose,
  student,
  onOpenUploadModal,
}) => {
  if (!isOpen || !student) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Achievement Gallery • ${student.name} (${student.department})`}
      maxWidth="max-w-5xl"
    >
      <div className="py-2">
        <CertificateGallery
          student={student}
          onOpenUploadModal={onOpenUploadModal}
          canVerify={true}
        />
      </div>
    </Modal>
  );
};
