import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import type { Task } from '../../types/api';
import { AlertTriangle, Loader2 } from 'lucide-react';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: Task | null;
  onConfirm: (id: number) => Promise<void>;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  onClose,
  task,
  onConfirm,
}) => {
  const [isDeleting, setIsDeleting] = useState(false);

  if (!task) return null;

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onConfirm(task.id);
      onClose();
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Delete Task"
      maxWidth="sm"
    >
      <div className="space-y-4">
        <div className="flex items-start space-x-3 text-amber-500 bg-amber-500/10 p-3.5 rounded-xl border border-amber-500/20">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="text-xs text-[var(--text-primary)]">
            <p className="font-semibold text-amber-500 mb-0.5">Are you sure?</p>
            <p className="text-[var(--text-secondary)]">
              This action will remove &ldquo;<span className="font-medium text-[var(--text-primary)]">{task.title}</span>&rdquo; from your active schedule.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end space-x-3 pt-3 border-t border-[var(--bg-border)]">
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 rounded-xl text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors focus:outline-none"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex items-center justify-center px-4 py-2 rounded-xl text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 active:bg-rose-800 shadow-sm shadow-rose-600/20 transition-all focus:outline-none focus:ring-2 focus:ring-rose-500 disabled:opacity-50"
          >
            {isDeleting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete Task'
            )}
          </button>
        </div>
      </div>
    </Modal>
  );
};
