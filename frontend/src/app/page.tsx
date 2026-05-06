'use client';

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface AgentInfo {
  id: string;
  name: string;
  description: string;
  status: string;
}

interface CharacterData {
  name: string;
  role: string;
  age?: number;
  personality: string;
  background: string;
  motivation: string;
  arc?: string;
  relationships?: Array<{ character_name: string; relation: string }>;
}

interface ActData {
  name: string;
  description: string;
  key_events?: string[];
}

interface ProposalContent {
  title?: string;
  genre?: string;
  synopsis?: string;
  acts?: ActData[];
  themes?: string[];
  characters?: CharacterData[];
  world_setting?: {
    era: string;
    location: string;
    rules?: string[];
    technology_level?: string;
    culture?: string;
    history?: string;
    factions?: string[];
  };
  dialogues?: Array<{
    scene: string;
    participants: string[];
    content: Array<{ character: string; line: string }>;
  }>;
}

interface AgentProposalState {
  agent_id: string;
  agent_name: string;
  summary: string;
  confidence: number;
  content: ProposalContent;
  round?: number;
}

interface Story {
  title: string;
  genre: string;
  synopsis: string;
  outline?: {
    acts?: Array<{ name: string; description: string; key_events?: string[] }>;
  };
  characters: Array<{
    name: string;
    role: string;
    personality: string;
    background: string;
    motivation: string;
    arc?: string;
  }>;
  dialogues: Array<{ scene: string; content: Array<{ character: string; line: string }> }>;
  world_setting?: {
    era: string;
    location: string;
    rules?: string[];
    technology_level?: string;
    culture?: string;
  };
}

interface SSEData {
  type: string;
  data: {
    message?: string;
    agent_id?: string;
    agent_name?: string;
    content?: any;
    summary?: string;
    confidence?: number;
    round?: number;
    story?: Story;
    suggestions?: string[];
    target_agent?: string;
  };
}

interface Message {
  id: string;
  agent_id: string;
  agent_name: string;
  content: string;
  type: 'status' | 'proposal' | 'discussion' | 'round' | 'complete' | 'error' | 'thinking';
  round?: number;
  timestamp: number;
}

const STORAGE_KEY = 'writing_session_v2';

interface StoredSession {
  sessionId: string;
  theme: string;
  genre: string;
}

const GENRE_LABELS: Record<string, string> = {
  science_fiction: '科幻',
  fantasy: '奇幻',
  realism: '现实',
  mystery: '悬疑',
  romance: '爱情',
  horror: '恐怖',
  adventure: '冒险',
  historical: '历史',
};

const AGENT_EMOJIS: Record<string, string> = {
  plot_agent: '📖',
  character_agent: '👤',
  world_agent: '🌍',
  dialogue_agent: '💬',
};

const AGENT_NAMES: Record<string, string> = {
  plot_agent: '剧情Agent',
  character_agent: '人物Agent',
  world_agent: '世界观Agent',
  dialogue_agent: '对话Agent',
};

