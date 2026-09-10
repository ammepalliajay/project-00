import React from 'react';
import { ArrowRight, Server, MessageSquare, Cpu, Database, HardDrive, CheckCircle2, ShieldCheck } from 'lucide-react';

export const ArchitectureDiagram: React.FC = () => {
  return (
    <div id="architecture-diagram" className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            Distributed Asynchronous Architecture
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Event-driven pipeline decoupling high-throughput API ingress from compute-heavy media rendering
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20 px-3 py-1.5 rounded-full">
          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
          Docker Compose Blueprint (Dev Mode)
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-6 items-center">
        {/* Node 1: Client & FastAPI */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-4 flex flex-col items-center text-center">
          <div className="w-10 h-10 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-2">
            <Server className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-200">FastAPI Producer</span>
          <span className="text-[11px] text-slate-400 mt-0.5">Validation & Ingress</span>
          <span className="text-[10px] font-mono text-amber-300 mt-2 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
            Preview / Port 8000
          </span>
        </div>

        {/* Arrow 1 */}
        <div className="hidden md:flex flex-col items-center text-slate-500">
          <span className="text-[10px] font-mono text-slate-400 mb-1">AMQP Publish</span>
          <ArrowRight className="w-5 h-5 text-slate-600" />
        </div>

        {/* Node 2: RabbitMQ */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-4 flex flex-col items-center text-center">
          <div className="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center mb-2">
            <MessageSquare className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-200">RabbitMQ Broker</span>
          <span className="text-[11px] text-slate-400 mt-0.5">Task Queue & Dead-letter</span>
          <span className="text-[10px] font-mono text-rose-300 mt-2 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
            Not connected (Docker)
          </span>
        </div>

        {/* Arrow 2 */}
        <div className="hidden md:flex flex-col items-center text-slate-500">
          <span className="text-[10px] font-mono text-slate-400 mb-1">Prefetch = 1</span>
          <ArrowRight className="w-5 h-5 text-slate-600" />
        </div>

        {/* Node 3: Celery Workers */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-4 flex flex-col items-center text-center">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-2">
            <Cpu className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-200">Celery Workers</span>
          <span className="text-[11px] text-slate-400 mt-0.5">Pillow & FFmpeg (2x)</span>
          <span className="text-[10px] font-mono text-rose-300 mt-2 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
            Not connected (Docker)
          </span>
        </div>
      </div>

      {/* Auxiliary Systems Row: Redis & Storage */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 pt-5 border-t border-slate-800">
        <div className="flex items-center gap-3 bg-slate-800/40 border border-slate-800 p-3 rounded-lg">
          <div className="w-9 h-9 rounded-md bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
            <Database className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold text-slate-200">Redis In-Memory State Store</div>
              <span className="text-[10px] font-mono text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded">Not connected</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">Stores atomic status updates: PENDING → PROCESSING → COMPLETED</div>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-slate-800/40 border border-slate-800 p-3 rounded-lg">
          <div className="w-9 h-9 rounded-md bg-cyan-500/20 text-cyan-400 flex items-center justify-center shrink-0">
            <HardDrive className="w-4 h-4" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold text-slate-200">Storage Subsystem</div>
              <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">Preview Sandbox</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">Local browser storage in preview; shared docker volume / AWS S3 in production</div>
          </div>
        </div>
      </div>
    </div>
  );
};
