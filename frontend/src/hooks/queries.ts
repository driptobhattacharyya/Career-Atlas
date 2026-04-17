import { useQuery } from '@tanstack/react-query';
import { insforge } from '../lib/insforge';
import { useAuth } from '../context/auth-context';

export function useProfile() {
  const { user } = useAuth();
  
  return useQuery({
    queryKey: ['profile', user?.id],
    queryFn: async () => {
      if (!user) return null;
      const { data, error } = await insforge
        .from('profiles')
        .select('*')
        .eq('user_id', user.id)
        .single();
        
      if (error && error.code !== 'PGRST116') throw error; // PGRST116 is "Rows not found"
      return data;
    },
    enabled: !!user,
  });
}

export function useSkills() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['skills', user?.id],
    queryFn: async () => {
      const { data, error } = await insforge.from('skills').select('*').eq('user_id', user?.id);
      if (error) throw error;
      return data;
    },
    enabled: !!user,
  });
}

export function useGapAnalysis() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['skill_gaps', user?.id],
    queryFn: async () => {
      const { data, error } = await insforge.from('skill_gaps').select('*').eq('user_id', user?.id);
      if (error) throw error;
      return data;
    },
    enabled: !!user,
  });
}

export function useRoadmap() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['milestones', user?.id],
    queryFn: async () => {
      const { data, error } = await insforge
        .from('milestones')
        .select('*')
        .eq('user_id', user?.id)
        .order('sort_order', { ascending: true });
      if (error) throw error;
      return data;
    },
    enabled: !!user,
  });
}

export function useJobMatches() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['job_matches', user?.id],
    queryFn: async () => {
      const { data, error } = await insforge
        .from('job_matches')
        .select('*')
        .eq('user_id', user?.id)
        .order('match_pct', { ascending: false });
      if (error) throw error;
      return data;
    },
    enabled: !!user,
  });
}

export function useTargetRoles() {
  return useQuery({
    queryKey: ['target_roles'],
    queryFn: async () => {
      const { data, error } = await insforge.from('target_roles').select('*');
      if (error) throw error;
      return data;
    }
  });
}
