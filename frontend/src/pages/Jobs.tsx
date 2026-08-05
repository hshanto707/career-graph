// Job Explorer -- a pure catalog browse of GET /jobs (F5, docs/features-todo.md).
//
// Decision (Open decision #3, documented in
// docs/algorithmic-agents-decisions.md): this page never shows a
// personalized match score or "why recommended" text. GET /jobs returns
// JobOut (id/title/company/location/type/source/salary range only -- see
// backend/app/schemas/job.py) with no per-student skill overlap data at
// all, and folding personalized scoring in here would require also calling
// the recommendations endpoint on every catalog row, which defeats the
// purpose of a plain browse/filter page. Personalized scores + narratives
// are exclusive to the Recommendations page (GET /recommendations/jobs).
//
// For the same reason this page does not reuse `components/ui/job-card.tsx`
// as-is: that component's props are the mock `Job` shape, which bakes in
// `matchPercentage`/`requiredSkills`/`whyRecommended` as required fields.
// Fabricating those from a catalog-only response would either lie (a fake
// score) or silently render broken/empty tags -- neither is acceptable.
// JobCard is left untouched here so it stays available, unmodified, for the
// Recommendations page's genuinely personalized cards.

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Building2, MapPin, DollarSign, Loader2, AlertCircle } from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { useJobs } from '@/hooks/useJobs';
import { jobsApi, type JobOut } from '@/lib/api/jobs';
import { ApiError, NetworkError } from '@/lib/apiClient';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';

const jobTypes = ['All', 'Full-time', 'Part-time', 'Internship', 'Contract'];
const locations = ['All', 'San Francisco, CA', 'Austin, TX', 'New York, NY', 'Remote'];

function describeError(error: unknown): string {
  if (error instanceof NetworkError) return error.message;
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return 'Something went wrong while loading jobs.';
}

function formatSalary(job: JobOut): string | null {
  if (job.salary_min == null && job.salary_max == null) return null;
  if (job.salary_min != null && job.salary_max != null) {
    return `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`;
  }
  const value = job.salary_min ?? job.salary_max;
  return value != null ? `$${value.toLocaleString()}` : null;
}

