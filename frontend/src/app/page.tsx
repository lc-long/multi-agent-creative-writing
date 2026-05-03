'use client';

import { useState } from 'react';
import axios from 'axios';

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
  const [theme, setTheme] = useState('');
  const [genre, setGenre] = useState('');
  const [loading, setLoading] = useState(false);
  const [story, setStory] = useState<Story | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!theme.trim()) {
      setError('请输入故事主题');
      return;
    }

    setLoading(true);
    setError(null);
    setStory(null);

    try {
      // 创建会话
      const createResponse = await axios.post('/api/v1/stories', {
        theme: theme,
        genre: genre || undefined,
      });

      const { session_id } = createResponse.data;
      setSessionId(session_id);

      // 开始生成
      const generateResponse = await axios.post(`/api/v1/stories/${session_id}/generate`);
      
      if (generateResponse.data.status === 'completed') {
        // 获取结果
        const storyResponse = await axios.get(`/api/v1/stories/${session_id}`);
        setStory(storyResponse.data.story);
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
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">
          多Agent创意写作系统
        </h1>
        
        <p className="text-center text-gray-600 mb-8">
          多个AI Agent协作，为您生成独特的故事
        </p>

        {/* 输入表单 */}
        <form onSubmit={handleSubmit} className="mb-12 p-6 bg-white rounded-lg shadow-md">
          <div className="mb-4">
            <label htmlFor="theme" className="block text-sm font-medium text-gray-700 mb-2">
              故事主题 *
            </label>
            <input
              type="text"
              id="theme"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
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
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
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
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? '正在生成...' : '开始生成'}
          </button>
        </form>

        {/* 错误信息 */}
        {error && (
          <div className="mb-8 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {/* 加载状态 */}
        {loading && (
          <div className="mb-8 p-6 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
              <span className="text-blue-700">
                Agent们正在协作生成故事，请稍候...
              </span>
            </div>
            {sessionId && (
              <p className="text-sm text-gray-500 mt-2 text-center">
                会话ID: {sessionId}
              </p>
            )}
          </div>
        )}

        {/* 故事结果 */}
        {story && (
          <div className="space-y-8">
            {/* 标题和简介 */}
            <div className="p-6 bg-white rounded-lg shadow-md">
              <h2 className="text-2xl font-bold mb-2">{story.title}</h2>
              <p className="text-gray-600 mb-2">类型：{story.genre}</p>
              <p className="text-gray-700">{story.synopsis}</p>
            </div>

            {/* 故事大纲 */}
            {story.outline && (
              <div className="p-6 bg-white rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-4">故事大纲</h3>
                <div className="space-y-4">
                  {story.outline.acts?.map((act: any, index: number) => (
                    <div key={index} className="border-l-4 border-blue-500 pl-4">
                      <h4 className="font-medium">{act.name}</h4>
                      <p className="text-gray-600 text-sm">{act.description}</p>
                      {act.key_events && (
                        <ul className="mt-2 list-disc list-inside text-sm text-gray-500">
                          {act.key_events.map((event: string, i: number) => (
                            <li key={i}>{event}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 角色设定 */}
            {story.characters && story.characters.length > 0 && (
              <div className="p-6 bg-white rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-4">角色设定</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {story.characters.map((char: any, index: number) => (
                    <div key={index} className="p-4 bg-gray-50 rounded-md">
                      <h4 className="font-medium">{char.name}</h4>
                      <p className="text-sm text-gray-500">{char.role}</p>
                      <p className="text-sm mt-2">{char.personality}</p>
                      <p className="text-sm text-gray-600 mt-1">{char.background}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 世界观设定 */}
            {story.world_setting && (
              <div className="p-6 bg-white rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-4">世界观设定</h3>
                <div className="space-y-2">
                  <p><strong>时代：</strong>{story.world_setting.era}</p>
                  <p><strong>地点：</strong>{story.world_setting.location}</p>
                  {story.world_setting.rules && (
                    <div>
                      <strong>世界规则：</strong>
                      <ul className="list-disc list-inside ml-4">
                        {story.world_setting.rules.map((rule: string, i: number) => (
                          <li key={i}>{rule}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 对话示例 */}
            {story.dialogues && story.dialogues.length > 0 && (
              <div className="p-6 bg-white rounded-lg shadow-md">
                <h3 className="text-xl font-semibold mb-4">对话示例</h3>
                {story.dialogues.map((dialogue: any, index: number) => (
                  <div key={index} className="mb-6 last:mb-0">
                    <p className="text-sm text-gray-500 mb-2">{dialogue.scene}</p>
                    <div className="space-y-2">
                      {dialogue.content?.map((line: any, i: number) => (
                        <div key={i} className="flex">
                          <span className="font-medium mr-2">{line.character}:</span>
                          <span>{line.line}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
