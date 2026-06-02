-- Schema PostgreSQL do projeto

CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY,
    username varchar(50) NOT NULL UNIQUE,
    hashed_password text NOT NULL,
    is_active boolean NOT NULL DEFAULT TRUE,
    role varchar(20) NOT NULL DEFAULT 'user',
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS plant (
    id uuid PRIMARY KEY,
    user_id uuid REFERENCES users(id),
    common_name varchar(100) NOT NULL,
    scientific_name varchar(150),
    description text,
    optimal_temp_min numeric NOT NULL,
    optimal_temp_max numeric NOT NULL,
    optimal_humidity_min numeric NOT NULL,
    optimal_humidity_max numeric NOT NULL,
    optimal_soil_moisture_min numeric NOT NULL,
    optimal_soil_moisture_max numeric NOT NULL,
    watering_interval_hours integer NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS device (
    id uuid PRIMARY KEY,
    plant_id uuid NOT NULL REFERENCES plant(id),
    name varchar(80) NOT NULL,
    mac_address varchar(17) NOT NULL UNIQUE,
    firmware_version varchar(20),
    location_description varchar(200),
    is_active boolean NOT NULL DEFAULT TRUE,
    last_seen_at timestamptz,
    created_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS sensor_reading (
    id uuid PRIMARY KEY,
    device_id uuid NOT NULL REFERENCES device(id),
    temperature_celsius numeric,
    humidity_percent numeric,
    soil_moisture_percent numeric,
    light_lux numeric,
    status varchar(20) NOT NULL,
    recorded_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS irrigation_event (
    id uuid PRIMARY KEY,
    device_id uuid NOT NULL REFERENCES device(id),
    started_at timestamptz NOT NULL,
    ended_at timestamptz,
    duration_seconds integer,
    triggered_by varchar(30) NOT NULL,
    notes text
);

CREATE TABLE IF NOT EXISTS plant_image (
    id uuid PRIMARY KEY,
    device_id uuid NOT NULL REFERENCES device(id),
    image_base64 text NOT NULL,
    analysis_id uuid,
    captured_at timestamptz NOT NULL,
    storage_path text
);

CREATE TABLE IF NOT EXISTS vision_analysis (
    id uuid PRIMARY KEY,
    image_id uuid NOT NULL REFERENCES plant_image(id),
    model_version varchar(30) NOT NULL,
    health_score numeric NOT NULL,
    health_status varchar(20) NOT NULL,
    leaf_coverage_percent numeric,
    detected_issues text,
    recommendations text,
    confidence_score numeric NOT NULL,
    processing_time_ms integer,
    analyzed_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS system_event (
    id uuid PRIMARY KEY,
    device_id uuid REFERENCES device(id),
    event_type varchar(50) NOT NULL,
    description text NOT NULL,
    occurred_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS alert (
    id uuid PRIMARY KEY,
    device_id uuid NOT NULL REFERENCES device(id),
    sensor_reading_id uuid REFERENCES sensor_reading(id),
    alert_type varchar(30) NOT NULL,
    metric_name varchar(50) NOT NULL,
    threshold_value numeric NOT NULL,
    actual_value numeric NOT NULL,
    message varchar(300) NOT NULL,
    resolved boolean NOT NULL DEFAULT FALSE,
    triggered_at timestamptz NOT NULL,
    resolved_at timestamptz
);