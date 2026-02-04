export type WorkspaceRole = "owner" | "member";

export interface WorkspaceMember {
  id: string;
  userId: string;
  name: string;
  email: string;
  avatarUrl?: string;
  role: WorkspaceRole;
  joinedAt: Date;
}

export interface Workspace {
  id: string;
  name: string;
  isPersonal: boolean;
  createdAt: Date;
  members: WorkspaceMember[];

  currentUserRole: WorkspaceRole;
}

export type WorkspaceMemberStored = Omit<WorkspaceMember, "joinedAt"> & { joinedAt: string };
export type WorkspaceStored = Omit<Workspace, "createdAt" | "members"> & {
  createdAt: string;
  members: WorkspaceMemberStored[];
};

export interface WorkspaceState {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  isLoading: boolean;
  error: string | null;
}