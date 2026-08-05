import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Check, X, Plus, Trash2 } from 'lucide-react';
import { AppLayout } from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Combobox } from '@/components/ui/combobox';
import { useProfile, useUpdateProfile, useAddSkill } from '@/hooks/useProfile';
import { useSkillSuggestions, useJobTitleSuggestions } from '@/hooks/useSuggestions';
import type { ExperienceItem, SkillEntry } from '@/lib/api/profile';
import { MONTH_NAMES, EXPERIENCE_YEAR_OPTIONS } from '@/lib/experienceDates';
import { COMMON_MAJORS } from '@/lib/majors';
import { toast } from '@/hooks/use-toast';

const CURRENT_YEAR = new Date().getFullYear();
const MIN_GRAD_YEAR = CURRENT_YEAR - 10;
const MAX_GRAD_YEAR = CURRENT_YEAR + 10;
/** Ascending so the picker reads chronologically -- most students are
 * choosing a future or near-future graduation year. */
const GRADUATION_YEAR_OPTIONS = Array.from(
  { length: MAX_GRAD_YEAR + 1 - MIN_GRAD_YEAR },
  (_, i) => MIN_GRAD_YEAR + i
);

const profileFormSchema = z.object({
  major: z.string().trim().max(200, 'Major is too long').optional().or(z.literal('')),
  graduationYear: z.coerce
    .number({ invalid_type_error: 'Graduation year must be a number' })
    .int('Graduation year must be a whole number')
    .min(MIN_GRAD_YEAR, `Graduation year must be ${MIN_GRAD_YEAR} or later`)
    .max(MAX_GRAD_YEAR, `Graduation year must be ${MAX_GRAD_YEAR} or earlier`),
});

type ProfileFormValues = z.infer<typeof profileFormSchema>;

function normalizeSkillName(name: string): string {
  return name.trim().toLowerCase();
}

