import { create } from 'zustand';

export interface ChannelItem {
  id: string;
  name: string;
  channel_type: 'CHANNEL' | 'DM';
  description?: string;
  department?: string;
  created_by?: string;
  created_at: string;
  member_count?: number;
  last_message?: string;
  last_message_at?: string;
  unread_count?: number;
}

export interface ChannelMessage {
  id: number;
  channel_id: string;
  sender_username: string;
  sender_role: string;
  content: string;
  message_type: 'TEXT' | 'FILE' | 'AI_RESPONSE' | 'SYSTEM';
  file_id?: string;
  file_name?: string;
  file_type?: string;
  file_size?: number;
  file_url?: string;
  created_at: string;
  is_streaming?: boolean;
}

export interface PlantUser {
  username: string;
  full_name: string;
  role: string;
  department: string;
  avatar_color: string;
  is_online?: boolean;
}

interface CollaborationState {
  channels: ChannelItem[];
  activeChannelId: string;
  messages: ChannelMessage[];
  users: PlantUser[];
  isLoadingChannels: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  typingUsers: string[];
  streamingAiText: string;
  isAiThinking: boolean;
  socket: WebSocket | null;
  isConnected: boolean;

  // Actions
  fetchChannels: (username?: string) => Promise<void>;
  fetchUsers: () => Promise<void>;
  selectChannel: (channelId: string, username?: string, role?: string) => Promise<void>;
  createChannel: (name: string, description: string, department: string, createdBy: string) => Promise<string | null>;
  startDirectMessage: (targetUsername: string, currentUsername: string) => Promise<string | null>;
  sendMessage: (content: string, options?: { askAi?: boolean; fileMeta?: any }) => Promise<void>;
  sendTyping: (isTyping: boolean) => void;
  uploadFile: (file: File, channelId: string, username: string) => Promise<any>;
  connectWebSocket: (channelId: string, username: string, role: string) => void;
  disconnectWebSocket: () => void;
}

