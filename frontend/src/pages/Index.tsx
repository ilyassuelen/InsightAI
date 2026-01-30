import { useState } from "react";
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

import { useDocuments } from "@/hooks/useDocuments";
import { cn } from "@/lib/utils";
import { useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { isAuthenticated, clearAccessToken } from "@/lib/auth";

type AppView = "landing" | "app";

const Index = () => {
  const [view, setView] = useState<AppView>("landing");
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showChat, setShowChat] = useState(false);

  const {
    documents,
    setDocuments,
    selectedDocument,
    report,
    isLoading,
    uploadDocument,
    selectDocument,
    error,
    refreshDocuments,
    resetState,
  } = useDocuments();

  // Auto-login on refresh (if token exists and /auth/me passes)
  useEffect(() => {
    const boot = async () => {
      if (!isAuthenticated()) return;
      try {
        const res = await apiFetch("/auth/me");
        if (res.ok) {
          setView("app");
          resetState();
          await refreshDocuments();
        } else {
          clearAccessToken();
          resetState();
        }
      } catch {
        clearAccessToken();
        resetState();
      }
    };
    boot();
  }, [refreshDocuments, resetState]);

  const handleStartAgent = () => setShowAuthModal(true);

  const handleAuthenticated = async () => {
    setShowAuthModal(false);
    setView("app");
    resetState();
    await refreshDocuments();
  };

  const handleLogout = () => {
    clearAccessToken();
    resetState();
    setShowChat(false);
    setSidebarOpen(true);
    setView("landing");
  };

  // -------------------- LANDING --------------------
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

  // -------------------- APP DASHBOARD --------------------
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} onLogout={handleLogout} />

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 300, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="hidden lg:block shrink-0 overflow-hidden"
            >
              <DocumentSidebar
                documents={documents}
                setDocuments={setDocuments}
                selectedDocument={selectedDocument}
                onSelectDocument={selectDocument}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Mobile sidebar overlay */}
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
                initial={{ x: -300 }}
                animate={{ x: 0 }}
                exit={{ x: -300 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="absolute left-0 top-0 bottom-0 w-[300px] shadow-2xl shadow-primary/10"
              >
                <DocumentSidebar
                  documents={documents}
                  setDocuments={setDocuments}
                  selectedDocument={selectedDocument}
                  onSelectDocument={(doc) => {
                    selectDocument(doc); // doc kann null sein ✅
                    setSidebarOpen(false);
                  }}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <main className="flex-1 flex overflow-hidden">
          <div
            className={cn(
              "flex-1 overflow-y-auto p-6 lg:p-8 transition-all relative",
              showChat && "lg:mr-0"
            )}
          >
            {/* Background decoration */}
            <div className="absolute inset-0 ai-dots opacity-10 pointer-events-none" />

            <div className="max-w-4xl mx-auto space-y-10 relative z-10">
              {/* Upload Section */}
              <section>
                <UploadZone onUpload={uploadDocument} />
                {error && <p className="text-xs text-error mt-3">{error}</p>}
              </section>

              {/* Process Steps */}
              <section>
                <div className="flex items-center gap-2 mb-6">
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider px-4">
                    How it works
                  </span>
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                </div>

                <ProcessSteps />
              </section>

              {/* Report Section */}
              <section>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <div className="h-px w-8 bg-gradient-to-r from-transparent to-border" />
                    <h2 className="text-sm font-display font-semibold text-muted-foreground uppercase tracking-wider">
                      Report
                    </h2>
                  </div>

                  <button
                    onClick={() => setShowChat(!showChat)}
                    className={cn(
                      "flex items-center gap-2 text-xs px-4 py-2 rounded-lg transition-all duration-200",
                      showChat
                        ? "gradient-bg text-primary-foreground glow-soft"
                        : "glass hover:border-primary/30 text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {showChat ? "Hide Chat" : "Show Chat"}
                  </button>
                </div>

                <div className="rounded-2xl glass-strong p-8">
                  <ReportViewer
                    report={report}
                    isLoading={isLoading}
                    documentName={selectedDocument?.name}
                  />
                </div>
              </section>
            </div>
          </div>

          {/* Chat Panel */}
          <AnimatePresence>
            {showChat && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 350, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="hidden lg:block shrink-0 overflow-hidden"
              >
                <ChatPreview
                  documentId={selectedDocument?.id != null ? String(selectedDocument.id) : undefined}
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