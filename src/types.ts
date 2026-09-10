export type MediaType = 'image' | 'video';

export type ImageOperation =
  | 'resize_image'
  | 'crop_image'
  | 'compress_image'
  | 'convert_image'
  | 'watermark_image';

export type VideoOperation =
  | 'video_thumbnail'
  | 'video_compress'
  | 'video_transcode';

export type OperationType = ImageOperation | VideoOperation;

export type JobStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface UploadedMediaItem {
  id: string;
  name: string;
  size: number;
  type: string;
  mediaType: MediaType;
  previewUrl: string;
  dimensions?: { width: number; height: number };
  uploadedAt: string;
  storagePath: string;
}

export interface JobRecord {
  job_id: string;
  status: JobStatus;
  operation: OperationType;
  media_type: MediaType;
  input_filename: string;
  parameters: Record<string, any>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  processing_time?: number;
  input_size: number;
  output_size?: number;
  output_url?: string;
  download_url?: string;
  celery_task_id?: string;
  error?: string;
  retry_count?: number;
}

export type ConnectionStatus = 'connected' | 'not_connected' | 'development_mode';

export interface ServiceNodeStatus {
  id: string;
  name: string;
  role: string;
  status: ConnectionStatus;
  statusText: string;
  hostPort: string;
  detail: string;
}
