import React, { useState } from 'react';
import { ArchitectureDiagram } from './components/ArchitectureDiagram';
import { ServiceStatusBanner } from './components/ServiceStatusBanner';
import { UploadArea } from './components/UploadArea';
import { JobsPlayground } from './components/JobsPlayground';
import { MetricsViewer } from './components/MetricsViewer';
import { CollegeDemoGuide } from './components/CollegeDemoGuide';
import { JobRecord, UploadedMediaItem } from './types';
import { Cpu, Terminal, Shield, Sparkles, Server } from 'lucide-react';

export default function App() {
  const [selectedFile, setSelectedFile] = useState<UploadedMediaItem | null>(null);

  const [jobs, setJobs] = useState<JobRecord[]>([
    {
      job_id: 'job_init_39a1',
      celery_task_id: 'celery_7f9b8c2d1e0a',
      status: 'COMPLETED',
      operation: 'resize_image',
      media_type: 'image',
      input_filename: 'sample_product.jpg',
      parameters: { width: 640, height: 480, quality: 80 },
      created_at: new Date(Date.now() - 60000).toISOString(),
      started_at: new Date(Date.now() - 59000).toISOString(),
      completed_at: new Date(Date.now() - 58000).toISOString(),
      input_size: 148500,
      output_size: 42300,
      processing_time: 0.038,
      download_url: '#download-job_init_39a1',
    },
    {
      job_id: 'job_init_41b2',
      celery_task_id: 'celery_3c5d6e7f8a9b',
      status: 'COMPLETED',
      operation: 'video_thumbnail',
      media_type: 'video',
      input_filename: 'sample_lecture.mp4',
      parameters: { timestamp_sec: 1.5, width: 640 },
      created_at: new Date(Date.now() - 30000).toISOString(),
      started_at: new Date(Date.now() - 29000).toISOString(),
      completed_at: new Date(Date.now() - 27500).toISOString(),
      input_size: 3420000,
      output_size: 38400,
      processing_time: 0.742,
      download_url: '#download-job_init_41b2',
    },
  ]);

  const handleJobDispatched = (updatedJob: JobRecord) => {
    setJobs((prev) => {
      const idx = prev.findIndex((j) => j.job_id === updatedJob.job_id);
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx] = updatedJob;
        return copy;
      }
      return [updatedJob, ...prev];
    });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500/30">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/20 shrink-0">
              <Cpu className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold text-slate-100 tracking-tight">
                  Distributed Media Processing Microservice
                </h1>
                <span className="hidden md:inline-flex text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  v1.0.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono">
                FastAPI • Celery • RabbitMQ • Redis • Pillow • FFmpeg
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div
              id="cluster-status-badge"
              className="flex items-center gap-2 text-xs font-mono bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-md"
            >
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              <span className="text-slate-300">Environment: Preview Mode</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Dashboard */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Real Cluster Node Status (Honest reporting: Development Mode / Not connected) */}
        <section id="section-service-status">
          <ServiceStatusBanner />
        </section>

        {/* Media Ingress & Upload Area */}
        <section id="section-upload">
          <UploadArea currentFile={selectedFile} onFileSelect={setSelectedFile} />
        </section>

        {/* Architecture & Flow Topology */}
        <section id="section-architecture">
          <ArchitectureDiagram />
        </section>

        {/* Live Jobs Processing Playground */}
        <section id="section-playground">
          <JobsPlayground
            selectedFile={selectedFile}
            onJobDispatched={handleJobDispatched}
            recentJobs={jobs}
          />
        </section>

        {/* Metrics & Observability */}
        <section id="section-metrics">
          <MetricsViewer jobs={jobs} />
        </section>

        {/* College Demo Presentation Guide & Docker Compose */}
        <section id="section-guide">
          <CollegeDemoGuide />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 font-mono">
        <p>Distributed Media Processing Microservice • College Demonstration Platform</p>
        <p className="text-[11px] text-slate-600 mt-1">
          FastAPI Backend Engine: <code className="text-indigo-400">/media-processing-service</code> • Docker Compose Ready
        </p>
      </footer>
    </div>
  );
}
