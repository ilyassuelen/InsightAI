import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Header } from '@/components/insight/Header';
import { DocumentSidebar } from '@/components/insight/DocumentSidebar';
import { UploadZone } from '@/components/insight/UploadZone';
import { ProcessSteps } from '@/components/insight/ProcessSteps';
import { ReportViewer } from '@/components/insight/ReportViewer';
import { ChatPreview } from '@/components/insight/ChatPreview';
import { useDocuments } from '@/hooks/useDocuments';
import { cn } from '@/lib/utils';

const Index = () => {
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
    error
  } = useDocuments();

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
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
                className="absolute inset-0 bg-background/80 backdrop-blur-sm"
                onClick={() => setSidebarOpen(false)}
              />
              <motion.div
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className="absolute left-0 top-0 bottom-0 w-[280px] shadow-xl"
              >
                <DocumentSidebar
                  documents={documents}
                  setDocuments={setDocuments}
                  selectedDocument={selectedDocument}
                  onSelectDocument={(doc) => {
                    selectDocument(doc);
                    setSidebarOpen(false);
                  }}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <main className="flex-1 flex overflow-hidden">
          <div className={cn(
            "flex-1 overflow-y-auto p-6 lg:p-8 transition-all",
            showChat && "lg:mr-0"
          )}>
            <div className="max-w-4xl mx-auto space-y-8">
              {/* Upload Section */}
              <section>
                <UploadZone onUpload={uploadDocument} />
                {error && (
                  <p className="text-xs text-error mt-2">{error}</p>
                )}
              </section>

              {/* Process Steps */}
              <section>
                <ProcessSteps status={selectedDocument?.status} />
              </section>

              {/* Report Section */}
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Report
                  </h2>
                  <button
                    onClick={() => setShowChat(!showChat)}
                    className={cn(
                      "text-xs px-3 py-1.5 rounded-lg transition-colors",
                      showChat
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {showChat ? 'Hide Chat' : 'Show Chat'}
                  </button>
                </div>

                <div className="bg-card rounded-xl border border-border p-6">
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
                animate={{ width: 320, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="hidden lg:block shrink-0 overflow-hidden"
              >
                <ChatPreview documentId={selectedDocument?.id ?? ''} />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

export default Index;