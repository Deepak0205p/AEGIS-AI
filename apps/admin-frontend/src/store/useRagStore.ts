import { create } from 'zustand';
import { api } from '@/lib/api';

export interface VectorStats {
  totalChunks: number;
  documentCount: number;
  lastIndexed: string;
  /** Null when no embedding model is in use (no vector dimensions exist). */
  dimensions: number | null;
  activeCollection: string;
  denseEngine: string;
  bm25Indexed: boolean;
}

export interface ChunkConfig {
  chunkSize: number;
  overlap: number;
  /**
   * Retained for UI compatibility only. The backend always builds its BM25
   * lexical index, so this is not sent and cannot be switched off remotely.
   */
  enableBM25: boolean;
  embeddingModel: string | null;
}

export interface IngestedDocumentItem {
  id: string;
  name: string;
  category: string;
  chunks: number;
  sizeKb: number;
  timestamp: string | null;
  provenance?: string;
  authoritative?: boolean;
  source?: string;
}

export type ReindexStage =
  | 'idle'
  | 'parsing'
  | 'extracting'
  | 'embedding'
  | 'committing'
  | 'completed'
  | 'error';

/** What the backend actually reported for an ingestion run. */
export interface IngestOutcome {
  files_submitted: number;
  documents: {
    filename: string;
    status?: 'INGESTED' | 'FAILED';
    chunks_created: number;
    bytes: number;
    error?: string;
  }[];
  failures: { filename: string; error: string }[];
  chunks_indexed: number;
  total_master_sops: number | null;
  message: string;
  persistence_note?: string;
}

/** How retrieval is actually scoring, as reported by the backend. */
export interface RetrievalInfo {
  method: string;
  dense_available: boolean;
  embedding_model: string | null;
  embedding_status: string;
  lexical_index: string;
  notice?: string;
  persistence_note?: string;
}

interface RagState {
  vectorStats: VectorStats;
  retrievalInfo: RetrievalInfo | null;
  chunkConfig: ChunkConfig;
  documentsList: IngestedDocumentItem[];
  isReindexing: boolean;
  reindexProgress: number; // 0 - 100
  reindexStage: ReindexStage;
  reindexStatusMessage: string;
  reindexError: string | null;

  // Actions
  fetchVectorStats: () => Promise<void>;  setChunkConfig: (config: Partial<ChunkConfig>) => void;
  triggerGlobalReindex: (files: File[], customConfig?: Partial<ChunkConfig>) => Promise<IngestOutcome | null>;
  resetReindex: () => void;
}

