CREATE UNIQUE INDEX uq_research_participants_active_linked_user
  ON public.research_participants (linked_user_id)
  WHERE linked_user_id IS NOT NULL AND is_active = true;
