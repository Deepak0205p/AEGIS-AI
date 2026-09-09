'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Users,
  MessageSquare,
  Hash,
  Send,
  Paperclip,
  Sparkles,
  Bot,
  Plus,
  Search,
  Check,
  ChevronDown,
  FileText,
  FileSpreadsheet,
  Presentation,
  Download,
  Eye,
  Shield,
  Clock,
  Radio,
  User,
  ArrowLeft,
  X,
  Smile,
  AlertCircle,
  FileCode,
  Image as ImageIcon
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/store/useAuthStore';
import { useCollaborationStore, ChannelItem, ChannelMessage, PlantUser } from '@/store/useCollaborationStore';
import { AppSidebar } from '@/components/sidebar/AppSidebar';
import { MarkdownContent } from '@/components/MarkdownContent';

export default function TeamCollaborationPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const {
    channels,
    activeChannelId,
    messages,
    users,
    isLoadingChannels,
    isLoadingMessages,
    typingUsers,
    streamingAiText,
    isAiThinking,
    isConnected,
    fetchChannels,
    fetchUsers,
    selectChannel,
    createChannel,
    startDirectMessage,
    sendMessage,
    sendTyping,
    uploadFile,
    disconnectWebSocket
  } = useCollaborationStore();

  const [inputMessage, setInputMessage] = useState('');
  const [askAiToggle, setAskAiToggle] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showNewDMModal, setShowNewDMModal] = useState(false);
  const [newChanName, setNewChanName] = useState('');
  const [newChanDesc, setNewChanDesc] = useState('');
  const [newChanDept, setNewChanDept] = useState('OPERATIONS');
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const currentUsername = user?.username || 'operator';
  const currentUserRole = user?.role || 'FIELD_OPERATOR';

  useEffect(() => {
    fetchChannels(currentUsername);
    fetchUsers();
    return () => {
      disconnectWebSocket();
    };
  }, [currentUsername, fetchChannels, fetchUsers, disconnectWebSocket]);

  useEffect(() => {
    if (channels.length > 0 && !activeChannelId) {
      selectChannel(channels[0].id, currentUsername, currentUserRole);
    }
  }, [channels, activeChannelId, selectChannel, currentUsername, currentUserRole]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingAiText, isAiThinking]);

  const activeChannel = channels.find((c) => c.id === activeChannelId) || {
    id: activeChannelId,
    name: 'refinery-operations',
    channel_type: 'CHANNEL',
    description: 'Plant operations discussion',
    department: 'OPERATIONS',
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    sendTyping(true);
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      sendTyping(false);
    }, 2000);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanText = inputMessage.trim();
    if (!cleanText && !selectedFile) return;

    let fileMeta = null;
    if (selectedFile) {
      setIsUploading(true);
      try {
        fileMeta = await uploadFile(selectedFile, activeChannelId, currentUsername);
      } catch (err) {
        console.error('File upload error:', err);
      } finally {
        setIsUploading(false);
        setSelectedFile(null);
      }
    }

    await sendMessage(cleanText, {
      askAi: askAiToggle || cleanText.toLowerCase().includes('@aegis') || cleanText.toLowerCase().includes('@ai'),
      fileMeta,
    });

    setInputMessage('');
    setAskAiToggle(false);
    sendTyping(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCreateChannelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newChanName.trim()) return;
    const newId = await createChannel(newChanName, newChanDesc, newChanDept, currentUsername);
    if (newId) {
      setShowCreateModal(false);
      setNewChanName('');
      setNewChanDesc('');
      selectChannel(newId, currentUsername, currentUserRole);
    }
  };

  const handleStartDM = async (targetUsername: string) => {
    const dmId = await startDirectMessage(targetUsername, currentUsername);
    if (dmId) {
      setShowNewDMModal(false);
      selectChannel(dmId, currentUsername, currentUserRole);
    }
  };

  const filteredChannels = channels.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const channelList = filteredChannels.filter((c) => c.channel_type === 'CHANNEL');
  const dmList = filteredChannels.filter((c) => c.channel_type === 'DM');

  const getFilePreviewIcon = (fileType?: string) => {
    const ft = (fileType || '').toLowerCase();
    if (ft.includes('doc')) return <FileText className="h-5 w-5 text-blue-500" />;
    if (ft.includes('xls') || ft.includes('csv')) return <FileSpreadsheet className="h-5 w-5 text-emerald-500" />;
    if (ft.includes('ppt')) return <Presentation className="h-5 w-5 text-amber-500" />;
    if (ft.includes('py') || ft.includes('code') || ft.includes('sql')) return <FileCode className="h-5 w-5 text-purple-500" />;
    if (ft.includes('png') || ft.includes('jpg') || ft.includes('jpeg')) return <ImageIcon className="h-5 w-5 text-pink-500" />;
    return <FileText className="h-5 w-5 text-slate-400" />;
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white text-slate-900 dark:bg-[#131314] dark:text-[#e3e3e3] font-sans antialiased">
      {/* Primary Sidebar */}
      <AppSidebar />

      {/* Main Collaboration Layout */}
      <div className="flex flex-1 h-full overflow-hidden">
        {/* Sub-Sidebar: Channels & Direct Messages Directory */}
        <div className="w-80 h-full border-r border-slate-200 dark:border-[#282a2c] bg-slate-50 dark:bg-[#18191a] flex flex-col shrink-0">
          {/* Header */}
          <div className="p-4 border-b border-slate-200 dark:border-[#282a2c] flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="h-8 w-8 rounded-lg bg-blue-600/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold">
                <Users className="h-4 w-4" />
              </div>
              <div>
                <h1 className="text-sm font-semibold text-slate-900 dark:text-white leading-tight">
                  Team Collaboration
                </h1>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
                  <span className={`h-2 w-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
                  {isConnected ? 'Sovereign LAN Active' : 'Connecting...'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-[#2a2b2e] text-slate-600 dark:text-slate-300 transition-colors"
              title="Create new channel"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          {/* Search Box */}
          <div className="p-3">
            <div className="relative">
              <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search channels or DMs..."
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-white dark:bg-[#1e1f20] border border-slate-200 dark:border-[#3c4043]/50 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          {/* Channels & DMs Scrollable List */}
          <div className="flex-1 overflow-y-auto px-2 space-y-4">
            {/* Channels Section */}
            <div>
              <div className="flex items-center justify-between px-2 mb-1.5">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 tracking-wider uppercase">
                  Plant Channels
                </span>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="text-[10px] text-blue-600 dark:text-blue-400 hover:underline"
                >
                  + Add
                </button>
              </div>
              <div className="space-y-0.5">
                {channelList.map((ch) => {
                  const isActive = ch.id === activeChannelId;
                  return (
                    <button
                      key={ch.id}
                      onClick={() => selectChannel(ch.id, currentUsername, currentUserRole)}
                      className={`w-full text-left px-3 py-2 rounded-lg flex items-center justify-between text-xs transition-all ${
                        isActive
                          ? 'bg-blue-50 text-blue-700 dark:bg-[#282a2c] dark:text-[#a8c7fa] font-medium shadow-sm'
                          : 'text-slate-700 dark:text-[#c4c7c5] hover:bg-slate-200/60 dark:hover:bg-[#222426]'
                      }`}
                    >
                      <div className="flex items-center space-x-2 truncate">
                        <Hash className={`h-3.5 w-3.5 shrink-0 ${isActive ? 'text-blue-600 dark:text-[#a8c7fa]' : 'text-slate-400'}`} />
                        <span className="truncate">{ch.name}</span>
                      </div>
                      {ch.member_count !== undefined && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-200 dark:bg-[#333538] text-slate-600 dark:text-slate-400">
                          {ch.member_count}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Direct Messages Section */}
            <div>
              <div className="flex items-center justify-between px-2 mb-1.5">
                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 tracking-wider uppercase">
                  Direct Messages
                </span>
                <button
                  onClick={() => setShowNewDMModal(true)}
                  className="text-[10px] text-blue-600 dark:text-blue-400 hover:underline"
                >
                  + Start DM
                </button>
              </div>
              <div className="space-y-0.5">
                {users
                  .filter((u) => u.username !== currentUsername)
                  .map((u) => {
                    const dmChannel = dmList.find((d) => d.name.toLowerCase().includes(u.username.toLowerCase()));
                    const isSelected = activeChannel.channel_type === 'DM' && activeChannel.name.toLowerCase().includes(u.username.toLowerCase());
                    return (
                      <button
                        key={u.username}
                        onClick={() => handleStartDM(u.username)}
                        className={`w-full text-left px-3 py-2 rounded-lg flex items-center justify-between text-xs transition-all ${
                          isSelected
                            ? 'bg-blue-50 text-blue-700 dark:bg-[#282a2c] dark:text-[#a8c7fa] font-medium'
                            : 'text-slate-700 dark:text-[#c4c7c5] hover:bg-slate-200/60 dark:hover:bg-[#222426]'
                        }`}
                      >
                        <div className="flex items-center space-x-2.5 truncate">
                          <div className="relative shrink-0">
                            <div
                              className="h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white uppercase shadow-sm"
                              style={{ backgroundColor: u.avatar_color || '#3B82F6' }}
                            >
                              {u.username.slice(0, 2)}
                            </div>
                            <span
                              className={`absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full border border-white dark:border-[#18191a] ${
                                u.is_online ? 'bg-emerald-500' : 'bg-slate-400'
                              }`}
                            />
                          </div>
                          <div className="truncate">
                            <p className="truncate font-medium text-slate-900 dark:text-white leading-none">
                              {u.full_name || u.username}
                            </p>
                            <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                              {u.department} • {u.role}
                            </p>
                          </div>
                        </div>
                      </button>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* Plant AI Co-op Tip Bar */}
          <div className="p-3 border-t border-slate-200 dark:border-[#282a2c] bg-blue-50/50 dark:bg-[#1a1c23] m-2 rounded-xl">
            <div className="flex items-start space-x-2">
              <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
              <div className="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed">
                <span className="font-semibold text-blue-700 dark:text-blue-400">Co-Op In-Chat AI:</span> Mention <code className="bg-blue-100 dark:bg-blue-950 px-1 py-0.5 rounded font-mono text-blue-700 dark:text-blue-300">@aegis</code> in any channel or DM to solve problems as a team.
              </div>
            </div>
          </div>
        </div>

        {/* Main Conversation Window */}
        <div className="flex-1 h-full flex flex-col bg-white dark:bg-[#131314] overflow-hidden">
          {/* Channel Header Bar */}
          <div className="h-14 border-b border-slate-200 dark:border-[#282a2c] px-6 flex items-center justify-between shrink-0 bg-white/80 dark:bg-[#131314]/80 backdrop-blur-md">
            <div className="flex items-center space-x-3 truncate">
              {activeChannel.channel_type === 'CHANNEL' ? (
                <div className="h-8 w-8 rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400 flex items-center justify-center font-bold">
                  <Hash className="h-4 w-4" />
                </div>
              ) : (
                <div className="h-8 w-8 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center font-bold">
                  <User className="h-4 w-4" />
                </div>
              )}
              <div className="truncate">
                <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>{activeChannel.name}</span>
                  {activeChannel.department && (
                    <span className="text-[10px] font-normal px-2 py-0.5 rounded-full bg-slate-100 dark:bg-[#282a2c] text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-[#3c4043]/40">
                      {activeChannel.department}
                    </span>
                  )}
                </h2>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                  {activeChannel.description || 'Enterprise collaboration and sovereign SOP review'}
                </p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setAskAiToggle(!askAiToggle)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-all shadow-sm ${
                  askAiToggle
                    ? 'bg-blue-600 text-white shadow-blue-500/20'
                    : 'bg-slate-100 dark:bg-[#282a2c] hover:bg-slate-200 dark:hover:bg-[#333538] text-slate-700 dark:text-[#c4c7c5]'
                }`}
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                <span>Ask @aegis AI</span>
              </button>
            </div>
          </div>

          {/* Messages Stream Container */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {isLoadingMessages ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                <div className="flex flex-col items-center space-y-2">
                  <div className="h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <span>Loading channel records...</span>
                </div>
              </div>
            ) : messages.length === 0 && !streamingAiText ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
                <div className="h-12 w-12 rounded-full bg-slate-100 dark:bg-[#1e1f20] flex items-center justify-center mb-3">
                  <MessageSquare className="h-6 w-6 text-slate-400" />
                </div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Welcome to #{activeChannel.name}
                </p>
                <p className="text-xs text-slate-500 mt-1 max-w-sm">
                  Start the shift conversation with your team, share documents or ask @aegis to generate procedures together.
                </p>
              </div>
            ) : (
              messages.map((msg) => {
                const isMe = msg.sender_username.toLowerCase() === currentUsername.toLowerCase();
                const isAi = msg.message_type === 'AI_RESPONSE' || msg.sender_username.includes('AEGIS');

                return (
                  <div
                    key={msg.id}
                    className={`flex items-start space-x-3 ${isAi ? 'bg-blue-50/40 dark:bg-[#1c2230]/40 p-4 rounded-2xl border border-blue-100/60 dark:border-blue-900/30 shadow-sm' : ''}`}
                  >
                    {/* Avatar */}
                    {isAi ? (
                      <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-amber-500 flex items-center justify-center text-white shrink-0 shadow-glow-blue">
                        <Bot className="h-4 w-4" />
                      </div>
                    ) : (
                      <div className="h-8 w-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-white shrink-0 uppercase">
                        {msg.sender_username.slice(0, 2)}
                      </div>
                    )}

                    {/* Message Body */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`text-xs font-bold ${isAi ? 'text-blue-700 dark:text-[#a8c7fa]' : 'text-slate-900 dark:text-white'}`}>
                          {msg.sender_username}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-200/70 dark:bg-[#282a2c] text-slate-500 dark:text-slate-400">
                          {msg.sender_role}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {msg.created_at ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                        </span>
                      </div>

                      {/* Content */}
                      <div className="text-xs leading-relaxed text-slate-800 dark:text-[#e3e3e3] select-text">
                        {isAi ? (
                          <MarkdownContent content={msg.content} />
                        ) : (
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        )}
                      </div>

                      {/* Shared File Card */}
                      {msg.file_id && (
                        <div className="mt-3 p-3 rounded-xl border border-slate-200 dark:border-[#3c4043]/60 bg-white dark:bg-[#1e1f20] flex items-center justify-between max-w-md shadow-sm">
                          <div className="flex items-center space-x-3 truncate">
                            {getFilePreviewIcon(msg.file_type)}
                            <div className="truncate">
                              <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                                {msg.file_name || 'Shared Document'}
                              </p>
                              <p className="text-[10px] text-slate-500 dark:text-slate-400 uppercase">
                                {msg.file_type?.replace('.', '') || 'FILE'} • {msg.file_size ? `${(msg.file_size / 1024).toFixed(1)} KB` : 'Ready'}
                              </p>
                            </div>
                          </div>
                          {msg.file_url && (
                            <a
                              href={msg.file_url}
                              download
                              className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-[#282a2c] text-blue-600 dark:text-blue-400 transition-colors"
                              title="Download document"
                            >
                              <Download className="h-4 w-4" />
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}

            {/* In-Flight Streaming Collaborative AI Response */}
            {(isAiThinking || streamingAiText) && (
              <div className="flex items-start space-x-3 bg-blue-50/50 dark:bg-[#1c2230]/50 p-4 rounded-2xl border border-blue-200 dark:border-blue-900/50 shadow-sm animate-pulse-subtle">
                <div className="h-8 w-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 animate-spin-slow">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-xs font-bold text-blue-600 dark:text-[#a8c7fa]">
                      AEGIS AI (Sovereign)
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                      Collaborative Response
                    </span>
                  </div>
                  {isAiThinking && !streamingAiText ? (
                    <div className="text-xs text-blue-600 dark:text-blue-400 flex items-center space-x-2 py-1">
                      <span className="h-2 w-2 rounded-full bg-blue-500 animate-ping" />
                      <span>Consulting sovereign plant KB & OISD standard rules...</span>
                    </div>
                  ) : (
                    <div className="text-xs leading-relaxed text-slate-800 dark:text-[#e3e3e3]">
                      <MarkdownContent content={streamingAiText} />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Typing Indicator */}
            {typingUsers.length > 0 && (
              <div className="flex items-center space-x-2 text-[11px] text-slate-500 dark:text-slate-400 italic">
                <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-bounce" />
                <span>{typingUsers.join(', ')} {typingUsers.length === 1 ? 'is' : 'are'} typing...</span>
              </div>
            )}

            <div ref={chatBottomRef} />
          </div>

          {/* Attachment Preview Chip */}
          {selectedFile && (
            <div className="px-6 py-2 bg-slate-50 dark:bg-[#1a1b1d] border-t border-slate-200 dark:border-[#282a2c] flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs text-slate-700 dark:text-slate-300 truncate">
                <Paperclip className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                <span className="font-semibold truncate">{selectedFile.name}</span>
                <span className="text-slate-400 text-[10px]">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white p-1"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Chat Input Bar */}
          <div className="p-4 border-t border-slate-200 dark:border-[#282a2c] bg-white dark:bg-[#131314] shrink-0">
            <div className={`relative flex flex-col bg-slate-50 dark:bg-[#1e1f20] border ${askAiToggle ? 'border-blue-500/80 ring-2 ring-blue-500/10' : 'border-slate-200 dark:border-[#3c4043]/50'} rounded-2xl p-2 transition-all`}>
              <textarea
                value={inputMessage}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={
                  askAiToggle
                    ? 'Ask AEGIS AI to assist this channel (e.g. Calculate reflux ratio or verify SOP)...'
                    : `Message #${activeChannel.name} or type @aegis to ask AI...`
                }
                rows={2}
                className="w-full bg-transparent border-none resize-none text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none p-1.5"
              />

              {/* Bottom Toolbar inside Input Container */}
              <div className="flex items-center justify-between pt-1.5 border-t border-slate-200/50 dark:border-[#2a2b2e]/50">
                <div className="flex items-center space-x-1.5">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-[#2a2b2e] text-slate-500 dark:text-slate-400 transition-colors"
                    title="Attach document, sheet, log or image"
                  >
                    <Paperclip className="h-4 w-4" />
                  </button>

                  <button
                    onClick={() => setAskAiToggle(!askAiToggle)}
                    className={`px-2 py-1 rounded-md text-[11px] font-semibold flex items-center space-x-1 transition-colors ${
                      askAiToggle
                        ? 'bg-blue-600 text-white'
                        : 'hover:bg-slate-200 dark:hover:bg-[#2a2b2e] text-slate-600 dark:text-slate-300'
                    }`}
                  >
                    <Sparkles className="h-3 w-3 text-amber-400" />
                    <span>@aegis</span>
                  </button>
                </div>

                <button
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() && !selectedFile}
                  className="h-8 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:hover:bg-blue-600 text-white font-medium text-xs flex items-center space-x-1.5 transition-all shadow-sm"
                >
                  <span>Send</span>
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Create Channel */}
      <AnimatePresence>
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-white dark:bg-[#1e1f20] rounded-2xl border border-slate-200 dark:border-[#3c4043] p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-[#2a2b2e]">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Hash className="h-5 w-5 text-blue-500" />
                  <span>Create Plant Channel</span>
                </h3>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleCreateChannelSubmit} className="space-y-4 mt-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Channel Name
                  </label>
                  <input
                    type="text"
                    required
                    value={newChanName}
                    onChange={(e) => setNewChanName(e.target.value)}
                    placeholder="e.g. cdu-furnace-monitoring"
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-[#131314] border border-slate-200 dark:border-[#3c4043] rounded-xl text-slate-900 dark:text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Department
                  </label>
                  <select
                    value={newChanDept}
                    onChange={(e) => setNewChanDept(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-[#131314] border border-slate-200 dark:border-[#3c4043] rounded-xl text-slate-900 dark:text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="OPERATIONS">Operations (CDU/VDU/HCU)</option>
                    <option value="HSE">HSE & Fire Safety</option>
                    <option value="MAINTENANCE">Mechanical / Electrical</option>
                    <option value="DRILLING">Upstream Drilling & E&P</option>
                    <option value="ALL">Plant-wide (General)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Description & Objectives
                  </label>
                  <textarea
                    value={newChanDesc}
                    onChange={(e) => setNewChanDesc(e.target.value)}
                    placeholder="Describe purpose of this channel..."
                    rows={3}
                    className="w-full px-3 py-2 text-xs bg-slate-50 dark:bg-[#131314] border border-slate-200 dark:border-[#3c4043] rounded-xl text-slate-900 dark:text-white focus:outline-none focus:border-blue-500 resize-none"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-[#282a2c]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-md transition-all"
                  >
                    Create Channel
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: New Direct Message */}
      <AnimatePresence>
        {showNewDMModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md bg-white dark:bg-[#1e1f20] rounded-2xl border border-slate-200 dark:border-[#3c4043] p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-[#2a2b2e]">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <User className="h-5 w-5 text-blue-500" />
                  <span>Start Direct Message</span>
                </h3>
                <button
                  onClick={() => setShowNewDMModal(false)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-2 mt-4 max-h-72 overflow-y-auto pr-1">
                {users
                  .filter((u) => u.username !== currentUsername)
                  .map((u) => (
                    <button
                      key={u.username}
                      onClick={() => handleStartDM(u.username)}
                      className="w-full p-3 rounded-xl border border-slate-200 dark:border-[#3c4043]/40 bg-slate-50 dark:bg-[#131314] hover:border-blue-500 flex items-center justify-between text-left transition-all"
                    >
                      <div className="flex items-center space-x-3 truncate">
                        <div
                          className="h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold text-white uppercase shadow-sm"
                          style={{ backgroundColor: u.avatar_color || '#3B82F6' }}
                        >
                          {u.username.slice(0, 2)}
                        </div>
                        <div className="truncate">
                          <p className="text-xs font-bold text-slate-900 dark:text-white leading-tight">
                            {u.full_name || u.username}
                          </p>
                          <p className="text-[10px] text-slate-500 dark:text-slate-400">
                            {u.department} • {u.role}
                          </p>
                        </div>
                      </div>
                      <span className="text-[11px] font-semibold text-blue-600 dark:text-blue-400">
                        Chat →
                      </span>
                    </button>
                  ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
