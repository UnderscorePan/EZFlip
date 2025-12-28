def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcard_sets(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                    )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    image_path TEXT,
                    video_path TEXT,
                    FOREIGN KEY (set_id) REFERENCES flashcard_sets(id)
                    )
    ''')

    conn.commit()


def update_table_schema(conn):
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys = OFF;')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards_new(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    image_path TEXT,
                    video_path TEXT,
                    FOREIGN KEY (set_id) REFERENCES flashcard_sets(id)
                    )
    ''')

    cursor.execute('''
        INSERT INTO flashcards_new (id, set_id, word, definition, image_path, video_path)
        SELECT id, set_id, word, definition, image_path, video_path FROM flashcards
    ''')

    cursor.execute('DROP TABLE flashcards')
    cursor.execute('ALTER TABLE flashcards_new RENAME TO flashcards')

    cursor.execute('PRAGMA foreign_keys = ON;')
    conn.commit()


def add_set(conn, name):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO flashcard_sets (name)
        VALUES(?)
    ''', (name,))
    set_id = cursor.lastrowid
    conn.commit()
    return set_id


def add_card(conn, set_id, word, definition, image_path=None, video_path=None):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO flashcards (set_id, word, definition, image_path, video_path)
        VALUES(?, ?, ?, ?, ?)
    ''', (set_id, word, definition, image_path, video_path))
    card_id = cursor.lastrowid
    conn.commit()
    print(f"Added card with video_path: {video_path}")
    return card_id


def get_sets(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name FROM flashcard_sets
    ''')
    rows = cursor.fetchall()
    sets = {row[1]: row[0] for row in rows}
    return sets


def get_cards(conn, set_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT word, definition, image_path, video_path FROM flashcards
        WHERE set_id = ?
    ''', (set_id,))
    rows = cursor.fetchall()
    cards = [(row[0], row[1], row[2] if row[2] else '', row[3] if row[3] else '') for row in rows]
    for card in cards:
        print(f"Retrieved card with video_path: {card[3]}")
    return cards
