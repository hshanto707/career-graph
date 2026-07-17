"""B5 — algorithmic agents: SkillGapAgent, RecommendationAgent,
PathFinderAgent, MarketAgent. Mirrors test-plan.md §B5 red/green tests +
edge cases exactly."""
from __future__ import annotations

from app.engine.algorithmic.market_agent import MarketAgent
from app.engine.algorithmic.path_finder_agent import PathFinderAgent
from app.engine.algorithmic.recommendation_agent import RecommendationAgent
from app.engine.algorithmic.skill_gap_agent import SkillGapAgent

# ==================================================================== #
# SkillGapAgent
# ==================================================================== #


def _skill(name, importance="must", frequency=1):
    return {"name": name, "importance": importance, "frequency": frequency}


def _student_skill(name, proficiency=5, years=1.0):
    return {"name": name, "proficiency": proficiency, "years": years}


def test_full_match_scores_100():
    """B5#1 — student has all must + nice skills -> readiness_score == 100."""
    agent = SkillGapAgent()
    required = [
        _skill("Python", "must"),
        _skill("SQL", "must"),
        _skill("Docker", "nice"),
    ]
    student = [
        _student_skill("Python", proficiency=10),
        _student_skill("SQL", proficiency=10),
        _student_skill("Docker", proficiency=10),
    ]
    result = agent.compute_gap(student, required)
    assert result.readiness_score == 100
    assert result.missing_skills == []
    assert set(result.matched_skills) == {"Python", "SQL", "Docker"}


def test_zero_match_scores_low():
    """B5#2 — student has none of the required skills -> low/zero score,
    missing_skills equals full required list."""
    agent = SkillGapAgent()
    required = [_skill("Python", "must"), _skill("SQL", "nice")]
    student = [_student_skill("Photoshop")]
    result = agent.compute_gap(student, required)
    assert result.readiness_score == 0
    missing_names = {m["name"] for m in result.missing_skills}
    assert missing_names == {"Python", "SQL"}
    assert result.matched_skills == []


def test_must_only_weighting_arithmetic_exact():
    """B5#3 — student matches all 'must' skills but none 'nice' -> score
    reflects the 0.7 weight exactly (assert arithmetic, not just direction)."""
    agent = SkillGapAgent()
    required = [
        _skill("Python", "must"),
        _skill("SQL", "must"),
        _skill("Docker", "nice"),
        _skill("Kubernetes", "nice"),
    ]
    # Zero proficiency isolates the base weighted score with no bonus noise.
    student = [
        _student_skill("Python", proficiency=0),
        _student_skill("SQL", proficiency=0),
    ]
    result = agent.compute_gap(student, required)
    # must_ratio=1.0 * 0.7 + nice_ratio=0.0 * 0.3 = 0.7 -> *100 = 70.0 base,
    # proficiency_bonus = 0 since matched skills have proficiency 0.
    assert result.readiness_score == 70.0
    assert result.must_matched == 2
    assert result.must_total == 2
    assert result.nice_matched == 0
    assert result.nice_total == 2


def test_proficiency_bonus_orders_students_strictly():
    """B5#4 — two students, identical skill sets, different proficiency ->
    higher-proficiency student scores strictly higher."""
    agent = SkillGapAgent()
    required = [_skill("Python", "must"), _skill("SQL", "must")]

    low = [_student_skill("Python", proficiency=1), _student_skill("SQL", proficiency=1)]
    high = [_student_skill("Python", proficiency=10), _student_skill("SQL", proficiency=10)]

    low_result = agent.compute_gap(low, required)
    high_result = agent.compute_gap(high, required)

    assert high_result.readiness_score > low_result.readiness_score
    # Exact arithmetic check on the bonus term.
    # base = 70.0 for both (all 2 must skills matched, 0.7 weight, no nice
    # skills in this required set at all -> nice_ratio term is 0).
    # bonus = sum((proficiency/10)*2.0 for matched) / total_required(=2)
    assert low_result.readiness_score == round(70.0 + (2 * (1 / 10 * 2.0)) / 2, 4)
    assert high_result.readiness_score == round(70.0 + (2 * (10 / 10 * 2.0)) / 2, 4)


def test_skill_gap_zero_division_safety_empty_required():
    """Edge case — a job with zero required skills must not divide by zero."""
    agent = SkillGapAgent()
    result = agent.compute_gap([_student_skill("Python")], [])
    assert result.readiness_score == 0
    assert result.missing_skills == []
    assert result.matched_skills == []


