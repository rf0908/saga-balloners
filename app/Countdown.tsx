'use client';

import { useEffect, useState } from 'react';

type Props = {
  targetDate: string; // "2026-04-01"
  targetTime: string; // "19:05"
};

function calcRemaining(targetDate: string, targetTime: string) {
  const target = new Date(`${targetDate}T${targetTime}:00+09:00`);
  const diff = target.getTime() - Date.now();
  if (diff <= 0) return null;
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);
  return { days, hours, minutes, seconds };
}

export default function Countdown({ targetDate, targetTime }: Props) {
  const [remaining, setRemaining] = useState(() =>
    calcRemaining(targetDate, targetTime)
  );

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining(calcRemaining(targetDate, targetTime));
    }, 1000);
    return () => clearInterval(id);
  }, [targetDate, targetTime]);

  if (!remaining) return null;

  return (
    <div className="mt-4 pt-4 border-t border-blue-100">
      <p className="text-xs text-blue-300 uppercase font-bold mb-2 tracking-wider text-center">
        Countdown
      </p>
      <div className="flex justify-center gap-3">
        {remaining.days > 0 && (
          <Unit value={remaining.days} label="日" />
        )}
        <Unit value={remaining.hours} label="時間" />
        <Unit value={remaining.minutes} label="分" />
        <Unit value={remaining.seconds} label="秒" />
      </div>
    </div>
  );
}

function Unit({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-2xl font-black tabular-nums leading-none text-white">
        {String(value).padStart(2, '0')}
      </span>
      <span className="text-[10px] text-blue-200 mt-0.5">{label}</span>
    </div>
  );
}
