// Mock data for the Labor Market Intelligence Platform

export interface Student {
  id: string;
  name: string;
  email: string;
  major: string;
  graduationYear: number;
  skills: string[];
  targetRoles: string[];
  experience: ExperienceItem[];
}

export interface ExperienceItem {
  title: string;
  company: string;
  duration: string;
  description: string;
}

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  type: 'Full-time' | 'Part-time' | 'Internship' | 'Contract';
  requiredSkills: string[];
  matchPercentage: number;
  description: string;
  whyRecommended: string;
}

export interface Skill {
  name: string;
  category: string;
  demandScore: number;
  owned: boolean;
  importance: 'Critical' | 'High' | 'Medium' | 'Low';
}

export interface Course {
  id: string;
  title: string;
  provider: string;
  duration: string;
  skill: string;
  matchScore: number;
  explanation: string;
}

export const mockStudent: Student = {
  id: '1',
  name: 'Alex Chen',
  email: 'alex.chen@university.edu',
  major: 'Computer Science',
  graduationYear: 2025,
  skills: ['Python', 'JavaScript', 'SQL', 'Data Analysis', 'Git'],
  targetRoles: ['Data Analyst', 'Software Engineer', 'ML Engineer'],
  experience: [
    {
      title: 'Software Engineering Intern',
      company: 'Tech Startup Inc.',
      duration: 'Jun 2024 - Aug 2024',
      description: 'Developed RESTful APIs and data pipelines for analytics dashboard.'
    },
    {
      title: 'Research Assistant',
      company: 'University AI Lab',
      duration: 'Jan 2024 - Present',
      description: 'Assisting with machine learning research and data preprocessing.'
    }
  ]
};

export const mockJobs: Job[] = [
  {
    id: '1',
    title: 'Junior Data Analyst',
    company: 'DataCorp Solutions',
    location: 'San Francisco, CA',
    type: 'Full-time',
    requiredSkills: ['Python', 'SQL', 'Tableau', 'Data Analysis', 'Statistics'],
    matchPercentage: 78,
    description: 'Analyze business data to drive decision-making processes.',
    whyRecommended: 'Strong match with your Python and SQL skills. Your data analysis experience aligns with core requirements. Learning Tableau would increase your match to 92%.'
  },
  {
    id: '2',
    title: 'Software Engineer',
    company: 'Innovation Labs',
    location: 'Austin, TX',
    type: 'Full-time',
    requiredSkills: ['JavaScript', 'React', 'Node.js', 'Git', 'AWS'],
    matchPercentage: 65,
    description: 'Build scalable web applications for enterprise clients.',
    whyRecommended: 'Your JavaScript and Git proficiency are valuable. Adding React and Node.js skills would significantly boost your candidacy for this role.'
  },
  {
    id: '3',
    title: 'ML Engineering Intern',
    company: 'AI Ventures',
    location: 'Remote',
    type: 'Internship',
    requiredSkills: ['Python', 'TensorFlow', 'Machine Learning', 'Statistics', 'Docker'],
    matchPercentage: 55,
    description: 'Develop and deploy machine learning models for production.',
    whyRecommended: 'Your Python skills and research experience are relevant. Focus on TensorFlow and Docker to become a strong candidate.'
  },
  {
    id: '4',
    title: 'Business Intelligence Analyst',
    company: 'Global Finance Corp',
    location: 'New York, NY',
    type: 'Full-time',
    requiredSkills: ['SQL', 'Power BI', 'Excel', 'Data Analysis', 'Financial Modeling'],
    matchPercentage: 60,
    description: 'Create dashboards and reports for executive decision-making.',
    whyRecommended: 'Your SQL and data analysis skills transfer well. Learning Power BI would open this career path.'
  }
];

export const mockSkills: Skill[] = [
  { name: 'Python', category: 'Programming', demandScore: 95, owned: true, importance: 'Critical' },
  { name: 'JavaScript', category: 'Programming', demandScore: 92, owned: true, importance: 'Critical' },
  { name: 'SQL', category: 'Data', demandScore: 90, owned: true, importance: 'Critical' },
  { name: 'React', category: 'Frontend', demandScore: 88, owned: false, importance: 'High' },
  { name: 'Machine Learning', category: 'AI/ML', demandScore: 87, owned: false, importance: 'High' },
  { name: 'AWS', category: 'Cloud', demandScore: 85, owned: false, importance: 'High' },
  { name: 'Docker', category: 'DevOps', demandScore: 82, owned: false, importance: 'High' },
  { name: 'Data Analysis', category: 'Data', demandScore: 80, owned: true, importance: 'Medium' },
  { name: 'Git', category: 'Tools', demandScore: 78, owned: true, importance: 'Medium' },
  { name: 'TensorFlow', category: 'AI/ML', demandScore: 75, owned: false, importance: 'Medium' },
  { name: 'Node.js', category: 'Backend', demandScore: 74, owned: false, importance: 'Medium' },
  { name: 'Tableau', category: 'Visualization', demandScore: 70, owned: false, importance: 'Low' },
];

export const mockCourses: Course[] = [
  {
    id: '1',
    title: 'React - The Complete Guide',
    provider: 'Coursera',
    duration: '40 hours',
    skill: 'React',
    matchScore: 92,
    explanation: 'Learning React would unlock 15+ more job matches and increase your average match score by 12%.'
  },
  {
    id: '2',
    title: 'AWS Cloud Practitioner',
    provider: 'AWS Training',
    duration: '20 hours',
    skill: 'AWS',
    matchScore: 88,
    explanation: 'AWS certification is highly valued. Would make you eligible for cloud-focused roles.'
  },
  {
    id: '3',
    title: 'Machine Learning Specialization',
    provider: 'Stanford Online',
    duration: '60 hours',
    skill: 'Machine Learning',
    matchScore: 85,
    explanation: 'Complements your Python skills and research experience. Opens ML Engineer career path.'
  },
  {
    id: '4',
    title: 'Docker for Developers',
    provider: 'LinkedIn Learning',
    duration: '15 hours',
    skill: 'Docker',
    matchScore: 78,
    explanation: 'Essential DevOps skill that appears in 40% of software engineering job listings.'
  }
];

export const marketSkillDemand = [
  { skill: 'Python', demand: 95 },
  { skill: 'JavaScript', demand: 92 },
  { skill: 'SQL', demand: 90 },
  { skill: 'React', demand: 88 },
  { skill: 'AWS', demand: 85 },
  { skill: 'Machine Learning', demand: 87 },
  { skill: 'Docker', demand: 82 },
  { skill: 'TypeScript', demand: 80 },
  { skill: 'Node.js', demand: 78 },
  { skill: 'Kubernetes', demand: 75 },
];

export const dashboardStats = {
  jobReadinessScore: 72,
  skillsMatched: 5,
  totalRequiredSkills: 8,
  missingHighDemandSkills: ['React', 'AWS', 'Docker'],
};