const AGENT_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  plot_agent: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
  character_agent: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  world_agent: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
  dialogue_agent: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700' },
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export default function Home() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [theme, setTheme] = useState('');
  const [genre, setGenre] = useState('');
  const [loading, setLoading] = useState(false);
  const [story, setStory] = useState<Story | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [themeError, setThemeError] = useState(false);
  const [currentRound, setCurrentRound] = useState(0);
  const [thinkingAgents, setThinkingAgents] = useState<Set<string>>(new Set());
  const [completedProposals, setCompletedProposals] = useState<Set<string>>(new Set());
  const [agentProposals, setAgentProposals] = useState<Record<string, AgentProposalState>>({});
  const [expandedRaw, setExpandedRaw] = useState<Record<string, boolean>>({});
  const [discussionFeedbacks, setDiscussionFeedbacks] = useState<Array<{
    agent_id: string;
    agent_name: string;
    content: string;
    round: number;
    suggestions: string[];
    target_agent: string;
    timestamp: number;
  }>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isGeneratingRef = useRef(false);

  useEffect(() => {
    loadAgents();
    restoreSession();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinkingAgents]);

  isGeneratingRef.current = isGenerating;

  const loadAgents = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/v1/agents`);
      setAgents(res.data.agents);
    } catch { }
  };

  const saveSession = (sessionId: string) => {
    const stored: StoredSession = { sessionId, theme, genre };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  };

  const restoreSession = async () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return;
      const session: StoredSession = JSON.parse(stored);
      if (!session.sessionId) return;

      const res = await axios.get(`${API_BASE}/api/v1/stories/${session.sessionId}`);
      const sessionData = res.data;

      setTheme(session.theme);
      setGenre(session.genre);

      if (sessionData.progress_messages && sessionData.progress_messages.length > 0) {
        const restoredMessages: Message[] = sessionData.progress_messages.map((msg: SSEData, idx: number) => ({
          id: `restored-${idx}`,
          agent_id: msg.data?.agent_id || 'system',
          agent_name: msg.data?.agent_name || '系统',
          content: msg.data?.message || msg.data?.content || msg.data?.summary || JSON.stringify(msg.data || ''),
          type: (msg.type || 'status') as Message['type'],
          round: msg.data?.round,
          timestamp: Date.now() - (sessionData.progress_messages.length - idx) * 100,
        }));
        setMessages(restoredMessages);

        const completed = new Set<string>();
        for (const msg of sessionData.progress_messages) {
          if (msg.type === 'proposal' && msg.data?.agent_id) completed.add(msg.data.agent_id);
          if (msg.type === 'round') setCurrentRound(msg.data?.round || 0);
        }
        setCompletedProposals(completed);
      }

      if (sessionData.status === 'completed') {
        setStory(sessionData.story);
        setCurrentPhase('生成完成！');
        localStorage.removeItem(STORAGE_KEY);
        return;
      }

      if (sessionData.status === 'processing' || sessionData.status === 'pending') {
        setIsGenerating(true);
        setCurrentPhase(sessionData.status === 'pending' ? '正在等待生成...' : '正在恢复会话...');
        connectToStream(session.sessionId);
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const addMessage = (msg: Omit<Message, 'id' | 'timestamp'>) => {
    const newMsg: Message = {
      ...msg,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, newMsg]);
  };

  const connectToStream = (sid: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${API_BASE}/api/v1/stories/${sid}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const parsed: SSEData = JSON.parse(event.data);

        if (parsed.type === 'end') {
          eventSource.close();
          return;
        }

        if (parsed.type === 'heartbeat') return;

        const d = parsed.data;

        switch (parsed.type) {
          case 'status':
            setCurrentPhase(d.message || '');
            addMessage({ agent_id: 'system', agent_name: '系统', content: d.message || '', type: 'status' });
            break;

          case 'thinking':
            if (d.agent_id) {
              setThinkingAgents(prev => new Set(prev).add(d.agent_id!));
            }
            setCurrentPhase(typeof d.content === 'string' ? d.content : `${d.agent_name}正在思考...`);
            addMessage({
              agent_id: d.agent_id || 'system',
              agent_name: d.agent_name || '系统',
              content: `⏳ ${String(d.content || '思考中...')}`,
              type: 'thinking',
              round: d.round,
            });
            break;

          case 'proposal':
            if (d.agent_id) {
              setThinkingAgents(prev => {
                const next = new Set(prev);
                next.delete(d.agent_id!);
                return next;
              });
              setCompletedProposals(prev => new Set(prev).add(d.agent_id!));
              setAgentProposals(prev => ({
                ...prev,
                [d.agent_id!]: {
                  agent_id: d.agent_id!,
                  agent_name: d.agent_name || '',
                  summary: d.summary || '',
                  confidence: d.confidence || 0,
                  content: (typeof d.content === 'object' ? d.content : {}) as ProposalContent,
                  round: d.round,
                }
              }));
              // Auto-expand raw data for new proposals
              setExpandedRaw(prev => ({ ...prev, [d.agent_id!]: false }));
            }
            setCurrentPhase(`${d.agent_name}已完成方案`);
            addMessage({
              agent_id: d.agent_id || 'system',
              agent_name: d.agent_name || '系统',
              content: `📋 提出方案 (置信度: ${((d.confidence || 0) * 100).toFixed(0)}%)\n${d.summary || ''}`,
              type: 'proposal',
              round: d.round,
            });
            break;

          case 'discussion':
            setCurrentPhase(`${d.agent_name}正在反馈`);
            setDiscussionFeedbacks(prev => [...prev, {
              agent_id: d.agent_id || '',
              agent_name: d.agent_name || '',
              content: String(d.content || ''),
              round: d.round || 0,
              suggestions: d.suggestions || [],
              target_agent: d.target_agent || '',
              timestamp: Date.now(),
            }]);
            addMessage({
              agent_id: d.agent_id || 'system',
              agent_name: d.agent_name || '系统',
              content: `💬 ${String(d.content || '')}`,
              type: 'discussion',
              round: d.round,
            });
            break;

          case 'round':
            setCurrentRound(d.round || 0);
            setCurrentPhase(`第${d.round}轮讨论`);
            addMessage({ agent_id: 'system', agent_name: '系统', content: `🔄 开始第 ${d.round} 轮讨论`, type: 'round', round: d.round });
            break;

          case 'blueprint':
            setCurrentPhase('故事蓝图已生成');
            {
              const b = d as any;
              addMessage({
                agent_id: 'system',
                agent_name: '系统',
                content: `📐 故事蓝图已生成：${b.title || ''}（${b.genre || ''}）\n核心冲突：${b.core_conflict || ''}\n角色：${(b.characters || []).map((c: any) => c.name).join('、') || '待定'}`,
                type: 'status',
              });
            }
            break;

          case 'complete':
            setStory(d.story || null);
            setThinkingAgents(new Set());
            setIsGenerating(false);
            setCurrentPhase('生成完成！');
            addMessage({ agent_id: 'system', agent_name: '系统', content: '✅ 故事生成完成！', type: 'complete' });
            localStorage.removeItem(STORAGE_KEY);
            eventSource.close();
            break;

          case 'error':
            setError(d.message || '未知错误');
            setThinkingAgents(new Set());
            setIsGenerating(false);
            addMessage({ agent_id: 'system', agent_name: '系统', content: `❌ 错误: ${d.message || '未知错误'}`, type: 'error' });
            eventSource.close();
            break;
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    };

    eventSource.onerror = () => {
      if (isGeneratingRef.current) {
        addMessage({ agent_id: 'system', agent_name: '系统', content: '⚠️ 连接中断，正在重连...', type: 'status' });
        setTimeout(() => {
          if (isGeneratingRef.current) connectToStream(sid);
        }, 3000);
      }
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedTheme = theme.trim();
    if (!trimmedTheme) {
      setThemeError(true);
      setError('请输入故事主题');
      textareaRef.current?.focus();
      return;
    }

    setThemeError(false);
    setMessages([]);
    setStory(null);
    setError(null);
    setCurrentPhase('正在创建会话...');
    setCurrentRound(0);
    setThinkingAgents(new Set());
    setCompletedProposals(new Set());
    setAgentProposals({});
    setDiscussionFeedbacks([]);
    setExpandedRaw({});
    setLoading(true);

    try {
      const createRes = await axios.post(`${API_BASE}/api/v1/stories`, {
        theme: trimmedTheme,
        genre: genre || undefined,
      });
      const { session_id } = createRes.data;

      setLoading(false);
      setIsGenerating(true);
      setCurrentPhase('正在连接Agent...');

      const stored: StoredSession = {
        sessionId: session_id,
        theme: trimmedTheme,
        genre: genre || '',
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
      connectToStream(session_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || '创建会话失败');
      setLoading(false);
      setIsGenerating(false);
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const s = (v: any): string => {
    if (typeof v === 'string') return v;
    if (v === null || v === undefined) return '';
    if (typeof v === 'object') return JSON.stringify(v);
    return String(v);
  };

  const renderPlotContent = (content: ProposalContent) => (
    <>
      {content.title && (
        <div>
          <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">故事标题</span>
          <p className="text-base font-semibold text-gray-800 mt-0.5">{s(content.title)}</p>
        </div>
      )}
      {content.genre && (
        <div className="mt-3">
          <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">类型</span>
          <p className="mt-0.5">{s(GENRE_LABELS[content.genre] || content.genre)}</p>
        </div>
      )}
      {content.synopsis && (
        <div className="mt-3">
          <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">简介</span>
          <p className="mt-0.5 leading-relaxed">{s(content.synopsis)}</p>
        </div>
      )}
      {Array.isArray(content.themes) && content.themes.length > 0 && (
        <div className="mt-3">
          <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">主题</span>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {content.themes.map((t, i) => (
              <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{s(t)}</span>
            ))}
          </div>
        </div>
      )}
      {Array.isArray(content.acts) && content.acts.length > 0 && (
        <div className="mt-3">
          <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">故事结构</span>
          <div className="mt-2 space-y-3">
            {content.acts.map((act, i) => (
              <div key={i} className="relative pl-4 border-l-2 border-blue-200">
                <div className="absolute -left-[9px] top-0 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-[8px] font-bold">
                  {i + 1}
                </div>
                <p className="font-medium text-gray-800">{s(act.name)}</p>
                <p className="text-gray-600 text-xs mt-0.5">{s(act.description)}</p>
                {Array.isArray(act.key_events) && act.key_events.length > 0 && (
                  <ul className="mt-1 space-y-0.5">
                    {act.key_events.map((evt, j) => (
                      <li key={j} className="text-xs text-gray-500 flex items-start gap-1.5">
                        <span className="text-blue-400 mt-0.5">▸</span>
                        {s(evt)}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );

  const renderCharacterContent = (content: ProposalContent) => {
    if (!Array.isArray(content.characters) || content.characters.length === 0) {
      return <p className="text-gray-400 italic">暂无角色数据</p>;
    }
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {content.characters.map((char, i) => (
          <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-800">{s(char.name)}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded ${
                char.role === 'protagonist' ? 'bg-green-100 text-green-700' :
                char.role === 'antagonist' ? 'bg-red-100 text-red-700' :
                'bg-gray-200 text-gray-600'
              }`}>
                {char.role === 'protagonist' ? '主角' : char.role === 'antagonist' ? '反派' : '配角'}
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-1"><span className="font-medium">性格：</span>{s(char.personality)}</p>
            <p className="text-xs text-gray-500 mb-1"><span className="font-medium">动机：</span>{s(char.motivation)}</p>
            {char.arc && <p className="text-xs text-gray-500"><span className="font-medium">成长弧：</span>{s(char.arc)}</p>}
            {Array.isArray(char.relationships) && char.relationships.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {char.relationships.map((rel, j) => (
                  <span key={j} className="text-xs px-1.5 py-0.5 bg-gray-200 rounded text-gray-600">
                    {s(rel.character_name)} · {s(rel.relation)}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderWorldContent = (content: ProposalContent) => {
    const ws = content.world_setting;
    if (!ws) return <p className="text-gray-400 italic">暂无世界观数据</p>;

    return (
      <>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-blue-50 rounded-lg">
            <span className="text-xs font-medium text-blue-600">时代背景</span>
            <p className="text-sm text-gray-800 mt-0.5">{s(ws.era)}</p>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <span className="text-xs font-medium text-purple-600">地点</span>
            <p className="text-sm text-gray-800 mt-0.5">{s(ws.location)}</p>
          </div>
          {ws.technology_level && (
            <div className="p-3 bg-green-50 rounded-lg">
              <span className="text-xs font-medium text-green-600">科技水平</span>
              <p className="text-sm text-gray-800 mt-0.5">{s(ws.technology_level)}</p>
            </div>
          )}
          {ws.culture && (
            <div className="p-3 bg-orange-50 rounded-lg">
              <span className="text-xs font-medium text-orange-600">文化背景</span>
              <p className="text-sm text-gray-800 mt-0.5">{s(ws.culture)}</p>
            </div>
          )}
        </div>
        {Array.isArray(ws.rules) && ws.rules.length > 0 && (
          <div className="mt-3">
            <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">世界规则</span>
            <ul className="mt-1.5 space-y-1">
              {ws.rules.map((rule, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-blue-500 mt-0.5">▸</span>
                  {s(rule)}
                </li>
              ))}
            </ul>
          </div>
        )}
        {Array.isArray(ws.factions) && ws.factions.length > 0 && (
          <div className="mt-3">
            <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">势力/派系</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {ws.factions.map((f, i) => (
                <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">{s(f)}</span>
              ))}
            </div>
          </div>
        )}
        {ws.history && (
          <div className="mt-3">
            <span className="font-medium text-gray-500 text-xs uppercase tracking-wide">历史背景</span>
            <p className="mt-0.5 text-sm text-gray-600">{s(ws.history)}</p>
          </div>
        )}
      </>
    );
  };

  const renderDialogueContent = (content: ProposalContent) => {
    if (!Array.isArray(content.dialogues) || content.dialogues.length === 0) {
      return <p className="text-gray-400 italic">暂无对话数据</p>;
    }
    return (
      <div className="space-y-4">
        {content.dialogues.map((dialogue, i) => (
          <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
            <p className="text-xs text-gray-500 mb-2 flex items-center gap-1.5">
              <span>📍</span> {s(dialogue.scene)}
              <span className="text-gray-300 mx-1">·</span>
              <span>{Array.isArray(dialogue.participants) ? s(dialogue.participants.join('、')) : s(dialogue.participants)}</span>
            </p>
            <div className="space-y-1.5 pl-3 border-l-2 border-blue-200">
              {Array.isArray(dialogue.content) && dialogue.content.map((line, j) => (
                <div key={j} className="flex items-start gap-2 text-sm">
                  <span className="font-medium text-blue-600 min-w-[70px] flex-shrink-0">{s(line.character)}：</span>
                  <span className="text-gray-700">{s(line.line)}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderProposalContent = (agentId: string, content?: ProposalContent) => {
    if (!content) return <p className="text-gray-400 italic">暂无数据</p>;
    switch (agentId) {
      case 'plot_agent': return renderPlotContent(content);
      case 'character_agent': return renderCharacterContent(content);
      case 'world_agent': return renderWorldContent(content);
      case 'dialogue_agent': return renderDialogueContent(content);
      default: return <p className="text-xs text-gray-500">{JSON.stringify(content).slice(0, 200)}...</p>;
    }
  };

  const handleReset = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setTheme('');
    setGenre('');
    setStory(null);
    setMessages([]);
    setError(null);
    setIsGenerating(false);
    setLoading(false);
    setCurrentPhase('');
    setCurrentRound(0);
    setThinkingAgents(new Set());
    setCompletedProposals(new Set());
    setAgentProposals({});
    localStorage.removeItem(STORAGE_KEY);
  };

  const formatTime = (timestamp: number) => {
    const d = new Date(timestamp);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
  };

  const getMessageStyle = (msg: Message) => {
    switch (msg.type) {
      case 'status': return 'bg-gray-50 border-gray-200';
      case 'round': return 'bg-indigo-50 border-indigo-200';
      case 'error': return 'bg-red-50 border-red-200';
      case 'complete': return 'bg-green-50 border-green-200';
      case 'thinking': return 'bg-yellow-50 border-yellow-200 animate-pulse';
      case 'proposal':
      case 'discussion': {
        const c = AGENT_COLORS[msg.agent_id];
        return c ? `${c.bg} ${c.border}` : 'bg-gray-50 border-gray-200';
      }
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const getMessageIcon = (msg: Message) => {
    switch (msg.type) {
      case 'status': return '📢';
      case 'round': return '🔄';
      case 'proposal': return '📋';
      case 'discussion': return '💬';
      case 'complete': return '✅';
      case 'error': return '❌';
      case 'thinking': return '⏳';
      default: return '📝';
    }
  };

  const agentProgress = (agentsList: AgentInfo[]) => {
    return agentsList.map(agent => {
      const isThinking = thinkingAgents.has(agent.id);
      const isCompleted = completedProposals.has(agent.id);
      let statusText: string;
      let progressPercent: number;
      let barColor: string;
      let textColor: string;
      let bgColor: string;

      if (isCompleted) {
        statusText = '已完成方案';
        progressPercent = 100;
        barColor = 'bg-green-500';
        textColor = 'text-green-700';
        bgColor = 'bg-green-100';
      } else if (isThinking) {
        statusText = '思考中...';
        progressPercent = 60;
        barColor = 'bg-yellow-500';
        textColor = 'text-yellow-700';
        bgColor = 'bg-yellow-100';
      } else if (currentRound > 0) {
        statusText = '等待轮次';
        progressPercent = 30;
        barColor = 'bg-gray-400';
        textColor = 'text-gray-500';
        bgColor = 'bg-gray-100';
      } else {
        statusText = '等待中';
        progressPercent = 10;
        barColor = 'bg-gray-300';
        textColor = 'text-gray-500';
        bgColor = 'bg-gray-100';
      }

      return { agent, statusText, progressPercent, barColor, textColor, bgColor };
    });
  };

  const agentsForDisplay = agents.length > 0 ? agents : Object.keys(AGENT_NAMES).map(id => ({
    id,
    name: AGENT_NAMES[id],
    description: '',
    status: '',
  }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">多Agent创意写作系统</h1>
              <p className="text-sm text-gray-500 mt-1">四个AI Agent协作，实时展示每一步创作过程</p>
            </div>
            <div className="flex items-center gap-2">
              {agentsForDisplay.map(agent => (
                <div key={agent.id} className="flex items-center gap-1 px-3 py-1 bg-gray-50 rounded-full text-xs">
                  <span>{AGENT_EMOJIS[agent.id] || '🤖'}</span>
                  <span className="text-gray-600">{agent.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">创作故事</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="theme" className="block text-sm font-medium text-gray-700 mb-2">
                    故事主题 <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    ref={textareaRef}
                    id="theme"
                    value={theme}
                    onChange={(e) => { setTheme(e.target.value); if (themeError && e.target.value.trim()) setThemeError(false); }}
                    placeholder="输入故事主题..."
                    rows={4}
                    maxLength={500}
                    disabled={loading || isGenerating}
                    className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-colors ${themeError ? 'border-red-400 bg-red-50' : 'border-gray-200'}`}
                  />
                  <div className="flex justify-between mt-1">
                    <p className="text-xs text-gray-400">描述故事的核心概念、背景或主题</p>
                    <p className="text-xs text-gray-400">{theme.length}/500</p>
                  </div>
                </div>

                <div>
                  <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-2">故事类型</label>
                  <select
                    id="genre"
                    value={genre}
                    onChange={(e) => setGenre(e.target.value)}
                    disabled={loading || isGenerating}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  >
                    <option value="">不限制类型</option>
                    {Object.entries(GENRE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading || isGenerating}
                  className="w-full bg-blue-500 text-white py-3 px-4 rounded-xl font-medium hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {loading ? '创建中...' : isGenerating ? '生成中...' : '🎬 开始生成'}
                </button>
              </form>

              {(isGenerating || story) && (
                <button onClick={handleReset} className="w-full mt-3 bg-gray-100 text-gray-700 py-2 px-4 rounded-xl font-medium hover:bg-gray-200 transition-colors">
                  重置
                </button>
              )}
            </div>

            {isGenerating && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-800">Agent 进度</h2>
                  <span className="flex items-center gap-1 text-xs text-blue-600">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                    进行中
                    {currentRound > 0 && <span> · 第{currentRound}轮</span>}
                  </span>
                </div>
                <div className="space-y-3">
                  {agentProgress(agentsForDisplay).map(({ agent, statusText, progressPercent, barColor, textColor, bgColor }) => (
                    <div key={agent.id} className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full ${bgColor} flex items-center justify-center text-lg flex-shrink-0`}>
                        {AGENT_EMOJIS[agent.id] || '🤖'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-700 truncate">{agent.name}</span>
                          <span className={`${textColor} text-xs flex-shrink-0 ml-2`}>{statusText}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                          <div className={`${barColor} h-2 rounded-full transition-all duration-700 ${progressPercent >= 60 ? '' : ''}`}
                            style={{ width: `${progressPercent}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(isGenerating || messages.length > 0) && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-800">实时日志</h2>
                  {isGenerating && <span className="text-xs text-gray-400">{messages.length} 条消息</span>}
                </div>
                <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`p-3 rounded-lg border text-sm ${getMessageStyle(msg)}`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span>{getMessageIcon(msg)}</span>
                          <span className="font-medium text-gray-700">{msg.agent_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {msg.round && (
                            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">
                              第{msg.round}轮
                            </span>
                          )}
                          <span className="text-xs text-gray-400">{formatTime(msg.timestamp)}</span>
                        </div>
                      </div>
                      <p className="text-gray-600 whitespace-pre-wrap leading-relaxed text-xs">{msg.content}</p>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">❌</span>
                  <div>
                    <h3 className="font-medium text-red-800">错误</h3>
                    <p className="text-sm text-red-600 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {!story && !isGenerating && !error && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <div className="text-6xl mb-4">📝</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">等待创作</h3>
                <p className="text-gray-500 max-w-md mx-auto">
                  输入故事主题后，四个专业AI Agent将协作创作完整的故事剧本
                </p>
                <div className="mt-8 flex justify-center gap-8 text-sm">
                  <div className="text-center">
                    <div className="text-2xl mb-1">📖</div>
                    <span className="text-gray-500">剧情设计</span>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-1">👤</div>
                    <span className="text-gray-500">人物塑造</span>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-1">🌍</div>
                    <span className="text-gray-500">世界观</span>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-1">💬</div>
                    <span className="text-gray-500">对话创作</span>
                  </div>
                </div>
              </div>
            )}

            {isGenerating && !story && (
              <div className="space-y-4">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-800">
                      {currentPhase || 'Agent 正在协作...'}
                    </h3>
                    <span className="text-sm text-gray-500">
                      {currentRound > 0 ? `第 ${currentRound} 轮讨论` : '初始提案阶段'}
                    </span>
                  </div>
                </div>

                {['plot_agent', 'character_agent', 'world_agent', 'dialogue_agent'].map((agentId) => {
                  const prop = agentProposals[agentId];
                  const isThinking = thinkingAgents.has(agentId);
                  const isDone = completedProposals.has(agentId);
                  const agentName = AGENT_NAMES[agentId] || agentId;

                  if (!isDone && !isThinking) {
                    return (
                      <div key={agentId} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 opacity-50">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="text-2xl">{AGENT_EMOJIS[agentId]}</span>
                          <div>
                            <h3 className="font-semibold text-gray-800">{agentName}</h3>
                            <p className="text-xs text-gray-400">等待进行</p>
                          </div>
                        </div>
                      </div>
                    );
                  }

                  if (isThinking) {
                    return (
                      <div key={agentId} className="bg-white rounded-xl shadow-sm border border-yellow-200 p-5">
                        <div className="flex items-center gap-3 mb-3">
                          <span className="text-2xl animate-bounce">{AGENT_EMOJIS[agentId]}</span>
                          <div>
                            <h3 className="font-semibold text-gray-800">{agentName}</h3>
                            <span className="inline-flex items-center gap-1 text-xs text-yellow-600">
                              <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
                              思考中...
                            </span>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div className="bg-yellow-400 h-1.5 rounded-full animate-pulse" style={{ width: '60%' }} />
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={agentId} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                      <div className={`px-5 py-3 flex items-center justify-between ${agentId === 'plot_agent' ? 'bg-blue-50' : agentId === 'character_agent' ? 'bg-green-50' : agentId === 'world_agent' ? 'bg-purple-50' : 'bg-orange-50'}`}>
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{AGENT_EMOJIS[agentId]}</span>
                          <div>
                            <h3 className="font-semibold text-gray-800">{agentName}</h3>
                            <p className="text-xs text-gray-500 line-clamp-1">{prop?.summary || ''}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {prop?.round && (
                            <span className="text-xs px-2 py-0.5 bg-white/80 rounded text-gray-500">第{prop.round}轮</span>
                          )}
                          <span className="text-xs px-2 py-0.5 bg-white/80 rounded text-green-600">已完成</span>
                        </div>
                      </div>

                      <div className="px-5 py-4 text-sm text-gray-700 space-y-3">
                        {renderProposalContent(agentId, prop?.content)}
                      </div>

                      <div className="px-5 py-2 border-t border-gray-100">
                        <button
                          onClick={() => setExpandedRaw(prev => ({ ...prev, [agentId]: !prev[agentId] }))}
                          className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1"
                        >
                          {expandedRaw[agentId] ? '收起原始方案 ▲' : '查看原始方案 ▼'}
                        </button>
                        {expandedRaw[agentId] && prop?.content && (
                          <pre className="mt-2 p-3 bg-gray-50 rounded border border-gray-200 text-xs text-gray-600 overflow-auto max-h-80 whitespace-pre-wrap leading-relaxed">
                            {JSON.stringify(prop.content, null, 2)}
                          </pre>
                        )}
                      </div>
                    </div>
                  );
                })}

                {discussionFeedbacks.length > 0 && (
                  <div className="space-y-3">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
                      <h3 className="text-base font-semibold text-gray-800">💬 讨论与反馈</h3>
                    </div>
                    {discussionFeedbacks.map((fb, idx) => (
                      <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        <div className="px-4 py-2 bg-yellow-50 border-b border-yellow-100 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span>{AGENT_EMOJIS[fb.agent_id] || '💬'}</span>
                            <span className="font-medium text-sm text-gray-800">{fb.agent_name}</span>
                            <span className="text-xs text-gray-500">→ 反馈给 {s(AGENT_NAMES[fb.target_agent] || fb.target_agent)}</span>
                          </div>
                          <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">第{fb.round}轮</span>
                        </div>
                          <div className="px-4 py-3 text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                            {s(fb.content)}
                          </div>
                        {Array.isArray(fb.suggestions) && fb.suggestions.length > 0 && (
                          <div className="px-4 pb-3">
                            <span className="text-xs font-medium text-gray-500">建议：</span>
                            <ul className="mt-1 space-y-0.5">
                              {fb.suggestions.map((s, i) => (
                                <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                                  <span className="text-blue-400 mt-0.5">▸</span>
                                  {s}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

              </div>
            )}

            {story && (
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl p-6 text-white">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-2xl font-bold mb-2">{story.title}</h2>
                      <p className="text-white/90 text-lg">{story.synopsis}</p>
                    </div>
                    <span className="px-3 py-1 bg-white/20 rounded-full text-sm flex-shrink-0 ml-4">
                      {GENRE_LABELS[story.genre] || story.genre}
                    </span>
                  </div>
                </div>

                {story.outline?.acts && story.outline.acts.length > 0 && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <span>📖</span> 故事大纲
                    </h3>
                    <div className="space-y-4">
                      {story.outline.acts.map((act, index) => (
                        <div key={index} className="relative pl-6 border-l-2 border-blue-200">
                          <div className="absolute -left-3 top-0 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                            {index + 1}
                          </div>
                          <h4 className="font-semibold text-gray-800">{act.name}</h4>
                          <p className="text-gray-600 text-sm mt-1">{act.description}</p>
                          {act.key_events && act.key_events.length > 0 && (
                            <ul className="mt-2 space-y-1">
                              {act.key_events.map((event, i) => (
                                <li key={i} className="text-sm text-gray-500 flex items-start gap-2">
                                  <span className="text-blue-400">▸</span>
                                  {event}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {story.characters?.length > 0 && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <span>👥</span> 角色设定
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {story.characters.map((char, index) => (
                        <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-blue-200 transition-colors">
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-gray-800">{char.name}</h4>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${char.role === 'protagonist' ? 'bg-green-100 text-green-700' : char.role === 'antagonist' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                              {char.role === 'protagonist' ? '主角' : char.role === 'antagonist' ? '反派' : '配角'}
                            </span>
                          </div>
                          <div className="space-y-2 text-sm">
                            <p><span className="font-medium text-gray-600">性格：</span>{char.personality}</p>
                            <p><span className="font-medium text-gray-600">背景：</span>{char.background}</p>
                            <p><span className="font-medium text-gray-600">动机：</span>{char.motivation}</p>
                            {char.arc && <p><span className="font-medium text-gray-600">成长弧：</span>{char.arc}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {story.world_setting && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <span>🌍</span> 世界观设定
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 bg-blue-50 rounded-lg">
                        <span className="text-xs font-medium text-blue-600">时代背景</span>
                        <p className="mt-1 text-gray-800">{story.world_setting.era}</p>
                      </div>
                      <div className="p-4 bg-purple-50 rounded-lg">
                        <span className="text-xs font-medium text-purple-600">地点</span>
                        <p className="mt-1 text-gray-800">{story.world_setting.location}</p>
                      </div>
                      {story.world_setting.technology_level && (
                        <div className="p-4 bg-green-50 rounded-lg">
                          <span className="text-xs font-medium text-green-600">科技水平</span>
                          <p className="mt-1 text-gray-800">{story.world_setting.technology_level}</p>
                        </div>
                      )}
                      {story.world_setting.culture && (
                        <div className="p-4 bg-orange-50 rounded-lg">
                          <span className="text-xs font-medium text-orange-600">文化背景</span>
                          <p className="mt-1 text-gray-800">{story.world_setting.culture}</p>
                        </div>
                      )}
                    </div>
                    {story.world_setting.rules && story.world_setting.rules.length > 0 && (
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <span className="text-sm font-medium text-gray-600">世界规则</span>
                        <ul className="mt-2 space-y-1">
                          {story.world_setting.rules.map((rule, i) => (
                            <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                              <span className="text-blue-500">▸</span>
                              {rule}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {story.dialogues?.length > 0 && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
                      <span>💬</span> 对话示例
                    </h3>
                    <div className="space-y-6">
                      {story.dialogues.map((dialogue, index) => (
                        <div key={index} className="p-4 bg-gray-50 rounded-lg">
                          <p className="text-sm text-gray-500 mb-3 flex items-center gap-2">
                            <span>📍</span> {dialogue.scene}
                          </p>
                          <div className="space-y-2 pl-4 border-l-2 border-blue-200">
                            {dialogue.content?.map((line, i) => (
                              <div key={i} className="flex items-start gap-3">
                                <span className="font-medium text-blue-600 min-w-[80px]">{line.character}：</span>
                                <span className="text-gray-700">{line.line}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