def test_skill_gap_zero_division_safety_only_must_no_nice():
    """Edge case — nice_total == 0 shouldn't raise; nice_ratio term contributes 0."""
    agent = SkillGapAgent()
    required = [_skill("Python", "must")]
    student = [_student_skill("Python", proficiency=0)]
    result = agent.compute_gap(student, required)
    assert result.readiness_score == 70.0  # 1.0 * 0.7 * 100, no nice bucket, no bonus


def test_skill_gap_student_zero_skills_well_defined():
    """Edge case — student with zero skills -> gap score is 0, not NaN."""
    agent = SkillGapAgent()
    required = [_skill("Python", "must"), _skill("SQL", "nice")]
    result = agent.compute_gap([], required)
    assert result.readiness_score == 0
    assert len(result.missing_skills) == 2


def test_skill_gap_duplicate_skill_entries_deduped():
    """Edge case — duplicate skill entries in input arrays shouldn't double-count."""
    agent = SkillGapAgent()
    required = [_skill("Python", "must"), _skill("Python", "must"), _skill("SQL", "nice")]
    student = [_student_skill("Python", proficiency=5), _student_skill("python", proficiency=8)]
    result = agent.compute_gap(student, required)
    assert result.must_total == 1  # deduped
    assert result.must_matched == 1


def test_skill_gap_defensive_default_missing_importance_treated_as_nice():
    """Defensive default documented in skill_gap_agent.py: a required skill
    missing 'importance' is treated as 'nice', never inflating 'must'."""
    agent = SkillGapAgent()
    required = [{"name": "Rust", "frequency": 1}]  # no "importance" key at all
    student = [_student_skill("Rust", proficiency=0)]
    result = agent.compute_gap(student, required)
    assert result.must_total == 0
    assert result.nice_total == 1
    assert result.nice_matched == 1


# ==================================================================== #
# RecommendationAgent
# ==================================================================== #


def _job(job_id, title, skill_names):
    return {
        "job_id": job_id,
        "title": title,
        "required_skills": [{"name": n} for n in skill_names],
    }


def test_identical_skill_sets_jaccard_exact_one():
    """B5#5 — identical skill sets -> Jaccard exact_score == 1.0."""
    agent = RecommendationAgent()
    student = [_student_skill("Python"), _student_skill("SQL")]
    jobs = [_job("j1", "Data Analyst", ["Python", "SQL"])]
    ranked = agent.rank_jobs(student, jobs)
    assert ranked[0].exact_score == 1.0
    # final_score = exact*0.8 + partial*0.2; no LEADS_TO edges -> partial=0.
    assert ranked[0].final_score == 0.8


def test_disjoint_sets_no_leads_to_path_scores_zero():
    """B5#6 — disjoint skill sets, no LEADS_TO path within depth 2 ->
    final_score == 0."""
    agent = RecommendationAgent()
    student = [_student_skill("Photoshop")]
    jobs = [_job("j1", "Backend Engineer", ["Python", "SQL"])]
    ranked = agent.rank_jobs(student, jobs, leads_to_edges=[])
    assert ranked[0].exact_score == 0.0
    assert ranked[0].partial_score == 0.0
    assert ranked[0].final_score == 0.0


def test_depth1_leads_to_partial_credit_nonzero_and_weighted():
    """B5#7 — disjoint exact match but a depth-1 LEADS_TO path exists
    (Python -> ML) -> partial_score contributes a nonzero, correctly
    weighted amount to final_score."""
    agent = RecommendationAgent()
    student = [_student_skill("Python")]
    jobs = [_job("j1", "ML Engineer", ["Machine Learning"])]
    edges = [{"from_skill": "Python", "to_skill": "Machine Learning", "difficulty_jump": 2}]
    ranked = agent.rank_jobs(student, jobs, leads_to_edges=edges)
    r = ranked[0]
    assert r.exact_score == 0.0
    # depth-1 credit = 1.0, / 1 required skill = 1.0 partial_score
    assert r.partial_score == 1.0
    assert r.final_score == round(0.0 * 0.8 + 1.0 * 0.2, 6)


def test_depth2_leads_to_partial_credit_smaller_than_depth1():
    """Depth-2 path contributes strictly less partial credit than an
    equivalent depth-1 path (asymmetric credit, documented decision)."""
    agent = RecommendationAgent()
    student = [_student_skill("Python")]
    jobs = [_job("j1", "AI Engineer", ["Deep Learning"])]
    edges = [
        {"from_skill": "Python", "to_skill": "Machine Learning", "difficulty_jump": 1},
        {"from_skill": "Machine Learning", "to_skill": "Deep Learning", "difficulty_jump": 1},
    ]
    ranked = agent.rank_jobs(student, jobs, leads_to_edges=edges)
    assert ranked[0].partial_score == 0.5  # depth-2 credit


