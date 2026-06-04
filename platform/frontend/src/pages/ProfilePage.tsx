/**
 * ProfilePage — Read-only view of the student profile with skills.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { profileApi } from '@/api/profileApi'
import { SkillBar } from '@/components/ui/SkillBar'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { PageHeader } from '@/components/ui/PageHeader'
import { EmptyState } from '@/components/ui/EmptyState'
import { GraduationCap, Target, Edit3, Plus, Trash2, BookOpen } from 'lucide-react'
import { useState } from 'react'
import type { AddSkillRequest } from '@/types'

export default function ProfilePage() {
  const queryClient = useQueryClient()
  const [addingSkill, setAddingSkill] = useState(false)
  const [newSkill, setNewSkill] = useState<AddSkillRequest>({ skill_name: '', proficiency: 5, years: 1 })
  const [addError, setAddError] = useState('')

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.getProfile,
  })

  const addMutation = useMutation({
    mutationFn: profileApi.addSkill,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      setAddingSkill(false)
      setNewSkill({ skill_name: '', proficiency: 5, years: 1 })
      setAddError('')
    },
    onError: (err: Error) => setAddError(err.message),
  })

  const removeMutation = useMutation({
    mutationFn: profileApi.removeSkill,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
  })

  if (isLoading) return <LoadingSpinner text="Loading profile..." />
  if (!profile) return <div className="text-red-500">Failed to load profile</div>

  return (
    <div className="max-w-3xl mx-auto">
      <PageHeader
        title="My Profile"
        action={
          <Link to="/profile/edit" className="btn-primary flex items-center gap-2">
            <Edit3 className="w-4 h-4" /> Edit Profile
          </Link>
        }
      />

      {/* Info card */}
      <div className="card p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
            <span className="text-primary-700 text-2xl font-bold">
              {profile.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-bold text-gray-900">{profile.name}</h2>
            <p className="text-gray-500 text-sm">{profile.email}</p>
            {profile.bio && <p className="text-gray-600 mt-2 text-sm">{profile.bio}</p>}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5 pt-5 border-t border-gray-100">
          {profile.university && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <GraduationCap className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span>{profile.university}{profile.graduation_year ? `, Class of ${profile.graduation_year}` : ''}</span>
            </div>
          )}
          {profile.target_roles.length > 0 && (
            <div className="flex items-start gap-2 text-sm text-gray-600">
              <Target className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
              <span>{profile.target_roles.join(' · ')}</span>
            </div>
          )}
        </div>
      </div>

      {/* Skills */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary-500" />
            Skills ({profile.skills.length})
          </h3>
          <button
            onClick={() => setAddingSkill(!addingSkill)}
            className="btn-secondary flex items-center gap-1.5 text-sm"
          >
            <Plus className="w-4 h-4" /> Add Skill
          </button>
        </div>

        {/* Add skill form */}
        {addingSkill && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Add a new skill</h4>
            {addError && <p className="text-red-500 text-xs mb-2">{addError}</p>}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-1">
                <label className="label text-xs">Skill name</label>
                <input
                  className="input text-sm"
                  placeholder="e.g. Python"
                  value={newSkill.skill_name}
                  onChange={e => setNewSkill(s => ({ ...s, skill_name: e.target.value }))}
                />
              </div>
              <div>
                <label className="label text-xs">Proficiency (0–10): {newSkill.proficiency}</label>
                <input
                  type="range" min={0} max={10} step={0.5}
                  value={newSkill.proficiency}
                  onChange={e => setNewSkill(s => ({ ...s, proficiency: parseFloat(e.target.value) }))}
                  className="w-full mt-2"
                />
              </div>
              <div>
                <label className="label text-xs">Years of experience: {newSkill.years}</label>
                <input
                  type="range" min={0} max={20} step={0.5}
                  value={newSkill.years}
                  onChange={e => setNewSkill(s => ({ ...s, years: parseFloat(e.target.value) }))}
                  className="w-full mt-2"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => addMutation.mutate(newSkill)}
                disabled={!newSkill.skill_name.trim() || addMutation.isPending}
                className="btn-primary text-sm py-1.5 px-4"
              >
                {addMutation.isPending ? 'Adding...' : 'Add'}
              </button>
              <button onClick={() => setAddingSkill(false)} className="btn-secondary text-sm py-1.5 px-4">
                Cancel
              </button>
            </div>
          </div>
        )}

        {profile.skills.length > 0 ? (
          <div className="divide-y divide-gray-50">
            {profile.skills.map(skill => (
              <div key={skill.name} className="flex items-center gap-2">
                <div className="flex-1 min-w-0">
                  <SkillBar name={skill.name} proficiency={skill.proficiency} years={skill.years} />
                </div>
                <button
                  onClick={() => removeMutation.mutate(skill.name)}
                  className="p-1.5 text-gray-300 hover:text-red-400 transition-colors flex-shrink-0 rounded"
                  title={`Remove ${skill.name}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<BookOpen className="w-12 h-12" />}
            title="No skills added yet"
            description="Add your technical skills to get personalized job recommendations and gap analysis."
            action={
              <button onClick={() => setAddingSkill(true)} className="btn-primary">
                <Plus className="w-4 h-4 mr-1.5" /> Add Your First Skill
              </button>
            }
          />
        )}
      </div>
    </div>
  )
}
