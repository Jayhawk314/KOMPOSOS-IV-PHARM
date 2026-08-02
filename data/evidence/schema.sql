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
