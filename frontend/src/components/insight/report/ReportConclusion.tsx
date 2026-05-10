import { CheckCircle } from "lucide-react";

interface ReportConclusionProps {
  conclusion: string;
}

export function ReportConclusion({ conclusion }: ReportConclusionProps) {
  return (
    <section
      id="conclusion"
      className="scroll-mt-28 rounded-[32px] border border-white/10 bg-gradient-to-br from-white/[0.03] to-primary/10 p-8"
    >
      <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-xs font-medium uppercase tracking-[0.2em] text-primary">
        <CheckCircle className="h-4 w-4" />
        Conclusion
      </div>

      <p className="max-w-4xl text-[15px] leading-8 text-white/75">
        {conclusion}
      </p>
    </section>
  );
}