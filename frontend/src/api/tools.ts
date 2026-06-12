const MOCK_LATENCY_MS = 400;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(value), MOCK_LATENCY_MS);
  });
}

export type ToolProvider =
  | "openai"
  | "anthropic"
  | "google"
  | "azure_openai"
  | "cohere"
  | "mistral"
  | "custom";

export type PricingModel = "per_token" | "per_seat" | "flat_fee" | "hybrid";

export interface ToolPricing {
  model: PricingModel;
  inputCostPer1K: number | null;
  outputCostPer1K: number | null;
  costPerSeat: number | null;
  seatCount: number | null;
  flatMonthlyCost: number | null;
  planName: string | null;
  includedTokens: number | null;
  overageRate: number | null;
}

export interface AiTool {
  id: string;
  name: string;
  provider: ToolProvider;
  description: string;
  pricing: ToolPricing;
  status: "active" | "inactive" | "error";
  apiKeyMasked: string;
  lastSyncAt: string | null;
  tokenCount: number;
  costTotal: number;
  createdAt: string;
}

export interface CreateToolRequest {
  name: string;
  provider: ToolProvider;
  apiKey: string;
  description: string;
  pricing: ToolPricing;
}

export type UpdateToolRequest = Partial<CreateToolRequest>;

function maskApiKey(apiKey: string): string {
  const lastFour = apiKey.slice(-4);
  return `sk-...${lastFour}`;
}

let mockTools: AiTool[] = [
  {
    id: "tool_1",
    name: "Production OpenAI",
    provider: "openai",
    description: "Primary GPT-4o production endpoint for engineering workloads.",
    pricing: {
      model: "per_token",
      inputCostPer1K: 0.005,
      outputCostPer1K: 0.015,
      costPerSeat: null,
      seatCount: null,
      flatMonthlyCost: null,
      planName: null,
      includedTokens: null,
      overageRate: null,
    },
    status: "active",
    apiKeyMasked: "sk-...a3Fb",
    lastSyncAt: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    tokenCount: 2_840_000,
    costTotal: 184.6,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 90).toISOString(),
  },
  {
    id: "tool_2",
    name: "Claude Enterprise",
    provider: "anthropic",
    description: "Anthropic Claude API for research and long-context tasks.",
    pricing: {
      model: "per_token",
      inputCostPer1K: 0.003,
      outputCostPer1K: 0.015,
      costPerSeat: null,
      seatCount: null,
      flatMonthlyCost: null,
      planName: null,
      includedTokens: null,
      overageRate: null,
    },
    status: "active",
    apiKeyMasked: "sk-...9kL2",
    lastSyncAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    tokenCount: 1_520_400,
    costTotal: 98.75,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 60).toISOString(),
  },
  {
    id: "tool_3",
    name: "Gemini Workspace",
    provider: "google",
    description: "Google Gemini models for design and content generation.",
    pricing: {
      model: "per_token",
      inputCostPer1K: 0.00125,
      outputCostPer1K: 0.005,
      costPerSeat: null,
      seatCount: null,
      flatMonthlyCost: null,
      planName: null,
      includedTokens: null,
      overageRate: null,
    },
    status: "inactive",
    apiKeyMasked: "sk-...pQ7x",
    lastSyncAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 14).toISOString(),
    tokenCount: 412_800,
    costTotal: 22.4,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 120).toISOString(),
  },
  {
    id: "tool_4",
    name: "Azure OpenAI EU",
    provider: "azure_openai",
    description: "EU-region Azure OpenAI deployment under enterprise agreement.",
    pricing: {
      model: "hybrid",
      inputCostPer1K: 0.003,
      outputCostPer1K: 0.012,
      costPerSeat: null,
      seatCount: null,
      flatMonthlyCost: 0,
      planName: "Enterprise",
      includedTokens: null,
      overageRate: null,
    },
    status: "error",
    apiKeyMasked: "sk-...mN4z",
    lastSyncAt: null,
    tokenCount: 89_200,
    costTotal: 5.12,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
  },
  {
    id: "tool_5",
    name: "Internal LLM Gateway",
    provider: "custom",
    description: "Self-hosted gateway routing to internal fine-tuned models.",
    pricing: {
      model: "flat_fee",
      inputCostPer1K: null,
      outputCostPer1K: null,
      costPerSeat: null,
      seatCount: null,
      flatMonthlyCost: 99,
      planName: "Team Pro",
      includedTokens: 1_000_000,
      overageRate: 0.002,
    },
    status: "active",
    apiKeyMasked: "sk-...rT8w",
    lastSyncAt: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    tokenCount: 678_500,
    costTotal: 41.9,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 45).toISOString(),
  },
];

export async function fetchTools(): Promise<AiTool[]> {
  return delay([...mockTools]);
}

export async function createTool(body: CreateToolRequest): Promise<AiTool> {
  const tool: AiTool = {
    id: `tool_${Date.now()}`,
    name: body.name,
    provider: body.provider,
    description: body.description,
    pricing: body.pricing,
    status: "active",
    apiKeyMasked: maskApiKey(body.apiKey),
    lastSyncAt: null,
    tokenCount: 0,
    costTotal: 0,
    createdAt: new Date().toISOString(),
  };
  mockTools = [...mockTools, tool];
  return delay(tool);
}

export async function updateTool(
  id: string,
  body: UpdateToolRequest,
): Promise<AiTool> {
  const index = mockTools.findIndex((tool) => tool.id === id);
  if (index === -1) {
    throw new Error("Tool not found");
  }

  const existing = mockTools[index];
  const updated: AiTool = {
    ...existing,
    ...(body.name !== undefined ? { name: body.name } : {}),
    ...(body.provider !== undefined ? { provider: body.provider } : {}),
    ...(body.description !== undefined ? { description: body.description } : {}),
    ...(body.pricing !== undefined ? { pricing: body.pricing } : {}),
    ...(body.apiKey ? { apiKeyMasked: maskApiKey(body.apiKey) } : {}),
  };

  mockTools = mockTools.map((tool) => (tool.id === id ? updated : tool));
  return delay(updated);
}

export async function deleteTool(id: string): Promise<void> {
  mockTools = mockTools.filter((tool) => tool.id !== id);
  await delay(undefined);
}

export async function syncTool(id: string): Promise<AiTool> {
  const index = mockTools.findIndex((tool) => tool.id === id);
  if (index === -1) {
    throw new Error("Tool not found");
  }

  const updated: AiTool = {
    ...mockTools[index],
    lastSyncAt: new Date().toISOString(),
  };

  mockTools = mockTools.map((tool) => (tool.id === id ? updated : tool));
  return delay(updated);
}

export const toolsApi = {
  fetchTools,
  createTool,
  updateTool,
  deleteTool,
  syncTool,
};