export default function Jobs() {
  // The catalog row (title/company/location/type/salary) renders instantly
  // on click; required_skills only exists on the GET /jobs/{id} detail
  // response (see backend/app/schemas/job.py's JobDetailOut), so it's
  // fetched separately and rendered once it resolves.
  const [selectedJob, setSelectedJob] = useState<JobOut | null>(null);
  const [typeFilter, setTypeFilter] = useState('All');
  const [locationFilter, setLocationFilter] = useState('All');
  const [searchInput, setSearchInput] = useState('');

  const {
    data: selectedJobDetail,
    isLoading: isDetailLoading,
    isError: isDetailError,
  } = useQuery({
    queryKey: ['job', selectedJob?.id],
    queryFn: () => jobsApi.get(selectedJob!.id),
    enabled: !!selectedJob,
  });

  const {
    jobs,
    isLoading,
    isError,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useJobs({ type: typeFilter, location: locationFilter, search: searchInput });

  return (
    <AppLayout>
      <div className="space-y-4 md:space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="page-title">Job Explorer</h1>
          <p className="page-subtitle">
            Browse open roles from the current job catalog
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 md:gap-4">
          {/* Search */}
          <div className="relative w-full md:max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search jobs or companies..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              aria-label="Search jobs or companies"
              className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
            />
          </div>

          {/* Filter Row */}
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Type Filter */}
            <div className="flex items-center gap-2 flex-1 sm:flex-none">
              <Filter className="h-4 w-4 text-muted-foreground shrink-0" />
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                aria-label="Filter by job type"
                className="flex-1 sm:flex-none px-3 py-2.5 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {jobTypes.map((type) => (
                  <option key={type} value={type}>
                    {type === 'All' ? 'All Types' : type}
                  </option>
                ))}
              </select>
            </div>

            {/* Location Filter */}
            <select
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              aria-label="Filter by location"
              className="flex-1 sm:flex-none px-3 py-2.5 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {locations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc === 'All' ? 'All Locations' : loc}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Loading state (initial load only -- pagination has its own indicator below) */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin" />
            <p className="text-sm">Loading jobs...</p>
          </div>
        )}

        {/* Error state */}
        {!isLoading && isError && (
          <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
            <AlertCircle className="h-6 w-6 text-destructive" />
            <p className="text-sm font-medium text-foreground">Couldn't load jobs</p>
            <p className="text-sm text-muted-foreground" role="alert">
              {describeError(error)}
            </p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && jobs.length === 0 && (
          <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
            <Search className="h-6 w-6 text-muted-foreground" />
            <p className="text-sm font-medium text-foreground">No jobs match your filters</p>
            <p className="text-sm text-muted-foreground">
              Try a different search term, type, or location.
            </p>
          </div>
        )}

        {/* Results */}
        {!isLoading && !isError && jobs.length > 0 && (
          <>
            <p className="text-sm text-muted-foreground">
              Showing {jobs.length} job{jobs.length === 1 ? '' : 's'}
            </p>

            <div className="grid gap-4">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  onClick={() => setSelectedJob(job)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') setSelectedJob(job);
                  }}
                  className="stat-card cursor-pointer hover:border-primary/50 transition-colors"
                >
                  <h3 className="font-semibold text-foreground text-sm md:text-base truncate">
                    {job.title ?? 'Untitled role'}
                  </h3>
                  <div className="flex flex-wrap items-center gap-2 md:gap-3 mt-1.5 md:mt-2 text-xs md:text-sm text-muted-foreground">
                    {job.company && (
                      <span className="flex items-center gap-1">
                        <Building2 className="h-3.5 w-3.5 md:h-4 md:w-4 shrink-0" />
                        <span className="truncate">{job.company}</span>
                      </span>
                    )}
                    {job.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 md:h-4 md:w-4 shrink-0" />
                        <span className="truncate">{job.location}</span>
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-2 mt-2 md:mt-3">
                    {job.type && <span className="skill-tag text-xs">{job.type}</span>}
                    {formatSalary(job) && (
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <DollarSign className="h-3 w-3" />
                        {formatSalary(job)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {hasNextPage && (
              <div className="flex justify-center pt-2">
                <Button
                  variant="outline"
                  onClick={() => fetchNextPage()}
                  disabled={isFetchingNextPage}
                >
                  {isFetchingNextPage ? (
                    <span className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" /> Loading more...
                    </span>
                  ) : (
                    'Load more'
                  )}
                </Button>
              </div>
            )}
          </>
        )}

        {/* Job Detail Sheet -- catalog fields only, no personalized data */}
        <Sheet open={!!selectedJob} onOpenChange={() => setSelectedJob(null)}>
          <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
            {selectedJob && (
              <>
                <SheetHeader>
                  <SheetTitle className="text-left">
                    {selectedJob.title ?? 'Untitled role'}
                  </SheetTitle>
                </SheetHeader>

                <div className="mt-6 space-y-6">
                  <div>
                    <p className="text-muted-foreground">
                      {[selectedJob.company, selectedJob.location].filter(Boolean).join(' · ')}
                    </p>
                    {selectedJob.type && (
                      <p className="text-sm text-muted-foreground mt-1">{selectedJob.type}</p>
                    )}
                  </div>

                  {formatSalary(selectedJob) && (
                    <div className="bg-accent/50 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">Salary Range</span>
                        <span className="text-lg font-bold text-primary">
                          {formatSalary(selectedJob)}
                        </span>
                      </div>
                    </div>
                  )}

                  <div>
                    <h3 className="text-sm font-medium text-foreground mb-2">Required Skills</h3>
                    {isDetailLoading ? (
                      <p className="text-sm text-muted-foreground flex items-center gap-2">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading skills...
                      </p>
                    ) : isDetailError ? (
                      <p className="text-sm text-muted-foreground">Couldn't load required skills.</p>
                    ) : selectedJobDetail && selectedJobDetail.required_skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {selectedJobDetail.required_skills.map((skill) => (
                          <span key={skill} className="skill-tag text-xs">
                            {skill}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No skills listed for this role.</p>
                    )}
                  </div>

                  {selectedJob.source && (
                    <p className="text-xs text-muted-foreground">Source: {selectedJob.source}</p>
                  )}
                </div>
              </>
            )}
          </SheetContent>
        </Sheet>
      </div>
    </AppLayout>
  );
}
