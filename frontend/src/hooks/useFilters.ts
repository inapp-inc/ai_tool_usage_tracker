import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import type { Period } from "@/types";

const PERIOD_KEY = "period";

export function useFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const period = (searchParams.get(PERIOD_KEY) as Period | null) ?? "30d";

  const setPeriod = useCallback(
    (next: Period) => {
      const params = new URLSearchParams(searchParams);
      params.set(PERIOD_KEY, next);
      setSearchParams(params, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  return useMemo(
    () => ({
      period,
      setPeriod,
      searchParams,
      setSearchParams,
    }),
    [period, searchParams, setPeriod, setSearchParams],
  );
}
