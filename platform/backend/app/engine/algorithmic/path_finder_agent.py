"""
PathFinderAgent — Generates an ordered learning roadmap using BFS + topological sort.

Algorithm:
1. BFS from each missing skill, following prerequisite graph backwards
2. Collect all skills that need to be learned (including transitive prereqs)
3. Topological sort to determine learning order
4. Group into weekly milestones

No LLM required. Pure Python.
"""
from collections import deque, defaultdict
from dataclasses import dataclass, field


@dataclass
class LearningPath:
    """An ordered learning roadmap."""
    milestones: list[dict]   # [{"week": 1, "skills": [...], "description": str}]
    weeks_estimate: int
    total_skills: int


SKILLS_PER_WEEK = 2  # Assume a student can learn ~2 skills per week


class PathFinderAgent:
    """
    Generates an ordered learning roadmap for a student.

    Uses BFS to discover all prerequisite skills, then topological sort
    to determine the correct learning order. This mirrors how a mentor
    would plan a study curriculum.
    """

    def build_learning_path(
        self,
        missing_skills: list[str],
        prereq_graph: dict[str, list[str]],  # {skill: [prerequisites]}
        student_skills: set[str],
    ) -> LearningPath:
        """
        Build a topologically ordered learning path.

        Args:
            missing_skills: Skills the student needs to learn.
            prereq_graph: Dict mapping skill -> list of prerequisite skills.
            student_skills: Skills the student already has (excluded from path).

        Returns:
            LearningPath with ordered milestones and time estimate.
        """
        if not missing_skills:
            return LearningPath(milestones=[], weeks_estimate=0, total_skills=0)

        student_lower = {s.lower() for s in student_skills}

        # BFS to collect all skills needed (including transitive prereqs)
        to_learn: set[str] = set()
        queue = deque(missing_skills)
        visited: set[str] = set()

        while queue:
            skill = queue.popleft()
            if skill in visited:
                continue
            visited.add(skill)
            if skill.lower() not in student_lower:
                to_learn.add(skill)
                for prereq in prereq_graph.get(skill, []):
                    if prereq not in visited:
                        queue.append(prereq)

        if not to_learn:
            return LearningPath(milestones=[], weeks_estimate=0, total_skills=0)

        # Topological sort (Kahn's algorithm)
        in_degree: dict[str, int] = defaultdict(int)
        adj: dict[str, list[str]] = defaultdict(list)  # skill -> skills that depend on it

        for skill in to_learn:
            for prereq in prereq_graph.get(skill, []):
                if prereq in to_learn:
                    in_degree[skill] += 1
                    adj[prereq].append(skill)

        ordered: list[str] = []
        zero_in_degree = deque(s for s in to_learn if in_degree[s] == 0)

        while zero_in_degree:
            skill = zero_in_degree.popleft()
            ordered.append(skill)
            for dependent in adj[skill]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    zero_in_degree.append(dependent)

        # Any remaining (cycle detection fallback — add remaining in any order)
        remaining = to_learn - set(ordered)
        ordered.extend(sorted(remaining))

        # Group into weekly milestones
        milestones = []
        for i in range(0, len(ordered), SKILLS_PER_WEEK):
            week_skills = ordered[i:i + SKILLS_PER_WEEK]
            week_num = i // SKILLS_PER_WEEK + 1
            milestones.append({
                "week": week_num,
                "skills": week_skills,
                "description": f"Week {week_num}: Learn {', '.join(week_skills)}",
            })

        weeks = len(milestones)
        return LearningPath(milestones=milestones, weeks_estimate=weeks, total_skills=len(ordered))
