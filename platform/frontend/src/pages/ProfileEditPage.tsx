/**
 * ProfileEditPage — Edit profile fields (name, university, graduation year, target roles, bio).
 */
import { useState, useEffect, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { profileApi } from '@/api/profileApi'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { PageHeader } from '@/components/ui/PageHeader'
import { Loader2, X, Plus } from 'lucide-react'

export default function ProfileEditPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.getProfile,
  })

  const [name, setName] = useState('')
  const [university, setUniversity] = useState('')
  const [graduationYear, setGraduationYear] = useState<number | ''>('')
  const [targetRoles, setTargetRoles] = useState<string[]>([])
  const [roleInput, setRoleInput] = useState('')
  const [bio, setBio] = useState('')
  const [error, setError] = useState('')

  // Pre-fill form when profile loads
  useEffect(() => {
    if (profile) {
      setName(profile.name ?? '')
      setUniversity(profile.university ?? '')
      setGraduationYear(profile.graduation_year ?? '')
      setTargetRoles(profile.target_roles ?? [])
      setBio(profile.bio ?? '')
    }
  }, [profile])

  const mutation = useMutation({
    mutationFn: profileApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      navigate('/profile')
    },
    onError: (err: Error) => setError(err.message),
  })

  function addRole() {
    const trimmed = roleInput.trim()
    if (trimmed && !targetRoles.includes(trimmed)) {
      setTargetRoles(r => [...r, trimmed])
      setRoleInput('')
    }
  }

  function removeRole(role: string) {
    setTargetRoles(r => r.filter(x => x !== role))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    mutation.mutate({
      name: name.trim() || undefined,
      university: university.trim() || undefined,
      graduation_year: graduationYear !== '' ? Number(graduationYear) : undefined,
      target_roles: targetRoles,
      bio: bio.trim() || undefined,
    })
  }

  if (isLoading) return <LoadingSpinner text="Loading profile..." />

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader title="Edit Profile" subtitle="Update your personal and academic information" />

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="card p-6 space-y-5">
        {/* Name */}
        <div>
          <label className="label">Full Name</label>
          <input className="input" value={name} onChange={e => setName(e.target.value)} placeholder="Your full name" />
        </div>

        {/* University */}
        <div>
          <label className="label">University / Institution</label>
          <input className="input" value={university} onChange={e => setUniversity(e.target.value)} placeholder="e.g. BRAC University" />
        </div>

        {/* Graduation Year */}
        <div>
          <label className="label">Expected Graduation Year</label>
          <input
            className="input" type="number"
            value={graduationYear} min={2020} max={2035}
            onChange={e => setGraduationYear(e.target.value ? Number(e.target.value) : '')}
            placeholder="e.g. 2026"
          />
        </div>

        {/* Target Roles */}
        <div>
          <label className="label">Target Roles</label>
          <div className="flex gap-2 mb-2">
            <input
              className="input flex-1"
              value={roleInput}
              onChange={e => setRoleInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addRole())}
              placeholder="e.g. Backend Engineer"
            />
            <button type="button" onClick={addRole} className="btn-secondary flex items-center gap-1">
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
          {targetRoles.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {targetRoles.map(role => (
                <span key={role} className="badge bg-primary-100 text-primary-700 flex items-center gap-1 pr-1">
                  {role}
                  <button type="button" onClick={() => removeRole(role)} className="hover:text-primary-900">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Bio */}
        <div>
          <label className="label">Bio</label>
          <textarea
            className="input resize-none h-24"
            value={bio}
            onChange={e => setBio(e.target.value)}
            placeholder="A short description about yourself and your career goals..."
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving...</>
            ) : 'Save Changes'}
          </button>
          <button type="button" className="btn-secondary" onClick={() => navigate('/profile')}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
