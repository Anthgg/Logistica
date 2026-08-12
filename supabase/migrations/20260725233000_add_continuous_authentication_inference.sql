ALTER TABLE public.sessions
  ADD COLUMN last_risk_action varchar(60),
  ADD COLUMN continuous_auth_status varchar(30)
    NOT NULL DEFAULT 'pending',
  ADD CONSTRAINT ck_sessions_continuous_auth_status
    CHECK (
      continuous_auth_status IN (
        'pending',
        'active',
        'degraded',
        'verification_required',
        'restricted',
        'terminated'
      )
    );

CREATE TABLE public.continuous_auth_evaluations (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL
    REFERENCES public.users(id) ON DELETE CASCADE,
  session_id uuid NOT NULL
    REFERENCES public.sessions(id) ON DELETE CASCADE,
  experimental_session_id uuid
    REFERENCES public.experimental_sessions(id) ON DELETE SET NULL,
  participant_id uuid
    REFERENCES public.research_participants(id) ON DELETE SET NULL,
  facial_capture_id uuid
    REFERENCES public.facial_captures(id) ON DELETE SET NULL,
  behavioral_window_id varchar(100),
  facial_available boolean NOT NULL,
  pad_available boolean NOT NULL,
  behavioral_available boolean NOT NULL,
  facial_score numeric(20, 10),
  pad_score numeric(20, 10),
  behavioral_score numeric(20, 10),
  facial_risk numeric(6, 5)
    CHECK (facial_risk IS NULL OR (facial_risk >= 0 AND facial_risk <= 1)),
  pad_risk numeric(6, 5)
    CHECK (pad_risk IS NULL OR (pad_risk >= 0 AND pad_risk <= 1)),
  behavioral_risk numeric(6, 5)
    CHECK (
      behavioral_risk IS NULL
      OR (behavioral_risk >= 0 AND behavioral_risk <= 1)
    ),
  combined_risk numeric(6, 5) NOT NULL
    CHECK (combined_risk >= 0 AND combined_risk <= 1),
  risk_level varchar(20) NOT NULL
    CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
  authentication_level varchar(50) NOT NULL
    CHECK (
      authentication_level IN (
        'traditional',
        'continuously_verified',
        'verification_required',
        'restricted',
        'terminated'
      )
    ),
  recommended_action varchar(60) NOT NULL,
  applied_action varchar(60) NOT NULL,
  model_versions jsonb NOT NULL,
  latency_ms numeric(12, 3) NOT NULL CHECK (latency_ms >= 0),
  latency_breakdown jsonb NOT NULL,
  evaluated_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_continuous_auth_evaluations_user_id
  ON public.continuous_auth_evaluations(user_id);
CREATE INDEX ix_continuous_auth_evaluations_session_id
  ON public.continuous_auth_evaluations(session_id);
CREATE INDEX ix_continuous_auth_evaluations_experimental_session_id
  ON public.continuous_auth_evaluations(experimental_session_id);
CREATE INDEX ix_continuous_auth_evaluations_participant_id
  ON public.continuous_auth_evaluations(participant_id);
CREATE INDEX ix_continuous_auth_evaluations_facial_capture_id
  ON public.continuous_auth_evaluations(facial_capture_id);
CREATE INDEX ix_continuous_auth_evaluations_risk_level
  ON public.continuous_auth_evaluations(risk_level);
CREATE INDEX ix_continuous_auth_evaluations_authentication_level
  ON public.continuous_auth_evaluations(authentication_level);
CREATE INDEX ix_continuous_auth_evaluations_evaluated_at
  ON public.continuous_auth_evaluations(evaluated_at);
CREATE INDEX ix_continuous_auth_evaluations_session_evaluated
  ON public.continuous_auth_evaluations(session_id, evaluated_at);
CREATE INDEX ix_continuous_auth_evaluations_user_evaluated
  ON public.continuous_auth_evaluations(user_id, evaluated_at);

CREATE TABLE public.risk_events (
  id uuid PRIMARY KEY,
  continuous_auth_evaluation_id uuid NOT NULL
    REFERENCES public.continuous_auth_evaluations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL
    REFERENCES public.users(id) ON DELETE CASCADE,
  session_id uuid NOT NULL
    REFERENCES public.sessions(id) ON DELETE CASCADE,
  previous_risk_level varchar(20)
    CHECK (
      previous_risk_level IS NULL OR
      previous_risk_level IN ('low', 'medium', 'high', 'critical')
    ),
  new_risk_level varchar(20) NOT NULL
    CHECK (new_risk_level IN ('low', 'medium', 'high', 'critical')),
  recommended_action varchar(60) NOT NULL,
  applied_action varchar(60) NOT NULL,
  reason_code varchar(80) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_risk_events_continuous_auth_evaluation_id
  ON public.risk_events(continuous_auth_evaluation_id);
CREATE INDEX ix_risk_events_user_id
  ON public.risk_events(user_id);
CREATE INDEX ix_risk_events_session_id
  ON public.risk_events(session_id);
CREATE INDEX ix_risk_events_created_at
  ON public.risk_events(created_at);
CREATE INDEX ix_risk_events_session_created
  ON public.risk_events(session_id, created_at);

ALTER TABLE public.continuous_auth_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_events ENABLE ROW LEVEL SECURITY;

GRANT ALL ON public.continuous_auth_evaluations TO service_role;
GRANT ALL ON public.risk_events TO service_role;
