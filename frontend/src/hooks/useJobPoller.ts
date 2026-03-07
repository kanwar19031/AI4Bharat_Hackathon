"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { JobStatusResponse } from "@/types";

/**
 * Polls job status every `intervalMs` until terminal state (COMPLETED / FAILED).
 */
export function useJobPoller(videoId: string | null, intervalMs = 3000) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setInterval>>(null);

  const stop = useCallback(() => {
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }, []);

  useEffect(() => {
    if (!videoId) return;

    const poll = async () => {
      try {
        const data = await api.status(videoId);
        setJob(data);
        if (data.status === "COMPLETED" || data.status === "FAILED") {
          stop();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Polling failed");
        stop();
      }
    };

    poll();
    timer.current = setInterval(poll, intervalMs);

    return stop;
  }, [videoId, intervalMs, stop]);

  return { job, error };
}
