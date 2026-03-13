#!/usr/bin/env python3
"""One-time migration helper: legacy SQLite -> PostgreSQL.

Migrates legacy tables from `instance/cafes.db`:
- user      -> users
- cafe      -> cafes + cafe_amenities + cafe_images + cafe_seats
- user_cafe -> bookmarks

Design goals:
- Safe re-runs (idempotent for users by email, cafes by legacy marker)
- Dry-run support
- Minimal assumptions about legacy data quality
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import psycopg2


DEFAULT_SQLITE_PATH = Path("instance/cafes.db")
DEFAULT_LATITUDE = 41.015137
DEFAULT_LONGITUDE = 28.979530
LEGACY_EMAIL_DOMAIN = "legacy.local"


@dataclass
class LegacyUserRow:
    legacy_id: int
    name: str
    email: str
    is_admin: bool
    is_confirmed: bool
    confirmed_on: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class LegacyCafeRow:
    legacy_id: int
    name: str
    map_url: str
    img_url: str
    location: str
    has_sockets: bool
    has_toilet: bool
    has_wifi: bool
    can_take_calls: bool
    seats: str
    coffee_price: str
    details: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class LegacyUserCafeRow:
    user_id: int
    cafe_id: int


@dataclass
class MigrationStats:
    users_total: int = 0
    users_inserted: int = 0
    users_existing: int = 0
    users_failed: int = 0
    cafes_total: int = 0
    cafes_inserted: int = 0
    cafes_skipped: int = 0
    cafes_failed: int = 0
    bookmarks_total: int = 0
    bookmarks_inserted: int = 0
    bookmarks_skipped: int = 0
    bookmarks_missing_refs: int = 0
    parsed_coordinates: int = 0
    fallback_coordinates: int = 0


def _boolify(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "t", "yes", "y"}:
            return True
        if v in {"0", "false", "f", "no", "n", ""}:
            return False
    return False


def _slugify(raw: str, *, fallback: str = "legacy") -> str:
    text = unicodedata.normalize("NFKD", (raw or "").strip())
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text if text else fallback


def _usernameify(raw: str, *, fallback: str = "legacy-user") -> str:
    text = unicodedata.normalize("NFKD", (raw or "").strip())
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9._-]+", "", text)
    text = text.strip("._-")
    if not text:
        text = fallback
    return text[:50]


def _parse_datetime(raw: Optional[str]) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)

    candidate = raw.strip()
    if not candidate:
        return datetime.now(timezone.utc)

    candidate = candidate.replace(" ", "T")
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    try:
        value = datetime.fromisoformat(candidate)
    except ValueError:
        return datetime.now(timezone.utc)

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _extract_lat_lng(map_url: str) -> tuple[float, float, bool]:
    text = (map_url or "").strip()
    if not text:
        return DEFAULT_LATITUDE, DEFAULT_LONGITUDE, False

    patterns = [
        re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)"),
        re.compile(r"[?&]q=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)"),
        re.compile(r"[?&]ll=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)"),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        return float(match.group(1)), float(match.group(2)), True

    return DEFAULT_LATITUDE, DEFAULT_LONGITUDE, False


def _extract_seat_count(seats_text: str) -> int:
    text = (seats_text or "").strip()
    if not text:
        return 0
    nums = [int(x) for x in re.findall(r"\d+", text)]
    if not nums:
        return 0
    if "+" in text:
        return nums[0]
    if len(nums) >= 2:
        return max(0, (nums[0] + nums[1]) // 2)
    return nums[0]


def _normalize_pg_url(url: str) -> str:
    value = url.strip()
    return value.replace("postgresql+asyncpg://", "postgresql://", 1)


def _pick_pg_url(explicit_url: Optional[str]) -> str:
    for candidate in (
        explicit_url,
        os.getenv("DATABASE_URL_DEV"),
        os.getenv("DATABASE_URL"),
        os.getenv("DATABASE_URL_PROD"),
    ):
        if candidate:
            return _normalize_pg_url(candidate)
    raise ValueError(
        "PostgreSQL URL bulunamadi. --pg-url verin veya DATABASE_URL_DEV / DATABASE_URL ayarlayin."
    )


def _sqlite_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _load_legacy_data(
    sqlite_path: Path,
) -> tuple[list[LegacyUserRow], list[LegacyCafeRow], list[LegacyUserCafeRow]]:
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    try:
        users: list[LegacyUserRow] = []
        cafes: list[LegacyCafeRow] = []
        user_cafes: list[LegacyUserCafeRow] = []

        if _sqlite_table_exists(conn, "user"):
            rows = conn.execute(
                """
                SELECT
                    id, name, email, is_admin, is_confirmed,
                    confirmed_on, created_at, updated_at
                FROM user
                ORDER BY id ASC
                """
            ).fetchall()
            for row in rows:
                users.append(
                    LegacyUserRow(
                        legacy_id=int(row["id"]),
                        name=str(row["name"] or "").strip(),
                        email=str(row["email"] or "").strip().lower(),
                        is_admin=_boolify(row["is_admin"]),
                        is_confirmed=_boolify(row["is_confirmed"]),
                        confirmed_on=str(row["confirmed_on"]) if row["confirmed_on"] is not None else None,
                        created_at=str(row["created_at"]) if row["created_at"] is not None else None,
                        updated_at=str(row["updated_at"]) if row["updated_at"] is not None else None,
                    )
                )

        if _sqlite_table_exists(conn, "cafe"):
            rows = conn.execute(
                """
                SELECT
                    id, name, map_url, img_url, location,
                    has_sockets, has_toilet, has_wifi, can_take_calls,
                    seats, coffee_price, details, created_at, updated_at
                FROM cafe
                ORDER BY id ASC
                """
            ).fetchall()
            for row in rows:
                cafes.append(
                    LegacyCafeRow(
                        legacy_id=int(row["id"]),
                        name=str(row["name"] or "").strip(),
                        map_url=str(row["map_url"] or "").strip(),
                        img_url=str(row["img_url"] or "").strip(),
                        location=str(row["location"] or "").strip(),
                        has_sockets=_boolify(row["has_sockets"]),
                        has_toilet=_boolify(row["has_toilet"]),
                        has_wifi=_boolify(row["has_wifi"]),
                        can_take_calls=_boolify(row["can_take_calls"]),
                        seats=str(row["seats"] or "").strip(),
                        coffee_price=str(row["coffee_price"] or "").strip(),
                        details=str(row["details"]) if row["details"] is not None else None,
                        created_at=str(row["created_at"]) if row["created_at"] is not None else None,
                        updated_at=str(row["updated_at"]) if row["updated_at"] is not None else None,
                    )
                )

        if _sqlite_table_exists(conn, "user_cafe"):
            rows = conn.execute(
                "SELECT user_id, cafe_id FROM user_cafe ORDER BY user_id ASC, cafe_id ASC"
            ).fetchall()
            for row in rows:
                user_cafes.append(
                    LegacyUserCafeRow(
                        user_id=int(row["user_id"]),
                        cafe_id=int(row["cafe_id"]),
                    )
                )

        return users, cafes, user_cafes
    finally:
        conn.close()


def _fetch_existing_users(cur) -> tuple[dict[str, str], set[str], set[str]]:
    cur.execute("SELECT id::text, email, username FROM users")
    email_to_id: dict[str, str] = {}
    used_usernames: set[str] = set()
    used_emails: set[str] = set()
    for row in cur.fetchall():
        user_id = str(row[0])
        email = str(row[1] or "").strip().lower()
        username = str(row[2] or "").strip().lower()
        if email:
            email_to_id[email] = user_id
            used_emails.add(email)
        if username:
            used_usernames.add(username)
    return email_to_id, used_usernames, used_emails


def _fetch_imported_legacy_cafes(cur) -> dict[int, str]:
    cur.execute(
        """
        SELECT id::text, description
        FROM cafes
        WHERE description ILIKE '%[legacy_cafe_id:%'
        """
    )
    mapping: dict[int, str] = {}
    pattern = re.compile(r"\[legacy_cafe_id:(\d+)\]")
    for row in cur.fetchall():
        cafe_id = str(row[0])
        description = str(row[1] or "")
        match = pattern.search(description)
        if not match:
            continue
        mapping[int(match.group(1))] = cafe_id
    return mapping


def _existing_slug_set(cur) -> set[str]:
    cur.execute("SELECT slug FROM cafes")
    return {str(row[0]) for row in cur.fetchall() if row and row[0]}


def _make_unique_slug(base_slug: str, known: set[str]) -> str:
    slug = base_slug[:220] or "legacy-cafe"
    index = 2
    while slug in known:
        suffix = f"-{index}"
        cut = 220 - len(suffix)
        slug = f"{base_slug[:cut]}{suffix}"
        index += 1
    known.add(slug)
    return slug


def _make_unique_username(base_username: str, used_usernames: set[str]) -> str:
    username = base_username[:50] or "legacy-user"
    index = 2
    while username in used_usernames:
        suffix = f"-{index}"
        cut = 50 - len(suffix)
        username = f"{base_username[:cut]}{suffix}"
        index += 1
    used_usernames.add(username)
    return username


def _make_unique_email(base_email: str, used_emails: set[str]) -> str:
    email = base_email
    if email not in used_emails:
        used_emails.add(email)
        return email

    local, _, domain = email.partition("@")
    if not local:
        local = "legacy-user"
    if not domain:
        domain = LEGACY_EMAIL_DOMAIN

    index = 2
    while True:
        candidate = f"{local}+{index}@{domain}"
        if candidate not in used_emails:
            used_emails.add(candidate)
            return candidate
        index += 1


def _safe_legacy_email(row: LegacyUserRow) -> str:
    candidate = (row.email or "").strip().lower()
    if "@" in candidate and "." in candidate.split("@")[-1]:
        return candidate
    return f"legacy-user-{row.legacy_id}@{LEGACY_EMAIL_DOMAIN}"


def _marker_for_cafe(row: LegacyCafeRow) -> str:
    return f"[legacy_cafe_id:{row.legacy_id}]"


def _description_for_cafe(row: LegacyCafeRow, imported_at: datetime) -> str:
    detail = (row.details or "").strip()
    legacy_meta = (
        "\n\n---\n"
        f"{_marker_for_cafe(row)}\n"
        f"legacy_map_url: {row.map_url}\n"
        f"legacy_coffee_price: {row.coffee_price}\n"
        f"legacy_can_take_calls: {str(row.can_take_calls).lower()}\n"
        f"legacy_has_toilet: {str(row.has_toilet).lower()}\n"
        f"legacy_imported_at: {imported_at.isoformat()}"
    )
    return (detail + legacy_meta).strip()


def _find_or_create_neighborhood(cur, cache: dict[str, str], location: str, dry_run: bool) -> Optional[str]:
    clean = (location or "").strip()
    if not clean:
        return None

    slug = _slugify(clean, fallback="legacy-neighborhood")[:120]
    if slug in cache:
        return cache[slug]

    cur.execute("SELECT id::text FROM neighborhoods WHERE slug = %s LIMIT 1", (slug,))
    found = cur.fetchone()
    if found:
        cache[slug] = str(found[0])
        return cache[slug]

    if dry_run:
        cache[slug] = f"<dry-neighborhood:{slug}>"
        return cache[slug]

    cur.execute(
        """
        INSERT INTO neighborhoods (name, city, district, slug, is_active, created_at)
        VALUES (%s, %s, %s, %s, true, now())
        RETURNING id::text
        """,
        (clean, "Legacy", None, slug),
    )
    created = cur.fetchone()
    cache[slug] = str(created[0])
    return cache[slug]


def _migrate_users(
    cur,
    *,
    users: list[LegacyUserRow],
    dry_run: bool,
    fail_fast: bool,
    stats: MigrationStats,
) -> dict[int, str]:
    user_map: dict[int, str] = {}
    email_to_id, used_usernames, used_emails = _fetch_existing_users(cur)

    for row in users:
        stats.users_total += 1
        try:
            safe_email = _safe_legacy_email(row)
            if safe_email in email_to_id:
                user_map[row.legacy_id] = email_to_id[safe_email]
                stats.users_existing += 1
                continue

            base_username = _usernameify(
                raw=row.email.split("@")[0] if "@" in row.email else row.name,
                fallback=f"legacy-user-{row.legacy_id}",
            )
            username = _make_unique_username(base_username, used_usernames)
            email = _make_unique_email(safe_email, used_emails)
            role = "admin" if row.is_admin else "user"
            created_at = _parse_datetime(row.created_at)
            updated_at = _parse_datetime(row.updated_at)
            email_verified_at = _parse_datetime(row.confirmed_on) if row.is_confirmed and row.confirmed_on else None

            if dry_run:
                fake_id = f"<dry-user:{row.legacy_id}>"
                user_map[row.legacy_id] = fake_id
                email_to_id[email] = fake_id
                stats.users_inserted += 1
                continue

            cur.execute(
                """
                INSERT INTO users (
                    email, username, display_name, role,
                    avatar_url, email_verified_at, is_active,
                    created_at, updated_at, deleted_at
                )
                VALUES (%s, %s, %s, %s, NULL, %s, true, %s, %s, NULL)
                RETURNING id::text
                """,
                (
                    email,
                    username,
                    row.name or None,
                    role,
                    email_verified_at,
                    created_at,
                    updated_at,
                ),
            )
            user_id = str(cur.fetchone()[0])
            user_map[row.legacy_id] = user_id
            email_to_id[email] = user_id
            stats.users_inserted += 1
        except Exception as exc:  # noqa: BLE001
            stats.users_failed += 1
            print(f"[warn] User satiri gecilemedi (legacy_user_id={row.legacy_id}): {exc}")
            if fail_fast:
                raise
    return user_map


def _migrate_cafes(
    cur,
    *,
    cafes: list[LegacyCafeRow],
    dry_run: bool,
    fail_fast: bool,
    stats: MigrationStats,
) -> dict[int, str]:
    cafe_map = _fetch_imported_legacy_cafes(cur)
    neighborhood_cache: dict[str, str] = {}
    known_slugs = _existing_slug_set(cur)

    for row in cafes:
        stats.cafes_total += 1
        marker = _marker_for_cafe(row)
        if row.legacy_id in cafe_map:
            stats.cafes_skipped += 1
            continue

        try:
            created_at = _parse_datetime(row.created_at)
            updated_at = _parse_datetime(row.updated_at)
            imported_at = datetime.now(timezone.utc)
            lat, lng, parsed_ok = _extract_lat_lng(row.map_url)
            if parsed_ok:
                stats.parsed_coordinates += 1
            else:
                stats.fallback_coordinates += 1

            neighborhood_id = _find_or_create_neighborhood(
                cur, neighborhood_cache, row.location, dry_run=dry_run
            )
            seat_count = _extract_seat_count(row.seats)
            slug = _make_unique_slug(_slugify(row.name, fallback=f"legacy-cafe-{row.legacy_id}"), known_slugs)
            description = _description_for_cafe(row, imported_at)

            if dry_run:
                cafe_map[row.legacy_id] = f"<dry-cafe:{row.legacy_id}>"
                stats.cafes_inserted += 1
                continue

            cur.execute(
                """
                INSERT INTO cafes (
                    owner_id, neighborhood_id, name, slug, description,
                    address, latitude, longitude, phone, website, instagram, google_maps_url,
                    is_verified, is_active, status,
                    total_capacity, indoor_capacity, outdoor_capacity,
                    avg_rating, review_count,
                    created_at, updated_at, deleted_at
                )
                VALUES (
                    NULL, %s, %s, %s, %s,
                    %s, %s, %s, NULL, NULL, NULL, %s,
                    false, true, 'active',
                    %s, %s, NULL,
                    0, 0,
                    %s, %s, NULL
                )
                RETURNING id::text
                """,
                (
                    None if neighborhood_id and neighborhood_id.startswith("<dry-neighborhood:") else neighborhood_id,
                    row.name or f"Legacy Cafe {row.legacy_id}",
                    slug,
                    description,
                    row.location or "Legacy location",
                    lat,
                    lng,
                    row.map_url or None,
                    seat_count,
                    seat_count,
                    created_at,
                    updated_at,
                ),
            )
            cafe_id = str(cur.fetchone()[0])
            cafe_map[row.legacy_id] = cafe_id

            cur.execute(
                """
                INSERT INTO cafe_amenities (
                    cafe_id, wifi_available, outlet_count, outlet_accessibility,
                    allows_laptop, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (cafe_id) DO NOTHING
                """,
                (
                    cafe_id,
                    row.has_wifi,
                    1 if row.has_sockets else 0,
                    "some_seats" if row.has_sockets else "none",
                    bool(row.can_take_calls),
                ),
            )

            if row.img_url:
                cur.execute(
                    """
                    INSERT INTO cafe_images (
                        cafe_id, uploaded_by, url, alt_text, is_primary, sort_order, created_at
                    )
                    VALUES (%s, NULL, %s, %s, true, 0, %s)
                    """,
                    (
                        cafe_id,
                        row.img_url,
                        f"{row.name} - legacy image",
                        created_at,
                    ),
                )

            cur.execute(
                """
                INSERT INTO cafe_seats (
                    cafe_id, seat_type, total_count, available_count, has_outlet, notes, updated_at
                )
                VALUES (%s, 'shared_table', %s, %s, %s, %s, now())
                """,
                (
                    cafe_id,
                    seat_count,
                    seat_count,
                    row.has_sockets,
                    f"legacy_seats={row.seats}; legacy_coffee_price={row.coffee_price}; marker={marker}",
                ),
            )

            stats.cafes_inserted += 1
        except Exception as exc:  # noqa: BLE001
            stats.cafes_failed += 1
            print(f"[warn] Cafe satiri gecilemedi (legacy_cafe_id={row.legacy_id}): {exc}")
            if fail_fast:
                raise

    return cafe_map


def _migrate_bookmarks(
    cur,
    *,
    links: list[LegacyUserCafeRow],
    user_map: dict[int, str],
    cafe_map: dict[int, str],
    dry_run: bool,
    stats: MigrationStats,
) -> None:
    for link in links:
        stats.bookmarks_total += 1
        user_id = user_map.get(link.user_id)
        cafe_id = cafe_map.get(link.cafe_id)
        if not user_id or not cafe_id:
            stats.bookmarks_missing_refs += 1
            continue

        if dry_run:
            stats.bookmarks_inserted += 1
            continue

        cur.execute(
            """
            INSERT INTO bookmarks (user_id, cafe_id, created_at)
            VALUES (%s, %s, now())
            ON CONFLICT (user_id, cafe_id) DO NOTHING
            """,
            (user_id, cafe_id),
        )
        if cur.rowcount > 0:
            stats.bookmarks_inserted += 1
        else:
            stats.bookmarks_skipped += 1


def migrate(
    *,
    sqlite_path: Path,
    pg_url: str,
    dry_run: bool,
    fail_fast: bool,
) -> int:
    if not sqlite_path.exists():
        print(f"[error] SQLite dosyasi bulunamadi: {sqlite_path}")
        return 1

    users, cafes, user_cafes = _load_legacy_data(sqlite_path)
    if not users and not cafes:
        print("[ok] Legacy tablolar bos, tasinacak veri yok.")
        return 0

    print(f"[info] Legacy users: {len(users)}")
    print(f"[info] Legacy cafes: {len(cafes)}")
    print(f"[info] Legacy user_cafe links: {len(user_cafes)}")
    print(f"[info] Dry-run: {'evet' if dry_run else 'hayir'}")

    stats = MigrationStats()

    conn = psycopg2.connect(pg_url)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            try:
                user_map = _migrate_users(
                    cur,
                    users=users,
                    dry_run=dry_run,
                    fail_fast=fail_fast,
                    stats=stats,
                )
                cafe_map = _migrate_cafes(
                    cur,
                    cafes=cafes,
                    dry_run=dry_run,
                    fail_fast=fail_fast,
                    stats=stats,
                )
                _migrate_bookmarks(
                    cur,
                    links=user_cafes,
                    user_map=user_map,
                    cafe_map=cafe_map,
                    dry_run=dry_run,
                    stats=stats,
                )
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                print(f"[error] Migration rollback edildi: {exc}")
                return 2

            if dry_run:
                conn.rollback()
            else:
                conn.commit()
    finally:
        conn.close()

    print("[summary]")
    print(
        f"- users: total={stats.users_total}, inserted={stats.users_inserted}, "
        f"existing={stats.users_existing}, failed={stats.users_failed}"
    )
    print(
        f"- cafes: total={stats.cafes_total}, inserted={stats.cafes_inserted}, "
        f"skipped={stats.cafes_skipped}, failed={stats.cafes_failed}"
    )
    print(
        f"- bookmarks: total={stats.bookmarks_total}, inserted={stats.bookmarks_inserted}, "
        f"skipped={stats.bookmarks_skipped}, missing_refs={stats.bookmarks_missing_refs}"
    )
    print(
        f"- coordinates: parsed={stats.parsed_coordinates}, fallback={stats.fallback_coordinates}"
    )

    return 0 if (stats.users_failed == 0 and stats.cafes_failed == 0) else 2


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy SQLite data into PostgreSQL schema."
    )
    parser.add_argument(
        "--sqlite-path",
        default=str(DEFAULT_SQLITE_PATH),
        help=f"Legacy SQLite dosya yolu (default: {DEFAULT_SQLITE_PATH})",
    )
    parser.add_argument(
        "--pg-url",
        default=None,
        help="PostgreSQL baglanti adresi (postgresql://...). verilmezse env degiskenlerinden okunur.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Yazma yapmadan import planini hesapla.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Ilk hatada islemi durdur.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = _parse_args(argv)
    sqlite_path = Path(args.sqlite_path)

    try:
        pg_url = _pick_pg_url(args.pg_url)
    except ValueError as exc:
        print(f"[error] {exc}")
        return 1

    return migrate(
        sqlite_path=sqlite_path,
        pg_url=pg_url,
        dry_run=bool(args.dry_run),
        fail_fast=bool(args.fail_fast),
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
