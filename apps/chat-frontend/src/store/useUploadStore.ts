import { create } from 'zustand';
import { getApiHost } from '@/lib/apiBase';
import { apiFetch } from '@/lib/apiFetch';

export interface ExtractedFinding {
  key: string;
  value: string;
  category: 'temperature' | 'corrosion' | 'tag' | 'sop_clause' | 'specification' | 'equipment' | 'operational';
  confidence: number;
  source_page?: number;
  highlight?: boolean;
}

export interface UploadedDocument {
  id: string;
  name: string;
  size_bytes: number;
  size_formatted: string;
  mime_type: string;
  type: 'inspection_pdf' | 'pid_drawing' | 'general';
  upload_timestamp: string;
  sha256_hash: string;
  ocr_engine: string;
  findings: ExtractedFinding[];
  raw_ocr_text: string;
  sop_violations: string[];
  status: 'pending' | 'processing' | 'ready' | 'error';
}

export type ProcessingStage = 
  | 'idle'
  | 'uploading' 
  | 'ocr_processing' 
  | 'vision_analyzing' 
  | 'chromadb_lookup' 
  | 'completed' 
  | 'error';

interface UploadState {
  documents: UploadedDocument[];
  selectedDocId: string | null;
  currentStage: ProcessingStage;
  stageProgress: number; // 0 - 100
  stageMessage: string;
  validationError: string | null;

  // Actions
  uploadDocument: (file: File | { name: string; size: number; type: string; rawFile?: File }) => Promise<void>;
  selectDocument: (id: string) => void;
  setValidationError: (err: string | null) => void;
  resetPipeline: () => void;
}

export const useUploadStore = create<UploadState>((set, get) => ({
  documents: [],
  selectedDocId: null,
  currentStage: 'idle',
  stageProgress: 0,
  stageMessage: '',
  validationError: null,

  setValidationError: (validationError) => set({ validationError }),
  resetPipeline: () => set({ currentStage: 'idle', stageProgress: 0, stageMessage: '', validationError: null }),

  selectDocument: (id) => set({ selectedDocId: id }),

  uploadDocument: async (fileInput) => {
    // Client-Side Security Pre-Validation
    const MAX_SIZE = 50 * 1024 * 1024; // 50MB
    const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg'];
    const fileExt = '.' + fileInput.name.split('.').pop()?.toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(fileExt)) {
      set({ validationError: `Invalid file extension "${fileExt}". Allowed: .pdf, .png, .jpg, .jpeg` });
      return;
    }

    if (fileInput.size > MAX_SIZE) {
      set({ validationError: `File exceeds maximum limit of 50MB (${(fileInput.size / 1024 / 1024).toFixed(1)} MB provided).` });
      return;
    }

    set({ validationError: null, currentStage: 'uploading', stageProgress: 20, stageMessage: 'Validating magic-bytes & transmitting to gateway...' });
    
    let actualFile: File | Blob;

    if ('rawFile' in fileInput && fileInput.rawFile) {
      actualFile = fileInput.rawFile;
    } else if (fileInput instanceof File) {
      actualFile = fileInput;
    } else {
      set({ 
        validationError: 'Please provide a real file for upload.',
        currentStage: 'error',
        stageProgress: 0,
        stageMessage: ''
      });
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', actualFile, fileInput.name);

      set({ currentStage: 'ocr_processing', stageProgress: 50, stageMessage: 'Running local PaddleOCR CPU & entity parser...' });

      const res = await apiFetch(`/api/upload`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || `Server returned status ${res.status}`);
      }

      set({ currentStage: 'chromadb_lookup', stageProgress: 85, stageMessage: 'Querying ChromaDB vector store for SOP violations...' });

      const backendResult: UploadedDocument = await res.json();
      
      set((state) => ({
        documents: [backendResult, ...state.documents.filter(d => d.id !== backendResult.id)],
        selectedDocId: backendResult.id,
        currentStage: 'completed',
        stageProgress: 100,
        stageMessage: `Ingestion complete. Extracted ${backendResult.findings?.length || 0} findings, ${backendResult.sop_violations?.length || 0} SOP alerts.`,
      }));

      return;
    } catch (err: any) {
      set({ 
        validationError: `Backend unavailable: ${(err as Error).message || 'Network error'}`,
        currentStage: 'error',
        stageProgress: 0,
        stageMessage: ''
      });
      return;
    }
  },
}));