import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Scale,
  ArrowRight,
  ShieldCheck,
  FileText,
  Search,
  CheckCircle2,
  AlertTriangle,
  GitCompare,
  Layers,
  Lock,
  Database,
  ExternalLink,
  ChevronRight,
  Sparkles,
  FileCheck,
  Hash,
  Eye,
  Sun,
  Moon,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<'answer' | 'citation' | 'contradiction'>('answer');

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-[var(--text-primary)] font-sans antialiased selection:bg-blue-500/20">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-[var(--bg-card)]/80 border-b border-[var(--border-color)]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-700 to-indigo-900 flex items-center justify-center text-white shadow-md">
              <Scale className="w-5 h-5 text-blue-200" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight flex items-center gap-1.5">
                CaseLens <span className="text-xs bg-blue-600/10 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-md font-semibold">AI</span>
              </span>
              <p className="text-[10px] text-[var(--text-muted)] font-medium -mt-0.5">
                Evidence-Grounded Legal Intelligence
              </p>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-[var(--text-muted)]">
            <a href="#features" className="hover:text-[var(--text-primary)] transition-colors">Features</a>
            <a href="#workflow" className="hover:text-[var(--text-primary)] transition-colors">Workflow</a>
            <a href="#citations" className="hover:text-[var(--text-primary)] transition-colors">How Citations Work</a>
            <a href="#contradictions" className="hover:text-[var(--text-primary)] transition-colors">Contradictions</a>
            <a href="#security" className="hover:text-[var(--text-primary)] transition-colors">Security & Privacy</a>
          </nav>

          <div className="flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] transition-colors"
              title={`Toggle ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>
            <button
              onClick={() => navigate('/caselens/overview')}
              className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg border border-[var(--border-color)] text-xs font-semibold hover:bg-[var(--bg-input)] transition-colors"
            >
              Explore Demo
            </button>
            <button
              onClick={() => navigate('/caselens/overview')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-all hover:shadow"
            >
              <span>Open Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-16 px-6 overflow-hidden">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-600/10 border border-blue-500/20 text-blue-700 dark:text-blue-300 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>Deterministic Grounding · Zero Hallucination Guarantee</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[var(--text-primary)] leading-[1.15]">
            Understand complex documents. <br />
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Verify every single claim.
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-base sm:text-lg text-[var(--text-muted)] font-normal leading-relaxed">
            CaseLens AI is an evidence-grounded legal document intelligence platform.
            Every claim is tied to an exact extracted passage, every contradiction is exposed side-by-side,
            and unsupported questions receive an honest refusal instead of a hallucinated answer.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => navigate('/caselens/overview')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-md transition-all hover:shadow-lg flex items-center justify-center gap-2"
            >
              <span>Open Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/caselens/ask')}
              className="w-full sm:w-auto px-6 py-3 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:bg-[var(--bg-input)] text-sm font-semibold text-[var(--text-primary)] transition-all flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Explore Demo Scenarios</span>
            </button>
          </div>

          {/* Tagline Banner */}
          <div className="pt-4 text-xs font-semibold tracking-wide uppercase text-[var(--text-muted)]">
            “Every claim has evidence. Every answer has a source.”
          </div>
        </div>

        {/* Interactive Product Preview */}
        <div className="max-w-6xl mx-auto mt-14 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] shadow-2xl overflow-hidden">
          {/* Mock Window Titlebar */}
          <div className="px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-input)]/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-400/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-amber-400/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-emerald-400/80 inline-block" />
              <span className="ml-3 text-xs font-mono text-[var(--text-muted)]">
                caselens.ai/workspace/demo-caselens-meridian
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Source Verified
              </span>
            </div>
          </div>

          {/* Preview Navigation Tabs */}
          <div className="px-6 pt-4 border-b border-[var(--border-color)] flex items-center gap-4 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('answer')}
              className={`pb-3 border-b-2 transition-all ${
                activeTab === 'answer'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Q&A with Passage Grounding
            </button>
            <button
              onClick={() => setActiveTab('citation')}
              className={`pb-3 border-b-2 transition-all ${
                activeTab === 'citation'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Citation & Explainability Panel
            </button>
            <button
              onClick={() => setActiveTab('contradiction')}
              className={`pb-3 border-b-2 transition-all ${
                activeTab === 'contradiction'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Cross-Document Contradiction
            </button>
          </div>

          {/* Tab Content Display */}
          <div className="p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 bg-[var(--bg-main)]/50 min-h-[380px]">
            {activeTab === 'answer' && (
              <>
                {/* Left Document View */}
                <div className="lg:col-span-6 p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-xs space-y-3 font-mono">
                  <div className="flex items-center justify-between pb-2 border-b border-[var(--border-color)]">
                    <span className="font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      01_Master_Services_Agreement_Acme_Apex.txt
                    </span>
                    <span className="text-[10px] bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 px-1.5 py-0.5 rounded">Page 1</span>
                  </div>
                  <p className="text-[var(--text-muted)] leading-relaxed">
                    SECTION 3: COMPENSATION AND PAYMENT SCHEDULE
                  </p>
                  <p className="text-[var(--text-primary)] leading-relaxed bg-amber-100/70 dark:bg-amber-950/40 p-2 rounded border border-amber-300/50 dark:border-amber-800/50">
                    <span className="font-bold text-amber-900 dark:text-amber-200">3.1 Base Retainer Fee:</span> Acme Corp shall pay Apex Logistics an annual base retainer fee of $150,000 USD payable quarterly in advance.
                  </p>
                  <p className="text-[var(--text-muted)] leading-relaxed">
                    SECTION 6: TERMINATION FOR CONVENIENCE<br />
                    6.1 Notice Period: Either party may terminate this Agreement without cause upon sixty (60) days prior written notice.
                  </p>
                </div>

                {/* Right Synthesized Answer */}
                <div className="lg:col-span-6 p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-muted)]">
                    <Search className="w-3.5 h-3.5 text-blue-600" />
                    <span>Question Asked:</span>
                  </div>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">
                    “What is the annual base retainer fee and payment frequency?”
                  </p>
                  <div className="p-3.5 rounded-lg bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-900/60 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-blue-900 dark:text-blue-200 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        Grounded Answer
                      </span>
                      <span className="text-[10px] font-mono text-blue-600 dark:text-blue-400 font-semibold">[CIT-1]</span>
                    </div>
                    <p className="text-[var(--text-primary)] leading-relaxed">
                      Based on the recorded provisions in 01_Master_Services_Agreement_Acme_Apex.txt (Page 1):
                      “Acme Corp shall pay Apex Logistics an annual base retainer fee of $150,000 USD payable quarterly in advance.”
                    </p>
                  </div>

                  <div className="pt-2 flex items-center justify-between text-[11px] text-[var(--text-muted)] border-t border-[var(--border-color)]">
                    <span>Provenance: Page 1 · Exact match confirmed</span>
                    <button onClick={() => navigate('/caselens/ask')} className="text-blue-600 hover:underline font-semibold flex items-center gap-1">
                      Try in Workspace <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'citation' && (
              <div className="lg:col-span-12 p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[var(--border-color)]">
                  <div>
                    <h3 className="font-semibold text-sm text-[var(--text-primary)]">Citation Verification Panel</h3>
                    <p className="text-xs text-[var(--text-muted)]">Real structural validation checks executed on every answer</p>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold text-xs flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> 4 Invariants Passed
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 rounded-lg bg-[var(--bg-input)] space-y-1">
                    <span className="font-medium text-[var(--text-muted)]">Citation ID Exists</span>
                    <p className="text-sm font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Validated
                    </p>
                    <p className="text-[10px] text-[var(--text-muted)]">Assigned CIT-1 in sequence</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--bg-input)] space-y-1">
                    <span className="font-medium text-[var(--text-muted)]">Document Association</span>
                    <p className="text-sm font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Verified
                    </p>
                    <p className="text-[10px] text-[var(--text-muted)]">Document ID matches catalog</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--bg-input)] space-y-1">
                    <span className="font-medium text-[var(--text-muted)]">Passage Match</span>
                    <p className="text-sm font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> 100% Substring
                    </p>
                    <p className="text-[10px] text-[var(--text-muted)]">No text alteration or drift</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--bg-input)] space-y-1">
                    <span className="font-medium text-[var(--text-muted)]">Claim Segmentation</span>
                    <p className="text-sm font-bold text-emerald-600 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Grounded
                    </p>
                    <p className="text-[10px] text-[var(--text-muted)]">Claim 1 linked to Citation 1</p>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)]/40 text-xs">
                  <span className="font-semibold text-[var(--text-primary)]">Limitations Disclosure:</span>
                  <p className="text-[var(--text-muted)] mt-1 leading-relaxed">
                    Source-existence validation confirms the cited passage exists in the designated document.
                    Semantic legal sufficiency requires human counsel review.
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'contradiction' && (
              <div className="lg:col-span-12 p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[var(--border-color)]">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-amber-500/15 flex items-center justify-center text-amber-600">
                      <AlertTriangle className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm text-[var(--text-primary)]">Potential Contradiction Detected</h3>
                      <p className="text-xs text-[var(--text-muted)]">Date Mismatch between Master Agreement and Addendum</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-700 dark:text-amber-300 font-semibold text-xs">
                    HIGH SEVERITY
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-color)] space-y-1.5">
                    <span className="font-semibold text-[var(--text-primary)]">Document A: 01_Master_Services_Agreement</span>
                    <p className="text-amber-800 dark:text-amber-300 bg-amber-100/50 dark:bg-amber-950/40 p-2 rounded">
                      “This Agreement shall commence on the Effective Date and shall expire on <span className="font-bold underline">30 June 2027</span>.”
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-color)] space-y-1.5">
                    <span className="font-semibold text-[var(--text-primary)]">Document B: 02_SLA_Amendment_Addendum</span>
                    <p className="text-amber-800 dark:text-amber-300 bg-amber-100/50 dark:bg-amber-950/40 p-2 rounded">
                      “The agreement expires on <span className="font-bold underline">31 July 2027</span> to align with international fiscal calendar requirements.”
                    </p>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-[var(--bg-input)] text-xs text-[var(--text-muted)] flex items-center justify-between">
                  <span>Recommendation: Review execution timeline or addendum precedence clause to determine operative term.</span>
                  <button onClick={() => navigate('/caselens/contradictions')} className="text-blue-600 hover:underline font-semibold shrink-0 ml-4">
                    View in Contradiction Hub →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 3-Step Workflow Section */}
      <section id="workflow" className="py-20 px-6 border-t border-[var(--border-color)] bg-[var(--bg-card)]/40">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
              Methodology
            </span>
            <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">
              Three-Step Verification Pipeline
            </h2>
            <p className="text-sm text-[var(--text-muted)] max-w-xl mx-auto">
              Every document is cataloged, chunked with page and character provenance, and independently audited.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4 relative">
              <div className="w-12 h-12 rounded-xl bg-blue-600/10 text-blue-600 flex items-center justify-center font-bold text-lg">
                1
              </div>
              <h3 className="font-bold text-base text-[var(--text-primary)]">Upload & Hash</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Ingest PDF, DOCX, and TXT files. Cryptographic SHA-256 fingerprinting guarantees file provenance.
                PyMuPDF extracts exact page numbers and offsets.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4 relative">
              <div className="w-12 h-12 rounded-xl bg-blue-600/10 text-blue-600 flex items-center justify-center font-bold text-lg">
                2
              </div>
              <h3 className="font-bold text-base text-[var(--text-primary)]">Analyze & Ground</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Hybrid BM25 vector retrieval ranks relevant passages. Obligations, timelines, entities, and
                cross-document contradictions are surfaced systematically.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-4 relative">
              <div className="w-12 h-12 rounded-xl bg-blue-600/10 text-blue-600 flex items-center justify-center font-bold text-lg">
                3
              </div>
              <h3 className="font-bold text-base text-[var(--text-primary)]">Verify & Export</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Inspect citations side-by-side with original text. If evidence is lacking, an explicit refusal is returned.
                Export structured reports to Markdown or PDF.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section id="features" className="py-20 px-6 border-t border-[var(--border-color)]">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
              Core Capabilities
            </span>
            <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">
              Built for High-Stakes Document Intelligence
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-blue-600/10 text-blue-600 flex items-center justify-center">
                <FileCheck className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-[var(--text-primary)]">Page-Level Citations</h4>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Clicking any citation jumps to the exact document, page number, and highlighted source passage.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/15 text-amber-600 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-[var(--text-primary)]">Contradiction Detection</h4>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Deterministic comparison reveals conflicting dates, disparate amounts, and incompatible notice periods across agreements.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-500/15 text-indigo-600 flex items-center justify-center">
                <GitCompare className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-[var(--text-primary)]">Document Comparison</h4>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Inspect added clauses, deleted conditions, and modified financial schedules across agreement revisions.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/15 text-emerald-600 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-[var(--text-primary)]">Missing Info Checklists</h4>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Audit contracts against standard service, lease, and employment templates to identify absent legal protections.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/15 text-blue-600 flex items-center justify-center">
                <Scale className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-[var(--text-primary)]">Obligation Extraction</h4>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Automatically identifies responsible parties, mandatory duties, and recurring deadlines with direct source links.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-3">
              <div className="w-10 h-10 rounded-lg bg-purple-500/15 text-purple-600 flex items-center justify-center">
                <Database className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-sm text-[var(--text-primary)]">Structured Reports</h4>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                Generate and export publication-ready audit reports compiling executive summaries, timelines, and evidence registers.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Security & Privacy Section */}
      <section id="security" className="py-20 px-6 border-t border-[var(--border-color)] bg-[var(--bg-card)]/40">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-3">
            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
              Transparency & Security
            </span>
            <h2 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">
              Implemented Security Protections
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              We describe actual implemented safeguards only — no fabricated enterprise compliance badges.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
                <Lock className="w-4 h-4 text-blue-600" />
                <span>Local-First SQLite Storage</span>
              </div>
              <p className="text-[var(--text-muted)] leading-relaxed">
                Documents and extracted chunk text are persisted strictly in your local SQLite database without third-party cloud synchronization.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
                <Hash className="w-4 h-4 text-blue-600" />
                <span>SHA-256 Provenance & Deduplication</span>
              </div>
              <p className="text-[var(--text-muted)] leading-relaxed">
                Every uploaded file is hashed at ingestion. File content hashes are verified before processing to prevent tampering.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <span>Path Traversal & Safe Names</span>
              </div>
              <p className="text-[var(--text-muted)] leading-relaxed">
                Filename sanitization strips directory traversal markers (`../`) and null bytes to prevent server-side path escape attacks.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] space-y-2">
              <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
                <Eye className="w-4 h-4 text-blue-600" />
                <span>Deterministic Zero-Cloud Engine</span>
              </div>
              <p className="text-[var(--text-muted)] leading-relaxed">
                Document search and citation verification run completely offline via local BM25 and deterministic pattern extractors.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Banner */}
      <section className="py-20 px-6 border-t border-[var(--border-color)] text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[var(--text-primary)]">
            Ready to explore verified legal document intelligence?
          </h2>
          <p className="text-sm text-[var(--text-muted)] max-w-xl mx-auto">
            Test Project Meridian sample documents immediately or upload your own agreements for instant provenance-grounded analysis.
          </p>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => navigate('/caselens/overview')}
              className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-md transition-all hover:shadow-lg flex items-center gap-2"
            >
              <span>Launch CaseLens Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-[var(--border-color)] text-xs text-[var(--text-muted)] bg-[var(--bg-card)]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-blue-600" />
            <span className="font-semibold text-[var(--text-primary)]">CaseLens AI</span>
            <span>— “Every claim has evidence. Every answer has a source.”</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="text-[11px]">MIT Licensed</span>
            <button onClick={() => navigate('/dashboard')} className="hover:text-[var(--text-primary)] transition-colors">
              ProofAI Data Analyst
            </button>
            <button onClick={() => navigate('/caselens/overview')} className="text-blue-600 hover:underline font-semibold">
              Demo Workspace
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
