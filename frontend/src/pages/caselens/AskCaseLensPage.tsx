import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import {
  FileText,
  Search,
  Sparkles,
  Send,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Shield,
  Layers,
  ArrowRight,
  ExternalLink,
  Info,
  Maximize2,
  RefreshCw,
  Hash,
} from 'lucide-react';
import { caselensApi } from '../../services/caselensApi';
import {
  DocumentMetadata,
  DocumentChunk,
  QuestionAnswerResponse,
  Citation,
} from '../../types/caselens';

export const AskCaseLensPage: React.FC = () => {
  const { currentWs } = useOutletContext<{ currentWs: string }>();
  const [searchParams] = useSearchParams();

  // Document viewer state (Left Panel)
  const [docs, setDocs] = useState<DocumentMetadata[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [docChunks, setDocChunks] = useState<DocumentChunk[]>([]);
  const [selectedPage, setSelectedPage] = useState<number>(1);
  const [docSearch, setDocSearch] = useState<string>('');
  const [activeHighlightSnippet, setActiveHighlightSnippet] = useState<string | null>(null);

  // Q&A state (Right Panel)
  const [question, setQuestion] = useState<string>('');
  const [asking, setAsking] = useState<boolean>(false);
  const [currentQA, setCurrentQA] = useState<QuestionAnswerResponse | null>(null);
  const [qaHistory, setQaHistory] = useState<QuestionAnswerResponse[]>([]);
  const [showVerificationPanel, setShowVerificationPanel] = useState<boolean>(true);

  const documentViewerRef = useRef<HTMLDivElement>(null);

  // Suggested prompt questions
  const suggestedQueries = [
    'What is the base retainer fee and payment frequency?',
    'What is the notice period required for termination without cause?',
    'What SLA availability percentage is required?',
    'What are the specific penalties and tariffs for quantum computing export violations?',
  ];

  useEffect(() => {
    loadInitialData();
  }, [currentWs]);

  // Handle URL query parameter if launched from overview scenario
  useEffect(() => {
    const qParam = searchParams.get('q');
    if (qParam) {
      setQuestion(qParam);
      handleAsk(qParam);
    }
  }, [searchParams]);

  const loadInitialData = async () => {
    try {
      const [docList, history] = await Promise.all([
        caselensApi.listDocuments(currentWs),
        caselensApi.getQAHistory(currentWs),
      ]);
      setDocs(docList);
      setQaHistory(history);

      if (history.length > 0) {
        setCurrentQA(history[0]);
      }

      if (docList.length > 0) {
        const initialDocId = docList[0].document_id;
        setSelectedDocId(initialDocId);
        loadDocChunks(initialDocId);
      }
    } catch (e) {
      console.error('Failed to load QA initial data', e);
    }
  };

  const loadDocChunks = async (docId: string) => {
    try {
      const chunks = await caselensApi.getDocumentChunks(docId);
      setDocChunks(chunks);
      setSelectedPage(1);
    } catch (e) {
      console.error('Failed to load doc chunks', e);
    }
  };

  const handleDocSelect = (docId: string) => {
    setSelectedDocId(docId);
    loadDocChunks(docId);
    setActiveHighlightSnippet(null);
  };

  const handleAsk = async (queryText?: string) => {
    const promptToAsk = queryText || question;
    if (!promptToAsk.trim() || asking) return;

    setAsking(true);
    try {
      const resp = await caselensApi.askQuestion(currentWs, promptToAsk, undefined, true);
      setCurrentQA(resp);
      setQaHistory(prev => [resp, ...prev]);

      // If answer has citations, jump to top citation automatically
      if (resp.citations.length > 0) {
        handleCitationClick(resp.citations[0]);
      }
    } catch (e: any) {
      alert('Error during Q&A: ' + e.message);
    } finally {
      setAsking(false);
    }
  };

  // Citation Click -> Jump to page, document, and highlight passage
  const handleCitationClick = async (citation: Citation) => {
    if (citation.document_id !== selectedDocId) {
      setSelectedDocId(citation.document_id);
      await loadDocChunks(citation.document_id);
    }
    setSelectedPage(citation.page_number);
    setActiveHighlightSnippet(citation.quoted_text);

    // Scroll viewer to top or highlighted element
    if (documentViewerRef.current) {
      documentViewerRef.current.scrollTop = 0;
    }
  };

  const currentDocObj = docs.find(d => d.document_id === selectedDocId);
  const totalPages = currentDocObj ? currentDocObj.page_count : 1;
  const pageChunks = docChunks.filter(c => c.page_number === selectedPage);

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-4">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--text-primary)] flex items-center gap-2">
            <span>Ask CaseLens</span>
            <span className="text-xs font-normal text-[var(--text-muted)]">
              — Split-Pane Document Intelligence
            </span>
          </h1>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-[var(--text-muted)]">Grounding Mode:</span>
          <span className="px-2.5 py-1 rounded-full bg-blue-600/10 text-blue-600 dark:text-blue-400 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            Verified Source Provenance
          </span>
        </div>
      </div>

      {/* Main Split-Pane Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0 overflow-hidden">
        {/* ================= LEFT PANEL: Document Viewer ================= */}
        <div className="lg:col-span-6 h-full flex flex-col rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-xs">
          {/* Document Header Controls */}
          <div className="p-3 border-b border-[var(--border-color)] bg-[var(--bg-input)]/50 flex flex-wrap items-center justify-between gap-2 shrink-0">
            {/* Document Selector */}
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <FileText className="w-4 h-4 text-blue-600 shrink-0" />
              <select
                value={selectedDocId}
                onChange={(e) => handleDocSelect(e.target.value)}
                className="w-full text-xs font-semibold bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg px-2.5 py-1.5 text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer truncate"
              >
                {docs.map((d) => (
                  <option key={d.document_id} value={d.document_id}>
                    {d.filename} ({d.page_count} pgs)
                  </option>
                ))}
              </select>
            </div>

            {/* Page Navigation */}
            <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
              <button
                onClick={() => setSelectedPage(Math.max(1, selectedPage - 1))}
                disabled={selectedPage <= 1}
                className="px-2 py-1 rounded border border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--bg-input)] disabled:opacity-40"
              >
                Prev
              </button>
              <span className="font-mono text-xs px-1">
                Page {selectedPage} of {totalPages}
              </span>
              <button
                onClick={() => setSelectedPage(Math.min(totalPages, selectedPage + 1))}
                disabled={selectedPage >= totalPages}
                className="px-2 py-1 rounded border border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--bg-input)] disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>

          {/* Document Search / Filter inside Left Panel */}
          <div className="px-3 py-2 border-b border-[var(--border-color)] bg-[var(--bg-card)] shrink-0">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-[var(--text-muted)]" />
              <input
                type="text"
                value={docSearch}
                onChange={(e) => setDocSearch(e.target.value)}
                placeholder="Find text on this page..."
                className="w-full text-xs bg-[var(--bg-input)] border border-[var(--border-color)] rounded-md pl-8 pr-3 py-1 text-[var(--text-primary)] focus:outline-none"
              />
            </div>
          </div>

          {/* Document Content Display */}
          <div ref={documentViewerRef} className="flex-1 overflow-y-auto p-5 space-y-4 font-mono text-xs">
            {pageChunks.length === 0 ? (
              <div className="p-8 text-center text-[var(--text-muted)] font-sans">
                No extracted text found on Page {selectedPage}.
              </div>
            ) : (
              pageChunks.map((chunk) => {
                const isSnippetActive =
                  activeHighlightSnippet &&
                  (chunk.text.includes(activeHighlightSnippet) || activeHighlightSnippet.includes(chunk.text.substring(0, 50)));

                return (
                  <div
                    key={chunk.chunk_id}
                    className={`p-4 rounded-xl border transition-all ${
                      isSnippetActive
                        ? 'bg-amber-50/80 dark:bg-amber-950/40 border-amber-400 dark:border-amber-600 shadow-sm ring-2 ring-amber-400/40'
                        : 'bg-[var(--bg-input)]/20 border-[var(--border-color)]'
                    }`}
                  >
                    {chunk.section_heading && (
                      <div className="text-[11px] font-bold text-blue-600 dark:text-blue-400 mb-2 font-sans">
                        {chunk.section_heading}
                      </div>
                    )}
                    <p className="leading-relaxed text-[var(--text-primary)] whitespace-pre-wrap">
                      {chunk.text}
                    </p>
                    <div className="mt-3 pt-2 border-t border-[var(--border-color)] flex items-center justify-between text-[10px] text-[var(--text-muted)] font-sans">
                      <span>Doc: {chunk.document_name} · Page {chunk.page_number}</span>
                      <span>Chars: {chunk.char_start}–{chunk.char_end}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Left Panel Footer Status */}
          <div className="p-2.5 border-t border-[var(--border-color)] bg-[var(--bg-input)]/30 flex items-center justify-between text-[11px] text-[var(--text-muted)] shrink-0">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Verbatim Document Text (PyMuPDF)</span>
            </span>
            {activeHighlightSnippet && (
              <button
                onClick={() => setActiveHighlightSnippet(null)}
                className="text-blue-600 hover:underline font-semibold"
              >
                Clear Passage Highlight
              </button>
            )}
          </div>
        </div>

        {/* ================= RIGHT PANEL: Q&A & Citations ================= */}
        <div className="lg:col-span-6 h-full flex flex-col rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden shadow-xs">
          {/* Query Input Header */}
          <div className="p-4 border-b border-[var(--border-color)] bg-[var(--bg-input)]/30 shrink-0 space-y-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAsk();
              }}
              className="flex items-center gap-2"
            >
              <div className="relative flex-1">
                <Sparkles className="w-4 h-4 absolute left-3 top-2.5 text-blue-600" />
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask any question regarding obligations, dates, fees, or terms..."
                  className="w-full text-xs bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl pl-9 pr-3 py-2.5 text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                />
              </div>
              <button
                type="submit"
                disabled={asking || !question.trim()}
                className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-all disabled:opacity-50 shrink-0"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{asking ? 'Searching...' : 'Ask'}</span>
              </button>
            </form>

            {/* Quick Suggestion Chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px]">
              <span className="text-[var(--text-muted)] shrink-0 font-medium">Examples:</span>
              {suggestedQueries.map((sq, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => {
                    setQuestion(sq);
                    handleAsk(sq);
                  }}
                  className="px-2.5 py-1 rounded-full bg-[var(--bg-card)] hover:bg-blue-50 hover:text-blue-700 dark:hover:bg-blue-950/60 dark:hover:text-blue-300 border border-[var(--border-color)] text-[var(--text-muted)] shrink-0 transition-colors"
                >
                  {sq}
                </button>
              ))}
            </div>
          </div>

          {/* Answer & Citations Scroll Area */}
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            {asking ? (
              <div className="p-12 text-center space-y-3">
                <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto" />
                <p className="text-xs font-semibold text-[var(--text-primary)]">
                  Retrieving and verifying passages from documents...
                </p>
                <p className="text-[11px] text-[var(--text-muted)]">
                  BM25 scoring and invariant verification in progress.
                </p>
              </div>
            ) : currentQA ? (
              <div className="space-y-5">
                {/* Question asked banner */}
                <div className="p-3 rounded-xl bg-[var(--bg-input)]/50 border border-[var(--border-color)]">
                  <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                    Question
                  </div>
                  <p className="text-sm font-bold text-[var(--text-primary)]">
                    {currentQA.question}
                  </p>
                </div>

                {/* Grounded Answer Card */}
                <div
                  className={`p-4 rounded-xl border space-y-3 ${
                    currentQA.has_sufficient_evidence
                      ? 'bg-blue-50/50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900/60'
                      : 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[var(--text-primary)] flex items-center gap-1.5">
                      {currentQA.has_sufficient_evidence ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          <span>Evidence-Grounded Response</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-4 h-4 text-amber-600" />
                          <span>Insufficient Evidence in Selected Corpus</span>
                        </>
                      )}
                    </span>
                    <span className="text-[10px] font-mono text-[var(--text-muted)]">
                      {currentQA.query_id}
                    </span>
                  </div>

                  <p className="text-xs leading-relaxed text-[var(--text-primary)] font-medium">
                    {currentQA.answer}
                  </p>

                  {!currentQA.has_sufficient_evidence && (
                    <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-[11px] text-[var(--text-muted)]">
                      <strong>Honest Refusal:</strong> The retrieval engine did not locate sufficient relevant passages in the current document set. CaseLens AI avoids generating unsupported assumptions.
                    </div>
                  )}
                </div>

                {/* Supporting Source Citations */}
                {currentQA.citations.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-[var(--text-primary)]">
                        Supporting Evidence Citations ({currentQA.citations.length})
                      </span>
                      <span className="text-[11px] text-[var(--text-muted)]">
                        Click citation to inspect source page
                      </span>
                    </div>

                    <div className="space-y-2">
                      {currentQA.citations.map((cit) => (
                        <div
                          key={cit.citation_id}
                          onClick={() => handleCitationClick(cit)}
                          className="p-3.5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:border-blue-500 cursor-pointer transition-all space-y-1.5 group shadow-2xs"
                        >
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-bold text-blue-600 dark:text-blue-400 group-hover:underline flex items-center gap-1">
                              <span>[{cit.citation_id}]</span>
                              <span className="text-[var(--text-primary)] font-semibold">{cit.document_name}</span>
                            </span>
                            <span className="px-2 py-0.5 rounded bg-[var(--bg-input)] text-[10px] font-medium text-[var(--text-muted)]">
                              Page {cit.page_number}
                            </span>
                          </div>

                          <p className="text-xs text-[var(--text-muted)] leading-relaxed italic bg-[var(--bg-input)]/40 p-2 rounded border border-[var(--border-color)]/60">
                            “{cit.quoted_text}”
                          </p>

                          <div className="flex items-center justify-between text-[10px] text-[var(--text-muted)] pt-1">
                            <span>Status: {cit.verification_status}</span>
                            <span className="text-blue-600 group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
                              Jump to Page {cit.page_number} →
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Collapsible Explainability & Verification Panel */}
                <div className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] overflow-hidden">
                  <button
                    onClick={() => setShowVerificationPanel(!showVerificationPanel)}
                    className="w-full p-3 flex items-center justify-between text-xs font-bold text-[var(--text-primary)] hover:bg-[var(--bg-input)]/40 transition-colors"
                  >
                    <span className="flex items-center gap-1.5">
                      <Shield className="w-4 h-4 text-blue-600" />
                      <span>Explainability & Citation Verification Invariants</span>
                    </span>
                    {showVerificationPanel ? (
                      <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
                    )}
                  </button>

                  {showVerificationPanel && (
                    <div className="p-4 border-t border-[var(--border-color)] space-y-3 bg-[var(--bg-input)]/20 text-xs">
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div className="p-2 rounded bg-[var(--bg-card)] border border-[var(--border-color)]">
                          <span className="text-[var(--text-muted)]">Citation ID Valid:</span>
                          <p className="font-bold text-emerald-600">
                            {currentQA.verification.citation_id_valid ? 'Verified' : 'Failed'}
                          </p>
                        </div>
                        <div className="p-2 rounded bg-[var(--bg-card)] border border-[var(--border-color)]">
                          <span className="text-[var(--text-muted)]">Document Exists:</span>
                          <p className="font-bold text-emerald-600">
                            {currentQA.verification.document_exists ? 'Verified in DB' : 'Failed'}
                          </p>
                        </div>
                        <div className="p-2 rounded bg-[var(--bg-card)] border border-[var(--border-color)]">
                          <span className="text-[var(--text-muted)]">Passage Match:</span>
                          <p className="font-bold text-emerald-600">
                            {currentQA.verification.passage_match_verified ? '100% Substring Grounded' : 'Mismatch'}
                          </p>
                        </div>
                        <div className="p-2 rounded bg-[var(--bg-card)] border border-[var(--border-color)]">
                          <span className="text-[var(--text-muted)]">Processing Mode:</span>
                          <p className="font-bold text-[var(--text-primary)] font-mono text-[10px]">
                            {currentQA.verification.processing_mode}
                          </p>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <span className="font-semibold text-[11px] text-[var(--text-primary)]">Limitations:</span>
                        <ul className="list-disc list-inside text-[11px] text-[var(--text-muted)] space-y-0.5">
                          {currentQA.verification.limitations.map((lim, idx) => (
                            <li key={idx}>{lim}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center text-xs text-[var(--text-muted)] space-y-2">
                <HelpCircle className="w-8 h-8 text-[var(--text-muted)] mx-auto opacity-40" />
                <p className="font-semibold text-[var(--text-primary)]">No query executed yet.</p>
                <p>Type a question above or click one of the suggested prompts to see evidence-grounded answers.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
