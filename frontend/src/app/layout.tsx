import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Multi-Agent Creative Writing System',
  description: '多Agent创意写作系统 - 多个AI Agent协作生成创意故事',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
