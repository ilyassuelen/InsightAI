import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Users, Pencil, Trash2, UserPlus, Loader2, Check, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Workspace } from '@/types/workspace';
import { MemberListItem } from './MemberListItem';

interface WorkspaceSettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workspace: Workspace | null;
  isOwner: boolean;
  onRename: (workspaceId: string, newName: string) => void;
  onDelete: (workspaceId: string) => void;
  onAddMember: (workspaceId: string, email: string, name?: string) => void;
  onRemoveMember: (workspaceId: string, memberId: string) => void;
}

export function WorkspaceSettingsModal({
  open,
  onOpenChange,
  workspace,
  isOwner,
  onRename,
  onDelete,
  onAddMember,
  onRemoveMember,
}: WorkspaceSettingsModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [newName, setNewName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [isInviting, setIsInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [removingMemberId, setRemovingMemberId] = useState<string | null>(null);

  if (!workspace) return null;

  const handleStartRename = () => {
    setNewName(workspace.name);
    setIsEditing(true);
  };

  const handleSaveRename = () => {
    const trimmed = newName.trim();
    if (trimmed && trimmed !== workspace.name) {
      onRename(workspace.id, trimmed);
    }
    setIsEditing(false);
  };

  const handleCancelRename = () => {
    setIsEditing(false);
    setNewName('');
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedEmail = inviteEmail.trim().toLowerCase();
    if (!trimmedEmail) {
      setInviteError('Email is required');
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setInviteError('Please enter a valid email address');
      return;
    }

    // Check if already a member
    if (workspace.members.some(m => m.email.toLowerCase() === trimmedEmail)) {
      setInviteError('This person is already a member');
      return;
    }

    setIsInviting(true);
    setInviteError(null);

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    try {
      onAddMember(workspace.id, trimmedEmail);
      setInviteEmail('');
    } catch (err) {
      setInviteError('Failed to invite member');
    } finally {
      setIsInviting(false);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    setRemovingMemberId(memberId);

    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    onRemoveMember(workspace.id, memberId);
    setRemovingMemberId(null);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg glass border-border/50">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg font-display">
            <Settings className="h-5 w-5 text-primary" />
            <span className="gradient-text">Workspace Settings</span>
          </DialogTitle>
          <DialogDescription className="text-muted-foreground text-sm">
            Manage your workspace and team members.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Workspace Name Section */}
          <div className="space-y-3">
            <Label className="text-sm font-medium text-foreground">
              Workspace Name
            </Label>

            {isEditing ? (
              <div className="flex items-center gap-2">
                <Input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="flex-1 bg-muted/50 border-border focus:border-primary"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveRename();
                    if (e.key === 'Escape') handleCancelRename();
                  }}
                />
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={handleSaveRename}
                  className="h-9 w-9 text-success hover:text-success hover:bg-success/10"
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={handleCancelRename}
                  className="h-9 w-9 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50">
                <span className="text-sm text-foreground">{workspace.name}</span>
                {isOwner && !workspace.isPersonal && (
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={handleStartRename}
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                )}
              </div>
            )}
          </div>

          <Separator className="bg-border/50" />

          {/* Members Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium text-foreground flex items-center gap-2">
                <Users className="h-4 w-4 text-primary" />
                Members ({workspace.members.length})
              </Label>
            </div>

            {/* Add Member Form - Owner Only */}
            {isOwner && !workspace.isPersonal && (
              <form onSubmit={handleInvite} className="flex gap-2">
                <div className="flex-1">
                  <Input
                    value={inviteEmail}
                    onChange={(e) => {
                      setInviteEmail(e.target.value);
                      setInviteError(null);
                    }}
                    placeholder="Enter email address"
                    className="bg-muted/50 border-border focus:border-primary"
                    disabled={isInviting}
                  />
                </div>
                <Button
                  type="submit"
                  disabled={isInviting || !inviteEmail.trim()}
                  className="gradient-bg glow-soft text-primary-foreground"
                >
                  {isInviting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <UserPlus className="h-4 w-4 mr-1.5" />
                      Invite
                    </>
                  )}
                </Button>
              </form>
            )}

            <AnimatePresence>
              {inviteError && (
                <motion.p
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -5 }}
                  className="text-xs text-destructive"
                >
                  {inviteError}
                </motion.p>
              )}
            </AnimatePresence>

            {/* Members List */}
            <ScrollArea className="h-[200px] pr-3">
              <div className="space-y-2">
                <AnimatePresence>
                  {workspace.members.map((member, index) => (
                    <motion.div
                      key={member.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <MemberListItem
                        member={member}
                        canRemove={isOwner && !workspace.isPersonal}
                        onRemove={handleRemoveMember}
                        isRemoving={removingMemberId === member.id}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>

                {workspace.members.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground text-sm">
                    No members yet. Invite someone to get started.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Delete Workspace - Owner Only, Non-Personal */}
          {isOwner && !workspace.isPersonal && (
            <>
              <Separator className="bg-border/50" />
              <div className="pt-2">
                <Button
                  variant="ghost"
                  onClick={() => {
                    if (confirm(`Are you sure you want to delete "${workspace.name}"? This action cannot be undone.`)) {
                      onDelete(workspace.id);
                      onOpenChange(false);
                    }
                  }}
                  className="w-full text-destructive hover:text-destructive hover:bg-destructive/10 border border-destructive/20"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Workspace
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
