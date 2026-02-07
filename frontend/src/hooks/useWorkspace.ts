import { useState, useEffect, useCallback } from "react";
import type { Workspace, WorkspaceMember } from "@/types/workspace";
import { apiFetch } from "@/lib/api";

/* ---------------- API Types ---------------- */

type WorkspaceApi = {
  id: number;
  name: string;
  type: "personal" | "team";
  owner_user_id: number;
};

type MemberApi = {
  user_id: number;
  email: string;
  full_name?: string | null;
  role: "owner" | "member";
};

type MeApi = {
  id: number;
  email: string;
  full_name?: string | null;
};

/* ---------------- Hook ---------------- */

export function useWorkspace() {
  const [me, setMe] = useState<MeApi | null>(null);

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] =
    useState<Workspace | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const meId = me?.id ?? null;
  const currentWorkspaceId = currentWorkspace?.id ?? null;

  /* ---------------- Load Me ---------------- */

  const loadMe = useCallback(async () => {
    const res = await apiFetch("/auth/me");

    if (!res.ok) throw new Error("Not authenticated");

    const data: MeApi = await res.json();
    setMe(data);
  }, []);

  /* ---------------- Load Workspaces ---------------- */

  const loadWorkspaces = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      await loadMe();

      const res = await apiFetch("/workspaces");

      if (!res.ok) throw new Error("Failed to load workspaces");

      const data: WorkspaceApi[] = await res.json();

      const mapped: Workspace[] = data.map((w) => ({
        id: String(w.id),
        name: w.name,
        isPersonal: w.type === "personal",
        createdAt: new Date(),
        members: [],
        currentUserRole: "member",
      }));

      setWorkspaces(mapped);

      const personal = mapped.find((w) => w.isPersonal);

      setCurrentWorkspace(personal || mapped[0] || null);
    } catch (err) {
      console.error(err);
      setError("Failed to load workspaces");
      setWorkspaces([]);
      setCurrentWorkspace(null);
      setMe(null);
    } finally {
      setIsLoading(false);
    }
  }, [loadMe]);

  /* ---------------- Load Members ---------------- */

  const loadMembers = useCallback(
    async (workspaceId: string, userId: number) => {
      try {
        const res = await apiFetch(`/workspaces/${workspaceId}/members`);

        if (res.status === 401) return;
        if (!res.ok) throw new Error("Failed to load members");

        const data: MemberApi[] = await res.json();

        const members: WorkspaceMember[] = data.map((m) => ({
          id: String(m.user_id),
          userId: String(m.user_id),
          name: m.full_name || m.email.split("@")[0],
          email: m.email,
          role: m.role,
          joinedAt: new Date(),
        }));

        const myRole = data.find((m) => m.user_id === userId)?.role || "member";

        setWorkspaces((prev) =>
          prev.map((w) =>
            w.id === workspaceId
              ? {
                  ...w,
                  members,
                  currentUserRole: myRole,
                }
              : w
          )
        );

        setCurrentWorkspace((prev) =>
          prev && prev.id === workspaceId
            ? {
                ...prev,
                members,
                currentUserRole: myRole,
              }
            : prev
        );
      } catch (err) {
        console.error(err);
      }
    },
    []
  );

  /* ---------------- Init ---------------- */

  useEffect(() => {
    loadWorkspaces();
  }, [loadWorkspaces]);

  useEffect(() => {
    if (currentWorkspaceId && meId) {
      void loadMembers(currentWorkspaceId, meId);
    }
  }, [currentWorkspaceId, meId, loadMembers]);

  /* ---------------- Switch ---------------- */

  const switchWorkspace = useCallback(
    (workspaceId: string) => {
      const ws = workspaces.find((w) => w.id === workspaceId);

      if (ws) setCurrentWorkspace(ws);
    },
    [workspaces]
  );

  /* ---------------- Create ---------------- */

  const createWorkspace = useCallback(
    async (name: string) => {
      const res = await apiFetch("/workspaces", {
        method: "POST",
        body: JSON.stringify({ name }),
      });

      if (!res.ok) throw new Error("Create failed");

      await loadWorkspaces();
    },
    [loadWorkspaces]
  );

  /* ---------------- Rename ---------------- */

  const renameWorkspace = useCallback(
    async (workspaceId: string, name: string) => {
      const res = await apiFetch(
        `/workspaces/${workspaceId}`,
        {
          method: "PATCH",
          body: JSON.stringify({ name }),
        }
      );

      if (!res.ok) throw new Error("Rename failed");

      await loadWorkspaces();
    },
    [loadWorkspaces]
  );

  /* ---------------- Delete ---------------- */

  const deleteWorkspace = useCallback(
    async (workspaceId: string) => {
      const res = await apiFetch(
        `/workspaces/${workspaceId}`,
        { method: "DELETE" }
      );

      if (!res.ok) throw new Error("Delete failed");

      await loadWorkspaces();
    },
    [loadWorkspaces]
  );

  /* ---------------- Add Member ---------------- */

  const addMember = useCallback(
    async (workspaceId: string, email: string) => {
      const res = await apiFetch(
        `/workspaces/${workspaceId}/members`,
        {
          method: "POST",
          body: JSON.stringify({ email }),
        }
      );

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Invite failed");
      }

      if (meId) await loadMembers(workspaceId, meId);
    },
    [loadMembers, meId]
  );

  /* ---------------- Remove Member ---------------- */

  const removeMember = useCallback(
    async (workspaceId: string, memberId: string) => {
      const res = await apiFetch(
        `/workspaces/${workspaceId}/members/${memberId}`,
        { method: "DELETE" }
      );

      if (!res.ok) throw new Error("Remove failed");

      if (meId) await loadMembers(workspaceId, meId);
    },
    [loadMembers, meId]
  );

  /* ---------------- Owner Check ---------------- */

  const isOwner =
    currentWorkspace?.currentUserRole === "owner";

  const resetWorkspaceState = useCallback(() => {
    // Clears stale workspace/me state on logout or auth failure
    setMe(null);
    setWorkspaces([]);
    setCurrentWorkspace(null);
    setError(null);
    setIsLoading(false);
  }, []);

  /* ---------------- API ---------------- */

  return {
    workspaces,
    currentWorkspace,
    isLoading,
    error,
    isOwner,

    switchWorkspace,
    createWorkspace,
    renameWorkspace,
    deleteWorkspace,
    addMember,
    removeMember,

    reloadWorkspaces: loadWorkspaces,
    resetWorkspaceState,
  };
}
