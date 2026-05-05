'use client';

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface AgentInfo {
  id: string;
  name: string;
  description: string;
  status: string;
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

interface Message {
  id: string;
  agent_id: string;
  agent_name: string;
  content: string;
  type: 'status' | 'proposal' | 'discussion' | 'round' | 'complete' | 'error';
  round?: number;
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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadAgents = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/v1/agents');
      setAgents(res.data.agents);
    } catch (err) {
      console.error('Failed to load agents:', err);
    }
  };

  const addMessage = (msg: Omit<Message, 'id'>) => {
    setMessages(prev => [...prev, {
      ...msg,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    }]);
  };

  const connectToStream = (sid: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Use direct backend URL for SSE to avoid proxy issues
    const streamUrl = `http://localhost:8000/api/v1/stories/${sid}/stream`;
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (event.type) {
          case 'status':
            setCurrentPhase(data.message);
            addMessage({ agent_id: 'system', agent_name: '系统', content: data.message, type: 'status' });
            break;
          case 'round':
            addMessage({ agent_id: 'system', agent_name: '系统', content: `开始第 ${data.round} 轮讨论`, type: 'round', round: data.round });
            break;
          case 'proposal':
            addMessage({ agent_id: data.agent_id, agent_name: data.agent_name, content: `提出方案 (置信度: ${(data.confidence * 100).toFixed(0)}%)\n${data.summary}`, type: 'proposal', round: data.round });
            break;
          case 'discussion':
            addMessage({ agent_id: data.agent_id, agent_name: data.agent_name, content: data.content, type: 'discussion', round: data.round });
            break;
          case 'complete':
            setStory(data.story);
            setIsGenerating(false);
            setCurrentPhase('生成完成！');
            addMessage({ agent_id: 'system', agent_name: '系统', content: '故事生成完成！', type: 'complete' });
            eventSource.close();
            break;
          case 'error':
            setError(data.message);
            setIsGenerating(false);
            addMessage({ agent_id: 'system', agent_name: '系统', content: `错误: ${data.message}`, type: 'error' });
            eventSource.close();
            break;
          case 'end':
            eventSource.close();
            break;
        }
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };

    eventSource.onerror = () => {
      setError('连接中断，请重试');
      setIsGenerating(false);
      eventSource.close();
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
    setLoading(true);
    setCurrentPhase('正在创建会话...');

    try {
      const createRes = await axios.post('http://localhost:8000/api/v1/stories', {
        theme: trimmedTheme,
        genre: genre || undefined,
      });

      const { session_id } = createRes.data;
      setLoading(false);
      setIsGenerating(true);
      setCurrentPhase('Agent 正在协作生成故事...');

      connectToStream(session_id);
      await axios.post(`http://localhost:8000/api/v1/stories/${session_id}/generate`);
    } catch (err: any) {
      setError(err.response?.data?.detail || '创建会话失败');
      setLoading(false);
      setIsGenerating(false);
    }
  };

  const handleThemeChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setTheme(e.target.value);
    if (themeError && e.target.value.trim()) {
      setThemeError(false);
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
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">多Agent创意写作系统</h1>
              <p className="text-sm text-gray-500 mt-1">多个AI Agent协作，生成精彩故事</p>
            </div>
            <div className="flex items-center gap-2">
              {agents.map(agent => (
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
              <h2 className="text-lg font-semibold text-gray-800 mb-4">创建故事</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="theme" className="block text-sm font-medium text-gray-700 mb-2">
                    故事主题 <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    ref={textareaRef}
                    id="theme"
                    value={theme}
                    onChange={handleThemeChange}
                    placeholder="输入故事主题，描述你想要创作的故事..."
                    rows={4}
                    maxLength={500}
                    disabled={loading || isGenerating}
                    style={{ color: '#374151', backgroundColor: 'white' }}
                    className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-colors ${
                      themeError ? 'border-red-400 bg-red-50' : 'border-gray-200 disabled:bg-gray-50'
                    }`}
                  />
                  <div className="flex justify-between mt-1">
                    <p className="text-xs text-gray-400">描述故事的核心概念、背景或想要探索的主题</p>
                    <p className="text-xs text-gray-400">{theme.length}/500</p>
                  </div>
                </div>

                <div>
                  <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-2">
                    故事类型
                  </label>
                  <select
                    id="genre"
                    value={genre}
                    onChange={(e) => setGenre(e.target.value)}
                    disabled={loading || isGenerating}
                    style={{ color: '#374151', backgroundColor: 'white' }}
                    className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 transition-colors"
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
                  {isGenerating ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      生成中...
                    </>
                  ) : loading ? (
                    '创建中...'
                  ) : (
                    '🎬 开始生成'
                  )}
                </button>
              </form>

              {(isGenerating || story) && (
                <button
                  onClick={handleReset}
                  className="w-full mt-3 bg-gray-100 text-gray-700 py-2 px-4 rounded-xl font-medium hover:bg-gray-200 transition-colors"
                >
                  重置
                </button>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-800">Agent 协作过程</h2>
                {isGenerating && (
                  <span className="flex items-center gap-1 text-xs text-blue-600">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                    进行中
                  </span>
                )}
              </div>

              {isGenerating && currentPhase && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-100 rounded-lg">
                  <p className="text-sm text-blue-700">{currentPhase}</p>
                </div>
              )}

              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {messages.length === 0 && !isGenerating && (
                  <div className="text-center py-12">
                    <div className="text-4xl mb-3">💭</div>
                    <p className="text-gray-400 text-sm">输入主题后，Agent将开始协作</p>
                  </div>
                )}

                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`p-3 rounded-lg border ${
                      msg.type === 'status' || msg.type === 'round' ? 'bg-gray-50 border-gray-200' :
                      msg.type === 'error' ? 'bg-red-50 border-red-200' :
                      msg.type === 'complete' ? 'bg-green-50 border-green-200' :
                      msg.agent_id === 'system' ? 'bg-gray-50 border-gray-200' :
                      msg.agent_id === 'plot_agent' ? 'bg-blue-50 border-blue-200' :
                      msg.agent_id === 'character_agent' ? 'bg-green-50 border-green-200' :
                      msg.agent_id === 'world_agent' ? 'bg-purple-50 border-purple-200' :
                      msg.agent_id === 'dialogue_agent' ? 'bg-orange-50 border-orange-200' :
                      'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{AGENT_EMOJIS[msg.agent_id] || '📝'}</span>
                        <span className="text-sm font-medium text-gray-700">{msg.agent_name}</span>
                      </div>
                      {msg.round && (
                        <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded">
                          第{msg.round}轮
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{msg.content}</p>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">❌</span>
                  <div>
                    <h3 className="font-medium text-red-800">生成失败</h3>
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
                  输入故事主题，四个专业AI Agent将协作创作完整的故事剧本
                </p>
                <div className="mt-8 flex justify-center gap-8 text-sm">
                  <div className="text-center">
                    <div className="text-2xl mb-1">📖</div>
                    <span className="text-gray-500">剧情设计</span>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-1">👤</div>
                    <span className="text-gray-500">角色塑造</span>
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
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
                <div className="text-5xl mb-4 animate-bounce">🎭</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">Agent 正在创作中...</h3>
                <p className="text-gray-500">请稍候，创作过程可能需要30-60秒</p>
                <div className="mt-6 flex justify-center gap-4">
                  <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-full">
                    <span className="animate-pulse">📖</span>
                    <span className="text-sm text-blue-700">剧情</span>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-2 bg-green-50 rounded-full">
                    <span className="animate-pulse">👤</span>
                    <span className="text-sm text-green-700">人物</span>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-2 bg-purple-50 rounded-full">
                    <span className="animate-pulse">🌍</span>
                    <span className="text-sm text-purple-700">世界观</span>
                  </div>
                  <div className="flex items-center gap-2 px-4 py-2 bg-orange-50 rounded-full">
                    <span className="animate-pulse">💬</span>
                    <span className="text-sm text-orange-700">对话</span>
                  </div>
                </div>
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
                    <span className="px-3 py-1 bg-white/20 rounded-full text-sm">
                      {GENRE_LABELS[story.genre] || story.genre}
                    </span>
                  </div>
                </div>

                {story.outline?.acts?.length > 0 && (
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
                          {act.key_events?.length > 0 && (
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
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              char.role === 'protagonist' ? 'bg-green-100 text-green-700' :
                              char.role === 'antagonist' ? 'bg-red-100 text-red-700' :
                              'bg-gray-100 text-gray-600'
                            }`}>
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
                    {story.world_setting.rules?.length > 0 && (
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