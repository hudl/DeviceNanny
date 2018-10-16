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
    time_checked_out INTEGER,
    last_reminded INTEGER,
    location TEXT NOT NULL,
    port INTEGER,
    FOREIGN KEY (checked_out_by) REFERENCES users (id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    slack_id TEXT,
    location TEXT
);

CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slack_channel TEXT,
    slack_team_channel TEXT,
    reminder_interval TEXT,
    checkout_length TEXT,
    message TEXT,
    office_location TEXT
);

INSERT INTO settings (slack_channel, slack_team_channel, reminder_interval, checkout_length, message, office_location) VALUES
('omananny', 'omananny', '5', '30', 'You have a device checked out', 'Omaha');

INSERT INTO users (user_id, first_name, last_name) VALUES ('0', '-', '-');

INSERT INTO users (user_id, first_name, last_name) VALUES ('1', 'Missing', 'Device');
