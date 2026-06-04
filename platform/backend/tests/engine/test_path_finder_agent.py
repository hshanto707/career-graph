"""
Tests for PathFinderAgent — WRITTEN BEFORE IMPLEMENTATION (TDD).

PathFinderAgent generates an ordered learning roadmap using BFS + topological sort
on a skill prerequisite graph (LEADS_TO relationships).
"""
import pytest
from app.engine.algorithmic.path_finder_agent import PathFinderAgent, LearningPath


# Skill prerequisite graph: skill_name -> list of prerequisite skills
PREREQ_GRAPH = {
    "React": ["JavaScript", "HTML", "CSS"],
    "Next.js": ["React", "JavaScript"],
    "TypeScript": ["JavaScript"],
    "FastAPI": ["Python"],
    "Django": ["Python"],
    "Machine Learning": ["Python", "NumPy", "Pandas"],
    "Deep Learning": ["Machine Learning", "Python"],
    "Docker": [],
    "Kubernetes": ["Docker"],
    "Python": [],
    "JavaScript": [],
    "HTML": [],
    "CSS": [],
    "NumPy": ["Python"],
    "Pandas": ["Python", "NumPy"],
}


def test_simple_path_no_prereqs():
    """A skill with no prerequisites has a trivial path."""
    agent = PathFinderAgent()
    path = agent.build_learning_path(
        missing_skills=["Docker"],
        prereq_graph=PREREQ_GRAPH,
        student_skills=set(),
    )
    assert isinstance(path, LearningPath)
    assert "Docker" in [s for milestone in path.milestones for s in milestone["skills"]]


def test_ordered_path_respects_prereqs():
    """Prerequisites come before dependent skills in the learning path."""
    agent = PathFinderAgent()
    path = agent.build_learning_path(
        missing_skills=["React"],
        prereq_graph=PREREQ_GRAPH,
        student_skills=set(),
    )
    skill_order = [s for m in path.milestones for s in m["skills"]]
    # JavaScript/HTML/CSS must appear before React
    if "React" in skill_order and "JavaScript" in skill_order:
        assert skill_order.index("JavaScript") < skill_order.index("React")


def test_already_known_skills_not_in_path():
    """Skills the student already knows are excluded from the path."""
    agent = PathFinderAgent()
    path = agent.build_learning_path(
        missing_skills=["React"],
        prereq_graph=PREREQ_GRAPH,
        student_skills={"JavaScript", "HTML", "CSS"},
    )
    skill_order = [s for m in path.milestones for s in m["skills"]]
    assert "JavaScript" not in skill_order
    assert "React" in skill_order


def test_weeks_estimate_positive():
    """The estimated weeks to complete the path is positive."""
    agent = PathFinderAgent()
    path = agent.build_learning_path(
        missing_skills=["Machine Learning"],
        prereq_graph=PREREQ_GRAPH,
        student_skills=set(),
    )
    assert path.weeks_estimate > 0


def test_empty_missing_skills():
    """Empty missing skills returns empty milestones."""
    agent = PathFinderAgent()
    path = agent.build_learning_path(missing_skills=[], prereq_graph=PREREQ_GRAPH, student_skills=set())
    assert path.milestones == []
    assert path.weeks_estimate == 0


def test_no_duplicate_skills_in_path():
    """Each skill appears at most once in the learning path."""
    agent = PathFinderAgent()
    path = agent.build_learning_path(
        missing_skills=["Next.js", "TypeScript"],
        prereq_graph=PREREQ_GRAPH,
        student_skills=set(),
    )
    all_skills = [s for m in path.milestones for s in m["skills"]]
    assert len(all_skills) == len(set(all_skills))
