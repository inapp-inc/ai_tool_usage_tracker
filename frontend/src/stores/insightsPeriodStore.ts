import { create } from "zustand";

import type { DateRange } from "@/types";
import { currentMonthUtcRange } from "@/utils/periods";

interface InsightsPeriodState {
  active: boolean;
  period: DateRange;
  onChange: ((period: DateRange) => void) | null;
  register: (onChange: (period: DateRange) => void) => void;
  setActive: (active: boolean) => void;
  syncPeriod: (period: DateRange) => void;
  changePeriod: (period: DateRange) => void;
}

export const useInsightsPeriodStore = create<InsightsPeriodState>((set, get) => ({
  active: false,
  period: currentMonthUtcRange(),
  onChange: null,
  register: (onChange) => set({ onChange }),
  setActive: (active) => set({ active }),
  syncPeriod: (period) => set({ period }),
  changePeriod: (period) => {
    set({ period });
    get().onChange?.(period);
  },
}));
