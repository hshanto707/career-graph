/**
 * JobsPage — Browse and search all job postings with filters.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobsApi'
import { JobCard } from '@/components/ui/JobCard'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { Search, Filter, Briefcase, ChevronLeft, ChevronRight } from 'lucide-react'
import type { JobFilters } from '@/types'

const EMPLOYMENT_TYPES = ['All', 'Full-time', 'Part-time', 'Contract', 'Internship']
const PAGE_SIZE = 12

export default function JobsPage() {
  const [filters, setFilters] = useState<JobFilters>({ limit: PAGE_SIZE, offset: 0 })
  const [searchInput, setSearchInput] = useState('')
  const [selectedType, setSelectedType] = useState('All')
  const [page, setPage] = useState(0)

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => jobsApi.getJobs(filters),
    placeholderData: prev => prev,
  })

  function applyFilters() {
    const newFilters: JobFilters = {
      limit: PAGE_SIZE,
      offset: 0,
      search: searchInput.trim() || undefined,
      employment_type: selectedType !== 'All' ? selectedType : undefined,
    }
    setFilters(newFilters)
    setPage(0)
  }

  function handlePageChange(direction: 'next' | 'prev') {
    const newPage = direction === 'next' ? page + 1 : page - 1
    const newOffset = newPage * PAGE_SIZE
    setPage(newPage)
    setFilters(f => ({ ...f, offset: newOffset }))
  }

  const total = data?.total ?? 0
  const jobs = data?.jobs ?? []
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const hasNext = page < totalPages - 1
  const hasPrev = page > 0

  return (
    <div className="max-w-5xl mx-auto">
      <PageHeader
        title="Job Explorer"
        subtitle={`${total.toLocaleString()} opportunities in the market`}
      />

      {/* Search + Filters */}
      <div className="card p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              className="input pl-10"
              placeholder="Search job titles or companies..."
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && applyFilters()}
            />
          </div>
          <button onClick={applyFilters} className="btn-primary flex items-center gap-2">
            <Filter className="w-4 h-4" /> Search
          </button>
        </div>

        {/* Employment Type filters */}
        <div className="flex gap-2 mt-3 flex-wrap">
          {EMPLOYMENT_TYPES.map(type => (
            <button
              key={type}
              onClick={() => {
                setSelectedType(type)
                const newFilters: JobFilters = {
                  limit: PAGE_SIZE, offset: 0,
                  search: searchInput.trim() || undefined,
                  employment_type: type !== 'All' ? type : undefined,
                }
                setFilters(newFilters)
                setPage(0)
              }}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedType === type
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Job List */}
      {isLoading ? (
        <LoadingSpinner text="Loading jobs..." />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="w-12 h-12" />}
          title="No jobs found"
          description="Try adjusting your search filters."
        />
      ) : (
        <>
          <div className={`grid grid-cols-1 gap-3 ${isFetching ? 'opacity-60' : ''}`}>
            {jobs.map(job => (
              <JobCard
                key={job.id}
                id={job.id}
                title={job.title}
                company={job.company}
                location={job.location}
                employment_type={job.employment_type}
                salary_min={job.salary_min}
                salary_max={job.salary_max}
                skills_required={job.skills_required}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 px-1">
              <p className="text-sm text-gray-500">
                Page {page + 1} of {totalPages} ({total.toLocaleString()} total)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange('prev')}
                  disabled={!hasPrev}
                  className="btn-secondary flex items-center gap-1 text-sm py-1.5"
                >
                  <ChevronLeft className="w-4 h-4" /> Prev
                </button>
                <button
                  onClick={() => handlePageChange('next')}
                  disabled={!hasNext}
                  className="btn-secondary flex items-center gap-1 text-sm py-1.5"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
