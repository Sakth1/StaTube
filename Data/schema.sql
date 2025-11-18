CREATE TABLE IF NOT EXISTS CHANNEL (
    channel_id TEXT PRIMARY KEY,
    name TEXT,
    url TEXT,
    sub_count TEXT,
    desc TEXT,
    profile_pic TEXT
);

CREATE TABLE IF NOT EXISTS VIDEO (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT,
    video_type TEXT,
    video_url TEXT,
    title TEXT,
    desc TEXT,
    duration TEXT,
    duration_in_seconds INTEGER,
    thumbnail_path TEXT,
    view_count INTEGER,
    time_since_published TEXT,
    upload_timestamp INTEGER,
    FOREIGN KEY(channel_id) REFERENCES CHANNEL(channel_id)
);

CREATE TABLE IF NOT EXISTS TRANSCRIPT (
    transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT, 
    file_path TEXT,
    language TEXT,
    FOREIGN KEY(video_id) REFERENCES VIDEO(video_id)
);

CREATE TABLE IF NOT EXISTS COMMENT (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    file_path TEXT,
    FOREIGN KEY(video_id) REFERENCES VIDEO(video_id)
);
