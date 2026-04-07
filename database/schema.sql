-- ═══════════════════════════════════════════════════════════════
-- CCTNS-GridX Database Schema
-- Crime Predictive Model & Hotspot Mapping — Tamil Nadu Police
-- ═══════════════════════════════════════════════════════════════

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ─── USERS ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    full_name       TEXT    NOT NULL,
    rank            TEXT    NOT NULL CHECK(rank IN ('SP','DSP','SHO','SI','CONSTABLE')),
    badge_number    TEXT    UNIQUE,
    police_station_id INTEGER,
    district_id     INTEGER,
    role            TEXT    NOT NULL DEFAULT 'viewer' CHECK(role IN ('admin','analyst','officer','viewer')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    last_login      TEXT,
    FOREIGN KEY (police_station_id) REFERENCES police_stations(id),
    FOREIGN KEY (district_id) REFERENCES districts(id)
);

-- ─── DISTRICTS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS districts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    code        TEXT    NOT NULL UNIQUE,
    lat         REAL    NOT NULL,
    lng         REAL    NOT NULL,
    population  INTEGER NOT NULL DEFAULT 0,
    area_sq_km  REAL    NOT NULL DEFAULT 0,
    zone        TEXT    NOT NULL DEFAULT 'General'
);

-- ─── POLICE STATIONS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS police_stations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    district_id         INTEGER NOT NULL,
    lat                 REAL    NOT NULL,
    lng                 REAL    NOT NULL,
    address             TEXT,
    jurisdiction_area   TEXT,
    station_type        TEXT    NOT NULL DEFAULT 'Regular' CHECK(station_type IN ('Regular','Women','Cyber','Traffic','Railway','Coastal')),
    contact_number      TEXT,
    sho_name            TEXT,
    FOREIGN KEY (district_id) REFERENCES districts(id)
);

-- ─── CRIME CATEGORIES ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crime_categories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    act_name        TEXT    NOT NULL,
    section         TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    severity        INTEGER NOT NULL DEFAULT 3 CHECK(severity BETWEEN 1 AND 5),
    crime_type      TEXT    NOT NULL,
    is_cognizable   INTEGER NOT NULL DEFAULT 1,
    is_bailable     INTEGER NOT NULL DEFAULT 0,
    UNIQUE(act_name, section)
);

-- ─── FIR RECORDS ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fir_records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fir_number          TEXT    NOT NULL UNIQUE,
    police_station_id   INTEGER NOT NULL,
    district_id         INTEGER NOT NULL,
    crime_category_id   INTEGER NOT NULL,
    -- Timing
    date_reported       TEXT    NOT NULL,
    date_of_crime       TEXT    NOT NULL,
    time_of_crime       TEXT,
    -- Location
    latitude            REAL    NOT NULL,
    longitude           REAL    NOT NULL,
    location_address    TEXT,
    location_landmark   TEXT,
    -- Complainant
    complainant_name    TEXT    NOT NULL,
    complainant_age     INTEGER,
    complainant_gender  TEXT    CHECK(complainant_gender IN ('Male','Female','Other')),
    complainant_contact TEXT,
    -- Accused
    accused_name        TEXT,
    accused_age         INTEGER,
    accused_gender      TEXT    CHECK(accused_gender IN ('Male','Female','Other')),
    accused_description TEXT,
    -- Victim
    victim_name         TEXT,
    victim_age          INTEGER,
    victim_gender       TEXT    CHECK(victim_gender IN ('Male','Female','Other')),
    -- Case details
    description         TEXT    NOT NULL,
    modus_operandi      TEXT,
    property_stolen     TEXT,
    property_value      REAL    DEFAULT 0,
    weapon_used         TEXT,
    -- Status
    status              TEXT    NOT NULL DEFAULT 'Registered' CHECK(status IN ('Registered','Under Investigation','Charge Sheet Filed','Closed','Undetected')),
    investigating_officer TEXT,
    -- Metadata
    created_by          INTEGER,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    cctns_synced        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (police_station_id) REFERENCES police_stations(id),
    FOREIGN KEY (district_id) REFERENCES districts(id),
    FOREIGN KEY (crime_category_id) REFERENCES crime_categories(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ─── PATROL ROUTES ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patrol_routes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    police_station_id   INTEGER NOT NULL,
    district_id         INTEGER NOT NULL,
    season              TEXT    NOT NULL CHECK(season IN ('Summer','Monsoon','Winter','Festival','General')),
    route_type          TEXT    NOT NULL DEFAULT 'Regular' CHECK(route_type IN ('Regular','Highway','Women Safety','Night','Emergency')),
    waypoints           TEXT    NOT NULL, -- JSON array of {lat, lng, name}
    total_distance_km   REAL,
    estimated_time_mins INTEGER,
    priority            INTEGER NOT NULL DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
    is_active           INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (police_station_id) REFERENCES police_stations(id),
    FOREIGN KEY (district_id) REFERENCES districts(id)
);

