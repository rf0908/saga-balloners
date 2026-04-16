import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '佐賀バルーナーズ 試合情報',
  description: '佐賀バルーナーズの試合日程・結果・順位をチェック',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja" className="h-full">
      <body className="min-h-full bg-gray-50 antialiased">{children}</body>
    </html>
  );
}
