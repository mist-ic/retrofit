/**
 * TypeScript mirrors of all Pydantic backend models.
 * Shape-only — no runtime validation.
 */

// ── Shared ────────────────────────────────────────────────────────────────────

export interface ColorSwatch {
  hex: string;
  h: number;
  s: number;
  l: number;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

// ── Ad Context ────────────────────────────────────────────────────────────────

export type OfferType = 'percent_discount' | 'amount_discount' | 'bogo' | 'free_shipping' | 'none';
export type AdTone = 'playful' | 'premium' | 'minimal' | 'bold' | 'informational' | 'other';
export type IntentStage = 'awareness' | 'consideration' | 'purchase';

export interface AdContext {
  headline: string;
  subheadline: string | null;
  body_text: string | null;
  primary_cta_text: string | null;
  secondary_cta_text: string | null;
  offer_type: OfferType;
  discount_percent: number | null;
  discount_amount: number | null;
  discount_code: string | null;
  urgency_phrase: string | null;
  primary_product: string | null;
  product_category: string | null;
  audience_segment: string | null;
  tone: AdTone | null;
  intent_stage: IntentStage | null;
  dominant_colors: ColorSwatch[];
  background_style: string | null;
  layout_style: string | null;
  language: string;
  detected_currencies: string[];
}

// ── Semantic Map ──────────────────────────────────────────────────────────────

export interface PageElement {
  role: string;
  selector: string;
  xpath: string | null;
  text: string | null;
  html: string | null;
  bbox: BoundingBox | null;
  is_above_the_fold: boolean | null;
  importance: number;
}

export type PageType = 'homepage' | 'collection' | 'product' | 'landing' | 'other';

export interface SemanticMap {
  url: string;
  page_title: string | null;
  hero_section: PageElement | null;
  hero_headline: PageElement | null;
  hero_subheadline: PageElement | null;
  hero_image: PageElement | null;
  primary_cta: PageElement | null;
  secondary_cta: PageElement | null;
  announcement_bar: PageElement | null;
  social_proof_blocks: PageElement[];
  trust_badges: PageElement[];
  price_block: PageElement | null;
  benefit_bullets: PageElement | null;
  is_shopify: boolean;
  shopify_theme: string | null;
  page_type: PageType | null;
}

// ── CRO Findings ──────────────────────────────────────────────────────────────

export type CriterionId =
  | 'message_match'
  | 'hero_clarity'
  | 'cta_visibility'
  | 'social_proof'
  | 'urgency_scarcity'
  | 'trust_signals'
  | 'mobile_readiness';

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface CriterionScore {
  criterion_id: CriterionId;
  label: string;
  score: number;
  weight: number;
  rationale: string;
}

export interface CROIssue {
  issue_id: string;
  severity: Severity;
  criterion_id: CriterionId;
  description: string;
  impact: string;
}

export interface ChangeCandidate {
  change_id: string;
  priority: number;
  target_selector: string;
  change_type: 'copy' | 'style' | 'structure';
  current_text: string | null;
  cro_principles: string[];
  proposed_direction: string;
  estimated_impact: 'high' | 'medium' | 'low';
}

export interface CROFindings {
  overall_score: number;
  criteria: CriterionScore[];
  top_issues: CROIssue[];
  change_candidates: ChangeCandidate[];
  summary: string;
}

// ── Patch Spec ────────────────────────────────────────────────────────────────

export type PatchOpType =
  | 'replaceText'
  | 'replaceAttribute'
  | 'addClass'
  | 'removeClass'
  | 'insertBefore'
  | 'insertAfter'
  | 'replaceStyle';

export interface ReplaceTextOp { op: 'replaceText'; selector: string; new_text: string; original_text: string | null; }
export interface ReplaceAttributeOp { op: 'replaceAttribute'; selector: string; attribute: string; new_value: string; }
export interface AddClassOp { op: 'addClass'; selector: string; class_name: string; }
export interface RemoveClassOp { op: 'removeClass'; selector: string; class_name: string; }
export interface InsertHtmlOp { op: 'insertBefore' | 'insertAfter'; selector: string; html: string; }
export interface ReplaceStyleOp { op: 'replaceStyle'; selector: string; css_text: string; }

export type PatchOperation =
  | ReplaceTextOp
  | ReplaceAttributeOp
  | AddClassOp
  | RemoveClassOp
  | InsertHtmlOp
  | ReplaceStyleOp;

export interface PatchSpec {
  variant_id: string;
  description: string;
  operations: PatchOperation[];
}

// ── QA Report ─────────────────────────────────────────────────────────────────

export interface StructuralIssue {
  severity: 'critical' | 'warning';
  code: string;
  message: string;
  selector: string | null;
}

export interface HallucinationFlag {
  code: string;
  message: string;
  offending_text: string;
}

export interface QAReport {
  variant_id: string;
  passed: boolean;
  is_valid_html: boolean;
  structural_issues: StructuralIssue[];
  key_elements_present: boolean;
  visual_diff_score: number | null;
  hallucination_flags: HallucinationFlag[];
  grounded_change_count: number;
  failure_reasons: string[];
}

// ── Pipeline ──────────────────────────────────────────────────────────────────

export interface ExplanationItem {
  change_id: string;
  element_selector: string;
  original_text: string | null;
  new_text: string | null;
  change_type: string;
  cro_principles: string[];
  rationale: string;
}

export type RunStatus = 'completed' | 'completed_with_warnings' | 'failed';

export interface RunResult {
  run_id: string;
  status: RunStatus;
  original_html_url: string;
  modified_html_url: string;
  original_screenshot_url: string;
  modified_screenshot_url: string;
  ad_context: AdContext;
  cro_findings: CROFindings;
  patch_spec: PatchSpec;
  qa_report: QAReport;
  explanations: ExplanationItem[];
  cro_score_before: number;
  cro_score_after: number;
  predicted_lift_range: string;
}

// ── SSE Events ────────────────────────────────────────────────────────────────

export type StageId =
  | 'ad_analyzer'
  | 'page_scraper'
  | 'cro_strategist'
  | 'copywriter'
  | 'code_modifier'
  | 'qa_verifier';

export type StageStatus = 'pending' | 'running' | 'complete' | 'error';

export interface StageState {
  id: StageId;
  label: string;
  icon: string;
  status: StageStatus;
  message?: string;
  startedAt?: number;
  completedAt?: number;
}

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
  timestamp: number;
}
