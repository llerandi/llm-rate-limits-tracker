export interface TierLimits {
  spend_threshold_usd: number | null;
  rpm: number | null;
  tpm: number | null;
  itpm?: number | null;
  otpm?: number | null;
  rpd: number | null;
  tpd: number | null;
  notes: string | null;
}

export interface Model {
  provider: string;
  provider_id: string;
  model_id: string;
  model_name: string;
  docs_url: string;
  notes: string | null;
  limits: Record<string, TierLimits>;
}

export interface RateLimitsData {
  last_updated: string;
  models: Model[];
}

export interface ProviderData {
  last_updated: string;
  provider: string;
  provider_id: string;
  models: Model[];
}

export declare const BASE_URL: string;

/** Fetch the full rate limits dataset (all providers and models). */
export declare function fetchRateLimits(): Promise<RateLimitsData>;

/** Fetch a single model by its identifier, or null if not found. */
export declare function getModel(modelId: string): Promise<Model | null>;

/** Fetch all models for a single provider by its lowercase hyphenated slug. */
export declare function getProvider(providerSlug: string): Promise<ProviderData>;
