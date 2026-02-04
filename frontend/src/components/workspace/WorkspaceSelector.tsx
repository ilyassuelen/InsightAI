import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Plus, Settings, Building2, User, Check } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Workspace } from '@/types/workspace';
import { CreateWorkspaceModal } from './CreateWorkspaceModal';
import { WorkspaceSettingsModal } from './WorkspaceSettingsModal';

interface WorkspaceSelectorProps {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  isOwner: boolean;
  onSwitchWorkspace: (workspaceId: string) => void;
  onCreateWorkspace: (name: string) => void;
  onRenameWorkspace: (workspaceId: string, newName: string) => void;
  onDeleteWorkspace: (workspaceId: string) => void;
  onAddMember: (workspaceId: string, email: string, name?: string) => void;
  onRemoveMember: (workspaceId: string, memberId: string) => void;
}

export function WorkspaceSelector({
  workspaces,
  currentWorkspace,
  isOwner,
  onSwitchWorkspace,
  onCreateWorkspace,
  onRenameWorkspace,
  onDeleteWorkspace,
  onAddMember,
  onRemoveMember,
}: WorkspaceSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  const handleSelectWorkspace = (workspaceId: string) => {
    onSwitchWorkspace(workspaceId);
    setIsOpen(false);
  };

  const handleOpenCreate = () => {
    setIsOpen(false);
    setShowCreateModal(true);
  };

  const handleOpenSettings = () => {
    setIsOpen(false);
    setShowSettingsModal(true);
  };

  return (
    <>
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            className="h-9 px-3 gap-2 bg-muted/50 border border-border hover:bg-muted hover:border-primary/30 transition-all"
          >
            {currentWorkspace?.isPersonal ? (
              <User className="h-3.5 w-3.5 text-primary" />
            ) : (
              <Building2 className="h-3.5 w-3.5 text-primary" />
            )}
            <span className="text-xs font-medium max-w-[120px] truncate hidden sm:inline">
              {currentWorkspace?.name || 'Select Workspace'}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </Button>
        </PopoverTrigger>

        <PopoverContent
          className="w-64 p-2 bg-background border-border shadow-xl"
          align="start"
          sideOffset={8}
        >
          <div className="space-y-1">
            {/* Workspaces List */}
            <div className="px-2 py-1.5">
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                Workspaces
              </span>
            </div>

            <AnimatePresence>
              {workspaces.map((workspace, index) => (
                <motion.button
                  key={workspace.id}
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03 }}
                  onClick={() => handleSelectWorkspace(workspace.id)}
                  className={`w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-left transition-colors ${
                    currentWorkspace?.id === workspace.id
                      ? 'bg-primary/10 text-primary'
                      : 'hover:bg-muted text-foreground'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {workspace.isPersonal ? (
                      <User className="h-4 w-4 shrink-0" />
                    ) : (
                      <Building2 className="h-4 w-4 shrink-0" />
                    )}
                    <span className="text-sm truncate">{workspace.name}</span>
                  </div>
                  {currentWorkspace?.id === workspace.id && (
                    <Check className="h-4 w-4 shrink-0 text-primary" />
                  )}
                </motion.button>
              ))}
            </AnimatePresence>

            <Separator className="my-2 bg-border/50" />

            {/* Settings Button */}
            {currentWorkspace && !currentWorkspace.isPersonal && (
              <button
                onClick={handleOpenSettings}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <Settings className="h-4 w-4" />
                <span className="text-sm">Workspace Settings</span>
              </button>
            )}

            {/* Create Workspace Button */}
            <button
              onClick={handleOpenCreate}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-primary hover:bg-primary/10 transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span className="text-sm font-medium">Create New Workspace</span>
            </button>
          </div>
        </PopoverContent>
      </Popover>

      {/* Create Workspace Modal */}
      <CreateWorkspaceModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        onCreateWorkspace={onCreateWorkspace}
      />

      {/* Workspace Settings Modal */}
      <WorkspaceSettingsModal
        open={showSettingsModal}
        onOpenChange={setShowSettingsModal}
        workspace={currentWorkspace}
        isOwner={isOwner}
        onRename={onRenameWorkspace}
        onDelete={onDeleteWorkspace}
        onAddMember={onAddMember}
        onRemoveMember={onRemoveMember}
      />
    </>
  );
}
