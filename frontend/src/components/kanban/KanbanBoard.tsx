import React from 'react';
import { Task, TaskStatus } from '../../types/task';
import { Project } from '../../types/project';
import { KANBAN_COLUMNS } from '../../types/kanban';
import { KanbanColumn } from './KanbanColumn';

interface KanbanBoardProps {
  tasks: Task[];
  projectsMap: Map<string, Project>;
  onEditTask: (task: Task) => void;
  onDeleteTask: (task: Task) => void;
  onDropTask: (taskId: string, targetStatus: TaskStatus) => void;
  onAddTask: (status: TaskStatus) => void;
  updatingTaskIds: Set<string>;
}

export const KanbanBoard: React.FC<KanbanBoardProps> = ({
  tasks,
  projectsMap,
  onEditTask,
  onDeleteTask,
  onDropTask,
  onAddTask,
  updatingTaskIds,
}) => {
  // Group tasks by status
  const tasksByStatus: Record<TaskStatus, Task[]> = {
    TODO: [],
    IN_PROGRESS: [],
    COMPLETED: [],
    CANCELLED: [],
  };

  tasks.forEach((t) => {
    if (tasksByStatus[t.status]) {
      tasksByStatus[t.status].push(t);
    } else {
      // Fallback
      tasksByStatus.TODO.push(t);
    }
  });

  return (
    <div className="flex flex-col md:flex-row gap-4 overflow-x-auto pb-4 items-stretch min-h-[500px]">
      {KANBAN_COLUMNS.map((colConfig) => (
        <KanbanColumn
          key={colConfig.id}
          config={colConfig}
          tasks={tasksByStatus[colConfig.id]}
          projectsMap={projectsMap}
          onEditTask={onEditTask}
          onDeleteTask={onDeleteTask}
          onDropTask={onDropTask}
          onAddTask={onAddTask}
          updatingTaskIds={updatingTaskIds}
        />
      ))}
    </div>
  );
};