export const useRagStore = create<RagState>((set, get) => ({
  vectorStats: {
    // Nothing is claimed until the backend reports live index statistics.
    totalChunks: 0,
    documentCount: 0,
    lastIndexed: 'Never indexed (awaiting backend)',
    dimensions: null,
    activeCollection: 'unknown',
    denseEngine: 'unknown',
    bm25Indexed: false,
  },
  chunkConfig: {
    chunkSize: 512,
    overlap: 100,
    enableBM25: true,
    // No default embedding model. /api/rag-admin/stats reports the real one
    // (or null when dense embeddings are unavailable); 'bge-m3-gguf' was a
    // value the backend explicitly documents as never having been used.
    embeddingModel: null,
  },
  documentsList: [],
  retrievalInfo: null,
  isReindexing: false,
  reindexProgress: 0,
  reindexStage: 'idle',
  reindexStatusMessage: '',
  reindexError: null,

  setChunkConfig: (newConfig) =>
    set((state) => ({ chunkConfig: { ...state.chunkConfig, ...newConfig } })),

  fetchVectorStats: async () => {
    try {
      const data = await api.get<any>('/api/rag-admin/stats');
      if (data && data.total_chunks !== undefined) {
        set({
          vectorStats: {
            totalChunks: data.total_chunks,
            documentCount: data.document_count || get().vectorStats.documentCount,
            lastIndexed: data.last_indexed || 'No upload ingested in this process',
            // Dimensions only exist when real embeddings are in use; a missing
            // value is reported as "n/a" rather than a made-up 1024.
            dimensions: typeof data.dimensions === 'number' ? data.dimensions : null,
            activeCollection: data.collection_name || 'in_process_knowledge_corpus',
            denseEngine: data.embedding_model || 'none (lexical BM25 only)',
            bm25Indexed: data.bm25_enabled ?? true,
          },
          retrievalInfo: {
            method: data.retrieval_method || 'unknown',
            dense_available: Boolean(data.dense_embeddings_enabled),
            embedding_model: data.embedding_model ?? null,
            embedding_status: data.embedding_status || 'not reported',
            lexical_index: data.lexical_index || 'unknown',
            notice: data.notice,
            persistence_note: data.persistence_note,
          },
        });
      }

      // Fetch authentic document inventory from server
      const docData = await api.get<any>('/api/rag-admin/documents');
      if (docData && Array.isArray(docData.documents)) {
        set({ documentsList: docData.documents });
      }
    } catch {
      // Keep state
    }
  },

  triggerGlobalReindex: async (files: File[], customConfig?: Partial<ChunkConfig>) => {
    const config = { ...get().chunkConfig, ...customConfig };

    if (!files.length) {
      set({ reindexError: 'No documents selected for ingestion.' });
      return null;
    }

    set({
      isReindexing: true,
      reindexProgress: 10,
      reindexStage: 'parsing',
      reindexStatusMessage: `Submitting ${files.length} document(s) to the ingestion endpoint...`,
      reindexError: null,
    });

    try {
      const formData = new FormData();
      files.forEach((f) => formData.append('files', f));
      formData.append('chunk_size', String(config.chunkSize));
      formData.append('overlap', String(config.overlap));

      // A failure here is a real failure — it is never swallowed or faked.
      const response: any = await api.post('/api/rag-admin/ingest-file', formData);

      set({
        reindexProgress: 80,
        reindexStage: 'committing',
        reindexStatusMessage: 'Server accepted the upload; refreshing live index statistics...',
      });

      // Pull the genuine post-ingest numbers instead of computing our own.
      await get().fetchVectorStats();

      const ingested: IngestOutcome['documents'] = Array.isArray(response?.files) ? response.files : [];
      const failures: IngestOutcome['failures'] = Array.isArray(response?.failures)
        ? response.failures
        : ingested
            .filter((d) => d?.status === 'FAILED')
            .map((d) => ({ filename: d.filename, error: d.error || 'Unknown ingestion failure.' }));
      // Only server-confirmed chunks are counted.
      const chunksIndexed = ingested.reduce(
        (sum, doc) => sum + (doc?.status === 'INGESTED' ? Number(doc?.chunks_created) || 0 : 0),
        0
      );

      const outcome: IngestOutcome = {
        files_submitted: files.length,
        documents: ingested,
        failures,
        chunks_indexed: chunksIndexed,
        total_master_sops: typeof response?.total_master_sops === 'number' ? response.total_master_sops : null,
        message: response?.message || `Ingested ${chunksIndexed} chunk(s).`,
        persistence_note: response?.persistence_note,
      };

      const failureNote = failures.length
        ? ` ${failures.length} file(s) failed: ${failures.map((f) => `${f.filename} (${f.error})`).join('; ')}`
        : '';

      set({
        isReindexing: false,
        reindexProgress: 100,
        reindexStage: failures.length ? 'error' : 'completed',
        reindexStatusMessage: `${outcome.message} ${chunksIndexed} chunk(s) created (server reported).${failureNote}`,
        reindexError: failures.length ? failureNote.trim() : null,
      });

      return outcome;
    } catch (err: any) {
      set({
        isReindexing: false,
        reindexStage: 'error',
        reindexError: err?.message || 'Ingestion failed.',
        reindexStatusMessage: 'Ingestion failed - no documents were indexed.',
      });
      return null;
    }
  },

  resetReindex: () => {
    set({
      isReindexing: false,
      reindexProgress: 0,
      reindexStage: 'idle',
      reindexStatusMessage: '',
      reindexError: null,
    });
  },
}));
