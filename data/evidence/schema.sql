PRAGMA foreign_keys = ON;

CREATE TABLE schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE receipts (
    receipt_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    resolves INTEGER,
    relevance_assessment TEXT NOT NULL DEFAULT '',
    review_note TEXT NOT NULL DEFAULT '',
    retrieved_at TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT '',
    UNIQUE(source_type, external_id)
);

CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    subject_name TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_name TEXT NOT NULL,
    scope_json TEXT NOT NULL DEFAULT '{}',
    polarity TEXT NOT NULL DEFAULT 'UNRESOLVED',
    source_text TEXT NOT NULL DEFAULT ''
);

CREATE TABLE candidate_reviews (
    review_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    drug TEXT NOT NULL,
    disease TEXT NOT NULL,
    mechanism_target TEXT NOT NULL DEFAULT '',
    terminal_relation TEXT NOT NULL DEFAULT '',
    terminal_tier TEXT NOT NULL DEFAULT '',
    terminal_provenance TEXT NOT NULL DEFAULT '',
    terminal_receipt_assessment TEXT NOT NULL DEFAULT '',
    direction TEXT NOT NULL DEFAULT '',
    cheap_generic TEXT NOT NULL DEFAULT '',
    evidence_state TEXT NOT NULL,
    human_testing_status TEXT NOT NULL,
    result_signal TEXT NOT NULL,
    candidate_assessment TEXT NOT NULL,
    review_note TEXT NOT NULL,
    negative_evidence_found TEXT NOT NULL,
    negative_evidence_note TEXT NOT NULL,
    evidence_sources TEXT NOT NULL DEFAULT '',
    reviewed_on TEXT NOT NULL,
    raw_json TEXT NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
);

CREATE TABLE studies (
    study_id TEXT PRIMARY KEY,
    primary_receipt_id TEXT,
    title TEXT NOT NULL DEFAULT '',
    phase_json TEXT NOT NULL DEFAULT '[]',
    recruitment_status TEXT NOT NULL DEFAULT 'UNKNOWN',
    completion_date TEXT NOT NULL DEFAULT '',
    has_posted_results INTEGER NOT NULL DEFAULT 0,
    why_stopped TEXT NOT NULL DEFAULT '',
    stop_class TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    -- Retrieval-only recoverability, set by evidence/acquire_trial_results.py.
    -- Says where results can be found, never what they showed.
    results_disposition TEXT NOT NULL DEFAULT 'NOT_ASSESSED',
    results_url TEXT NOT NULL DEFAULT '',
    results_checked_on TEXT NOT NULL DEFAULT '',
    -- PUBLISHED / NOT_PUBLISHED for recovered results. NOT_PUBLISHED is the
    -- interesting case: posted to a registry, invisible to literature search.
    results_publication_state TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (primary_receipt_id) REFERENCES receipts(receipt_id)
);

CREATE TABLE study_roles (
    role_id TEXT PRIMARY KEY,
    study_id TEXT NOT NULL,
    role TEXT NOT NULL,
    graph_object_name TEXT,
    literal_name TEXT NOT NULL,
    attributes_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (study_id) REFERENCES studies(study_id)
);

CREATE TABLE study_pair_links (
    study_id TEXT NOT NULL,
    claim_id TEXT NOT NULL,
    review_id TEXT NOT NULL,
    pair_linkage TEXT NOT NULL,
    PRIMARY KEY (study_id, claim_id),
    FOREIGN KEY (study_id) REFERENCES studies(study_id),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
    FOREIGN KEY (review_id) REFERENCES candidate_reviews(review_id)
);

CREATE TABLE outcomes (
    outcome_id TEXT PRIMARY KEY,
    study_id TEXT,
    claim_id TEXT,
    endpoint TEXT NOT NULL DEFAULT '',
    result_signal TEXT NOT NULL,
    comparator TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    receipt_id TEXT,
    human_reviewed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (study_id) REFERENCES studies(study_id),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id),
    CHECK (study_id IS NOT NULL OR claim_id IS NOT NULL)
);

CREATE TABLE claim_evidence (
    claim_id TEXT NOT NULL,
    receipt_id TEXT NOT NULL,
    relationship TEXT NOT NULL,
    review_note TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (claim_id, receipt_id),
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);

CREATE TABLE review_events (
    review_event_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    assessment TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    reviewer TEXT NOT NULL DEFAULT 'project_review',
    reviewed_at TEXT NOT NULL
);

-- Measured PRISM Repurposing viability adjudication, written by
-- evidence/acquire_prism.py against a pre-registration frozen before any
-- outcome was read.
--
-- LABELS, NOT FEATURES. This table is read-only context for the UI. Nothing in
-- oracle/, core/, validation/ or data/ may read it, and it must never enter the
-- scored graph path: these are exactly the external labels the ranker would
-- otherwise have to be tested against.
--
-- Selectivity, not potency. Cell lines are not patients; no row here supports
-- an efficacy claim in either direction, and absence from the screen is
-- recorded as absence rather than inactivity.
CREATE TABLE prism_observations (
    observation_id TEXT PRIMARY KEY,
    review_id TEXT NOT NULL,
    drug TEXT NOT NULL,
    disease TEXT NOT NULL,
    stratum TEXT NOT NULL,
    correspondence_type TEXT NOT NULL DEFAULT 'REFUSED',
    prism_lineage TEXT NOT NULL DEFAULT '',
    endpoint TEXT NOT NULL DEFAULT '',
    screen_id TEXT NOT NULL DEFAULT '',
    n_target_lines INTEGER,
    n_other_lines INTEGER,
    median_auc_target REAL,
    median_auc_other REAL,
    selectivity_delta REAL,
    mannwhitney_p REAL,
    bh_q REAL,
    pan_lineage_cytotoxic INTEGER,
    verdict TEXT NOT NULL,
    source_file TEXT NOT NULL DEFAULT '',
    source_sha256 TEXT NOT NULL DEFAULT '',
    human_reviewed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (review_id) REFERENCES candidate_reviews(review_id)
);

CREATE VIRTUAL TABLE evidence_fts USING fts5(
    record_type UNINDEXED,
    record_id UNINDEXED,
    title,
    body,
    tokenize = 'unicode61 remove_diacritics 2'
);

CREATE INDEX idx_candidate_pair ON candidate_reviews(drug, disease);
CREATE INDEX idx_study_roles_study ON study_roles(study_id);
CREATE INDEX idx_study_roles_literal ON study_roles(literal_name);
CREATE INDEX idx_study_pairs_claim ON study_pair_links(claim_id);
CREATE INDEX idx_outcomes_claim ON outcomes(claim_id);
CREATE INDEX idx_claim_evidence_claim ON claim_evidence(claim_id);
CREATE INDEX idx_prism_review ON prism_observations(review_id);
CREATE INDEX idx_prism_pair ON prism_observations(drug, disease);
