import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SECRET_KEY,
  {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false
    }
  }
);

const CONDITION_URLS = {
  C1: process.env.CONDITION_C1_URL,
  C2: process.env.CONDITION_C2_URL,
  C3: process.env.CONDITION_C3_URL,
  C4: process.env.CONDITION_C4_URL,
  C5: process.env.CONDITION_C5_URL,
  C6: process.env.CONDITION_C6_URL
};

export default async function handler(request, response) {
  if (request.method !== 'POST') {
    return response.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { browserToken } = request.body ?? {};

    if (!browserToken || typeof browserToken !== 'string') {
      return response.status(400).json({ error: 'browserToken is required' });
    }

    const { data, error } = await supabase.rpc('assign_participant', {
      p_browser_token: browserToken
    });

    if (error) throw error;

    const assignment = Array.isArray(data) ? data[0] : data;
    if (!assignment?.participant_id || !assignment?.condition_code) {
      throw new Error('Invalid assignment response');
    }

    const baseUrl = CONDITION_URLS[assignment.condition_code];
    if (!baseUrl) throw new Error(`Missing URL for ${assignment.condition_code}`);

    // 참가자에게 보이는 조건 페이지 URL에는 participant_id만 전달합니다.
    // condition_code는 Supabase DB에만 저장되며 URL에는 노출하지 않습니다.
    const redirect = new URL(baseUrl);
    redirect.searchParams.set('participant_id', assignment.participant_id);

    return response.status(200).json({
      participantId: assignment.participant_id,
      redirectUrl: redirect.toString()
    });
  } catch (err) {
    console.error(err);
    return response.status(500).json({ error: 'Assignment failed' });
  }
}
