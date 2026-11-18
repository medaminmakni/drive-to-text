"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api, errorMessage } from "./api";
import type { Batch, BatchRequest } from "./types";

/**
 * Starts a batch and follows it until it is completed.
 *
 * Polling uses a chain of setTimeout, not setInterval: the next request is only
 * scheduled once the previous answer arrived, so slow answers never pile up.
 */
export function useBatch(intervalMs = 1000) {
  const [batch, setBatch] = useState<Batch | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stop = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }, []);

  const follow = useCallback(
    (id: string) => {
      function tick() {
        timer.current = setTimeout(async () => {
          try {
            const next = await api.getBatch(id);
            setBatch(next);
            if (next.status === "running") tick();
          } catch (err) {
            setError(errorMessage(err));
          }
        }, intervalMs);
      }
      tick();
    },
    [intervalMs],
  );

  const start = useCallback(
    async (request: BatchRequest) => {
      stop();
      setError(null);
      setBatch(null);
      setStarting(true);
      try {
        const created = await api.startBatch(request);
        setBatch(created);
        follow(created.batch_id);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setStarting(false);
      }
    },
    [follow, stop],
  );

  const reset = useCallback(() => {
    stop();
    setBatch(null);
    setError(null);
  }, [stop]);

  useEffect(() => stop, [stop]); // stop polling when the page is left

  const running = starting || batch?.status === "running";
  return { batch, error, running, start, reset };
}