def test_ranking_sort_order_strictly_descending():
    """B5#8 — given 3+ jobs with known expected scores, returned list is
    sorted strictly descending by final_score."""
    agent = RecommendationAgent()
    student = [_student_skill("Python"), _student_skill("SQL"), _student_skill("Docker")]
    jobs = [
        _job("low", "Low Match", ["Photoshop", "Illustrator"]),
        _job("high", "High Match", ["Python", "SQL", "Docker"]),
        _job("mid", "Mid Match", ["Python", "Photoshop"]),
    ]
    ranked = agent.rank_jobs(student, jobs)
    scores = [r.final_score for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranked[0].job_id == "high"
    assert ranked[-1].job_id == "low"


def test_recommendation_zero_jobs_and_skills_empty_result():
    """Edge case — empty database -> empty result, not an exception."""
    agent = RecommendationAgent()
    assert agent.rank_jobs([], []) == []


def test_recommendation_job_with_zero_required_skills_no_div_by_zero():
    """Edge case — a job with zero required skills; Jaccard must not
    divide by zero."""
    agent = RecommendationAgent()
    student = [_student_skill("Python")]
    jobs = [_job("j1", "Mystery Job", [])]
    ranked = agent.rank_jobs(student, jobs)
    assert ranked[0].exact_score == 0.0
    assert ranked[0].partial_score == 0.0


def test_recommendation_duplicate_skills_not_double_counted():
    """Edge case — duplicate required skill entries within one job
    shouldn't inflate scores."""
    agent = RecommendationAgent()
    student = [_student_skill("Python")]
    jobs = [_job("j1", "Dup Job", ["Python", "Python", "Python"])]
    ranked = agent.rank_jobs(student, jobs)
    assert ranked[0].exact_score == 1.0  # union/intersection both size 1 after dedup


# ==================================================================== #
# PathFinderAgent
# ==================================================================== #


def test_linear_prerequisite_chain_bfs_topsort_order():
    """B5#9 — simple linear chain A->B->C, missing C -> BFS + topological
    sort returns [A, B, C] in that order."""
    agent = PathFinderAgent()
    edges = [
        {"from_skill": "A", "to_skill": "B", "difficulty_jump": 1},
        {"from_skill": "B", "to_skill": "C", "difficulty_jump": 1},
    ]
    path = agent.find_path(["C"], leads_to_edges=edges)
    assert path.ordered_skill_names == ["A", "B", "C"]


def test_missing_skill_with_no_prerequisites_single_step_no_crash():
    """B5#10 — missing skill with no prerequisites -> path is just that
    single skill, no crash."""
    agent = PathFinderAgent()
    path = agent.find_path(["Standalone Skill"], leads_to_edges=[])
    assert path.ordered_skill_names == ["Standalone Skill"]
    assert path.milestones[0].weeks_estimate == 2  # BASE_WEEKS, no bonus


def test_leads_to_cycle_terminates_with_defined_result():
    """B5#11 — LEADS_TO graph containing a cycle -> algorithm terminates
    (no infinite loop) and produces a deterministic, defined result."""
    agent = PathFinderAgent()
    edges = [
        {"from_skill": "A", "to_skill": "B", "difficulty_jump": 1},
        {"from_skill": "B", "to_skill": "A", "difficulty_jump": 1},  # cycle
    ]
    path = agent.find_path(["B"], leads_to_edges=edges)
    # Must terminate and include both nodes in some defined order.
    assert set(path.ordered_skill_names) == {"a", "b"} or set(
        n.lower() for n in path.ordered_skill_names
    ) == {"a", "b"}
    assert len(path.ordered_skill_names) == 2
    # Deterministic: running twice yields the identical order.
    path_again = agent.find_path(["B"], leads_to_edges=edges)
    assert path_again.ordered_skill_names == path.ordered_skill_names


def test_courses_attached_per_milestone():
    """B5#12 — each milestone with a TEACHES course shows it; a skill with
    no course shows an empty/handled state, not a crash."""
    agent = PathFinderAgent()
    edges = [{"from_skill": "Python", "to_skill": "Machine Learning", "difficulty_jump": 3}]
    courses = [
        {"skill_name": "Python", "title": "Python 101", "provider": "Coursera"},
    ]
    path = agent.find_path(["Machine Learning"], leads_to_edges=edges, courses=courses)
    milestones_by_name = {m.skill_name: m for m in path.milestones}
    assert milestones_by_name["Python"].courses == [
        {"skill_name": "Python", "title": "Python 101", "provider": "Coursera"}
    ]
    assert milestones_by_name["Machine Learning"].courses == []  # no crash, empty list
    # weeks_estimate for ML reflects the incoming edge's difficulty_jump
    assert milestones_by_name["Machine Learning"].weeks_estimate == 2 + 3


def test_pathfinder_empty_graph_zero_division_safety():
    """Edge case — empty database / no missing skills -> empty path, no crash."""
    agent = PathFinderAgent()
    path = agent.find_path([], leads_to_edges=[], courses=[])
    assert path.milestones == []
    assert path.ordered_skill_names == []


def test_pathfinder_duplicate_missing_skills_deduped():
    """Edge case — duplicate skill entries in missing_skills shouldn't
    produce duplicate milestones."""
    agent = PathFinderAgent()
    path = agent.find_path(["Python", "python", "PYTHON"], leads_to_edges=[])
    assert path.ordered_skill_names == ["Python"]


# ==================================================================== #
# MarketAgent
# ==================================================================== #


def test_demand_aggregation_normalized_proportional_to_max():
    """B5#13 — a skill appearing in N postings has demand_score
    proportional to N relative to the dataset max, normalized 0-100."""
    agent = MarketAgent()
    jobs = [
        _job("j1", "Job1", ["Python", "SQL"]),
        _job("j2", "Job2", ["Python"]),
        _job("j3", "Job3", ["Python", "Docker"]),
    ]
    data = agent.aggregate_demand(jobs)
    by_name = {sd.skill_name: sd for sd in data.skill_demand}
    assert by_name["Python"].demand_count == 3
    assert by_name["Python"].demand_score == 100.0  # max in dataset
    assert by_name["SQL"].demand_count == 1
    assert by_name["SQL"].demand_score == round(1 / 3 * 100, 4)
    assert by_name["Docker"].demand_score == round(1 / 3 * 100, 4)


def test_trending_skills_matches_documented_formula():
    """B5#14 — given a previous snapshot (the agreed v1 proxy), trend
    calculation matches the documented formula exactly."""
    agent = MarketAgent()
    jobs = [
        _job("j1", "Job1", ["Python", "Rust"]),
        _job("j2", "Job2", ["Python"]),
    ]
    previous = {"python": 1, "rust": 1}
    data = agent.aggregate_demand(jobs, previous_demand_counts=previous)
    by_name = {sd.skill_name: sd for sd in data.skill_demand}
    assert by_name["Python"].trend == 2 - 1  # current 2, previous 1
    assert by_name["Rust"].trend == 1 - 1
    assert data.trending_skills == ["Python"]  # only positive trend


def test_trend_unavailable_without_previous_snapshot():
    """Documented v1 decision — without a previous snapshot, trend is
    explicitly None (unknown), not a fabricated 0."""
    agent = MarketAgent()
    jobs = [_job("j1", "Job1", ["Python"])]
    data = agent.aggregate_demand(jobs)
    assert data.skill_demand[0].trend is None
    assert data.trending_skills == []


def test_market_agent_empty_graph_zero_division_safety():
    """Edge case — zero jobs in the graph -> empty result, not an exception."""
    agent = MarketAgent()
    data = agent.aggregate_demand([])
    assert data.skill_demand == []
    assert data.trending_skills == []


def test_market_agent_duplicate_skill_within_job_not_double_counted():
    """Edge case — duplicate skill entries within a single job's required
    list shouldn't double-count that job's contribution to demand."""
    agent = MarketAgent()
    jobs = [_job("j1", "Job1", ["Python", "Python", "SQL"])]
    data = agent.aggregate_demand(jobs)
    by_name = {sd.skill_name: sd for sd in data.skill_demand}
    assert by_name["Python"].demand_count == 1
    assert by_name["SQL"].demand_count == 1


# ==================================================================== #
# Cross-cutting edge cases (all four agents)
# ==================================================================== #


def test_large_skill_sets_perf_sanity():
    """Edge case — stress case with larger skill sets, rough perf sanity
    (not full load testing): should complete quickly with correct counts."""
    gap_agent = SkillGapAgent()
    rec_agent = RecommendationAgent()
    market_agent = MarketAgent()

    n = 500
    required = [_skill(f"skill_{i}", "must" if i % 2 == 0 else "nice") for i in range(n)]
    student = [_student_skill(f"skill_{i}", proficiency=5) for i in range(0, n, 2)]

    gap_result = gap_agent.compute_gap(student, required)
    assert gap_result.must_matched == n // 2  # all evens (must) matched
    assert gap_result.nice_matched == 0

    jobs = [_job("big", "Big Job", [f"skill_{i}" for i in range(n)])]
    ranked = rec_agent.rank_jobs(student, jobs)
    assert len(ranked[0].matched_skills) == n // 2

    demand = market_agent.aggregate_demand(jobs)
    assert len(demand.skill_demand) == n
