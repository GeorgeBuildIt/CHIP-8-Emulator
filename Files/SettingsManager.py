import sqlite3

DB_FILE = "settings.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. PROFILES TABLE (Updated Schema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            bg_color TEXT,
            fg_color TEXT,
            crt_enabled INTEGER,
            ips INTEGER,
            audio INTEGER,
            rainbow_enabled INTEGER DEFAULT 0
        )
    """)

    # --- MIGRATION: Add column if it doesn't exist in an old DB ---
    try:
        cursor.execute("ALTER TABLE profiles ADD COLUMN rainbow_enabled INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        # If the column already exists, SQLite throws an error; we just ignore it
        pass
    
    # 2. ROM-PROFILE LINKS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rom_profiles (
            rom_path TEXT PRIMARY KEY,
            profile_id INTEGER,
            FOREIGN KEY(profile_id) REFERENCES profiles(id)
        )
    """)

    # 3. FAVORITES TABLE
    cursor.execute("CREATE TABLE IF NOT EXISTS favorites (path TEXT PRIMARY KEY)")
    
    # Ensure Default profile exists (Update columns here too)
    cursor.execute("SELECT * FROM profiles WHERE name='Default'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO profiles (name, bg_color, fg_color, crt_enabled, ips, audio, rainbow_enabled) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Default", "#0a140a", "#00ff00", 1, 700, 1, 0))
        
    conn.commit()
    conn.close()

# --- PROFILE LOGIC ---
def get_profiles():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles")
    rows = cursor.fetchall()
    conn.close()
    return {row["name"]: dict(row) for row in rows}

def get_rom_settings(rom_path):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find which profile this ROM uses
    cursor.execute("""
        SELECT p.* FROM profiles p
        JOIN rom_profiles r ON p.id = r.profile_id
        WHERE r.rom_path = ?
    """, (rom_path,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    
    #Fallback to Default if no link exists
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE name='Default'")
    res = dict(cursor.fetchone())
    conn.close()
    return res

def save_rom_profile_link(rom_path, profile_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM profiles WHERE name=?", (profile_name,))
    pid = cursor.fetchone()[0]
    cursor.execute("INSERT OR REPLACE INTO rom_profiles (rom_path, profile_id) VALUES (?, ?)", (rom_path, pid))
    conn.commit()
    conn.close()

def save_profile(name, bg, fg, crt, ips, audio, rainbow):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profiles (name, bg_color, fg_color, crt_enabled, ips, audio, rainbow_enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            bg_color=excluded.bg_color,
            fg_color=excluded.fg_color,
            crt_enabled=excluded.crt_enabled,
            ips=excluded.ips,
            audio=excluded.audio,
            rainbow_enabled=excluded.rainbow_enabled
    """, (name, bg, fg, int(crt), ips, int(audio), int(rainbow)))
    conn.commit()
    conn.close()

def delete_profile(name):
    if name == "Default":
        return False # Protect the default profile
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Find the ID
    cursor.execute("SELECT id FROM profiles WHERE name=?", (name,))
    result = cursor.fetchone()
    if result:
        pid = result[0]
        # 2. Reset any ROMs using this profile back to 'Default' (ID 1)
        cursor.execute("UPDATE rom_profiles SET profile_id = 1 WHERE profile_id = ?", (pid,))
        # 3. Delete the profile
        cursor.execute("DELETE FROM profiles WHERE id = ?", (pid,))
        
    conn.commit()
    conn.close()
    return True

# --- FAVORITES LOGIC ---
def toggle_favorite(path):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM favorites WHERE path = ?", (path,))
    if cursor.fetchone():
        cursor.execute("DELETE FROM favorites WHERE path = ?", (path,))
    else:
        cursor.execute("INSERT INTO favorites (path) VALUES (?)", (path,))
    conn.commit()
    conn.close()

def get_favorites():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM favorites")
    favs = [row[0] for row in cursor.fetchall()]
    conn.close()
    return favs