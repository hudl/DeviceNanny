DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS settings;

CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    serial_udid TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    device_type TEXT NOT NULL,
    os_version TEXT NOT NULL,
    checked_out_by INTEGER,
    time_checked_out TIMESTAMP,
    last_reminded TIMESTAMP,
    location TEXT NOT NULL,
    port INTEGER,
    FOREIGN KEY (checked_out_by) REFERENCES users (id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name text NOT NULL,
    last_name text NOT NULL,
    slack_id text NOT NULL,
    location text
);

CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slack_channel text,
    slack_team_channel text,
    reminder_interval text,
    checkout_length text,
    message text,
    office_location text
);

INSERT INTO settings (slack_channel, slack_team_channel, reminder_interval, checkout_length, message, office_location) VALUES
('omananny', 'omananny', '5', '30', 'You have a device checked out', 'Omaha')
