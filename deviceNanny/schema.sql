DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS users;

CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    device_name TEXT NOT NULL,
    serial_udid TEXT NOT NULL,
    manufacturer TEXT NOT NULL,
    model TEXT NOT NULL,
    type TEXT NOT NULL,
    os TEXT NOT NULL,
    checked_out_by INTEGER NOT NULL,
    time_checked_out TIMESTAMP NOT NULL,
    last_reminded TIMESTAMP NOT NULL,
    location TEXT NOT NULL,
    port INTEGER,
    FOREIGN KEY (checked_out_by) REFERENCES users (id)
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  first_name text NOT NULL,
  last_name text NOT NULL,
  slack_id text NOT NULL,
  office text
);