-- ─── PATROL UNITS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patrol_units (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_name       TEXT    NOT NULL,
    unit_type       TEXT    NOT NULL DEFAULT 'Vehicle' CHECK(unit_type IN ('Vehicle','Bike','Foot','Highway')),
    police_station_id INTEGER NOT NULL,
    current_lat     REAL,
    current_lng     REAL,
    status          TEXT    NOT NULL DEFAULT 'Idle' CHECK(status IN ('Active','Idle','On Break','Emergency','Off Duty')),
    route_id        INTEGER,
    officers_count  INTEGER NOT NULL DEFAULT 2,
    contact_number  TEXT,
    last_updated    TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (police_station_id) REFERENCES police_stations(id),
    FOREIGN KEY (route_id) REFERENCES patrol_routes(id)
);

-- ─── WOMEN SAFETY ZONES ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS women_safety_zones (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    zone_type           TEXT    NOT NULL CHECK(zone_type IN ('Highway','City','Residential','Commercial','Industrial','Educational')),
    lat                 REAL    NOT NULL,
    lng                 REAL    NOT NULL,
    radius_meters       INTEGER NOT NULL DEFAULT 500,
    risk_level          TEXT    NOT NULL CHECK(risk_level IN ('Low','Medium','High','Critical')),
    patrol_frequency    TEXT    NOT NULL DEFAULT 'Regular' CHECK(patrol_frequency IN ('Hourly','Regular','Daily','Weekly')),
    district_id         INTEGER NOT NULL,
    total_incidents     INTEGER NOT NULL DEFAULT 0,
    has_cctv            INTEGER NOT NULL DEFAULT 0,
    has_streetlight      INTEGER NOT NULL DEFAULT 1,
    nearest_station_id  INTEGER,
    notes               TEXT,
    FOREIGN KEY (district_id) REFERENCES districts(id),
    FOREIGN KEY (nearest_station_id) REFERENCES police_stations(id)
);

-- ─── ACCIDENT ZONES ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS accident_zones (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name       TEXT    NOT NULL,
    lat                 REAL    NOT NULL,
    lng                 REAL    NOT NULL,
    road_name           TEXT,
    road_type           TEXT    NOT NULL CHECK(road_type IN ('National Highway','State Highway','District Road','City Road','Village Road')),
    accident_count      INTEGER NOT NULL DEFAULT 0,
    fatality_count      INTEGER NOT NULL DEFAULT 0,
    injury_count        INTEGER NOT NULL DEFAULT 0,
    severity            TEXT    NOT NULL CHECK(severity IN ('Low','Medium','High','Critical')),
    primary_cause       TEXT,
    district_id         INTEGER NOT NULL,
    last_accident_date  TEXT,
    speed_limit         INTEGER,
    has_signal          INTEGER NOT NULL DEFAULT 0,
    has_divider         INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (district_id) REFERENCES districts(id)
);

-- ─── BEHAVIORAL PROFILES ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS behavioral_profiles (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    crime_category_id       INTEGER NOT NULL,
    district_id             INTEGER NOT NULL,
    -- Time patterns (JSON: hourly distribution)
    hourly_pattern          TEXT,
    -- Day of week patterns (JSON)
    day_of_week_pattern     TEXT,
    -- Monthly patterns (JSON)
    monthly_pattern         TEXT,
    -- Seasonal
    peak_season             TEXT,
    -- Demographics
    avg_accused_age         REAL,
    predominant_gender      TEXT,
    -- Financial
    financial_correlation   TEXT    CHECK(financial_correlation IN ('Low Income','Middle Income','High Income','Mixed')),
    -- Recurrence
    repeat_offender_rate    REAL    DEFAULT 0,
    avg_recurrence_days     REAL,
    -- Spatial
    urban_rural_ratio       REAL    DEFAULT 1.0,
    -- Analysis metadata
    sample_size             INTEGER NOT NULL DEFAULT 0,
    last_analyzed           TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (crime_category_id) REFERENCES crime_categories(id),
    FOREIGN KEY (district_id) REFERENCES districts(id)
);

-- ─── INDEXES ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_fir_district ON fir_records(district_id);
CREATE INDEX IF NOT EXISTS idx_fir_station ON fir_records(police_station_id);
CREATE INDEX IF NOT EXISTS idx_fir_category ON fir_records(crime_category_id);
CREATE INDEX IF NOT EXISTS idx_fir_date ON fir_records(date_of_crime);
CREATE INDEX IF NOT EXISTS idx_fir_coords ON fir_records(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_fir_status ON fir_records(status);
CREATE INDEX IF NOT EXISTS idx_station_district ON police_stations(district_id);
CREATE INDEX IF NOT EXISTS idx_patrol_station ON patrol_routes(police_station_id);
CREATE INDEX IF NOT EXISTS idx_accident_district ON accident_zones(district_id);
CREATE INDEX IF NOT EXISTS idx_women_district ON women_safety_zones(district_id);
CREATE INDEX IF NOT EXISTS idx_behavioral_crime ON behavioral_profiles(crime_category_id);