export default function EditProfile() {
  const navigate = useNavigate();
  const { data: profile, isLoading } = useProfile();
  const updateProfile = useUpdateProfile();
  const addSkill = useAddSkill();

  const [targetRoles, setTargetRoles] = useState<string[]>([]);
  const [newRole, setNewRole] = useState('');
  const [experience, setExperience] = useState<ExperienceItem[]>([]);

  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillProficiency, setNewSkillProficiency] = useState(5);
  const [newSkillYears, setNewSkillYears] = useState(0);
  const [skillError, setSkillError] = useState<string | null>(null);

  const { suggestions: skillSuggestions, isLoading: skillSuggestionsLoading } =
    useSkillSuggestions(newSkillName);
  const { suggestions: roleSuggestions, isLoading: roleSuggestionsLoading } =
    useJobTitleSuggestions(newRole);

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    values: profile
      ? {
          major: profile.major ?? '',
          graduationYear: profile.graduation_year ?? CURRENT_YEAR,
        }
      : undefined,
  });

  // Target roles / experience aren't validated fields, so they're kept as
  // plain component state, seeded once the profile data arrives.
  useEffect(() => {
    if (profile) {
      setTargetRoles(profile.target_roles ?? []);
      setExperience(profile.experience ?? []);
    }
  }, [profile]);

  const skills: SkillEntry[] = useMemo(() => profile?.skills ?? [], [profile]);

  const watchedGraduationYear = watch('graduationYear');
  const graduationYearLabel =
    watchedGraduationYear != null && watchedGraduationYear < CURRENT_YEAR
      ? 'Graduation Year'
      : 'Expected Graduation Year';

  const handleAddRole = () => {
    const trimmed = newRole.trim();
    if (!trimmed || targetRoles.includes(trimmed)) return;
    setTargetRoles((prev) => [...prev, trimmed]);
    setNewRole('');
  };

  const handleRemoveRole = (role: string) => {
    setTargetRoles((prev) => prev.filter((r) => r !== role));
  };

  const handleAddExperience = () => {
    const now = new Date();
    setExperience((prev) => [
      ...prev,
      {
        title: '',
        company: '',
        start_month: now.getMonth() + 1,
        start_year: now.getFullYear(),
        end_month: null,
        end_year: null,
        is_current: false,
        description: '',
      },
    ]);
  };

  const handleExperienceChange = <K extends keyof ExperienceItem>(
    index: number,
    field: K,
    value: ExperienceItem[K]
  ) => {
    setExperience((prev) =>
      prev.map((item, i) => (i === index ? { ...item, [field]: value } : item))
    );
  };

  const handleExperienceCurrentToggle = (index: number, isCurrent: boolean) => {
    setExperience((prev) =>
      prev.map((item, i) =>
        i === index
          ? {
              ...item,
              is_current: isCurrent,
              end_month: isCurrent ? null : item.end_month,
              end_year: isCurrent ? null : item.end_year,
            }
          : item
      )
    );
  };

  const handleRemoveExperience = (index: number) => {
    setExperience((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddSkill = async () => {
    const trimmed = newSkillName.trim();
    if (!trimmed) {
      setSkillError('Skill name is required');
      return;
    }
    const isDuplicate = skills.some((s) => normalizeSkillName(s.name) === normalizeSkillName(trimmed));
    if (isDuplicate) {
      setSkillError(`"${trimmed}" is already in your skill list`);
      return;
    }
    setSkillError(null);
    try {
      await addSkill.mutateAsync({
        name: trimmed,
        proficiency: newSkillProficiency,
        years: newSkillYears,
      });
      setNewSkillName('');
      setNewSkillProficiency(5);
      setNewSkillYears(0);
      toast({ title: 'Skill added', description: `${trimmed} was added to your profile.` });
    } catch {
      toast({
        title: 'Could not add skill',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleRemoveSkill = async (name: string) => {
    const remaining = skills.filter((s) => s.name !== name);
    try {
      await updateProfile.mutateAsync({ skills: remaining });
      toast({ title: 'Skill removed', description: `${name} was removed from your profile.` });
    } catch {
      toast({
        title: 'Could not remove skill',
        description: 'Please try again.',
        variant: 'destructive',
      });
    }
  };

  const onSubmit = async (values: ProfileFormValues) => {
    const incompleteIndex = experience.findIndex(
      (exp) => !exp.is_current && (exp.end_month == null || exp.end_year == null)
    );
    if (incompleteIndex !== -1) {
      toast({
        title: 'Missing end date',
        description: `Set an end date for experience #${incompleteIndex + 1}, or check "I currently work here".`,
        variant: 'destructive',
      });
      return;
    }
    try {
      await updateProfile.mutateAsync({
        major: values.major || null,
        graduation_year: values.graduationYear,
        target_roles: targetRoles,
        experience,
        skills,
      });
      toast({
        title: 'Profile Updated',
        description: 'Recommendations refreshed based on your new profile.',
      });
      navigate('/profile');
    } catch {
      toast({
        title: 'Could not save profile',
        description: 'Please check your connection and try again.',
        variant: 'destructive',
      });
    }
  };

  const handleCancel = () => {
    navigate('/profile');
  };

  if (isLoading) {
    return (
      <AppLayout>
        <div className="space-y-6 md:space-y-8 max-w-4xl" data-testid="edit-profile-loading">
          <Skeleton className="h-8 w-48" />
          <div className="stat-card space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <form className="space-y-6 md:space-y-8 max-w-4xl" onSubmit={handleSubmit(onSubmit)} noValidate>
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="page-title">Edit Profile</h1>
            <p className="page-subtitle">Update your skills and career goals</p>
          </div>
          <div className="flex gap-3">
            <Button type="button" variant="outline" onClick={handleCancel} className="gap-2 flex-1 sm:flex-none">
              <X className="h-4 w-4" />
              <span className="hidden sm:inline">Cancel</span>
            </Button>
            <Button type="submit" disabled={updateProfile.isPending} className="gap-2 flex-1 sm:flex-none">
              <Check className="h-4 w-4" />
              <span className="hidden sm:inline">{updateProfile.isPending ? 'Saving…' : 'Save Changes'}</span>
              <span className="sm:hidden">Save</span>
            </Button>
          </div>
        </div>

        {/* Basic Info */}
        <div className="stat-card space-y-4">
          <h2 className="section-title">Basic Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="major">Major</Label>
              <Controller
                control={control}
                name="major"
                render={({ field }) => (
                  <Combobox
                    id="major"
                    value={field.value ?? ''}
                    onChange={field.onChange}
                    options={COMMON_MAJORS.filter((m) =>
                      m.toLowerCase().includes((field.value ?? '').trim().toLowerCase())
                    )}
                    placeholder="e.g. Computer Science"
                  />
                )}
              />
              {errors.major && (
                <p className="text-sm text-destructive">{errors.major.message}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="graduationYear">{graduationYearLabel}</Label>
              <Controller
                control={control}
                name="graduationYear"
                render={({ field }) => (
                  <Select
                    value={field.value != null ? String(field.value) : ''}
                    onValueChange={(v) => field.onChange(Number(v))}
                  >
                    <SelectTrigger id="graduationYear" aria-label={graduationYearLabel}>
                      <SelectValue placeholder="Year" />
                    </SelectTrigger>
                    <SelectContent>
                      {GRADUATION_YEAR_OPTIONS.map((year) => (
                        <SelectItem key={year} value={String(year)}>
                          {year}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.graduationYear && (
                <p className="text-sm text-destructive">{errors.graduationYear.message}</p>
              )}
            </div>
          </div>
        </div>

        {/* Skills */}
        <div className="stat-card">
          <h2 className="section-title">Your Skills</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Add the skills you currently possess, with proficiency and years of experience.
          </p>

          {skills.length === 0 ? (
            <p className="text-sm text-muted-foreground mb-4">
              No skills added yet — it's OK to save without any for now.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2 mb-4">
              {skills.map((skill) => (
                <span
                  key={skill.name}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium bg-muted text-foreground"
                >
                  {skill.name} · P{skill.proficiency} · {skill.years}y
                  <button
                    type="button"
                    aria-label={`Remove ${skill.name}`}
                    onClick={() => handleRemoveSkill(skill.name)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
            <div className="space-y-1.5 flex-1 w-full sm:w-auto">
              <Label htmlFor="newSkillName">Skill name</Label>
              <Combobox
                id="newSkillName"
                value={newSkillName}
                onChange={(value) => {
                  setNewSkillName(value);
                  setSkillError(null);
                }}
                options={skillSuggestions}
                isLoading={skillSuggestionsLoading}
                placeholder="e.g. Python"
              />
            </div>
            <div className="space-y-1.5 w-full sm:w-32">
              <Label htmlFor="newSkillProficiency">Proficiency (0-10)</Label>
              <Input
                id="newSkillProficiency"
                type="number"
                min={0}
                max={10}
                value={newSkillProficiency}
                onChange={(e) => setNewSkillProficiency(Number(e.target.value))}
              />
            </div>
            <div className="space-y-1.5 w-full sm:w-32">
              <Label htmlFor="newSkillYears">Years</Label>
              <Input
                id="newSkillYears"
                type="number"
                min={0}
                step={0.5}
                value={newSkillYears}
                onChange={(e) => setNewSkillYears(Number(e.target.value))}
              />
            </div>
            <Button type="button" onClick={handleAddSkill} disabled={addSkill.isPending} className="gap-2 w-full sm:w-auto">
              <Plus className="h-4 w-4" />
              Add Skill
            </Button>
          </div>
          {skillError && <p className="text-sm text-destructive mt-2">{skillError}</p>}
        </div>

        {/* Target Roles */}
        <div className="stat-card">
          <h2 className="section-title">Target Job Roles</h2>
          <p className="text-sm text-muted-foreground mb-4">Add the roles you're aiming for.</p>

          {targetRoles.length === 0 ? (
            <p className="text-sm text-muted-foreground mb-4">No target roles set yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2 mb-4">
              {targetRoles.map((role) => (
                <span
                  key={role}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-muted text-sm font-medium text-foreground"
                >
                  {role}
                  <button
                    type="button"
                    aria-label={`Remove ${role}`}
                    onClick={() => handleRemoveRole(role)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </span>
              ))}
            </div>
          )}

          <div className="flex gap-3">
            <div className="flex-1">
              <Combobox
                value={newRole}
                onChange={setNewRole}
                options={roleSuggestions}
                isLoading={roleSuggestionsLoading}
                placeholder="e.g. Data Analyst"
                aria-label="New target role"
              />
            </div>
            <Button type="button" onClick={handleAddRole} variant="outline" className="gap-2">
              <Plus className="h-4 w-4" />
              Add
            </Button>
          </div>
        </div>

        {/* Experience */}
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title mb-0">Experience</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddExperience}
              aria-label="Add experience"
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              Add
            </Button>
          </div>

          {experience.length === 0 ? (
            <p className="text-sm text-muted-foreground">No experience added yet.</p>
          ) : (
            <div className="space-y-4">
              {experience.map((exp, index) => (
                <div key={index} className="border border-border rounded-lg p-4 space-y-3">
                  <div className="flex justify-end">
                    <button
                      type="button"
                      aria-label={`Remove experience ${index + 1}`}
                      onClick={() => handleRemoveExperience(index)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <Input
                      value={exp.title}
                      onChange={(e) => handleExperienceChange(index, 'title', e.target.value)}
                      placeholder="Title"
                      aria-label={`Experience ${index + 1} title`}
                    />
                    <Input
                      value={exp.company}
                      onChange={(e) => handleExperienceChange(index, 'company', e.target.value)}
                      placeholder="Company"
                      aria-label={`Experience ${index + 1} company`}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label className="text-xs text-muted-foreground">Start Date</Label>
                    <div className="grid grid-cols-2 gap-3">
                      <Select
                        value={String(exp.start_month)}
                        onValueChange={(v) => handleExperienceChange(index, 'start_month', Number(v))}
                      >
                        <SelectTrigger aria-label={`Experience ${index + 1} start month`}>
                          <SelectValue placeholder="Month" />
                        </SelectTrigger>
                        <SelectContent>
                          {MONTH_NAMES.map((month, i) => (
                            <SelectItem key={month} value={String(i + 1)}>
                              {month}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <Select
                        value={String(exp.start_year)}
                        onValueChange={(v) => handleExperienceChange(index, 'start_year', Number(v))}
                      >
                        <SelectTrigger aria-label={`Experience ${index + 1} start year`}>
                          <SelectValue placeholder="Year" />
                        </SelectTrigger>
                        <SelectContent>
                          {EXPERIENCE_YEAR_OPTIONS.map((year) => (
                            <SelectItem key={year} value={String(year)}>
                              {year}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Checkbox
                      id={`experience-${index}-current`}
                      checked={exp.is_current}
                      onCheckedChange={(checked) => handleExperienceCurrentToggle(index, checked === true)}
                    />
                    <Label htmlFor={`experience-${index}-current`} className="text-sm font-normal cursor-pointer">
                      I currently work here
                    </Label>
                  </div>

                  {!exp.is_current && (
                    <div className="space-y-1.5">
                      <Label className="text-xs text-muted-foreground">End Date</Label>
                      <div className="grid grid-cols-2 gap-3">
                        <Select
                          value={exp.end_month != null ? String(exp.end_month) : ''}
                          onValueChange={(v) => handleExperienceChange(index, 'end_month', Number(v))}
                        >
                          <SelectTrigger aria-label={`Experience ${index + 1} end month`}>
                            <SelectValue placeholder="Month" />
                          </SelectTrigger>
                          <SelectContent>
                            {MONTH_NAMES.map((month, i) => (
                              <SelectItem key={month} value={String(i + 1)}>
                                {month}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Select
                          value={exp.end_year != null ? String(exp.end_year) : ''}
                          onValueChange={(v) => handleExperienceChange(index, 'end_year', Number(v))}
                        >
                          <SelectTrigger aria-label={`Experience ${index + 1} end year`}>
                            <SelectValue placeholder="Year" />
                          </SelectTrigger>
                          <SelectContent>
                            {EXPERIENCE_YEAR_OPTIONS.map((year) => (
                              <SelectItem key={year} value={String(year)}>
                                {year}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}

                  <Input
                    value={exp.description ?? ''}
                    onChange={(e) => handleExperienceChange(index, 'description', e.target.value)}
                    placeholder="Description"
                    aria-label={`Experience ${index + 1} description`}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="bg-accent/50 border border-accent rounded-lg p-4">
          <p className="text-sm text-accent-foreground">
            <strong>Note:</strong> When you save changes, the system will automatically refresh
            your job recommendations, skill gap analysis, and course suggestions based on your
            updated profile.
          </p>
        </div>
      </form>
    </AppLayout>
  );
}
