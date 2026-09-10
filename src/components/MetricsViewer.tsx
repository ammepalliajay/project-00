import React, { useState } from 'react';
import { Activity, Check, Clock, Layers, Code, Terminal, ChevronDown, ChevronUp } from 'lucide-react';
import { JobRecord } from '../types';

interface MetricsViewerProps {
  jobs: JobRecord[];
}

export const MetricsViewer: React.FC<MetricsViewerProps> = ({ jobs }) => {
  const [showRawPrometheus, setShowRawPrometheus] = useState<boolean>(false);

  const total = jobs.length;
  const completed = jobs.filter((j) => j.status === 'COMPLETED').length;
  const failed = jobs.filter((j) => j.status === 'FAILED').length;
  const active = jobs.filter((j) => j.status === 'PROCESSING' || j.status === 'PENDING').length;
  const avgDuration =
    completed > 0
      ? (
          jobs
            .filter((j) => j.processing_time !== undefined)
            .reduce((acc, curr) => acc + (curr.processing_time || 0), 0) / completed
        ).toFixed(3)
      : '0.000';

  const rawPrometheusText = `# HELP media_jobs_total Total count of media processing jobs dispatched
# TYPE media_jobs_total counter
media_jobs_total{operation="resize_image",media_type="image"} ${jobs.filter((j) => j.operation === 'resize_image').length}
media_jobs_total{operation="compress_image",media_type="image"} ${jobs.filter((j) => j.operation === 'compress_image').length}
media_jobs_total{operation="video_thumbnail",media_type="video"} ${jobs.filter((j) => j.operation === 'video_thumbnail').length}

# HELP media_jobs_completed_total Total completed jobs
# TYPE media_jobs_completed_total counter
media_jobs_completed_total ${completed}

# HELP media_jobs_active_gauge Currently in-flight jobs in RabbitMQ / Celery
# TYPE media_jobs_active_gauge gauge
media_jobs_active_gauge ${active}

# HELP media_jobs_failed_total Total failed jobs
# TYPE media_jobs_failed_total counter
media_jobs_failed_total ${failed}

# HELP media_processing_duration_seconds Average processing duration
# TYPE media_processing_duration_seconds gauge
media_processing_duration_seconds ${avgDuration}`;

  return (
    <div id="metrics-viewer" className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Activity className="w-4 h-4 text-rose-400" />
            Prometheus Observability Engine
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Decoupled worker telemetry scraped at <code className="text-rose-300 font-mono">/metrics</code>
          </p>
        </div>

        <button
          onClick={() => setShowRawPrometheus(!showRawPrometheus)}
          className="flex items-center gap-1.5 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition-colors cursor-pointer"
        >
          <Code className="w-3.5 h-3.5 text-indigo-400" />
          <span>{showRawPrometheus ? 'Hide Scrape Output' : 'View /metrics Scrape'}</span>
          {showRawPrometheus ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Metric Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
        <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            media_jobs_total
          </div>
          <div className="text-xl font-mono font-bold text-slate-100">{total}</div>
          <div className="text-[10px] text-slate-500 mt-1">Dispatched jobs</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Check className="w-3.5 h-3.5 text-emerald-400" />
            media_jobs_completed
          </div>
          <div className="text-xl font-mono font-bold text-emerald-400">{completed}</div>
          <div className="text-[10px] text-slate-500 mt-1">HTTP 200 outputs</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            media_jobs_active_gauge
          </div>
          <div className="text-xl font-mono font-bold text-amber-400">{active}</div>
          <div className="text-[10px] text-slate-500 mt-1">In queue / processing</div>
        </div>

        <div className="bg-slate-950 border border-slate-800 p-3.5 rounded-lg">
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            avg_duration (sec)
          </div>
          <div className="text-xl font-mono font-bold text-cyan-400">{avgDuration}s</div>
          <div className="text-[10px] text-slate-500 mt-1">Worker exec mean</div>
        </div>
      </div>

      {/* Raw Prometheus Exporter Output */}
      {showRawPrometheus && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2 font-mono">
            <div className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-rose-400" />
              <span>Prometheus Standard Exposition Format (Content-Type: text/plain; version=0.0.4)</span>
            </div>
          </div>
          <pre className="bg-slate-950 border border-slate-800 rounded-lg p-3.5 text-emerald-400/90 font-mono text-[11px] overflow-x-auto leading-relaxed">
            {rawPrometheusText}
          </pre>
        </div>
      )}
    </div>
  );
};
