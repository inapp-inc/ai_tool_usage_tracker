import { create } from "zustand";
import { persist } from "zustand/middleware";

interface OrgScopeState {
  /** null = all customer organizations (super admin only). */
  selectedOrganizationId: string | null;
  setSelectedOrganizationId: (id: string | null) => void;
}

export const useOrgScopeStore = create<OrgScopeState>()(
  persist(
    (set) => ({
      selectedOrganizationId: null,
      setSelectedOrganizationId: (id) => set({ selectedOrganizationId: id }),
    }),
    { name: "org-scope" },
  ),
);
