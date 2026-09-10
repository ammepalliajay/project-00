import React, { useState } from 'react';
import { Terminal, Copy, Check, BookOpen, ExternalLink, ShieldCheck } from 'lucide-react';

export const CollegeDemoGuide: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const steps = [
    {
      title: '1. Launch Complete Distributed Microservice (Docker Desktop)',
      cmd: 'docker compose up --build -d && docker compose ps',
      desc: 'Starts RabbitMQ (5672/15672), Redis (6379), FastAPI API (8000), and Celery Worker with FFmpeg.',
    },
    {
      title: '2. Check System Health & Dependency Probes',
      cmd: 'curl -s http://localhost:8000/health | jq .',
      desc: 'Validates socket checks to RabbitMQ, Redis PING, and FFmpeg binary execution.',
    },
    {
      title: '3. Run Live Interactive Demo Script',
      cmd: 'python3 scripts/demo.py --url http://localhost:8000',
      desc: 'Executes the end-to-end college demonstration: upload -> queue -> poll -> download -> metrics.',
    },
    {
      title: '4. Run Pytest Suite with Mocked AWS S3 & 100% Test Coverage',
      cmd: 'PYTHONPATH=. pytest tests -v',
      desc: 'Runs 33 automated tests validating MIME, path traversal, Pillow engines, FFmpeg, and Celery tasks.',
    },
  ];

  return (
    <div id="college-demo-guide" className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-cyan-400" />
          Live College Demonstration Script & Commands
        </h3>
        <div className="flex gap-2">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs font-mono text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 px-3 py-1 rounded border border-indigo-500/20"
          >
            Swagger /docs <ExternalLink className="w-3 h-3" />
          </a>
          <a
            href="http://localhost:8000/metrics"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs font-mono text-rose-400 hover:text-rose-300 bg-rose-500/10 px-3 py-1 rounded border border-rose-500/20"
          >
            /metrics <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      <div className="space-y-4 mt-4">
        {steps.map((step, idx) => (
          <div key={idx} className="bg-slate-950 border border-slate-800 rounded-lg p-3.5">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-200">{step.title}</span>
              <button
                onClick={() => copyToClipboard(step.cmd, idx)}
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
              >
                {copiedIndex === idx ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span className="text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    Copy
                  </>
                )}
              </button>
            </div>
            <p className="text-[11px] text-slate-400 mb-2">{step.desc}</p>
            <div className="bg-slate-900 border border-slate-800/80 rounded px-3 py-2 font-mono text-xs text-indigo-300 flex items-center justify-between">
              <code>{step.cmd}</code>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
