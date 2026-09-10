import React from 'react';
import { Server, MessageSquare, Database, Cpu, HardDrive, Info, AlertCircle, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { ServiceNodeStatus } from '../types';

export const ServiceStatusBanner: React.FC = () => {
  const services: ServiceNodeStatus[] = [
    {
      id: 'fastapi',
      name: 'FastAPI Producer',
      role: 'Ingress & Validation API',
      status: 'development_mode',
      statusText: 'Development / Preview Mode',
      hostPort: 'port 8000 (prod) / 3000 (web)',
      detail: 'API ingress active; validates jobs according to Pydantic schemas and routes tasks.',
    },
    {
      id: 'rabbitmq',
      name: 'RabbitMQ Broker',
      role: 'Message Broker (AMQP 0-9-1)',
      status: 'not_connected',
      statusText: 'Not connected',
      hostPort: 'port 5672 / 15672 (management)',
      detail: 'External container required. Launch via `docker compose up` for live broker queues.',
    },
    {
      id: 'redis',
      name: 'Redis Cache',
      role: 'State Store & Task Metadata',
      status: 'not_connected',
      statusText: 'Not connected',
      hostPort: 'port 6379',
      detail: 'In-memory state backend. Persists PENDING → PROCESSING → COMPLETED states in production.',
    },
    {
      id: 'celery',
      name: 'Celery Workers',
      role: 'Async Media Engine (Pillow/FFmpeg)',
      status: 'not_connected',
      statusText: 'Not connected',
      hostPort: 'concurrency -c 2 (worker container)',
      detail: 'Heavy compute cluster. Executed inside dedicated non-root worker container.',
    },
    {
      id: 'storage',
      name: 'Storage Subsystem',
      role: 'Local Volume / AWS S3',
      status: 'development_mode',
      statusText: 'Preview Sandbox',
      hostPort: 'shared_volume / S3 Boto3',
      detail: 'Client-side media memory in preview; shared docker volume / AWS S3 in production.',
    },
  ];

  const getStatusBadge = (status: ServiceNodeStatus['status'], text: string) => {
    switch (status) {
      case 'development_mode':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Info className="w-3 h-3" />
            {text}
          </span>
        );
      case 'not_connected':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3 h-3" />
            {text}
          </span>
        );
      case 'connected':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            {text}
          </span>
        );
    }
  };

  const getServiceIcon = (id: string) => {
    switch (id) {
      case 'fastapi':
        return <Server className="w-4 h-4 text-indigo-400" />;
      case 'rabbitmq':
        return <MessageSquare className="w-4 h-4 text-amber-400" />;
      case 'redis':
        return <Database className="w-4 h-4 text-rose-400" />;
      case 'celery':
        return <Cpu className="w-4 h-4 text-emerald-400" />;
      default:
        return <HardDrive className="w-4 h-4 text-cyan-400" />;
    }
  };

  return (
    <div id="service-status-banner" className="space-y-4">
      {/* Informational Notification */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-md">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center shrink-0 mt-0.5">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-200 flex items-center gap-2">
              <span>Environment Status: Google AI Studio Sandbox (UI Preview & Verification Mode)</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
              RabbitMQ, Redis, and Celery worker daemons require local Docker execution. The interactive dashboard allows you to test uploads, configure transformations, and observe task lifecycles in preview, while the production backend in <code className="text-indigo-300 font-mono">/media-processing-service</code> is configured for <code className="text-indigo-300 font-mono">docker compose up --build</code>.
            </p>
          </div>
        </div>

        <div className="shrink-0 flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
          <span>Dual Mode Architecture Active</span>
        </div>
      </div>

      {/* Grid of Microservice Nodes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {services.map((svc) => (
          <div
            key={svc.id}
            id={`service-card-${svc.id}`}
            className="bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-colors rounded-lg p-3.5 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="w-7 h-7 rounded-md bg-slate-800 flex items-center justify-center">
                  {getServiceIcon(svc.id)}
                </div>
                {getStatusBadge(svc.status, svc.statusText)}
              </div>
              <div className="text-xs font-bold text-slate-100">{svc.name}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{svc.role}</div>
            </div>

            <div className="mt-3 pt-2.5 border-t border-slate-800/80">
              <div className="text-[10px] font-mono text-slate-500 mb-1">{svc.hostPort}</div>
              <div className="text-[10px] text-slate-400 line-clamp-2 leading-relaxed">{svc.detail}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
