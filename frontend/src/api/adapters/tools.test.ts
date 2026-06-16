import { describe, expect, it } from "vitest";

import {
  finalizeWriteBody,
  normalizePricing,
  pricingToApiFields,
  toToolUpdateBody,
  toToolUpdateBodyFromPartial,
  toToolWriteBody,
  type ApiToolWriteBody,
} from "./tools";

describe("tools adapter", () => {
  it("maps flat_fee pricing to package_allowance, overage_price, and plan_name", () => {
    const body = toToolWriteBody({
      name: "Enterprise OpenAI",
      provider: "openai",
      apiKey: "sk-test-key-12345678",
      description: "Flat package",
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
    });

    expect(body.pricing_model).toBe("package_with_overage");
    expect(body.package_allowance).toBe(1_000_000);
    expect(body.overage_price).toBe(0.002);
    expect(body.pricing_config).toMatchObject({
      model: "flat_fee",
      plan_name: "Team Pro",
      included_tokens: 1_000_000,
      overage_rate: 0.002,
      flat_monthly_cost: 99,
    });
  });

  it("maps hybrid pricing with package fields to top-level columns", () => {
    const fields = pricingToApiFields(
      normalizePricing({
        model: "hybrid",
        inputCostPer1K: 0.003,
        outputCostPer1K: 0.012,
        costPerSeat: null,
        seatCount: null,
        flatMonthlyCost: 49,
        planName: "Hybrid Plan",
        includedTokens: 500_000,
        overageRate: 0.0015,
      }),
      "openai",
    );

    expect(fields.pricing_model).toBe("package_with_overage");
    expect(fields.package_allowance).toBe(500_000);
    expect(fields.overage_price).toBe(0.0015);
    expect(fields.pricing_config).toMatchObject({
      model: "hybrid",
      plan_name: "Hybrid Plan",
    });
  });

  it("sends full OpenAPI-shaped payload on update", () => {
    const body = toToolUpdateBodyFromPartial({
      name: "Updated Tool",
      provider: "openai",
      description: "Updated",
      pricing: {
        model: "flat_fee",
        inputCostPer1K: null,
        outputCostPer1K: null,
        costPerSeat: null,
        seatCount: null,
        flatMonthlyCost: 120,
        planName: "Business",
        includedTokens: 2_000_000,
        overageRate: 0.003,
      },
    });

    expect(body.name).toBe("Updated Tool");
    expect(body.vendor).toBe("openai");
    expect(body.description).toBe("Updated");
    expect(body.pricing_model).toBe("package_with_overage");
    expect(body.package_allowance).toBe(2_000_000);
    expect(body.overage_price).toBe(0.003);
    expect(body.api_key).toBeUndefined();
    expect(body.pricing_config).toMatchObject({ plan_name: "Business" });
  });

  it("omits api_key on update when unchanged", () => {
    const body = toToolUpdateBody({
      name: "Tool",
      provider: "openai",
      apiKey: "",
      description: "",
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
    });

    expect(body.api_key).toBeUndefined();
  });

  it("includes api_key on update when rotated", () => {
    const body = toToolUpdateBody({
      name: "Tool",
      provider: "openai",
      apiKey: "sk-new-key-12345678",
      description: "",
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
    });

    expect(body.api_key).toBe("sk-new-key-12345678");
  });

  it("create body matches OpenAPI flat structure", () => {
    const body: ApiToolWriteBody = toToolWriteBody({
      name: "Enterprise OpenAI",
      provider: "openai",
      apiKey: "sk-test-key-12345678",
      description: "Flat package",
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
    });

    expect(body).toEqual({
      name: "Enterprise OpenAI",
      vendor: "openai",
      description: "Flat package",
      api_key: "sk-test-key-12345678",
      pricing_model: "package_with_overage",
      token_price: 0.002,
      package_allowance: 1_000_000,
      overage_price: 0.002,
      pricing_config: {
        model: "flat_fee",
        provider_slug: "openai",
        flat_monthly_cost: 99,
        plan_name: "Team Pro",
        included_tokens: 1_000_000,
        overage_rate: 0.002,
        input_cost_per_1k: null,
        output_cost_per_1k: null,
        cost_per_seat: null,
        seat_count: null,
      },
    });
  });

  it("uses package_with_overage when package fields filled on per_token model", () => {
    const fields = pricingToApiFields(
      normalizePricing({
        model: "per_token",
        inputCostPer1K: 0.005,
        outputCostPer1K: 0.015,
        costPerSeat: null,
        seatCount: null,
        flatMonthlyCost: 99,
        planName: "Team Pro",
        includedTokens: 1_000_000,
        overageRate: 0.002,
      }),
      "openai",
    );

    expect(fields.pricing_model).toBe("package_with_overage");
    expect(fields.package_allowance).toBe(1_000_000);
    expect(fields.overage_price).toBe(0.002);
    expect(fields.pricing_config.plan_name).toBe("Team Pro");
  });

  it("finalizeWriteBody always includes explicit package keys", () => {
    const body = finalizeWriteBody({
      name: "Tool",
      vendor: "openai",
      description: "",
      pricing_model: "flat_token",
      token_price: 0.005,
      package_allowance: null,
      overage_price: null,
      pricing_config: {
        model: "per_token",
        plan_name: null,
        included_tokens: null,
        overage_rate: null,
      },
    });

    expect(body).toHaveProperty("package_allowance", null);
    expect(body).toHaveProperty("overage_price", null);
    expect(body.pricing_config.plan_name).toBeNull();
  });

  it("trims plan name and preserves numeric package fields", () => {
    const normalized = normalizePricing({
      model: "flat_fee",
      inputCostPer1K: null,
      outputCostPer1K: null,
      costPerSeat: null,
      seatCount: null,
      flatMonthlyCost: null,
      planName: "  Team Pro  ",
      includedTokens: 750_000,
      overageRate: 0.0025,
    });

    expect(normalized.planName).toBe("Team Pro");
    expect(normalized.includedTokens).toBe(750_000);
    expect(normalized.overageRate).toBe(0.0025);
  });
});
