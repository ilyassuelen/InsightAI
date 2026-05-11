from typing import List
from backend.services.reporting.report_schema import ReportChart, ChartDataPoint


def validate_charts(charts: List[ReportChart]) -> List[ReportChart]:
    valid_charts: List[ReportChart] = []

    for chart in charts or []:
        if not chart.title or not chart.data:
            continue

        clean_points: List[ChartDataPoint] = []

        for point in chart.data:
            if not point.label:
                continue

            try:
                value = float(point.value)
            except (TypeError, ValueError):
                continue

            clean_points.append(
                ChartDataPoint(
                    label=str(point.label)[:80],
                    value=value,
                )
            )

        if len(clean_points) < 2:
            continue

        valid_charts.append(
            ReportChart(
                title=chart.title[:120],
                type=chart.type if chart.type in ["bar", "line", "pie"] else "bar",
                unit=chart.unit or "",
                data=clean_points[:12],
            )
        )

    return valid_charts[:3]
