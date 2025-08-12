-- Language Teacher Bot Database Schema
-- SQLite schema for user progress, learning data, and gamification

-- User profiles and basic information
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    telegram_chat_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    target_language TEXT NOT NULL,
    native_language TEXT NOT NULL,
    proficiency_level TEXT NOT NULL CHECK (proficiency_level IN (
        'beginner', 'elementary', 'intermediate', 
        'upper_intermediate', 'advanced', 'proficient'
    )),
    learning_goals TEXT, -- JSON array of goals
    preferred_teacher TEXT CHECK (preferred_teacher IN ('conversation_teacher', 'homework_teacher')),
    daily_goal_minutes INTEGER DEFAULT 30,
    timezone TEXT DEFAULT 'UTC',
    total_xp INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Learning progress for each skill
CREATE TABLE IF NOT EXISTS learning_progress (
    progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_type TEXT NOT NULL CHECK (skill_type IN (
        'reading', 'writing', 'speaking', 'listening', 'vocabulary', 'grammar'
    )),
    current_level REAL DEFAULT 0.0, -- 0-100 scale
    xp_points INTEGER DEFAULT 0,
    exercises_completed INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    total_attempts INTEGER DEFAULT 0,
    last_practiced DATETIME,
    mastery_percentage REAL DEFAULT 0.0, -- 0-1 scale
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    UNIQUE(user_id, skill_type)
);

-- Active learning sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_type TEXT NOT NULL CHECK (session_type IN (
        'conversation', 'homework', 'test', 'vocabulary_drill', 'grammar_practice'
    )),
    current_teacher TEXT NOT NULL CHECK (current_teacher IN (
        'conversation_teacher', 'homework_teacher'
    )),
    session_state TEXT, -- JSON state data
    exercises_completed INTEGER DEFAULT 0,
    current_exercise TEXT, -- JSON exercise data
    is_active BOOLEAN DEFAULT TRUE,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Exercise definitions and templates
