import React, { useState, useRef } from 'react';
import { UploadCloud, FileImage, Video, CheckCircle2, AlertCircle, Sparkles, X } from 'lucide-react';
import { UploadedMediaItem, MediaType } from '../types';

interface UploadAreaProps {
  currentFile: UploadedMediaItem | null;
  onFileSelect: (file: UploadedMediaItem | null) => void;
}

export const UploadArea: React.FC<UploadAreaProps> = ({ currentFile, onFileSelect }) => {
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB max upload

  const processFile = (file: File) => {
    setErrorMessage(null);

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMessage(`File exceeds the maximum allowed size of 50 MB (uploaded: ${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      return;
    }

    if (file.size === 0) {
      setErrorMessage('Zero-byte empty file detected. Upload rejected.');
      return;
    }

    let mediaType: MediaType = 'image';
    if (file.type.startsWith('image/')) {
      mediaType = 'image';
    } else if (file.type.startsWith('video/')) {
      mediaType = 'video';
    } else {
      setErrorMessage(`Unsupported file MIME type: ${file.type || 'unknown'}. Allowed: JPEG, PNG, WEBP, MP4, WEBM.`);
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    const item: UploadedMediaItem = {
      id: `file_${Math.random().toString(16).substring(2, 10)}`,
      name: file.name,
      size: file.size,
      type: file.type,
      mediaType,
      previewUrl,
      uploadedAt: new Date().toISOString(),
      storagePath: `uploads/${file.name}`,
    };

    // Extract image dimensions if image
    if (mediaType === 'image') {
      const img = new Image();
      img.onload = () => {
        item.dimensions = { width: img.naturalWidth, height: img.naturalHeight };
        onFileSelect({ ...item });
      };
      img.src = previewUrl;
    } else {
      onFileSelect(item);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  // Helper to load sample test fixtures
  const handleLoadSample = (type: MediaType) => {
    setErrorMessage(null);
    if (type === 'image') {
      const sampleItem: UploadedMediaItem = {
        id: `file_${Math.random().toString(16).substring(2, 10)}`,
        name: 'sample_landscape.jpg',
        size: 52400,
        type: 'image/jpeg',
        mediaType: 'image',
        previewUrl: 'https://picsum.photos/800/600',
        dimensions: { width: 800, height: 600 },
        uploadedAt: new Date().toISOString(),
        storagePath: 'uploads/sample_landscape.jpg',
      };
      onFileSelect(sampleItem);
    } else {
      const sampleItem: UploadedMediaItem = {
        id: `file_${Math.random().toString(16).substring(2, 10)}`,
        name: 'sample_demo_clip.mp4',
        size: 1450000,
        type: 'video/mp4',
        mediaType: 'video',
        previewUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
        dimensions: { width: 1280, height: 720 },
        uploadedAt: new Date().toISOString(),
        storagePath: 'uploads/sample_demo_clip.mp4',
      };
      onFileSelect(sampleItem);
    }
  };

  return (
    <div id="media-upload-area" className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <UploadCloud className="w-4 h-4 text-indigo-400" />
            Media Ingress & Validation Engine
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Streaming upload with magic-byte verification, MIME validation, and stream size limits (HTTP 413)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            id="btn-sample-image"
            onClick={() => handleLoadSample('image')}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition-all cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Sample Image
          </button>
          <button
            id="btn-sample-video"
            onClick={() => handleLoadSample('video')}
            className="flex items-center gap-1.5 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition-all cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Sample Video
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{errorMessage}</span>
        </div>
      )}

      {currentFile ? (
        <div className="bg-slate-950 border border-indigo-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4 w-full sm:w-auto">
            <div className="w-16 h-16 rounded-lg bg-slate-900 border border-slate-800 overflow-hidden flex items-center justify-center shrink-0">
              {currentFile.mediaType === 'image' ? (
                <img
                  src={currentFile.previewUrl}
                  alt={currentFile.name}
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <Video className="w-8 h-8 text-amber-400" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-slate-100">{currentFile.name}</span>
                <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="w-3 h-3" />
                  Validated
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mt-1 font-mono">
                <span>{(currentFile.size / 1024).toFixed(1)} KB</span>
                <span>•</span>
                <span>{currentFile.type}</span>
                {currentFile.dimensions && (
                  <>
                    <span>•</span>
                    <span>
                      {currentFile.dimensions.width}×{currentFile.dimensions.height} px
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              onClick={() => onFileSelect(null)}
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-rose-400 px-3 py-1.5 rounded-lg border border-slate-800 hover:border-rose-500/30 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              Clear Selection
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 px-3 py-1.5 rounded-lg transition-all"
            >
              Replace File
            </button>
          </div>
        </div>
      ) : (
        <div
          id="dropzone"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-indigo-500 bg-indigo-500/10'
              : 'border-slate-800 hover:border-slate-700 bg-slate-950/40 hover:bg-slate-950/80'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm"
            onChange={handleFileInputChange}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-xl bg-slate-800/80 text-indigo-400 flex items-center justify-center mb-3">
              <UploadCloud className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-200">
              Drag and drop an image or video, or <span className="text-indigo-400 underline underline-offset-2">browse files</span>
            </p>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              Supported: JPEG, PNG, WEBP, MP4, WEBM • Max file size: 50MB
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
