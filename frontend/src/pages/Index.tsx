import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { HeroSection } from "@/components/landing/HeroSection";
import { WorkflowSection } from "@/components/landing/WorkflowSection";
import { TechSlider } from "@/components/landing/TechSlider";
import { Footer } from "@/components/landing/Footer";
import { AuthModal } from "@/components/landing/AuthModal";
import { LandingHeader } from "@/components/landing/LandingHeader";

import { Header } from "@/components/insight/Header";
import { DocumentSidebar } from "@/components/insight/DocumentSidebar";
import { UploadZone } from "@/components/insight/UploadZone";
import { ProcessSteps } from "@/components/insight/ProcessSteps";
import { ReportViewer } from "@/components/insight/ReportViewer";
import { ChatPreview } from "@/components/insight/ChatPreview";
import { DashboardHero } from "@/components/insight/DashboardHero";

import { useDocuments } from "@/hooks/useDocuments";
import { useWorkspace } from "@/hooks/useWorkspace";
import { cn } from "@/lib/utils";
import { apiFetch } from "@/lib/api";
import { isAuthenticated, clearAccessToken } from "@/lib/auth";

type AppView = "landing" | "app";

const Index = () => {
  const [view, setView] = useState<AppView>("landing");
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showChat, setShowChat] = useState(false);

  const {
    workspaces,
    currentWorkspace,
    isOwner,
    switchWorkspace,
    createWorkspace,
    renameWorkspace,
    deleteWorkspace,
    addMember,
    removeMember,
    reloadWorkspaces,
    resetWorkspaceState,
  } = useWorkspace();

  const {
    documents,
    setDocuments,
    selectedDocument,
    report,
    isLoading,
    uploadDocument,
    selectDocument,
    error,
    transferDocument,
    resetState,
  } = useDocuments(currentWorkspace?.id);

  useEffect(() => {
    const boot = async () => {
      if (!isAuthenticated()) return;

      try {
        const res = await apiFetch("/auth/me");

        if (res.ok) {
          setView("app");
          resetState();
          await reloadWorkspaces();
        } else {
          clearAccessToken();
          resetState();
          resetWorkspaceState();
        }
      } catch {
        clearAccessToken();
        resetState();
        resetWorkspaceState();
      }
    };

    boot();
  }, [resetState, reloadWorkspaces, resetWorkspaceState]);

  const handleStartAgent = () => setShowAuthModal(true);

  const handleAuthenticated = async () => {
    setShowAuthModal(false);
    setView("app");
    resetState();
    await reloadWorkspaces();
  };

  const handleLogout = () => {
    clearAccessToken();
    resetState();
    resetWorkspaceState();
    setShowChat(false);
    setSidebarOpen(true);
    setView("landing");
  };

  const handleWorkspaceSwitch = (workspaceId: string) => {
    resetState();
    switchWorkspace(workspaceId);
  };

  const handleCreateWorkspace = async (name: string) => {
    resetState();
    await createWorkspace(name);
  };

  const handleDeleteWorkspace = async (workspaceId: string) => {
    resetState();
    await deleteWorkspace(workspaceId);
  };

  if (view === "landing") {
    return (
      <div className="min-h-screen bg-background">
        <LandingHeader onStartAgent={handleStartAgent} />
        <HeroSection onStartAgent={handleStartAgent} />
        <WorkflowSection />
        <TechSlider />
        <Footer />

        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          onAuthenticated={handleAuthenticated}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
        onLogout={handleLogout}
        workspaces={workspaces}
        currentWorkspace={currentWorkspace}
        isWorkspaceOwner={isOwner}
        onSwitchWorkspace={handleWorkspaceSwitch}
        onCreateWorkspace={handleCreateWorkspace}
        onRenameWorkspace={renameWorkspace}
        onDeleteWorkspace={handleDeleteWorkspace}
        onAddMember={addMember}
        onRemoveMember={removeMember}
      />

      <div className="flex flex-1 overflow-hidden">
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="hidden lg:block shrink-0 overflow-hidden"
            >
              <DocumentSidebar
                documents={documents}
                setDocuments={setDocuments}
                selectedDocument={selectedDocument}
                onSelectDocument={selectDocument}
                currentWorkspace={currentWorkspace}
                workspaces={workspaces}
                onTransferDocument={transferDocument}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-40"
            >
              <div
                className="absolute inset-0 bg-background/90 backdrop-blur-md"
                onClick={() => setSidebarOpen(false)}
              />
              <motion.div
                initial={{ x: -320 }}
                animate={{ x: 0 }}
                exit={{ x: -320 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="absolute left-0 top-0 bottom-0 w-[320px] shadow-2xl shadow-primary/10"
              >
                <DocumentSidebar
                  documents={documents}
                  setDocuments={setDocuments}
                  selectedDocument={selectedDocument}
                  onSelectDocument={(doc) => {
                    selectDocument(doc);
                    setSidebarOpen(false);
                  }}
                  currentWorkspace={currentWorkspace}
                  workspaces={workspaces}
                  onTransferDocument={transferDocument}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <main className="flex-1 flex overflow-hidden">
          <div
            className={cn(
              "relative flex-1 overflow-y-auto p-4 transition-all sm:p-6 lg:p-8",
              showChat && "lg:mr-0"
            )}
          >
            <div className="pointer-events-none absolute inset-0 ai-grid opacity-40" />
            <div className="pointer-events-none absolute -top-40 left-1/4 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
            <div className="pointer-events-none absolute bottom-0 right-10 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />

            <div className="relative z-10 mx-auto max-w-7xl space-y-8">
              <DashboardHero
                documents={documents}
                currentWorkspace={currentWorkspace}
                showChat={showChat}
                onToggleChat={() => setShowChat(!showChat)}
              />

              <div className="grid gap-8 xl:grid-cols-[1.05fr_0.95fr]">
                <section className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-[0.2em] text-primary">
                        New analysis
                      </p>
                      <h2 className="mt-1 font-display text-xl font-semibold text-foreground">
                        Upload source material
                      </h2>
                    </div>
                  </div>

                  <UploadZone onUpload={uploadDocument} />
                  {error && (
                    <p className="rounded-xl border border-error/20 bg-error/10 px-4 py-3 text-xs text-error">
                      {error}
                    </p>
                  )}
                </section>

                <section className="space-y-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-primary">
                      Pipeline
                    </p>
                    <h2 className="mt-1 font-display text-xl font-semibold text-foreground">
                      How InsightAI processes files
                    </h2>
                  </div>

                  <ProcessSteps />
                </section>
              </div>

              <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-card/90 via-card/70 to-primary/5 p-5 shadow-2xl shadow-primary/5 backdrop-blur-xl lg:p-8">
                  <div className="pointer-events-none absolute inset-0 ai-grid opacity-25" />
                  <div className="pointer-events-none absolute -top-32 right-10 h-72 w-72 rounded-full bg-primary/15 blur-3xl" />
                  <div className="pointer-events-none absolute -bottom-32 left-10 h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl" />

                  <div className="relative z-10 mb-6 flex flex-wrap items-end justify-between gap-4">
                    <div>
                        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary">
                            Report Section
                        </div>

                        <h2 className="font-display text-2xl font-semibold text-foreground">
                            Structured report
                        </h2>

                        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                            Review the generated analysis, key figures and detailed findings from your selected document.
                        </p>
                    </div>

                    {selectedDocument && (
                        <div className="rounded-2xl border border-border/60 bg-background/40 px-4 py-3 text-sm text-muted-foreground">
                            Source:{" "}
                            <span className="font-medium text-foreground">
                                {selectedDocument.filename}
                            </span>
                        </div>
                    )}
                  </div>

                  <div className="relative z-10 overflow-hidden rounded-2xl border border-white/10 bg-background/35 p-4 backdrop-blur-xl lg:p-6">
                    <ReportViewer
                      report={report}
                      isLoading={isLoading}
                      documentName={selectedDocument?.filename}
                    />
                  </div>
              </section>
            </div>
          </div>

          <AnimatePresence>
            {showChat && (
                <motion.div
                  initial={{ opacity: 0, y: 24, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 24, scale: 0.96 }}
                  transition={{ duration: 0.25, ease: "easeOut" }}
                  className="fixed bottom-4 right-4 z-50 h-[min(620px,calc(100vh-7rem))] w-[min(420px,calc(100vw-2rem))] overflow-hidden rounded-3xl border border-white/10 bg-card/90 shadow-2xl shadow-primary/20 backdrop-blur-xl lg:bottom-6 lg:right-6"
                >
                    <ChatPreview
                        workspaceId={currentWorkspace?.id}
                        onClose={() => setShowChat(false)}
                    />
                </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default Index;