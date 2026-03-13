#!/usr/bin/env python3
"""One-time migration helper: legacy SQLite cafe rows -> PostgreSQL schema.

This script imports rows from `instance/cafes.db` (`cafe` table) into the new
PostgreSQL tables (`cafes`, `cafe_amenities`, `cafe_images`, `cafe_seats`).

Design goals:
- Safe re-runs (idempotent by legacy marker in description)
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


def _slugify(raw: str) -> str:
    text = unicodedata.normalize("NFKD", (raw or "").strip())
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:220] if text else "legacy-cafe"


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


def _normalize_pg_url(url: str) -> str:
    value = url.strip()
    value = value.replace("postgresql+asyncpg://", "postgresql://", 1)
    return value


def _load_legacy_rows(sqlite_path: Path) -> list[LegacyCafeRow]:
    conn = sqlite3.connect(str(sqlite_path))
    conn.row_factory = sqlite3.Row
    try:
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
    finally:
        conn.close()

    result: list[LegacyCafeRow] = []
    for row in rows:
        result.append(
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
    return result


def _marker_for(row: LegacyCafeRow) -> str:
    return f"[legacy_cafe_id:{row.legacy_id}]"


def _description_for(row: LegacyCafeRow, imported_at: datetime) -> str:
    detail = (row.details or "").strip()
    legacy_meta = (
        "\n\n---\n"
        f"{_marker_for(row)}\n"
        f"legacy_map_url: {row.map_url}\n"
        f"legacy_coffee_price: {row.coffee_price}\n"
        f"legacy_can_take_calls: {str(row.can_take_calls).lower()}\n"
        f"legacy_has_toilet: {str(row.has_toilet).lower()}\n"
        f"legacy_imported_at: {imported_at.isoformat()}"
    )
    return (detail + legacy_meta).strip()


def _existing_slug_set(cur) -> set[str]:
    cur.execute("SELECT slug FROM cafes")
    return {str(row[0]) for row in cur.fetchall() if row and row[0]}


def _make_unique_slug(base_slug: str, known: set[str]) -> str:
    slug = base_slug
    index = 2
    while slug in known:
        suffix = f"-{index}"
        cut = 220 - len(suffix)
        slug = f"{base_slug[:cut]}{suffix}"
        index += 1
    known.add(slug)
    return slug


def _legacy_already_imported(cur, marker: str) -> bool:
    cur.execute("SELECT 1 FROM cafes WHERE description ILIKE %s LIMIT 1", (f"%{marker}%",))
    return cur.fetchone() is not None


def _find_or_create_neighborhood(cur, cache: dict[str, str], location: str, dry_run: bool) -> Optional[str]:
    clean = (location or "").strip()
    if not clean:
        return None

    slug = _slugify(clean)
    if slug in cache:
        return cache[slug]

    cur.execute("SELECT id::text FROM neighborhoods WHERE slug = %s LIMIT 1", (slug,))
    found = cur.fetchone()
    if found:
        cache[slug] = str(found[0])
        return cache[slug]

    if dry_run:
        cache[slug] = "<dry-run-neighborhood>"
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

    rows = _load_legacy_rows(sqlite_path)
    if not rows:
        print("[ok] Legacy cafe tablosu bos, tasinacak veri yok.")
        return 0

    print(f"[info] Legacy satir sayisi: {len(rows)}")
    print(f"[info] Dry-run: {'evet' if dry_run else 'hayir'}")

    inserted = 0
    skipped = 0
    failed = 0
    parsed_coordinates = 0
    fallback_coordinates = 0
    neighborhood_cache: dict[str, str] = {}

    conn = psycopg2.connect(pg_url)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            known_slugs = _existing_slug_set(cur)

            for row in rows:
                marker = _marker_for(row)
                try:
                    if _legacy_already_imported(cur, marker):
                        skipped += 1
                        continue

                    created_at = _parse_datetime(row.created_at)
                    updated_at = _parse_datetime(row.updated_at)
                    imported_at = datetime.now(timezone.utc)
                    lat, lng, parsed_ok = _extract_lat_lng(row.map_url)
                    if parsed_ok:
                        parsed_coordinates += 1
                    else:
                        fallback_coordinates += 1

                    neighborhood_id = _find_or_create_neighborhood(
                        cur, neighborhood_cache, row.location, dry_run=dry_run
                    )
                    seat_count = _extract_seat_count(row.seats)
                    slug = _make_unique_slug(_slugify(row.name), known_slugs)
                    description = _description_for(row, imported_at)

                    if dry_run:
                        inserted += 1
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
                            None if neighborhood_id == "<dry-run-neighborhood>" else neighborhood_id,
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
                            row.can_take_calls or True,
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
                            f"legacy_seats={row.seats}; legacy_coffee_price={row.coffee_price}",
                        ),
                    )

                    inserted += 1
                except Exception as exc:  # noqa: BLE001 - migration helper should continue if configured
                    failed += 1
                    print(f"[warn] Satir gecilemedi (legacy_id={row.legacy_id}): {exc}")
                    conn.rollback()
                    if fail_fast:
                        raise
                    # Re-open cursor state after rollback.
                    with conn.cursor() as recovery_cur:
                        known_slugs = _existing_slug_set(recovery_cur)
                    continue

            if dry_run:
                conn.rollback()
            else:
                conn.commit()

    finally:
        conn.close()

    print("[summary]")
    print(f"- eklenecek/eklenen: {inserted}")
    print(f"- atlanan (zaten import): {skipped}")
    print(f"- hatali: {failed}")
    print(f"- koordinat parse basarili: {parsed_coordinates}")
    print(f"- koordinat fallback kullanildi: {fallback_coordinates}")

    return 0 if failed == 0 else 2


def _parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy SQLite cafes into PostgreSQL cafes schema."
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
