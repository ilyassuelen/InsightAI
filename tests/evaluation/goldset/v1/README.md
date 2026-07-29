# InsightAI RAG-Goldstandard v1

## Umfang

Der Datensatz ist vollständig synthetisch und enthält:

- 6 Dokumente aus 6 fachlichen Genres
- 2 unterstützte Quelldateiformate: Markdown und TXT
- 36 stabile Quellstellen mit Dokument, Abschnitt, Zeilenbereich und exaktem Zitat
- 54 Fragen mit erwarteter Antwort, erforderlichen Fakten und Quellen
- dokumentweite und workspace-weite Fragen
- deutsche und englische Fragen
- Single-Hop-, Multi-Hop-, Vergleichs-, Rechen-, Listen-, Termin-, Richtlinien- und Negativfragen

## Dateien

- `manifest.json`: Version, Dokumente, Scope und geplante Metriken
- `documents/`: synthetischer Dokumentkorpus
- `sources.json`: normalisierte Goldquellen
- `questions.jsonl`: eine versionierbare Frage pro Zeile
- `tests/evaluation/validate_goldset.py`: Offline-Konsistenzprüfung

## Frageschema

Jede Frage besitzt:

- stabile ID
- Suchscope `document` oder `workspace`
- Workspace-ID und erwartete relevante Dokument-IDs
- Sprache und Fragetyp
- natürliche Frage
- Kennzeichnung, ob sie beantwortbar ist
- erwartete Referenzantwort
- atomare erforderliche Fakten
- normalisierte Quellen-IDs
- Auswertungstags

Bei `document` bezeichnet `document_ids` das direkt abgefragte Dokument. Bei `workspace` bezeichnet das Feld die Dokumente, aus denen die Goldquellen erwartet werden; gesucht wird trotzdem im vollständigen Korpus des angegebenen Workspaces.

## Quellenvertrag

Eine Goldquelle verweist auf genau ein Korpusdokument und enthält:

- stabile Quellen-ID
- Dokument-ID
- Abschnittsname
- einsbasierten Start- und Endzeilenindex
- exaktes Zitat

Der Validator vergleicht jedes Zitat bytegenau mit dem angegebenen Zeilenbereich. Änderungen am Korpus können dadurch keine stillen, veralteten Quellenreferenzen hinterlassen.

## Validierung

Vom Projektstamm aus:

```bash
.venv/bin/python tests/evaluation/validate_goldset.py
```

Oder über die Backend-Suite:

```bash
.venv/bin/python -m unittest tests.backend.test_rag_goldset -v
```

Die Validierung führt keine OpenAI-, Gemini-, Qdrant-, R2- oder Langfuse-Aufrufe aus.

## Noch nicht enthalten

Der Goldstandard definiert die Soll-Daten, misst aber noch keine Retrieval- oder Antwortmetrik. Der nächste getrennte Schritt ist ein Evaluationsrunner für Recall@K, Precision@K, MRR, Faithfulness, Antwortrelevanz und Quellenkorrektheit. Ergebnisse müssen nach Dokument- und Workspace-Scope sowie nach Fragetyp getrennt ausgewiesen werden.
