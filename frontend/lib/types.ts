export type DashboardSummary = {
  total_jobs: number;
  analyzed_jobs: number;
  matched_jobs: number;
  jobs_needing_review: number;
  profile_completeness: number;
  portfolio_count: number;
};

export type Job = {
  id: string;
  title: string;
  description: string;
  budget_type: string | null;
  budget_min: string | null;
  budget_max: string | null;
  currency: string | null;
  required_skills: string[];
  source: string;
  status: string;
  analysis_state: string;
  compatibility_status: string;
};

export type Match = {
  compatibility_score: string;
  exact_matches: string[];
  related_matches: {required_skill: string; evidence: string}[];
  missing_skills: string[];
  portfolio_project_ids: string[];
  concerns: string[];
  explanation: string;
  model_used: string | null;
};

export type JobDetail = Job & {
  analysis: null | {
    required_skills: string[];
    preferred_skills: string[];
    responsibilities: string[];
    deliverables: string[];
    unclear_requirements: string[];
    questions: string[];
  };
  match: Match | null;
};

export type JobPage = {
  items: Job[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type Profile = {
  title: string | null;
  overview: string | null;
  location: string | null;
  years_experience: string | null;
  primary_skills: string[];
  secondary_skills: string[];
  programming_languages: string[];
  frameworks: string[];
  tools: string[];
  domains: string[];
  work_experience: {role: string; organization: string | null; description: string | null}[];
  internships: {role: string; organization: string | null; description: string | null}[];
  completeness: number;
  verification_status: string;
};

export type Claim = {
  id: string;
  claim: string;
  category: string;
  source: string;
  verification_status: string;
};

export type PortfolioProject = {
  id: string;
  title: string;
  description: string;
  problem: string | null;
  solution: string | null;
  result: string | null;
  technologies: string[];
  skills: string[];
  tags: string[];
  verification_status: string;
  verified_claim_ids: string[];
};
