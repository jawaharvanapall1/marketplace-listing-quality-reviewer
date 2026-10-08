"""Thin DB layer: MySQL in production (mysql-connector), SQLite for local dev/tests. No ORM."""
import json, sqlite3, threading, time
from urllib.parse import urlparse, unquote

AUTO = {"mysql": "INT AUTO_INCREMENT PRIMARY KEY", "sqlite": "INTEGER PRIMARY KEY AUTOINCREMENT"}

def ddl(kind):
    a, tail = AUTO[kind], (" ENGINE=InnoDB DEFAULT CHARSET=utf8mb4" if kind == "mysql" else "")
    return [
        f"""CREATE TABLE IF NOT EXISTS listings (
            id {a}, title VARCHAR(500) NOT NULL, description TEXT, category VARCHAR(100), price VARCHAR(32),
            attributes TEXT, seller VARCHAR(200), tags TEXT, created_at BIGINT NOT NULL){tail}""",
        f"""CREATE TABLE IF NOT EXISTS reviews (
            id {a}, listing_id INT NOT NULL, mode VARCHAR(16) NOT NULL, note TEXT, dropped INT NOT NULL DEFAULT 0,
            validation LONGTEXT, findings LONGTEXT, retrieved LONGTEXT, created_at BIGINT NOT NULL,
            FOREIGN KEY (listing_id) REFERENCES listings(id)){tail}""",
        f"""CREATE TABLE IF NOT EXISTS revisions (
            id {a}, review_id INT NOT NULL, listing_id INT NOT NULL, field_name VARCHAR(32) NOT NULL,
            original TEXT, suggested TEXT, final_text TEXT, status VARCHAR(16) NOT NULL DEFAULT 'pending',
            updated_at BIGINT NOT NULL, FOREIGN KEY (review_id) REFERENCES reviews(id)){tail}""",
        f"""CREATE TABLE IF NOT EXISTS history_events (
            id {a}, listing_id INT NOT NULL, review_id INT NULL, field_name VARCHAR(32), action VARCHAR(40) NOT NULL,
            before_text TEXT, after_text TEXT, created_at BIGINT NOT NULL){tail}""",
    ]

class DB:
    def __init__(self, url):
        self.kind = "mysql" if url.startswith("mysql") else "sqlite"
        self.url, self._lock = url, threading.RLock()
        if self.kind == "sqlite":
            path = url.replace("sqlite:///", "", 1)
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        for stmt in ddl(self.kind):
            self.execute(stmt)

    def _mysql(self):
        import mysql.connector
        u = urlparse(self.url)
        return mysql.connector.connect(host=u.hostname, port=u.port or 3306, user=unquote(u.username or ""),
                                       password=unquote(u.password or ""), database=u.path.lstrip("/"), charset="utf8mb4")

    def _run(self, sql, params, fetch):
        with self._lock:
            if self.kind == "sqlite":
                cur = self._conn.execute(sql.replace("%s", "?"), params)
                rows = [dict(r) for r in cur.fetchall()] if fetch else None
                self._conn.commit()
                return rows, cur.lastrowid
            conn = self._mysql()
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute(sql, params)
                rows = cur.fetchall() if fetch else None
                conn.commit()
                return rows, cur.lastrowid
            finally:
                conn.close()

    def query(self, sql, params=()):
        return self._run(sql, params, True)[0]

    def one(self, sql, params=()):
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql, params=()):
        return self._run(sql, params, False)[1]

now = lambda: int(time.time() * 1000)
dumps = lambda v: json.dumps(v, ensure_ascii=False)
loads = lambda s: json.loads(s) if s else None
