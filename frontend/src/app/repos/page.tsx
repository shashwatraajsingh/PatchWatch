'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Shield, ArrowLeft, Plus, Eye, EyeOff, Trash2, RefreshCw,
  Copy, Check, GitBranch, Webhook, Clock, Activity, Loader2
} from 'lucide-react';
import {
  fetchWatchedRepos, addWatchedRepo, toggleRepo, deleteRepo,
  regenerateSecret, WatchedRepo
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button onClick={handleCopy} className="text-white/30 hover:text-white transition-colors p-1">
      {copied ? <Check className="w-3 h-3 text-[#00ff88]" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

function RepoCard({
  repo,
  onToggle,
  onDelete,
  onRegenerate,
}: {
  repo: WatchedRepo;
  onToggle: () => void;
  onDelete: () => void;
  onRegenerate: () => void;
}) {
  const [showSecret, setShowSecret] = useState(false);
  const [showSetup, setShowSetup] = useState(false);

  return (
    <div className={`border ${repo.enabled ? 'border-white/10' : 'border-white/5 opacity-60'} transition-all`}>
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2 h-2 rounded-full ${repo.enabled ? 'bg-[#00ff88] animate-pulse' : 'bg-white/20'}`} />
              <span className="text-sm font-mono text-white/80">{repo.repo_full_name}</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono text-white/30">
              <span className="flex items-center gap-1">
                <GitBranch className="w-3 h-3" />
                {repo.branches.join(', ')}
              </span>
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3" />
                {repo.total_scans} scans
              </span>
              {repo.last_scan_at && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Last: {new Date(repo.last_scan_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button onClick={onToggle} className="p-2 text-white/30 hover:text-white transition-colors" title={repo.enabled ? 'Pause' : 'Enable'}>
              {repo.enabled ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
            <button onClick={onDelete} className="p-2 text-white/30 hover:text-red-400 transition-colors" title="Remove">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Webhook secret */}
        <div className="bg-white/[0.02] border border-white/5 p-3 mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] font-mono text-white/30 tracking-wider">WEBHOOK SECRET</span>
            <div className="flex items-center gap-1">
              <button onClick={() => setShowSecret(!showSecret)} className="text-white/30 hover:text-white transition-colors p-1">
                {showSecret ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              </button>
              <CopyButton text={repo.webhook_secret} />
              <button onClick={onRegenerate} className="text-white/30 hover:text-white transition-colors p-1" title="Regenerate">
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
          </div>
          <code className="text-[11px] font-mono text-white/50 break-all">
            {showSecret ? repo.webhook_secret : '•'.repeat(32)}
          </code>
        </div>

        {/* Webhook URL */}
        <div className="bg-white/[0.02] border border-white/5 p-3 mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[9px] font-mono text-white/30 tracking-wider">WEBHOOK URL</span>
            <CopyButton text={repo.webhook_url} />
          </div>
          <code className="text-[11px] font-mono text-white/50">{repo.webhook_url}</code>
        </div>

        {/* Setup instructions toggle */}
        <button
          onClick={() => setShowSetup(!showSetup)}
          className="text-[10px] font-mono text-white/30 hover:text-white/50 transition-colors flex items-center gap-1"
        >
          <Webhook className="w-3 h-3" />
          {showSetup ? 'HIDE' : 'SHOW'} SETUP INSTRUCTIONS
        </button>
      </div>

      {/* Setup instructions */}
      {showSetup && (
        <div className="border-t border-white/5 p-5 bg-white/[0.01]">
          <div className="text-[10px] font-mono text-white/40 space-y-3">
            <p className="text-white/60 mb-2">Go to your repo → Settings → Webhooks → Add webhook:</p>
            <div className="space-y-2">
              <div className="flex gap-2">
                <span className="text-white/20 w-4 text-right">1.</span>
                <span><span className="text-white/50">Payload URL:</span> {repo.webhook_url}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-white/20 w-4 text-right">2.</span>
                <span><span className="text-white/50">Content type:</span> application/json</span>
              </div>
              <div className="flex gap-2">
                <span className="text-white/20 w-4 text-right">3.</span>
                <span><span className="text-white/50">Secret:</span> Copy the webhook secret above</span>
              </div>
              <div className="flex gap-2">
                <span className="text-white/20 w-4 text-right">4.</span>
                <span><span className="text-white/50">Events:</span> Just the push event</span>
              </div>
              <div className="flex gap-2">
                <span className="text-white/20 w-4 text-right">5.</span>
                <span><span className="text-white/50">Active:</span> ✓ checked</span>
              </div>
            </div>
            <p className="text-white/20 mt-3 border-t border-white/5 pt-3">
              Once configured, every push to {repo.branches.join(' or ')} will auto-trigger a security scan.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ReposPage() {
  const { user, loading: authLoading, login } = useAuth();
  const [repos, setRepos] = useState<WatchedRepo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newRepo, setNewRepo] = useState('');
  const [newBranches, setNewBranches] = useState('main');
  const [addError, setAddError] = useState('');
  const [adding, setAdding] = useState(false);

  const loadRepos = async () => {
    try {
      const data = await fetchWatchedRepos();
      setRepos(data);
    } catch {}
    setLoading(false);
  };

  useEffect(() => {
    if (user) loadRepos();
  }, [user]);

  if (authLoading) {
    return (
      <main className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-5 h-5 text-white/30 animate-spin" />
      </main>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-8 h-8 text-white/10 mx-auto mb-4" />
          <p className="text-white/30 text-sm font-mono mb-4">AUTHENTICATION REQUIRED</p>
          <button onClick={login} className="text-xs font-mono text-white/50 border border-white/20 px-6 py-2 hover:border-white/40 hover:text-white transition-colors">
            SIGN IN WITH GITHUB
          </button>
        </div>
      </main>
    );
  }


  const handleAdd = async () => {
    if (!newRepo) return;
    setAdding(true);
    setAddError('');
    try {
      const branches = newBranches.split(',').map(b => b.trim()).filter(Boolean);
      await addWatchedRepo(newRepo, branches);
      setNewRepo('');
      setNewBranches('main');
      setShowAdd(false);
      await loadRepos();
    } catch (e: any) {
      setAddError(e.message || 'Failed to add repo');
    }
    setAdding(false);
  };

  const handleToggle = async (repo: WatchedRepo) => {
    await toggleRepo(repo.id, !repo.enabled);
    await loadRepos();
  };

  const handleDelete = async (repo: WatchedRepo) => {
    await deleteRepo(repo.id);
    await loadRepos();
  };

  const handleRegenerate = async (repo: WatchedRepo) => {
    await regenerateSecret(repo.id);
    await loadRepos();
  };

  return (
    <main className="min-h-screen bg-black relative">
      <div className="absolute inset-0 stars-bg" />

      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-white/20 z-20" />
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-white/20 z-20" />

      {/* Header */}
      <div className="relative z-10 border-b border-white/10">
        <div className="container mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-white/40 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div className="h-4 w-px bg-white/10" />
            <Shield className="w-4 h-4 text-white/60" />
            <span className="font-mono text-white text-sm tracking-[0.15em]">PATCHWATCH</span>
            <div className="h-4 w-px bg-white/10" />
            <span className="text-white/30 text-[10px] font-mono tracking-wider">AUTO SCAN</span>
          </div>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="text-[10px] font-mono text-white/40 hover:text-white border border-white/10 px-3 py-1.5 hover:border-white/30 transition-colors flex items-center gap-2"
          >
            <Plus className="w-3 h-3" />
            ADD REPO
          </button>
        </div>
      </div>

      <div className="relative z-10 container mx-auto px-8 py-8 max-w-3xl">
        {/* Add repo form */}
        {showAdd && (
          <div className="border border-white/10 p-5 mb-6">
            <div className="flex items-center gap-2 mb-4 opacity-60">
              <Plus className="w-3 h-3 text-white" />
              <span className="text-[10px] font-mono text-white tracking-wider">REGISTER REPOSITORY</span>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-[10px] font-mono text-white/40 tracking-wider mb-1">REPOSITORY</label>
                <input
                  type="text"
                  value={newRepo}
                  onChange={(e) => setNewRepo(e.target.value)}
                  placeholder="owner/repo"
                  className="w-full bg-white/[0.03] border border-white/10 text-white font-mono text-sm px-4 py-2.5 placeholder:text-white/15 focus:border-white/30 focus:outline-none transition-colors"
                />
              </div>
              <div>
                <label className="block text-[10px] font-mono text-white/40 tracking-wider mb-1">BRANCHES (comma-separated, or * for all)</label>
                <input
                  type="text"
                  value={newBranches}
                  onChange={(e) => setNewBranches(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/10 text-white font-mono text-sm px-4 py-2.5 placeholder:text-white/15 focus:border-white/30 focus:outline-none transition-colors"
                />
              </div>

              {addError && (
                <p className="text-xs font-mono text-red-400">{addError}</p>
              )}

              <button
                onClick={handleAdd}
                disabled={!newRepo || adding}
                className="w-full px-6 py-2.5 border border-white text-white font-mono text-sm hover:bg-white hover:text-black transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                {adding ? 'REGISTERING...' : 'REGISTER & GET WEBHOOK SECRET'}
              </button>
            </div>
          </div>
        )}

        {/* Section header */}
        <div className="flex items-center gap-2 mb-6 opacity-40">
          <div className="w-8 h-px bg-white" />
          <Webhook className="w-3 h-3 text-white" />
          <span className="text-[10px] font-mono text-white">WATCHED REPOSITORIES</span>
          <div className="flex-1 h-px bg-white" />
        </div>

        {/* Repos list */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="border border-white/5 p-5 animate-pulse">
                <div className="h-3 bg-white/5 w-1/3 mb-3" />
                <div className="h-2 bg-white/5 w-2/3" />
              </div>
            ))}
          </div>
        ) : repos.length === 0 ? (
          <div className="border border-white/10 p-12 text-center">
            <Webhook className="w-8 h-8 text-white/10 mx-auto mb-4" />
            <p className="text-white/30 text-sm font-mono mb-2">NO REPOS REGISTERED</p>
            <p className="text-white/15 text-xs font-mono mb-6">Add a repo to enable automatic security scanning on every push.</p>
            <button
              onClick={() => setShowAdd(true)}
              className="text-xs font-mono text-white/50 hover:text-white border border-white/20 px-4 py-2 hover:border-white/40 transition-colors"
            >
              + ADD YOUR FIRST REPO
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {repos.map((repo) => (
              <RepoCard
                key={repo.id}
                repo={repo}
                onToggle={() => handleToggle(repo)}
                onDelete={() => handleDelete(repo)}
                onRegenerate={() => handleRegenerate(repo)}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
