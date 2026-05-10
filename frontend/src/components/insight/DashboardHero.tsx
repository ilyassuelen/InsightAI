import { motion } from "framer-motion";
import {
  Sparkles,
  FileText,
  CheckCircle,
  Layers,
  MessageSquare,
  Users,
} from "lucide-react";

import type { Document } from "@/types/document";
import type { Workspace } from "@/types/workspace";
import { cn } from "@/lib/utils";

interface DashboardHeroProps {
  documents: Document[];
  currentWorkspace: Workspace | null;
  showChat: boolean;
  onToggleChat: () => void;
}

export function DashboardHero({
  documents,
  currentWorkspace,
  showChat,
  onToggleChat,
}: DashboardHeroProps) {
  const completedDocuments = documents.filter(
    (doc) => doc.file_status === "completed"
  ).length;

  const activeDocuments = documents.filter(
    (doc) =>
      doc.file_status !== "completed" &&
      doc.file_status !== "failed" &&
      doc.file_status !== "parsed_empty"
  ).length;

  const failedDocuments = documents.filter(
    (doc) => doc.file_status === "failed"
  ).length;

  const stats = [
    {
      label: "Documents",
      value: documents.length,
      icon: FileText,
      tone: "from-violet-500/20 to-fuchsia-500/10 text-violet-300",
    },
    {
      label: "Completed",
      value: completedDocuments,
      icon: CheckCircle,
      tone: "from-emerald-500/20 to-teal-500/10 text-emerald-300",
    },
    {
      label: "Processing",
      value: activeDocuments,
      icon: Layers,
      tone: "from-cyan-500/20 to-blue-500/10 text-cyan-300",
    },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-card/90 via-card/70 to-primary/10 p-6 lg:p-8 shadow-2xl shadow-primary/10"
    >
      <div className="absolute inset-0 ai-grid opacity-40" />
      <div className="absolute -top-32 -right-24 h-72 w-72 rounded-full bg-primary/25 blur-3xl" />
      <div className="absolute -bottom-32 -left-20 h-72 w-72 rounded-full bg-cyan-500/15 blur-3xl" />

      <div className="relative z-10 grid gap-8 lg:grid-cols-[1.4fr_1fr] lg:items-center">
        <div>
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium text-primary">
            <Sparkles className="h-4 w-4" />
            Workspace active
          </div>

          <h1 className="font-display text-3xl font-semibold tracking-tight text-foreground lg:text-4xl">
            Analyze documents with{" "}
            <span className="gradient-text">structured intelligence.</span>
          </h1>

          <p className="mt-4 max-w-2xl text-sm leading-7 text-muted-foreground lg:text-base">
            Upload documents, generate grounded reports, collaborate in team
            workspaces and ask questions directly against your sources.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl border border-border/60 bg-background/40 px-4 py-2 text-sm text-muted-foreground">
              {currentWorkspace?.isPersonal ? (
                <FileText className="h-4 w-4 text-primary" />
              ) : (
                <Users className="h-4 w-4 text-primary" />
              )}
              <span>
                Workspace:{" "}
                <span className="font-medium text-foreground">
                  {currentWorkspace?.name ?? "Personal"}
                </span>
              </span>
            </div>

            {failedDocuments > 0 && (
              <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-300">
                {failedDocuments} failed
              </div>
            )}

            <button
              onClick={onToggleChat}
              className={cn(
                "flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200",
                showChat
                  ? "gradient-bg text-primary-foreground shadow-lg shadow-primary/20"
                  : "border border-border/60 bg-background/40 text-muted-foreground hover:border-primary/30 hover:text-foreground"
              )}
            >
              <MessageSquare className="h-4 w-4" />
              {showChat ? "Hide Chat" : "Open Chat"}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              whileHover={{ y: -4 }}
              className="rounded-2xl border border-white/10 bg-background/35 p-4 backdrop-blur-xl"
            >
              <div
                className={cn(
                  "mb-4 inline-flex rounded-xl bg-gradient-to-br p-2",
                  stat.tone
                )}
              >
                <stat.icon className="h-4 w-4" />
              </div>

              <div className="text-2xl font-semibold text-foreground">
                {stat.value}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.section>
  );
}
