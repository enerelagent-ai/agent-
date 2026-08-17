-- V1.5 has one authenticated admin account, so notification read state is a
-- singleton. Seed at migration time: existing historical deals are the
-- baseline, and only deals scraped after deployment start as unread.
CREATE TABLE IF NOT EXISTS notification_state (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    last_seen_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO notification_state (id, last_seen_at)
VALUES (1, now())
ON CONFLICT (id) DO NOTHING;
