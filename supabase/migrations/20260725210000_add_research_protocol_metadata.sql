ALTER TABLE public.experimental_sessions
  ADD COLUMN protocol_version varchar(50) NOT NULL DEFAULT 'pilot-protocol-v0.1.0',
  ADD COLUMN collector_version varchar(50) NOT NULL DEFAULT 'web-v0.1.0',
  ADD COLUMN identity_label varchar(20) NOT NULL DEFAULT 'genuine',
  ADD COLUMN sample_role varchar(30) NOT NULL DEFAULT 'verification',
  ADD COLUMN operator_change_at timestamptz,
  ADD COLUMN presentation_label varchar(20),
  ADD COLUMN attack_type varchar(30),
  ADD COLUMN source_device varchar(100),
  ADD COLUMN pad_source_id varchar(100),
  ADD COLUMN annotation_status varchar(20) NOT NULL DEFAULT 'pending',
  ADD COLUMN annotated_by uuid,
  ADD COLUMN annotated_at timestamptz,
  ADD COLUMN annotation_notes text,
  ADD COLUMN capture_interval_seconds integer NOT NULL DEFAULT 5,
  ADD COLUMN batch_interval_seconds integer NOT NULL DEFAULT 3,
  ADD COLUMN max_batch_events integer NOT NULL DEFAULT 100,
  ADD COLUMN max_image_size_bytes integer NOT NULL DEFAULT 1048576,
  ADD COLUMN client_timezone_offset_minutes integer,
  ADD COLUMN client_language varchar(20),
  ADD COLUMN screen_pixel_ratio numeric(5,2);

ALTER TABLE public.experimental_sessions
  ADD CONSTRAINT fk_experimental_sessions_annotated_by_users
    FOREIGN KEY (annotated_by) REFERENCES public.users(id) ON DELETE SET NULL,
  ADD CONSTRAINT ck_experimental_sessions_identity_label
    CHECK (identity_label IN ('genuine', 'impostor')),
  ADD CONSTRAINT ck_experimental_sessions_sample_role
    CHECK (sample_role IN ('enrollment', 'verification', 'change_operator')),
  ADD CONSTRAINT ck_experimental_sessions_annotation_status
    CHECK (annotation_status IN ('pending', 'confirmed')),
  ADD CONSTRAINT ck_experimental_sessions_presentation_label
    CHECK (presentation_label IS NULL OR presentation_label IN ('bona_fide', 'attack')),
  ADD CONSTRAINT ck_experimental_sessions_attack_type
    CHECK (
      attack_type IS NULL OR
      attack_type IN ('none', 'printed_photo', 'screen_photo', 'replayed_video')
    ),
  ADD CONSTRAINT ck_experimental_sessions_timezone_offset
    CHECK (
      client_timezone_offset_minutes IS NULL OR
      client_timezone_offset_minutes BETWEEN -840 AND 840
    );

CREATE INDEX ix_experimental_sessions_annotation_status
  ON public.experimental_sessions (annotation_status);
CREATE INDEX ix_experimental_sessions_annotated_by
  ON public.experimental_sessions (annotated_by);

ALTER TABLE public.facial_captures
  ADD COLUMN client_timezone_offset_minutes integer,
  ADD COLUMN capture_source varchar(30) NOT NULL DEFAULT 'webcam',
  ADD COLUMN camera_facing_mode varchar(20),
  ADD CONSTRAINT ck_facial_captures_timezone_offset
    CHECK (
      client_timezone_offset_minutes IS NULL OR
      client_timezone_offset_minutes BETWEEN -840 AND 840
    ),
  ADD CONSTRAINT ck_facial_captures_source
    CHECK (capture_source IN ('webcam', 'controlled_upload'));

ALTER TABLE public.behavioral_batches
  ADD COLUMN visibility_state varchar(30),
  ADD COLUMN client_timezone_offset_minutes integer,
  ADD COLUMN dropped_event_count integer NOT NULL DEFAULT 0,
  ADD COLUMN collector_error_count integer NOT NULL DEFAULT 0,
  ADD CONSTRAINT ck_behavioral_batches_timezone_offset
    CHECK (
      client_timezone_offset_minutes IS NULL OR
      client_timezone_offset_minutes BETWEEN -840 AND 840
    ),
  ADD CONSTRAINT ck_behavioral_batches_dropped_events
    CHECK (dropped_event_count >= 0),
  ADD CONSTRAINT ck_behavioral_batches_collector_errors
    CHECK (collector_error_count >= 0);
