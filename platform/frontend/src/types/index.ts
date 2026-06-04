// ─── Auth ────────────────────────────────────────────────────────────────────
export interface RegisterRequest {
  email: string
  name: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenData {
  access_token: string
  token_type: string
  user_id: string
  name: string
  email: string
}

// ─── Profile ─────────────────────────────────────────────────────────────────
export interface SkillEntry {
  name: string
  proficiency: number  // 0–10
  years: number
}

export interface Profile {
  user_id: string
  name: string
  email: string
  university: string | null
  graduation_year: number | null
  target_roles: string[]
  bio: string | null
  skills: SkillEntry[]
}

export interface ProfileUpdateRequest {
  name?: string
  university?: string
  graduation_year?: number
  target_roles?: string[]
  bio?: string
}

export interface AddSkillRequest {
  skill_name: string
  proficiency: number  // 0–10
  years: number
}

// ─── Jobs ─────────────────────────────────────────────────────────────────────
export interface Job {
  id: string
  title: string
  company: string
  location: string
  employment_type: string
  salary_min: number | null
  salary_max: number | null
  skills_required: string[]
  description: string
  posted_date: string
}

export interface JobSkill {
  name: string
  importance: 'must' | 'nice' | string
}

export interface JobDetail {
  id: string
  title: string
  company: string
  location: string
  employment_type: string
  salary_min: number | null
  salary_max: number | null
  skills_required: JobSkill[]
  description: string
  posted_date: string
}

export interface JobsResponse {
  jobs: Job[]
  total: number
  limit: number
  offset: number
}

export interface JobFilters {
  search?: string
  location?: string
  employment_type?: string
  skill?: string
  limit?: number
  offset?: number
}

// ─── Skills ───────────────────────────────────────────────────────────────────
export interface MarketSkill {
  name: string
  demand_count: number
  demand_score: number  // 0–100
}

export interface MarketSkillsResponse {
  top_skills: MarketSkill[]
  total_jobs: number
}

export interface SkillGapResponse {
  readiness_score: number  // 0–100
  matched_skills: string[]
  missing_skills: string[]
  must_matched: number
  must_total: number
}

// ─── Recommendations ──────────────────────────────────────────────────────────
export interface JobRecommendation {
  job_id: string
  title: string
  company: string
  location: string
  employment_type: string
  salary_min: number | null
  salary_max: number | null
  score: number  // 0–1
  matched_skills: string[]
  missing_skills: string[]
  why_recommended?: string
}

export interface RecommendedSkill {
  name: string
  demand_count: number
  demand_score: number
}

export interface Course {
  id: string
  title: string
  provider: string
  url?: string
  duration?: string
  free?: boolean
  teaches_skills: string[]
}

// ─── Gap Analysis ─────────────────────────────────────────────────────────────
export interface GapAnalysisRequest {
  target_job_id: string
  explain?: boolean
}

export interface RoadmapMilestone {
  week: number
  skills: string[]
  description: string
}

export interface Roadmap {
  milestones: RoadmapMilestone[]
  weeks_estimate: number
  total_skills: number
  summary?: string
}

export interface GapAnalysisResult {
  target_job_id: string
  target_job_title: string
  readiness_score: number  // 0–100
  matched_skills: string[]
  missing_skills: string[]
  must_matched: number
  must_total: number
  nice_matched: number
  nice_total: number
  roadmap?: Roadmap
  explanation?: string
  encouragement?: string
  weeks_to_learn?: number
}

// ─── Market ───────────────────────────────────────────────────────────────────
export interface MarketInsights {
  total_jobs: number
  top_skills: MarketSkill[]
  top_categories: { name: string; job_count: number }[]
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export interface DashboardStats {
  skills_count: number
  top_job_readiness: number  // 0–100
  total_jobs_in_market: number
  top_demanded_skill: string
}

// ─── Generic API response envelope ───────────────────────────────────────────
export interface APIResponse<T> {
  success: boolean
  data: T | null
  message: string
}
