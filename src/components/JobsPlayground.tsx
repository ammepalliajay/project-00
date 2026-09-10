import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Play,
  CheckCircle2,
  Clock,
  Download,
  AlertTriangle,
  FileImage,
  Video,
  FileCheck,
  RefreshCw,
  ExternalLink,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import { JobRecord, MediaType, OperationType, UploadedMediaItem } from '../types';

interface JobsPlaygroundProps {
  selectedFile: UploadedMediaItem | null;
  onJobDispatched: (job: JobRecord) => void;
  recentJobs: JobRecord[];
}

export const JobsPlayground: React.FC<JobsPlaygroundProps> = ({
  selectedFile,
  onJobDispatched,
  recentJobs,
}) => {
  const [mediaType, setMediaType] = useState<MediaType>('image');
  const [operation, setOperation] = useState<OperationType>('resize_image');
  const [width, setWidth] = useState<number>(640);
  const [height, setHeight] = useState<number>(480);
  const [quality, setQuality] = useState<number>(80);
  const [targetFormat, setTargetFormat] = useState<string>('WEBP');
  const [watermarkText, setWatermarkText] = useState<string>('DISTRIBUTED-MEDIA');
  const [timestampSec, setTimestampSec] = useState<number>(1.5);
  const [crf, setCrf] = useState<number>(26);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'all' | 'active' | 'completed'>('all');
  const [previewModalJob, setPreviewModalJob] = useState<JobRecord | null>(null);

  // Sync with uploaded file when provided
  useEffect(() => {
    if (selectedFile) {
      setMediaType(selectedFile.mediaType);
      if (selectedFile.mediaType === 'image') {
        setOperation('resize_image');
        if (selectedFile.dimensions) {
          setWidth(Math.round(selectedFile.dimensions.width / 2) || 640);
          setHeight(Math.round(selectedFile.dimensions.height / 2) || 480);
        }
      } else {
        setOperation('video_thumbnail');
      }
    }
  }, [selectedFile]);

  const handleMediaTypeChange = (type: MediaType) => {
    setMediaType(type);
    if (type === 'image') {
      setOperation('resize_image');
    } else {
      setOperation('video_thumbnail');
    }
  };

  const handleSubmitJob = () => {
    setIsSubmitting(true);
    const jobId = `job_${Math.random().toString(16).substring(2, 10)}`;
    const celeryTaskId = `celery_${Math.random().toString(36).substring(2, 15)}`;

    const filename = selectedFile?.name || (mediaType === 'image' ? 'input_image.jpg' : 'input_video.mp4');
    const inputSize = selectedFile?.size || (mediaType === 'image' ? 128000 : 2850000);

    const initialJob: JobRecord = {
      job_id: jobId,
      celery_task_id: celeryTaskId,
      status: 'PENDING',
      operation,
      media_type: mediaType,
      input_filename: filename,
      parameters: {
        width: ['resize_image', 'video_thumbnail', 'video_transcode'].includes(operation) ? width : undefined,
        height: ['resize_image', 'video_transcode'].includes(operation) ? height : undefined,
        quality: ['compress_image', 'resize_image'].includes(operation) ? quality : undefined,
        format: operation === 'convert_image' ? targetFormat : undefined,
        watermark_text: operation === 'watermark_image' ? watermarkText : undefined,
        timestamp_sec: operation === 'video_thumbnail' ? timestampSec : undefined,
        crf: operation === 'video_compress' ? crf : undefined,
      },
      created_at: new Date().toISOString(),
      input_size: inputSize,
      retry_count: 0,
    };

    onJobDispatched(initialJob);

    // Transition 1: Picked up by Celery worker
    setTimeout(() => {
      onJobDispatched({
        ...initialJob,
        status: 'PROCESSING',
        started_at: new Date().toISOString(),
      });
    }, 700);

    // Transition 2: Completed processing with output payload
    setTimeout(() => {
      const processingTime = mediaType === 'image' ? +(Math.random() * 0.08 + 0.02).toFixed(3) : +(Math.random() * 0.9 + 0.45).toFixed(3);
      const compressionRatio = operation.includes('compress') ? 0.42 : operation === 'video_thumbnail' ? 0.05 : 0.68;
      const outputSize = Math.max(1024, Math.round(inputSize * compressionRatio));

      onJobDispatched({
        ...initialJob,
        status: 'COMPLETED',
        started_at: new Date(Date.now() - 1000).toISOString(),
        completed_at: new Date().toISOString(),
        processing_time: processingTime,
        output_size: outputSize,
        output_url: selectedFile?.previewUrl || (mediaType === 'image' ? 'https://picsum.photos/640/480' : ''),
        download_url: `#download-${jobId}`,
      });
      setIsSubmitting(false);
    }, 2200);
  };

  const filteredJobs = recentJobs.filter((job) => {
    if (activeTab === 'active') return job.status === 'PENDING' || job.status === 'PROCESSING';
    if (activeTab === 'completed') return job.status === 'COMPLETED';
    return true;
  });

  return (
    <div id="jobs-playground" className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Configuration & Dispatch Panel */}
      <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-400" />
                Job Dispatch Engine
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                FastAPI schema validation & AMQP event emission to Celery
              </p>
            </div>

            {selectedFile && (
              <span className="text-[10px] font-mono text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2 py-1 rounded">
                Attached: {selectedFile.name.substring(0, 16)}
              </span>
            )}
          </div>

          {/* Media Category Selection */}
          <div className="flex gap-2 p-1 bg-slate-950 border border-slate-800 rounded-lg mb-4">
            <button
              id="btn-tab-image"
              onClick={() => handleMediaTypeChange('image')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-medium rounded-md transition-all cursor-pointer ${
                mediaType === 'image'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <FileImage className="w-3.5 h-3.5" />
              Image Pipeline (Pillow)
            </button>
            <button
              id="btn-tab-video"
              onClick={() => handleMediaTypeChange('video')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-medium rounded-md transition-all cursor-pointer ${
                mediaType === 'video'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Video className="w-3.5 h-3.5" />
              Video Pipeline (FFmpeg)
            </button>
          </div>

          {/* Operation & Parameter Forms */}
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Processing Operation</label>
              <select
                id="select-operation"
                value={operation}
                onChange={(e) => setOperation(e.target.value as OperationType)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                {mediaType === 'image' ? (
                  <>
                    <option value="resize_image">Resize Image (Lanczos Resampling)</option>
                    <option value="crop_image">Crop Image (Bounding Coordinates)</option>
                    <option value="compress_image">Compress Image (Quality & Strip Metadata)</option>
                    <option value="convert_image">Convert Format (JPEG / PNG / WEBP)</option>
                    <option value="watermark_image">Overlay Text Watermark (Bottom-Right)</option>
                  </>
                ) : (
                  <>
                    <option value="video_thumbnail">Extract Frame Thumbnail (FFmpeg -ss)</option>
                    <option value="video_compress">Video Compression (H.264 CRF Tuning)</option>
                    <option value="video_transcode">Transcode Resolution & FPS (Scale Filter)</option>
                  </>
                )}
              </select>
            </div>

            {/* Dynamic Parameter Settings */}
            {(operation === 'resize_image' || operation === 'video_thumbnail' || operation === 'video_transcode') && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Target Width (px)</label>
                  <input
                    id="input-param-width"
                    type="number"
                    value={width}
                    onChange={(e) => setWidth(Math.max(16, Number(e.target.value)))}
                    className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-slate-400 mb-1">Target Height (px)</label>
                  <input
                    id="input-param-height"
                    type="number"
                    value={height}
                    onChange={(e) => setHeight(Math.max(16, Number(e.target.value)))}
                    className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                  />
                </div>
              </div>
            )}

            {(operation === 'compress_image' || operation === 'resize_image') && (
              <div>
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Compression Quality Level</span>
                  <span className="font-mono text-indigo-400">{quality}%</span>
                </div>
                <input
                  id="slider-quality"
                  type="range"
                  min="10"
                  max="100"
                  value={quality}
                  onChange={(e) => setQuality(Number(e.target.value))}
                  className="w-full accent-indigo-500 cursor-pointer"
                />
              </div>
            )}

            {operation === 'convert_image' && (
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Target Format</label>
                <select
                  id="select-convert-format"
                  value={targetFormat}
                  onChange={(e) => setTargetFormat(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                >
                  <option value="WEBP">WEBP (Optimized for Web Delivery)</option>
                  <option value="JPEG">JPEG (Universal Baseline)</option>
                  <option value="PNG">PNG (Lossless with Alpha Channel)</option>
                </select>
              </div>
            )}

            {operation === 'watermark_image' && (
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Watermark Overlay Text</label>
                <input
                  id="input-watermark-text"
                  type="text"
                  value={watermarkText}
                  onChange={(e) => setWatermarkText(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                />
              </div>
            )}

            {operation === 'video_thumbnail' && (
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Seek Timestamp Offset (Seconds)</label>
                <input
                  id="input-video-timestamp"
                  type="number"
                  step="0.1"
                  value={timestampSec}
                  onChange={(e) => setTimestampSec(Math.max(0, Number(e.target.value)))}
                  className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200"
                />
              </div>
            )}

            {operation === 'video_compress' && (
              <div>
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Constant Rate Factor (CRF: 18=Lossless, 36=High Compression)</span>
                  <span className="font-mono text-amber-400">{crf}</span>
                </div>
                <input
                  id="slider-crf"
                  type="range"
                  min="18"
                  max="36"
                  value={crf}
                  onChange={(e) => setCrf(Number(e.target.value))}
                  className="w-full accent-amber-500 cursor-pointer"
                />
              </div>
            )}
          </div>
        </div>

        {/* Action Button */}
        <div className="mt-6 pt-4 border-t border-slate-800">
          <button
            id="btn-dispatch-job"
            onClick={handleSubmitJob}
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Validating & Publishing to RabbitMQ...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Dispatch Asynchronous Job
              </>
            )}
          </button>
          <div className="text-[10px] text-slate-500 text-center mt-2 font-mono">
            FastAPI returns HTTP 202 Accepted + Celery Task UUID in {'<'} 15ms
          </div>
        </div>
      </div>

      {/* Task Queue & Live Execution Feed */}
      <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <div>
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <Clock className="w-4 h-4 text-emerald-400" />
                Redis Task Status Stream
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Real-time lifecycle inspection: PENDING → PROCESSING → COMPLETED
              </p>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-[10px] font-mono">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-2 py-1 rounded transition-colors ${
                  activeTab === 'all' ? 'bg-slate-800 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                All ({recentJobs.length})
              </button>
              <button
                onClick={() => setActiveTab('active')}
                className={`px-2 py-1 rounded transition-colors ${
                  activeTab === 'active' ? 'bg-slate-800 text-amber-300 font-semibold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Active ({recentJobs.filter((j) => j.status === 'PENDING' || j.status === 'PROCESSING').length})
              </button>
              <button
                onClick={() => setActiveTab('completed')}
                className={`px-2 py-1 rounded transition-colors ${
                  activeTab === 'completed' ? 'bg-slate-800 text-emerald-400 font-semibold' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Done ({recentJobs.filter((j) => j.status === 'COMPLETED').length})
              </button>
            </div>
          </div>

          {/* Jobs List */}
          <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1">
            {filteredJobs.length === 0 ? (
              <div className="h-full min-h-[220px] flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-800 rounded-lg text-slate-500">
                <FileCheck className="w-8 h-8 text-slate-600 mb-2" />
                <p className="text-xs font-medium text-slate-400">No jobs matching current filter</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Upload an asset and click "Dispatch Asynchronous Job"
                </p>
              </div>
            ) : (
              filteredJobs.map((job) => {
                const compressionPercent =
                  job.output_size && job.input_size
                    ? Math.round(((job.input_size - job.output_size) / job.input_size) * 100)
                    : null;

                return (
                  <div
                    key={job.job_id}
                    id={`job-card-${job.job_id}`}
                    className="bg-slate-950 border border-slate-800 hover:border-slate-700/80 transition-colors rounded-lg p-3.5 text-xs text-slate-300"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-100">{job.job_id}</span>
                        <span className="text-[10px] font-mono bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded border border-slate-700">
                          {job.operation}
                        </span>
                      </div>

                      {/* Status Badges */}
                      {job.status === 'COMPLETED' && (
                        <span className="flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" />
                          COMPLETED
                        </span>
                      )}
                      {job.status === 'PROCESSING' && (
                        <span className="flex items-center gap-1 text-[10px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full border border-indigo-500/20">
                          <RefreshCw className="w-3 h-3 animate-spin" />
                          PROCESSING (Worker-01)
                        </span>
                      )}
                      {job.status === 'PENDING' && (
                        <span className="flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                          <Clock className="w-3 h-3" />
                          PENDING (RabbitMQ)
                        </span>
                      )}
                      {job.status === 'FAILED' && (
                        <span className="flex items-center gap-1 text-[10px] font-mono text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                          <AlertTriangle className="w-3 h-3" />
                          FAILED
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] text-slate-400 bg-slate-900/60 p-2.5 rounded-md mt-2">
                      <div>
                        File: <span className="font-mono text-slate-200 block truncate">{job.input_filename}</span>
                      </div>
                      <div>
                        Input Size: <span className="font-mono text-slate-200 block">{(job.input_size / 1024).toFixed(1)} KB</span>
                      </div>
                      <div>
                        Output Size:
                        <span className="font-mono text-slate-200 block">
                          {job.output_size ? `${(job.output_size / 1024).toFixed(1)} KB` : 'Computing...'}
                        </span>
                      </div>

                      {job.processing_time && (
                        <div className="col-span-2 text-emerald-400 font-mono text-[10px]">
                          Worker Duration: {job.processing_time}s
                          {compressionPercent !== null && (
                            <span className="ml-2 text-indigo-300">
                              (Saved {compressionPercent > 0 ? `${compressionPercent}%` : '0%'})
                            </span>
                          )}
                        </div>
                      )}

                      {job.celery_task_id && (
                        <div className="col-span-full text-[10px] font-mono text-slate-500 truncate">
                          Task ID: {job.celery_task_id}
                        </div>
                      )}
                    </div>

                    {job.status === 'COMPLETED' && (
                      <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-mono">
                          Finished: {new Date(job.completed_at || '').toLocaleTimeString()}
                        </span>
                        <button
                          onClick={() => setPreviewModalJob(job)}
                          className="flex items-center gap-1 text-[11px] font-medium text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer"
                        >
                          <ExternalLink className="w-3 h-3" />
                          View Output Payload
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Worker Concurrency: 2 Slots (Non-blocking AMQP prefetch=1)</span>
          <span className="font-mono text-slate-400">Queue: media.tasks</span>
        </div>
      </div>

      {/* Payload Modal */}
      {previewModalJob && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h4 className="text-sm font-bold text-slate-100">Job Result Payload</h4>
              </div>
              <button
                onClick={() => setPreviewModalJob(null)}
                className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800"
              >
                Close
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="text-slate-400 font-mono text-[11px]">
                FastAPI Response Schema (<code className="text-indigo-300">GET /api/v1/jobs/{previewModalJob.job_id}</code>):
              </div>
              <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-slate-300 font-mono text-[11px] overflow-x-auto leading-relaxed">
                {JSON.stringify(
                  {
                    job_id: previewModalJob.job_id,
                    celery_task_id: previewModalJob.celery_task_id,
                    status: previewModalJob.status,
                    operation: previewModalJob.operation,
                    input_filename: previewModalJob.input_filename,
                    parameters: previewModalJob.parameters,
                    created_at: previewModalJob.created_at,
                    completed_at: previewModalJob.completed_at,
                    processing_time: previewModalJob.processing_time,
                    input_size_bytes: previewModalJob.input_size,
                    output_size_bytes: previewModalJob.output_size,
                    storage_provider: 'local_volume (s3_ready)',
                  },
                  null,
                  2
                )}
              </pre>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setPreviewModalJob(null)}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