export const useCollaborationStore = create<CollaborationState>((set, get) => ({
  channels: [],
  activeChannelId: 'chan_refinery_ops',
  messages: [],
  users: [],
  isLoadingChannels: false,
  isLoadingMessages: false,
  isSending: false,
  typingUsers: [],
  streamingAiText: '',
  isAiThinking: false,
  socket: null,
  isConnected: false,

  fetchChannels: async (username = 'operator') => {
    set({ isLoadingChannels: true });
    try {
      const res = await fetch(`/api/collaboration/channels?username=${encodeURIComponent(username)}`);
      if (res.ok) {
        const data = await res.json();
        set({ channels: data.channels || [] });
      }
    } catch (e) {
      console.error('Failed to fetch collaboration channels:', e);
    } finally {
      set({ isLoadingChannels: false });
    }
  },

  fetchUsers: async () => {
    try {
      const res = await fetch('/api/collaboration/users');
      if (res.ok) {
        const data = await res.json();
        set({ users: data.users || [] });
      }
    } catch (e) {
      console.error('Failed to fetch plant directory users:', e);
    }
  },

  selectChannel: async (channelId: string, username = 'operator', role = 'FIELD_OPERATOR') => {
    set({ activeChannelId: channelId, isLoadingMessages: true, messages: [], streamingAiText: '', isAiThinking: false });
    get().connectWebSocket(channelId, username, role);

    try {
      const res = await fetch(`/api/collaboration/channels/${encodeURIComponent(channelId)}/messages`);
      if (res.ok) {
        const data = await res.json();
        set({ messages: data.messages || [] });
      }
    } catch (e) {
      console.error(`Failed to load messages for channel ${channelId}:`, e);
    } finally {
      set({ isLoadingMessages: false });
    }
  },

  createChannel: async (name: string, description: string, department: string, createdBy: string) => {
    try {
      const res = await fetch('/api/collaboration/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description, department, created_by: createdBy }),
      });
      if (res.ok) {
        const data = await res.json();
        await get().fetchChannels(createdBy);
        return data.channel_id;
      }
    } catch (e) {
      console.error('Failed to create channel:', e);
    }
    return null;
  },

  startDirectMessage: async (targetUsername: string, currentUsername: string) => {
    try {
      const res = await fetch('/api/collaboration/dm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_username: targetUsername, current_username: currentUsername }),
      });
      if (res.ok) {
        const data = await res.json();
        await get().fetchChannels(currentUsername);
        return data.channel?.id || null;
      }
    } catch (e) {
      console.error('Failed to start direct message:', e);
    }
    return null;
  },

  connectWebSocket: (channelId: string, username: string, role: string) => {
    const prevSocket = get().socket;
    if (prevSocket) {
      try {
        prevSocket.close();
      } catch (e) {}
    }

    if (typeof window === 'undefined') return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/collaboration/ws?channel_id=${encodeURIComponent(channelId)}&username=${encodeURIComponent(username)}&role=${encodeURIComponent(role)}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      set({ socket: ws, isConnected: true });
    };

    ws.onclose = () => {
      set({ isConnected: false });
    };

    ws.onerror = (err) => {
      console.warn('[COLLAB_WS_CLIENT_ERR]', err);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const currentActive = get().activeChannelId;
        if (data.channel_id && data.channel_id !== currentActive) return;

        if (data.event === 'new_message') {
          const newMsg: ChannelMessage = {
            id: data.id || Date.now(),
            channel_id: data.channel_id,
            sender_username: data.sender_username,
            sender_role: data.sender_role,
            content: data.content,
            message_type: data.message_type,
            file_id: data.file_id,
            file_name: data.file_name,
            file_type: data.file_type,
            file_size: data.file_size,
            file_url: data.file_url,
            created_at: data.created_at || new Date().toISOString(),
          };
          set((state) => ({
            messages: [...state.messages, newMsg],
            typingUsers: state.typingUsers.filter((u) => u !== data.sender_username),
          }));
        } else if (data.event === 'typing') {
          set((state) => {
            const current = state.typingUsers.filter((u) => u !== data.username);
            return {
              typingUsers: data.is_typing ? [...current, data.username] : current,
            };
          });
        } else if (data.event === 'ai_response_start') {
          set({ isAiThinking: true, streamingAiText: '' });
        } else if (data.event === 'ai_response_token') {
          set((state) => ({
            isAiThinking: false,
            streamingAiText: state.streamingAiText + (data.token || ''),
          }));
        } else if (data.event === 'ai_response_done') {
          const aiMsg: ChannelMessage = {
            id: data.id || Date.now(),
            channel_id: data.channel_id,
            sender_username: 'AEGIS AI',
            sender_role: 'SOVEREIGN_AI_ASSISTANT',
            content: data.content || get().streamingAiText,
            message_type: 'AI_RESPONSE',
            created_at: data.created_at || new Date().toISOString(),
          };
          set((state) => ({
            messages: [...state.messages, aiMsg],
            streamingAiText: '',
            isAiThinking: false,
          }));
        }
      } catch (e) {
        console.error('Failed to parse incoming WebSocket message:', e);
      }
    };

    set({ socket: ws });
  },

  disconnectWebSocket: () => {
    const s = get().socket;
    if (s) {
      try {
        s.close();
      } catch (e) {}
    }
    set({ socket: null, isConnected: false });
  },

  sendTyping: (isTyping: boolean) => {
    const ws = get().socket;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ event: 'typing', is_typing: isTyping }));
    }
  },

  sendMessage: async (content: string, options?: { askAi?: boolean; fileMeta?: any }) => {
    const ws = get().socket;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('Cannot send message: WebSocket is not open');
      return;
    }

    const payload = {
      event: 'message',
      content,
      ask_ai: options?.askAi || false,
      message_type: options?.fileMeta ? 'FILE' : 'TEXT',
      file_id: options?.fileMeta?.file_id,
      file_name: options?.fileMeta?.file_name,
      file_type: options?.fileMeta?.file_type,
      file_size: options?.fileMeta?.file_size,
      file_url: options?.fileMeta?.file_url,
    };

    ws.send(JSON.stringify(payload));
  },

  uploadFile: async (file: File, channelId: string, username: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('channel_id', channelId);
    formData.append('username', username);

    const res = await fetch('/api/collaboration/upload', {
      method: 'POST',
      body: formData,
    });

    if (res.ok) {
      return await res.json();
    }
    throw new Error('File upload failed');
  },
}));
