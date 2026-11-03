import React from 'react';
import { Search, X } from 'lucide-react';

interface TaskSearchProps {
  value: string;
  onChange: (val: string) => void;
}

export const TaskSearch: React.FC<TaskSearchProps> = ({ value, onChange }) => {
  return (
    <div className="relative flex-1">
      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
      <input
        type="text"
        placeholder="Search tasks by title or details..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full pl-10 pr-9 py-2.5 rounded-2xl bg-slate-900/80 border border-slate-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-white placeholder-slate-500 text-sm outline-none transition"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-white transition"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};