CREATE TABLE IF NOT EXISTS exercises (
    exercise_id TEXT PRIMARY KEY,
    exercise_type TEXT NOT NULL,
    skill_type TEXT NOT NULL CHECK (skill_type IN (
        'reading', 'writing', 'speaking', 'listening', 'vocabulary', 'grammar'
    )),
    difficulty_level REAL NOT NULL, -- 0-1 scale
    content TEXT NOT NULL, -- JSON content
    expected_answer TEXT NOT NULL, -- JSON expected answers
    hints TEXT, -- JSON array of hints
    explanation TEXT,
    time_limit_seconds INTEGER,
    points_value INTEGER DEFAULT 10,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User exercise attempts and results
CREATE TABLE IF NOT EXISTS user_exercises (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    session_id TEXT,
    user_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    score REAL NOT NULL, -- 0-1 scale
    time_taken_seconds INTEGER,
    hints_used INTEGER DEFAULT 0,
    feedback_given TEXT,
    completed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exercise_id) REFERENCES exercises (exercise_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
);

-- Achievement definitions
CREATE TABLE IF NOT EXISTS achievements (
    achievement_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    icon TEXT,
    points_reward INTEGER DEFAULT 0,
    unlock_condition TEXT NOT NULL, -- JSON condition
    category TEXT,
    is_hidden BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User achieved achievements
CREATE TABLE IF NOT EXISTS user_achievements (
    user_achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (achievement_id) REFERENCES achievements (achievement_id),
    UNIQUE(user_id, achievement_id)
);

-- Vocabulary items for spaced repetition
CREATE TABLE IF NOT EXISTS vocabulary_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    translation TEXT NOT NULL,
    language TEXT NOT NULL,
    context_sentence TEXT,
    difficulty_level REAL DEFAULT 0.5,
    repetition_interval INTEGER DEFAULT 1, -- days
    easiness_factor REAL DEFAULT 2.5, -- SM-2 algorithm
    next_review_date DATE,
    review_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_reviewed DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Vocabulary review history
CREATE TABLE IF NOT EXISTS vocabulary_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    quality INTEGER NOT NULL CHECK (quality >= 0 AND quality <= 5), -- SM-2 quality
    previous_interval INTEGER,
    new_interval INTEGER,
    previous_easiness REAL,
    new_easiness REAL,
    reviewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES vocabulary_items (item_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Learning paths and curriculum
CREATE TABLE IF NOT EXISTS learning_paths (
    path_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    target_level TEXT NOT NULL,
    estimated_duration_weeks INTEGER,
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER NOT NULL,
    steps TEXT NOT NULL, -- JSON array of steps
    progress_percentage REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Daily activity tracking
CREATE TABLE IF NOT EXISTS daily_activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    activity_date DATE NOT NULL,
    exercises_completed INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    xp_gained INTEGER DEFAULT 0,
    skills_practiced TEXT, -- JSON array of skills
    streak_day INTEGER DEFAULT 0,
    goals_met BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    UNIQUE(user_id, activity_date)
);

-- Conversation history for analysis
CREATE TABLE IF NOT EXISTS conversation_history (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT,
    teacher_type TEXT NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    language_detected TEXT,
    sentiment_score REAL,
    grammar_errors INTEGER DEFAULT 0,
    vocabulary_level REAL,
    message_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
);

-- User preferences and settings
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY,
    notification_enabled BOOLEAN DEFAULT TRUE,
    reminder_time TIME DEFAULT '09:00:00',
    difficulty_preference TEXT DEFAULT 'adaptive',
    feedback_style TEXT DEFAULT 'encouraging', -- encouraging, direct, detailed
    voice_enabled BOOLEAN DEFAULT TRUE,
    practice_duration_minutes INTEGER DEFAULT 15,
    daily_reminder BOOLEAN DEFAULT TRUE,
    weekend_practice BOOLEAN DEFAULT FALSE,
    language_interface TEXT DEFAULT 'en',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Performance analytics cache
CREATE TABLE IF NOT EXISTS performance_analytics (
    user_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    time_period TEXT NOT NULL, -- daily, weekly, monthly
    calculated_date DATE NOT NULL,
    metadata TEXT, -- JSON additional data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, metric_name, time_period, calculated_date),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_chat_id ON users(telegram_chat_id);
CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
CREATE INDEX IF NOT EXISTS idx_learning_progress_user_skill ON learning_progress(user_id, skill_type);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_exercises_user_completed ON user_exercises(user_id, completed_at);
CREATE INDEX IF NOT EXISTS idx_vocabulary_items_review_date ON vocabulary_items(user_id, next_review_date);
CREATE INDEX IF NOT EXISTS idx_daily_activity_user_date ON daily_activity(user_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_conversation_history_user_session ON conversation_history(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_performance_analytics_user_period ON performance_analytics(user_id, time_period, calculated_date);

-- Create triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
    AFTER UPDATE ON users
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_learning_progress_timestamp 
    AFTER UPDATE ON learning_progress
    BEGIN
        UPDATE learning_progress SET updated_at = CURRENT_TIMESTAMP WHERE progress_id = NEW.progress_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_user_sessions_last_activity 
    AFTER UPDATE ON user_sessions
    BEGIN
        UPDATE user_sessions SET last_activity = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_learning_paths_timestamp 
    AFTER UPDATE ON learning_paths
    BEGIN
        UPDATE learning_paths SET updated_at = CURRENT_TIMESTAMP WHERE path_id = NEW.path_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_user_preferences_timestamp 
    AFTER UPDATE ON user_preferences
    BEGIN
        UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
    END;

-- Insert default achievements
INSERT OR IGNORE INTO achievements (achievement_id, title, description, icon, points_reward, unlock_condition, category) VALUES
('first_lesson', 'First Steps', 'Complete your first lesson', '👶', 50, '{"exercises_completed": 1}', 'milestone'),
('week_streak', 'Week Warrior', 'Practice for 7 days straight', '🔥', 200, '{"streak_days": 7}', 'consistency'),
('vocab_master', 'Word Wizard', 'Learn 100 vocabulary words', '📚', 300, '{"vocabulary_learned": 100}', 'vocabulary'),
('conversation_starter', 'Chat Champion', 'Complete 10 conversation sessions', '💬', 150, '{"conversation_sessions": 10}', 'speaking'),
('grammar_guru', 'Grammar Master', 'Ace 20 grammar exercises', '✏️', 250, '{"grammar_correct": 20}', 'grammar'),
('speed_demon', 'Quick Learner', 'Complete an exercise in under 30 seconds', '⚡', 100, '{"exercise_time": 30}', 'achievement'),
('perfectionist', 'Perfect Score', 'Get 100% on 5 exercises in a row', '🎯', 300, '{"perfect_streak": 5}', 'accuracy'),
('early_bird', 'Early Bird', 'Practice before 8 AM', '🌅', 100, '{"practice_time": "08:00"}', 'habit'),
('night_owl', 'Night Owl', 'Practice after 10 PM', '🦉', 100, '{"practice_time": "22:00"}', 'habit'),
('monthly_champion', 'Monthly Master', 'Complete 30 days of practice', '🏆', 500, '{"monthly_days": 30}', 'milestone');

-- Insert sample exercise templates
INSERT OR IGNORE INTO exercises (exercise_id, exercise_type, skill_type, difficulty_level, content, expected_answer, hints, explanation, points_value) VALUES
('vocab_001', 'multiple_choice', 'vocabulary', 0.3, 
 '{"question": "What does ''hello'' mean in Spanish?", "options": ["Hola", "Adiós", "Gracias", "Por favor"]}',
 '["Hola"]', 
 '["Think about common greetings", "It starts with H"]',
 'Hola is the Spanish word for hello, used in both formal and informal situations.',
 10),
('grammar_001', 'fill_blank', 'grammar', 0.5,
 '{"sentence": "I ___ going to the store.", "blank_position": 1}',
 '["am"]',
 '["Use the first person singular form of ''to be''", "It''s the present continuous tense"]',
 'The correct form is ''am'' because the subject is ''I'' and we use present continuous tense.',
 15),
('reading_001', 'comprehension', 'reading', 0.4,
 '{"passage": "The cat sat on the mat. It was a sunny day.", "question": "What was the weather like?"}',
 '["sunny", "sunny day", "it was sunny"]',
 '["Look for weather-related words in the passage", "Check the second sentence"]',
 'The passage mentions ''It was a sunny day'' which describes the weather.',
 20);

-- Create views for common queries
CREATE VIEW IF NOT EXISTS user_stats AS
SELECT 
    u.user_id,
    u.username,
    u.target_language,
    u.proficiency_level,
    u.total_xp,
    u.current_streak,
    COUNT(DISTINCT ue.exercise_id) as exercises_completed,
    AVG(ue.score) as avg_score,
    COUNT(DISTINCT ua.achievement_id) as achievements_unlocked
FROM users u
LEFT JOIN user_exercises ue ON u.user_id = ue.user_id
LEFT JOIN user_achievements ua ON u.user_id = ua.user_id
GROUP BY u.user_id;

CREATE VIEW IF NOT EXISTS active_learners AS
SELECT 
    u.user_id,
    u.username,
    u.last_active,
    COUNT(da.activity_date) as active_days_last_month
FROM users u
LEFT JOIN daily_activity da ON u.user_id = da.user_id 
    AND da.activity_date >= date('now', '-30 days')
WHERE u.last_active >= datetime('now', '-7 days')
GROUP BY u.user_id
ORDER BY active_days_last_month DESC;