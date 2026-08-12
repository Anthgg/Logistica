ALTER TABLE public.experimental_sessions
  ADD CONSTRAINT ck_experimental_sessions_pad_consistency
    CHECK (
      (presentation_label IS NULL AND attack_type IS NULL) OR
      (presentation_label = 'bona_fide' AND attack_type = 'none') OR
      (
        presentation_label = 'attack' AND
        attack_type IN ('printed_photo', 'screen_photo', 'replayed_video')
      )
    ),
  ADD CONSTRAINT ck_experimental_sessions_operator_change_consistency
    CHECK (
      (sample_role = 'change_operator' AND operator_change_at IS NOT NULL) OR
      (sample_role <> 'change_operator' AND operator_change_at IS NULL)
    ),
  ADD CONSTRAINT ck_experimental_sessions_annotation_confirmation
    CHECK (
      annotation_status = 'pending' OR
      (annotated_by IS NOT NULL AND annotated_at IS NOT NULL)
    ),
  ADD CONSTRAINT ck_experimental_sessions_annotation_notes_length
    CHECK (annotation_notes IS NULL OR char_length(annotation_notes) <= 500);
