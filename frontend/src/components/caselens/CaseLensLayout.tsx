import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  FileText,
  Search,
  MessageSquare,
  FileSearch,
  AlertTriangle,
  FileCheck,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Sun,
  Moon,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Layers,
  CheckCircle2,
  Bell,
  Scale,
  GitCompare,
  FileQuestion,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { caselensApi } from '../../services/caselensApi';
import { Workspace } from '../../types/caselens';

export const CaseLensLayout: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWs, setCurrentWs] = useState<string>('demo-caselens-meridian');
  const [resetting, setResetting] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      const list = await caselensApi.listWorkspaces();
      setWorkspaces(list);
      if (list.length > 0 && !list.find(w => w.id === currentWs)) {
        setCurrentWs(list[0].id);
      }
    } catch (e) {
      console.error('Failed to load workspaces', e);
    }
  };

  const handleResetDemo = async () => {
    setResetting(true);
    try {
      await caselensApi.resetDemoWorkspace();
      await loadWorkspaces();
      // Reload current page to refresh data
      window.location.reload();
    } catch (e) {
      alert('Failed to reset demo workspace: ' + e);
    } finally {
      setResetting(false);
    }
  };

  const navItems = [
    { label: 'Overview', path: '/caselens/overview', icon: Layers },
    { label: 'Documents', path: '/caselens/documents', icon: FileText },
    { label: 'Ask CaseLens', path: '/caselens/ask', icon: MessageSquare },
    { label: 'Case Analysis', path: '/caselens/analysis', icon: Scale },
    { label: 'Contradictions', path: '/caselens/contradictions', icon: AlertTriangle },
    { label: 'Comparison', path: '/caselens/compare', icon: GitCompare },
    { label: 'Missing Info', path: '/caselens/missing-info', icon: FileQuestion },
    { label: 'Reports', path: '/caselens/reports', icon: FileCheck },
    { label: 'Activity', path: '/caselens/activity', icon: Activity },
    { label: 'Settings', path: '/caselens/settings', icon: Settings },
  ];

  const activeWsObj = workspaces.find(w => w.id === currentWs);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--bg-main)] text-[var(--text-primary)]">
      {/* Sidebar */}
      <aside
        className={`h-full border-r border-[var(--border-color)] bg-[var(--bg-card)] flex flex-col transition-all duration-300 z-30 shrink-0 ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-[var(--border-color)]">
          <div
            onClick={() => navigate('/caselens/overview')}
            className="flex items-center gap-3 cursor-pointer overflow-hidden"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-700 to-indigo-900 flex items-center justify-center text-white shadow-md shrink-0">
              <Scale className="w-5 h-5 text-blue-200" />
            </div>
            {!collapsed && (
              <div className="truncate">
                <span className="font-bold text-base tracking-tight flex items-center gap-1.5 font-sans text-[var(--text-primary)]">
                  CaseLens <span className="text-xs bg-blue-600/10 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded-md font-semibold">AI</span>
                </span>
                <p className="text-[10px] text-[var(--text-muted)] font-medium truncate">
                  Evidence-Grounded Legal Intel
                </p>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] transition-colors"
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Workspace Quick Indicator */}
        {!collapsed && (
          <div className="p-3 border-b border-[var(--border-color)] bg-[var(--bg-input)]/40">
            <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Active Workspace</span>
              {activeWsObj?.is_demo && (
                <span className="text-[10px] bg-amber-500/15 text-amber-600 dark:text-amber-400 px-1.5 py-0.2 rounded font-semibold">Demo</span>
              )}
            </div>
            <select
              value={currentWs}
              onChange={(e) => setCurrentWs(e.target.value)}
              className="w-full text-xs font-medium bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg px-2.5 py-1.5 text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer truncate"
            >
              {workspaces.map((ws) => (
                <option key={ws.id} value={ws.id}>
                  {ws.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Navigation Links */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600/10 text-blue-600 dark:text-blue-400 font-semibold shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-input)]'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>

        {/* Mode & Switcher Footer */}
        <div className="p-3 border-t border-[var(--border-color)] space-y-2">
          {!collapsed && (
            <div className="p-2.5 rounded-lg bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/50 dark:border-blue-900/50 text-xs">
              <div className="flex items-center gap-1.5 text-blue-800 dark:text-blue-300 font-semibold mb-1">
                <Shield className="w-3.5 h-3.5 text-blue-600" />
                <span>Zero Hallucination</span>
              </div>
              <p className="text-[11px] text-blue-700/80 dark:text-blue-300/70 leading-relaxed">
                Every claim is verified against exact extracted page passages.
              </p>
            </div>
          )}

          {/* Quick link to ProofAI Data Analyst */}
          <button
            onClick={() => navigate('/dashboard')}
            className={`w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-medium rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-input)] transition-colors border border-transparent hover:border-[var(--border-color)] ${
              collapsed ? 'px-0' : ''
            }`}
            title="Switch to ProofAI Data Intelligence Workspace"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            {!collapsed && <span>Switch to ProofAI</span>}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-[var(--border-color)] bg-[var(--bg-card)] flex items-center justify-between px-6 shrink-0 z-20">
          <div className="flex items-center gap-4">
            <h2 className="text-base font-semibold text-[var(--text-primary)] hidden md:block">
              {activeWsObj?.name || 'Legal Document Intelligence'}
            </h2>
            <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] bg-[var(--bg-input)] px-2.5 py-1 rounded-full border border-[var(--border-color)]">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
              <span>Offline Deterministic Mode</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick Demo Reset Button */}
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)] transition-colors disabled:opacity-50"
              title="Reset sample case documents and analyses"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Reset Demo</span>
            </button>

            {/* New Analysis / Ask CTA */}
            <button
              onClick={() => navigate('/caselens/ask')}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-all hover:shadow"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Ask CaseLens</span>
            </button>

            {/* Notifications toggle */}
            <div className="relative">
              <button
                onClick={() => setNotifOpen(!notifOpen)}
                className="p-2 rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] transition-colors relative"
              >
                <Bell className="w-4 h-4" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-600" />
              </button>
              {notifOpen && (
                <div className="absolute right-0 mt-2 w-72 p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-xl z-50 text-xs">
                  <div className="font-semibold text-[var(--text-primary)] mb-2 flex items-center justify-between">
                    <span>Audit Notifications</span>
                    <span className="text-[10px] text-blue-600 font-normal">Mark read</span>
                  </div>
                  <div className="space-y-2">
                    <div className="p-2 rounded-lg bg-[var(--bg-input)]/60">
                      <p className="font-medium text-[var(--text-primary)]">Contradiction Detected</p>
                      <p className="text-[11px] text-[var(--text-muted)]">Conflicting expiration dates: 30 June 2027 vs 31 July 2027.</p>
                    </div>
                    <div className="p-2 rounded-lg bg-[var(--bg-input)]/60">
                      <p className="font-medium text-[var(--text-primary)]">Sample Case Loaded</p>
                      <p className="text-[11px] text-[var(--text-muted)]">Project Meridian documents indexed with full provenance.</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] transition-colors"
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Public Landing Link */}
            <button
              onClick={() => navigate('/')}
              className="p-2 rounded-lg text-[var(--text-muted)] hover:bg-[var(--bg-input)] hover:text-[var(--text-primary)] transition-colors"
              title="Return to Public Landing Page"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-[var(--bg-main)]">
          <Outlet context={{ currentWs, workspaces, reloadWorkspaces: loadWorkspaces }} />
        </main>
      </div>
    </div>
  );
};
