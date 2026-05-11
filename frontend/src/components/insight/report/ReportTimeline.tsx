import { CalendarDays } from "lucide-react";
import type { TimelineEvent } from "@/types/report";

interface ReportTimelineProps {
  timeline: TimelineEvent[];
}

export function ReportTimeline({ timeline }: ReportTimelineProps) {
  if (!timeline.length) return null;

  return (
    <section id="timeline" className="scroll-mt-28">
      <div className="mb-5 flex items-center gap-2">
        <CalendarDays className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold text-white">Timeline</h3>
      </div>

      <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-7 backdrop-blur-xl">
        <div className="space-y-6">
          {timeline.map((event, index) => (
            <div key={`${event.label}-${index}`} className="relative flex gap-4">
              <div className="flex flex-col items-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary/20 bg-primary/10 text-xs font-semibold text-primary">
                  {index + 1}
                </div>

                {index < timeline.length - 1 && (
                  <div className="mt-3 h-full w-px bg-white/10" />
                )}
              </div>

              <div className="pb-4">
                <p className="mb-1 text-xs font-medium uppercase tracking-[0.18em] text-primary">
                  {event.label}
                </p>

                <h4 className="mb-2 text-base font-semibold text-white">
                  {event.title}
                </h4>

                {event.description && (
                  <p className="text-sm leading-7 text-white/60">
                    {event.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}