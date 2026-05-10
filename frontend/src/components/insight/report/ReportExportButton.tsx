import { Download } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReportExportButtonProps {
  targetId: string;
  filename: string;
  disabled?: boolean;
}

export function ReportExportButton({
  targetId,
  filename,
  disabled,
}: ReportExportButtonProps) {
  const handleExport = () => {
    const reportElement = document.getElementById(targetId);
    if (!reportElement) return;

    const printWindow = window.open("", "_blank", "width=1200,height=900");
    if (!printWindow) return;

    const safeTitle = filename.replace(/[<>:"/\\|?*]+/g, "-");

    printWindow.document.write(`
      <!doctype html>
      <html>
        <head>
          <title>${safeTitle}</title>
          <style>
            body {
              margin: 0;
              padding: 32px;
              background: #ffffff;
              color: #111827;
              font-family: Inter, Arial, sans-serif;
            }

            * {
              box-sizing: border-box;
            }

            .no-print {
              display: none !important;
            }

            h1, h2, h3, h4, p {
              color: #111827 !important;
            }

            pre {
              white-space: pre-wrap;
              font-family: Inter, Arial, sans-serif;
              color: #111827 !important;
            }

            button {
              display: none !important;
            }

            section, div {
              break-inside: avoid;
            }

            @media print {
              body {
                padding: 24px;
              }
            }
          </style>
        </head>
        <body>
          ${reportElement.innerHTML}
          <script>
            window.onload = function () {
              window.print();
            };
          </script>
        </body>
      </html>
    `);

    printWindow.document.close();
  };

  return (
    <button
      onClick={handleExport}
      disabled={disabled}
      className={cn(
        "inline-flex h-11 items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-4 text-sm font-medium text-white/70 transition-all",
        "hover:border-primary/30 hover:bg-primary/10 hover:text-white",
        "disabled:cursor-not-allowed disabled:opacity-40"
      )}
    >
      <Download className="h-4 w-4" />
      Export PDF
    </button>
  );
}