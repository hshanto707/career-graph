/**
 * GapResult — reusable gap analysis result display.
 * Used by: SkillsPage, JobDetailPage, RoadmapPage.
 */
import { CheckCircle2, XCircle, BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { GapAnalysisResult } from '@/types'

interface GapResultProps {
  data: GapAnalysisResult
  showRoadmap?: boolean
}

function scoreColor(score: number): string {
  if (score >= 70) return '#16a34a'
  if (score >= 40) return '#d97706'
  return '#dc2626'
}

function scoreBg(score: number): string {
  if (score >= 70) return 'bg-green-50 border-green-100'
  if (score >= 40) return 'bg-amber-50 border-amber-100'
  return 'bg-red-50 border-red-100'
}

export function GapResult({ data, showRoadmap = false }: GapResultProps) {
  const [roadmapOpen, setRoadmapOpen] = useState(showRoadmap)
  const milestones = data.roadmap?.milestones ?? []

  return (
    <div className="space-y-4">
      {/* Readiness score ring */}
      <div className={`text-center py-5 rounded-xl border ${scoreBg(data.readiness_score)}`}>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Readiness Score</p>
        <p
          className="text-5xl font-bold"
          style={{ color: scoreColor(data.readiness_score) }}
        >
          {Math.round(data.readiness_score)}%
        </p>
        <p className="text-sm font-medium text-gray-700 mt-1">{data.target_job_title}</p>
        <p className="text-xs text-gray-400 mt-0.5">
          {data.must_matched}/{data.must_total} required skills matched
        </p>
      </div>

      {/* Matched skills */}
      {data.matched_skills.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-600 flex items-center gap-1.5 mb-2">
            <CheckCircle2 className="w-4 h-4 text-green-500" />
            You have ({data.matched_skills.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {data.matched_skills.map(s => (
              <span key={s} className="badge bg-green-100 text-green-700">{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Missing skills */}
      {data.missing_skills.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-600 flex items-center gap-1.5 mb-2">
            <XCircle className="w-4 h-4 text-red-400" />
            Skills to learn ({data.missing_skills.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {data.missing_skills.map(s => (
              <span key={s} className="badge bg-red-50 text-red-600 border border-red-100">{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* LLM explanation */}
      {data.explanation && (
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
          <p className="text-sm text-blue-700">{data.explanation}</p>
          {data.encouragement && (
            <p className="text-xs text-blue-500 mt-2 font-medium">{data.encouragement}</p>
          )}
        </div>
      )}

      {/* Learning Roadmap */}
      {(milestones.length > 0 || data.missing_skills.length === 0) && (
        <div>
          <button
            onClick={() => setRoadmapOpen(o => !o)}
            className="flex items-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-800"
          >
            <BookOpen className="w-4 h-4" />
            {roadmapOpen ? 'Hide Learning Path' : 'Show Learning Path'}
            {roadmapOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {roadmapOpen && (
            <div className="mt-3 space-y-2">
              {milestones.length === 0 ? (
                <div className="bg-green-50 rounded-lg p-4 border border-green-100 text-center">
                  <CheckCircle2 className="w-6 h-6 text-green-500 mx-auto mb-1" />
                  <p className="text-sm font-medium text-green-700">You're fully ready for this role!</p>
                </div>
              ) : (
                milestones.map(m => (
                  <div key={m.week} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-7 h-7 rounded-full bg-primary-100 text-primary-700 text-xs font-bold flex items-center justify-center flex-shrink-0">
                        {m.week}
                      </div>
                      <div className="w-0.5 bg-gray-100 flex-1 mt-1" />
                    </div>
                    <div className="pb-3 flex-1">
                      <div className="card p-3">
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Week {m.week}</p>
                        <div className="flex flex-wrap gap-1.5">
                          {m.skills.map(s => (
                            <span key={s} className="badge bg-primary-50 text-primary-700">{s}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
              {data.roadmap?.summary && (
                <p className="text-xs text-gray-500 italic px-1">{data.roadmap.summary}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
