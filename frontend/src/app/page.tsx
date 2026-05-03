'use client';

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface AgentMessage {
  agent_id: string;
  agent_name: string;
  content: string;
  message_type: string;
  round?: number;
}

interface Story {
  title: string;
  genre: string;
  synopsis: string;
  outline: any;
  characters: any[];
  dialogues: any[];
  world_setting: any;
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [story, setStory] = useState<Story | null>(null);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentPhase, setCurrentPhase] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getAgentName = (agentId: string) => {
    const names: Record<string, string> = {
      plot_agent: '剧情Agent',
      character_agent: '人物Agent',
      world_agent: '世界观Agent',
      dialogue_agent: '对话Agent',
    };
    return names[agentId] || agentId;
  };

  const getAgentColor = (agentId: string) => {
    const colors: Record<string, string> = {
      plot_agent: 'bg-blue-100 border-blue-300',
      character_agent: 'bg-green-100 border-green-300',
      world_agent: 'bg-purple-100 border-purple-300',
      dialogue_agent: 'bg-orange-100 border-orange-300',
    };
    return colors[agentId] || 'bg-gray-100 border-gray-300';
  };

  const getAgentEmoji = (agentId: string) => {
    const emojis: Record<string, string> = {
      plot_agent: '📖',
      character_agent: '👤',
      world_agent: '🌍',
      dialogue_agent: '💬',
    };
    return emojis[agentId] || '🤖';
  };

  const addMessage = (msg: AgentMessage) => {
    setMessages(prev => [...prev, msg]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const themeInput = form.elements.namedItem('theme') as HTMLInputElement;
    const genreSelect = form.elements.namedItem('genre') as HTMLSelectElement;
    const theme = themeInput.value.trim();
    const genre = genreSelect.value;

    if (!theme) {
      alert('请输入故事主题');
      return;
    }

    setMessages([]);
    setStory(null);
    setLoading(true);
    setError(null);
    setCurrentPhase('准备中...');

    try {
      const createResponse = await axios.post('/api/v1/stories', {
        theme,
        genre: genre || undefined,
      });

      const { session_id } = createResponse.data;
      setSessionId(session_id);
      setCurrentPhase('Agent们正在协作生成故事...');

      // 调用生成接口
      const generateResponse = await axios.post(`/api/v1/stories/${session_id}/generate`);

      if (generateResponse.data.status === 'completed') {
        // 获取结果
        const storyResponse = await axios.get(`/api/v1/stories/${session_id}`);
        setStory(storyResponse.data.story);
        setCurrentPhase('生成完成！');
      } else {
        setError('故事生成失败');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '生成过程中出现错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 text-center text-gray-800">
          多Agent创意写作系统
        </h1>
        <p className="text-center text-gray-500 mb-8">
          剧情Agent · 人物Agent · 世界观Agent · 对话Agent 协作为您创作故事
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：输入和讨论过程 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 输入表单 */}
            <form onSubmit={handleSubmit} className="p-6 bg-white rounded-lg shadow-md">
              <h2 className="text-lg font-semibold mb-4">故事设定</h2>
              
              <div className="mb-4">
                <label htmlFor="theme" className="block text-sm font-medium text-gray-700 mb-2">
                  故事主题 *
                </label>
                <input
                  type="text"
                  id="theme"
                  name="theme"
                  placeholder="例如：未来世界的AI觉醒"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                />
              </div>

              <div className="mb-6">
                <label htmlFor="genre" className="block text-sm font-medium text-gray-700 mb-2">
                  故事类型
                </label>
                <select
                  id="genre"
                  name="genre"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                >
                  <option value="">请选择类型（可选）</option>
                  <option value="science_fiction">科幻</option>
                  <option value="fantasy">奇幻</option>
                  <option value="realism">现实</option>
                  <option value="mystery">悬疑</option>
                  <option value="romance">爱情</option>
                  <option value="horror">恐怖</option>
                  <option value="adventure">冒险</option>
                  <option value="historical">历史</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? '生成中...' : '开始生成'}
              </button>
            </form>

            {/* 讨论过程 */}
            <div className="p-6 bg-white rounded-lg shadow-md">
              <h2 className="text-lg font-semibold mb-4">Agent讨论过程</h2>
              
              {loading && (
                <div className="mb-4 p-3 bg-blue-50 rounded-md">
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
                    <span className="text-sm text-blue-700">{currentPhase}</span>
                  </div>
                </div>
              )}

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {messages.length === 0 && !loading && (
                  <p className="text-gray-400 text-sm text-center py-8">
                    等待开始生成...
                  </p>
                )}
                
                {messages.map((msg, index) => (
                  <div 
                    key={index}
                    className={`p-3 rounded-md border ${
                      msg.agent_id === 'system' 
                        ? 'bg-gray-100 border-gray-300' 
                        : getAgentColor(msg.agent_id)
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">
                        {getAgentEmoji(msg.agent_id)} {msg.agent_name}
                      </span>
                      {msg.round && (
                        <span className="text-xs text-gray-500">第{msg.round}轮</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{msg.content}</p>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          {/* 右侧：生成结果 */}
          <div className="lg:col-span-2 space-y-6">
            {error && (
              <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
                ❌ {error}
              </div>
            )}

            {!story && !loading && !error && (
              <div className="p-12 bg-white rounded-lg shadow-md text-center">
                <div className="text-6xl mb-4">📝</div>
                <h3 className="text-xl font-semibold text-gray-700 mb-2">
                  等待生成故事
                </h3>
                <p className="text-gray-500">
                  输入主题并点击"开始生成"，四个AI Agent将协作为您创作故事
                </p>
              </div>
            )}

            {story && (
              <>
                {/* 标题和简介 */}
                <div className="p-6 bg-white rounded-lg shadow-md">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-bold text-gray-800">{story.title}</h2>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                      {story.genre}
                    </span>
                  </div>
                  <p className="text-gray-600 text-lg">{story.synopsis}</p>
                </div>

                {/* 故事大纲 */}
                {story.outline?.acts && (
                  <div className="p-6 bg-white rounded-lg shadow-md">
                    <h3 className="text-xl font-semibold mb-4 flex items-center">
                      <span className="mr-2">📖</span> 故事大纲
                    </h3>
                    <div className="space-y-4">
                      {story.outline.acts.map((act: any, index: number) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                          <h4 className="font-semibold text-gray-800">
                            第{index + 1}幕：{act.name}
                          </h4>
                          <p className="text-gray-600 text-sm mt-1">{act.description}</p>
                          {act.key_events?.length > 0 && (
                            <ul className="mt-2 space-y-1">
                              {act.key_events.map((event: string, i: number) => (
                                <li key={i} className="text-sm text-gray-500 flex items-start">
                                  <span className="mr-2">•</span>
                                  <span>{event}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 角色设定 */}
                {story.characters?.length > 0 && (
                  <div className="p-6 bg-white rounded-lg shadow-md">
                    <h3 className="text-xl font-semibold mb-4 flex items-center">
                      <span className="mr-2">👥</span> 角色设定
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {story.characters.map((char: any, index: number) => (
                        <div key={index} className="p-4 bg-gray-50 rounded-lg border">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-gray-800">{char.name}</h4>
                            <span className={`px-2 py-1 rounded text-xs ${
                              char.role === 'protagonist' ? 'bg-green-100 text-green-700' :
                              char.role === 'antagonist' ? 'bg-red-100 text-red-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {char.role === 'protagonist' ? '主角' :
                               char.role === 'antagonist' ? '反派' : '配角'}
                            </span>
                          </div>
                          <div className="space-y-2 text-sm">
                            <p><span className="font-medium">性格：</span>{char.personality}</p>
                            <p><span className="font-medium">背景：</span>{char.background}</p>
                            <p><span className="font-medium">动机：</span>{char.motivation}</p>
                            {char.arc && <p><span className="font-medium">成长：</span>{char.arc}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 世界观设定 */}
                {story.world_setting && (
                  <div className="p-6 bg-white rounded-lg shadow-md">
                    <h3 className="text-xl font-semibold mb-4 flex items-center">
                      <span className="mr-2">🌍</span> 世界观设定
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 bg-gray-50 rounded">
                        <span className="text-sm font-medium text-gray-500">时代背景</span>
                        <p className="mt-1">{story.world_setting.era}</p>
                      </div>
                      <div className="p-3 bg-gray-50 rounded">
                        <span className="text-sm font-medium text-gray-500">地点</span>
                        <p className="mt-1">{story.world_setting.location}</p>
                      </div>
                      {story.world_setting.technology_level && (
                        <div className="p-3 bg-gray-50 rounded">
                          <span className="text-sm font-medium text-gray-500">科技水平</span>
                          <p className="mt-1">{story.world_setting.technology_level}</p>
                        </div>
                      )}
                      {story.world_setting.culture && (
                        <div className="p-3 bg-gray-50 rounded">
                          <span className="text-sm font-medium text-gray-500">文化背景</span>
                          <p className="mt-1">{story.world_setting.culture}</p>
                        </div>
                      )}
                    </div>
                    {story.world_setting.rules?.length > 0 && (
                      <div className="mt-4">
                        <span className="text-sm font-medium text-gray-500">世界规则</span>
                        <ul className="mt-2 space-y-1">
                          {story.world_setting.rules.map((rule: string, i: number) => (
                            <li key={i} className="text-sm flex items-start">
                              <span className="text-blue-500 mr-2">▸</span>
                              <span>{rule}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* 对话示例 */}
                {story.dialogues?.length > 0 && (
                  <div className="p-6 bg-white rounded-lg shadow-md">
                    <h3 className="text-xl font-semibold mb-4 flex items-center">
                      <span className="mr-2">💬</span> 对话示例
                    </h3>
                    {story.dialogues.map((dialogue: any, index: number) => (
                      <div key={index} className="mb-6 last:mb-0">
                        <p className="text-sm text-gray-500 mb-3 italic">📍 {dialogue.scene}</p>
                        <div className="space-y-2 pl-4 border-l-2 border-gray-200">
                          {dialogue.content?.map((line: any, i: number) => (
                            <div key={i} className="flex items-start">
                              <span className="font-medium text-gray-700 mr-2 min-w-[60px]">{line.character}：</span>
                              <span className="text-gray-600">{line.line}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
