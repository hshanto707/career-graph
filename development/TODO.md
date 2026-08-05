# Development TODO

- playwright FE e2e feature tests (e.g. registration -> login -> profile completion -> recommendations -> job explorer)
- make sure test credentials expire and get re-created


## Skills / target roles: dropdown suggestions in profile

Status: **done** (2026-08-02). Implemented per the plan below:

- `GraphService.list_skill_names` / `list_job_titles` (`backend/app/services/graph_service.py`)
  and matching `FakeGraphService` methods (`backend/tests/fakes.py`).
- `GET /skills?search=` (`backend/app/routers/skills.py`, unauthenticated) and
  `GET /jobs/titles?search=` (`backend/app/routers/jobs.py`, unauthenticated,
  registered before `/jobs/{job_id}`).
- Tests in `backend/tests/test_routers.py` covering search filtering, empty-search
  full list, dedup/sort, and no-auth-required.
- Frontend: `frontend/src/lib/api/skills.ts` (`skillsApi.search`) and
  `frontend/src/lib/api/jobs.ts` (`jobsApi.titles`), debounced hooks in
  `frontend/src/hooks/useSuggestions.ts`, and a reusable
  `frontend/src/components/ui/combobox.tsx` (free-text still allowed) wired
  into `EditProfile.tsx`'s skill-name and target-role inputs.

## Major: dropdown suggestions

Status: **done** (2026-08-02). Static list in `frontend/src/lib/majors.ts`
(`COMMON_MAJORS`), filtered client-side and wired into the `major` field via
the same `Combobox` component (`react-hook-form` `Controller`), free-text
still allowed for anything not listed.

## Graduation year: dropdown + dynamic label

Status: **done** (2026-08-02). `graduationYear` in `EditProfile.tsx` is now a
`Select` over `MIN_GRAD_YEAR..MAX_GRAD_YEAR` (ascending), same pattern as the
experience year pickers. Label switches between "Expected Graduation Year"
(selected year >= current year) and "Graduation Year" (selected year < current
year). `frontend/src/pages/EditProfile.test.tsx` covers the label switch.
