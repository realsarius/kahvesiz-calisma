#!/usr/bin/env python3
"""Seed development data for PostgreSQL (FastAPI schema).

Creates/updates:
- 1 admin user
- a few normal users
- neighborhoods
- cafes + amenities + hours + images + seats
- bookmarks
- sample reviews + review votes

Safe for re-run:
- users upsert by email
- neighborhoods upsert by slug
- cafes upsert by slug
- bookmarks/reviews/review_votes upsert by unique constraints
- seed-only seats/images/hours are refreshed using [seed] marker
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable

import psycopg2


SEED_MARKER = "[seed]"
TARGET_CAFE_COUNT = 120
GENERATED_USER_COUNT = 64


USERS = [
    {
        "email": "admin@kahvesiz.local",
        "username": "admin",
        "display_name": "Kahvesiz Admin",
        "role": "admin",
        "city": "Istanbul",
    },
    {
        "email": "zeynep@kahvesiz.local",
        "username": "zeynep",
        "display_name": "Zeynep",
        "role": "user",
        "city": "Istanbul",
    },
    {
        "email": "mert@kahvesiz.local",
        "username": "mert",
        "display_name": "Mert",
        "role": "user",
        "city": "Istanbul",
    },
    {
        "email": "ayse@kahvesiz.local",
        "username": "ayse",
        "display_name": "Ayse",
        "role": "user",
        "city": "Istanbul",
    },
]


def _slugify(value: str) -> str:
    base = (value or "").strip().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return base


def _build_generated_users(count: int) -> list[dict]:
    generated: list[dict] = []
    first_names = [
        "Ayse",
        "Mehmet",
        "Fatma",
        "Can",
        "Elif",
        "Deniz",
        "Berk",
        "Zehra",
        "Merve",
        "Kaan",
        "Seda",
        "Emre",
        "Ece",
        "Ali",
        "Derya",
        "Onur",
    ]
    last_names = [
        "Yilmaz",
        "Demir",
        "Kaya",
        "Celik",
        "Sahin",
        "Aydin",
        "Arslan",
        "Ozdemir",
        "Koc",
        "Kurt",
        "Aslan",
        "Cetin",
        "Acar",
        "Polat",
        "Bulut",
        "Tas",
    ]
    for index in range(1, count + 1):
        first = first_names[(index - 1) % len(first_names)]
        last = last_names[((index - 1) // len(first_names)) % len(last_names)]
        generated.append(
            {
                "email": f"devuser{index:03d}@kahvesiz.local",
                "username": f"devuser{index:03d}",
                "display_name": f"{first} {last}",
                "role": "user",
                "city": "Istanbul",
            }
        )
    return generated


USERS.extend(_build_generated_users(GENERATED_USER_COUNT))


NEIGHBORHOODS = [
    {"name": "Moda", "city": "Istanbul", "district": "Kadikoy", "slug": "moda"},
    {"name": "Besiktas Merkez", "city": "Istanbul", "district": "Besiktas", "slug": "besiktas-merkez"},
    {"name": "Cihangir", "city": "Istanbul", "district": "Beyoglu", "slug": "cihangir"},
]


CAFES = [
    {
        "name": "Monk Brew Lab",
        "slug": "monk-brew-lab",
        "neighborhood_slug": "moda",
        "owner_email": "admin@kahvesiz.local",
        "address": "Moda Caddesi No:11, Kadikoy",
        "latitude": 40.98341,
        "longitude": 29.02675,
        "phone": "+90 216 000 00 11",
        "website": "https://example.com/monk-brew-lab",
        "google_maps_url": "https://maps.google.com/?q=40.98341,29.02675",
        "status": "active",
        "total_capacity": 58,
        "indoor_capacity": 42,
        "outdoor_capacity": 16,
        "amenity": {
            "wifi_available": True,
            "wifi_speed_mbps": 130,
            "outlet_count": 24,
            "outlet_accessibility": "some_seats",
            "noise_level": "moderate",
            "has_natural_light": True,
            "has_ac": True,
            "has_heating": True,
            "has_parking": False,
            "has_accessible_entry": True,
            "allows_laptop": True,
            "min_spend_try": 120.0,
            "has_food": True,
            "has_alcohol": False,
            "pet_friendly": True,
        },
        "hours": [(0, "08:00", "22:00"), (1, "08:00", "22:00"), (2, "08:00", "22:00"), (3, "08:00", "22:00"), (4, "08:00", "23:00"), (5, "09:00", "23:00"), (6, "09:00", "22:00")],
        "images": [
            "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085",
            "https://images.unsplash.com/photo-1509042239860-f550ce710b93",
        ],
        "seats": [
            ("shared_table", 20, 15, True, f"{SEED_MARKER} ortak masa"),
            ("solo_desk", 12, 8, True, f"{SEED_MARKER} tek kisilik masa"),
            ("outdoor", 10, 6, False, f"{SEED_MARKER} dis alan"),
        ],
    },
    {
        "name": "Northlight Study Cafe",
        "slug": "northlight-study-cafe",
        "neighborhood_slug": "besiktas-merkez",
        "owner_email": "admin@kahvesiz.local",
        "address": "Sinanpasa Mah. No:7, Besiktas",
        "latitude": 41.04322,
        "longitude": 29.00577,
        "phone": "+90 212 000 00 77",
        "website": "https://example.com/northlight",
        "google_maps_url": "https://maps.google.com/?q=41.04322,29.00577",
        "status": "active",
        "total_capacity": 46,
        "indoor_capacity": 40,
        "outdoor_capacity": 6,
        "amenity": {
            "wifi_available": True,
            "wifi_speed_mbps": 180,
            "outlet_count": 36,
            "outlet_accessibility": "all_seats",
            "noise_level": "quiet",
            "has_natural_light": True,
            "has_ac": True,
            "has_heating": True,
            "has_parking": True,
            "has_accessible_entry": True,
            "allows_laptop": True,
            "min_spend_try": 140.0,
            "has_food": True,
            "has_alcohol": False,
            "pet_friendly": False,
        },
        "hours": [(0, "07:30", "22:30"), (1, "07:30", "22:30"), (2, "07:30", "22:30"), (3, "07:30", "22:30"), (4, "07:30", "23:00"), (5, "08:00", "23:00"), (6, "08:00", "22:00")],
        "images": [
            "https://images.unsplash.com/photo-1445116572660-236099ec97a0",
            "https://images.unsplash.com/photo-1453614512568-c4024d13c247",
        ],
        "seats": [
            ("shared_table", 18, 12, True, f"{SEED_MARKER} ortak masa"),
            ("solo_desk", 14, 10, True, f"{SEED_MARKER} sessiz alan"),
            ("bar", 8, 5, True, f"{SEED_MARKER} bar alani"),
        ],
    },
    {
        "name": "Cihangir Corner",
        "slug": "cihangir-corner",
        "neighborhood_slug": "cihangir",
        "owner_email": "admin@kahvesiz.local",
        "address": "Susam Sok. No:4, Cihangir",
        "latitude": 41.03312,
        "longitude": 28.98657,
        "phone": "+90 212 000 00 44",
        "website": "https://example.com/cihangir-corner",
        "google_maps_url": "https://maps.google.com/?q=41.03312,28.98657",
        "status": "active",
        "total_capacity": 34,
        "indoor_capacity": 26,
        "outdoor_capacity": 8,
        "amenity": {
            "wifi_available": True,
            "wifi_speed_mbps": 95,
            "outlet_count": 10,
            "outlet_accessibility": "rare",
            "noise_level": "loud",
            "has_natural_light": False,
            "has_ac": True,
            "has_heating": True,
            "has_parking": False,
            "has_accessible_entry": False,
            "allows_laptop": True,
            "min_spend_try": 100.0,
            "has_food": True,
            "has_alcohol": True,
            "pet_friendly": True,
        },
        "hours": [(0, "09:00", "21:00"), (1, "09:00", "21:00"), (2, "09:00", "21:00"), (3, "09:00", "21:00"), (4, "09:00", "22:00"), (5, "09:30", "22:00"), (6, "09:30", "21:00")],
        "images": [
            "https://images.unsplash.com/photo-1414235077428-338989a2e8c0",
            "https://images.unsplash.com/photo-1498804103079-a6351b050096",
        ],
        "seats": [
            ("shared_table", 12, 7, False, f"{SEED_MARKER} ortak masa"),
            ("sofa", 6, 4, False, f"{SEED_MARKER} kanepe"),
            ("outdoor", 8, 5, False, f"{SEED_MARKER} sokak masasi"),
        ],
    },
    {
        "name": "Starbuck Kafe",
        "slug": "starbuck-kafe",
        "neighborhood_slug": "moda",
        "owner_email": "admin@kahvesiz.local",
        "address": "Moda Iskele Sok. No:9, Kadikoy",
        "latitude": 40.98391,
        "longitude": 29.02811,
        "phone": "+90 216 111 11 11",
        "website": "https://example.com/starbuck-kafe",
        "instagram": "starbuckkafe",
        "google_maps_url": "https://maps.google.com/?q=40.98391,29.02811",
        "status": "active",
        "total_capacity": 52,
        "indoor_capacity": 39,
        "outdoor_capacity": 13,
        "amenity": {
            "wifi_available": True,
            "wifi_speed_mbps": 150,
            "outlet_count": 26,
            "outlet_accessibility": "some_seats",
            "noise_level": "moderate",
            "has_natural_light": True,
            "has_ac": True,
            "has_heating": True,
            "has_parking": False,
            "has_accessible_entry": True,
            "allows_laptop": True,
            "min_spend_try": 130.0,
            "has_food": True,
            "has_alcohol": False,
            "pet_friendly": False,
        },
        "hours": [(0, "08:00", "22:00"), (1, "08:00", "22:00"), (2, "08:00", "22:00"), (3, "08:00", "22:00"), (4, "08:00", "23:00"), (5, "09:00", "23:00"), (6, "09:00", "22:00")],
        "images": [
            "https://images.unsplash.com/photo-1521017432531-fbd92d768814",
            "https://images.unsplash.com/photo-1481833761820-0509d3217039",
        ],
        "seats": [
            ("shared_table", 16, 11, True, f"{SEED_MARKER} ortak masa"),
            ("solo_desk", 14, 9, True, f"{SEED_MARKER} calisma masasi"),
            ("outdoor", 10, 7, False, f"{SEED_MARKER} dis alan"),
        ],
    },
    {
        "name": "Ashley Coffee",
        "slug": "ashley-coffee",
        "neighborhood_slug": "besiktas-merkez",
        "owner_email": "admin@kahvesiz.local",
        "address": "Ihlamurdere Cad. No:23, Besiktas",
        "latitude": 41.04412,
        "longitude": 29.00748,
        "phone": "+90 212 222 22 22",
        "website": "https://example.com/ashley-coffee",
        "instagram": "ashleycoffee",
        "google_maps_url": "https://maps.google.com/?q=41.04412,29.00748",
        "status": "active",
        "total_capacity": 44,
        "indoor_capacity": 33,
        "outdoor_capacity": 11,
        "amenity": {
            "wifi_available": True,
            "wifi_speed_mbps": 175,
            "outlet_count": 28,
            "outlet_accessibility": "all_seats",
            "noise_level": "quiet",
            "has_natural_light": True,
            "has_ac": True,
            "has_heating": True,
            "has_parking": True,
            "has_accessible_entry": True,
            "allows_laptop": True,
            "min_spend_try": 145.0,
            "has_food": True,
            "has_alcohol": False,
            "pet_friendly": True,
        },
        "hours": [(0, "07:30", "22:30"), (1, "07:30", "22:30"), (2, "07:30", "22:30"), (3, "07:30", "22:30"), (4, "07:30", "23:00"), (5, "08:30", "23:00"), (6, "08:30", "22:00")],
        "images": [
            "https://images.unsplash.com/photo-1507133750040-4a8f57021571",
            "https://images.unsplash.com/photo-1521305916504-4a1121188589",
        ],
        "seats": [
            ("shared_table", 14, 10, True, f"{SEED_MARKER} ortak masa"),
            ("bar", 10, 6, True, f"{SEED_MARKER} bar bolumu"),
            ("sofa", 8, 5, False, f"{SEED_MARKER} koltuk bolumu"),
        ],
    },
    {
        "name": "Ayse Kahve Evi",
        "slug": "ayse-kahve-evi",
        "neighborhood_slug": "cihangir",
        "owner_email": "admin@kahvesiz.local",
        "address": "Siraselviler Sok. No:18, Cihangir",
        "latitude": 41.03419,
        "longitude": 28.98795,
        "phone": "+90 212 333 33 33",
        "website": "https://example.com/ayse-kahve-evi",
        "instagram": "aysekahveevi",
        "google_maps_url": "https://maps.google.com/?q=41.03419,28.98795",
        "status": "active",
        "total_capacity": 36,
        "indoor_capacity": 27,
        "outdoor_capacity": 9,
        "amenity": {
            "wifi_available": True,
            "wifi_speed_mbps": 110,
            "outlet_count": 16,
            "outlet_accessibility": "some_seats",
            "noise_level": "moderate",
            "has_natural_light": False,
            "has_ac": True,
            "has_heating": True,
            "has_parking": False,
            "has_accessible_entry": False,
            "allows_laptop": True,
            "min_spend_try": 115.0,
            "has_food": True,
            "has_alcohol": True,
            "pet_friendly": True,
        },
        "hours": [(0, "09:00", "21:30"), (1, "09:00", "21:30"), (2, "09:00", "21:30"), (3, "09:00", "21:30"), (4, "09:00", "22:30"), (5, "09:30", "22:30"), (6, "09:30", "21:30")],
        "images": [
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4",
            "https://images.unsplash.com/photo-1554118811-1e0d58224f24",
        ],
        "seats": [
            ("shared_table", 10, 7, True, f"{SEED_MARKER} ortak masa"),
            ("sofa", 8, 5, False, f"{SEED_MARKER} koltuk"),
            ("outdoor", 6, 4, False, f"{SEED_MARKER} dis masa"),
        ],
    },
]

IMAGE_POOL = [
    "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085",
    "https://images.unsplash.com/photo-1509042239860-f550ce710b93",
    "https://images.unsplash.com/photo-1445116572660-236099ec97a0",
    "https://images.unsplash.com/photo-1453614512568-c4024d13c247",
    "https://images.unsplash.com/photo-1414235077428-338989a2e8c0",
    "https://images.unsplash.com/photo-1498804103079-a6351b050096",
]


def _load_internet_cafe_source() -> list[dict]:
    data_path = Path(__file__).resolve().parent / "data" / "istanbul_cafes_seed.json"
    if not data_path.exists():
        return []
    try:
        payload = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _build_cafes_from_internet_source(rows: list[dict], target_count: int) -> list[dict]:
    neighborhoods = ["moda", "besiktas-merkez", "cihangir"]
    noise_levels = ["silent", "quiet", "moderate", "loud"]
    outlet_access = ["all_seats", "some_seats", "rare"]
    seat_types = ["shared_table", "solo_desk", "bar", "sofa", "outdoor"]

    generated: list[dict] = []
    slug_seen: set[str] = {item["slug"] for item in CAFES}

    for index, row in enumerate(rows, start=1):
        if len(generated) >= target_count:
            break
        name = (row.get("name") or "").strip()
        if not name:
            continue

        base_slug = _slugify(name) or f"istanbul-cafe-{index:03d}"
        slug = base_slug
        suffix = 2
        while slug in slug_seen:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        slug_seen.add(slug)

        latitude = float(row.get("latitude") or 40.98)
        longitude = float(row.get("longitude") or 29.02)
        neighborhood_slug = neighborhoods[(index - 1) % len(neighborhoods)]
        total_capacity = 22 + (index % 36)
        indoor_capacity = max(total_capacity - (index % 12), 12)
        outdoor_capacity = max(total_capacity - indoor_capacity, 0)
        outlet_count = 8 + (index % 30)
        noise_level = noise_levels[index % len(noise_levels)]
        wifi_speed = 80 + ((index * 13) % 180)
        min_spend = float(85 + (index % 8) * 18)

        seats: list[tuple[str, int, int, bool, str]] = []
        for offset in range(3):
            seat_type = seat_types[(index + offset) % len(seat_types)]
            seat_total = 5 + ((index + offset * 5) % 12)
            available = max(seat_total - ((index + offset) % 4), 0)
            seats.append(
                (
                    seat_type,
                    seat_total,
                    available,
                    offset != 2,
                    f"{SEED_MARKER} otomatik koltuk duzeni {offset + 1}",
                )
            )

        website = (row.get("website") or "").strip() or f"https://example.com/{slug}"
        phone = (row.get("phone") or "").strip() or f"+90 212 9{index % 10}0 {index % 100:02d} {((index * 7) % 100):02d}"
        instagram = (row.get("instagram") or "").strip() or f"kahvesiz_{_slugify(name)[:20]}"
        address = (row.get("address") or "").strip() or "Istanbul"

        generated.append(
            {
                "name": name,
                "slug": slug,
                "neighborhood_slug": neighborhood_slug,
                "owner_email": "admin@kahvesiz.local",
                "address": address,
                "latitude": round(latitude, 8),
                "longitude": round(longitude, 8),
                "phone": phone,
                "website": website,
                "instagram": instagram,
                "google_maps_url": f"https://maps.google.com/?q={round(latitude, 8)},{round(longitude, 8)}",
                "status": "active",
                "total_capacity": total_capacity,
                "indoor_capacity": indoor_capacity,
                "outdoor_capacity": outdoor_capacity,
                "amenity": {
                    "wifi_available": True,
                    "wifi_speed_mbps": wifi_speed,
                    "outlet_count": outlet_count,
                    "outlet_accessibility": outlet_access[index % len(outlet_access)],
                    "noise_level": noise_level,
                    "has_natural_light": index % 2 == 0,
                    "has_ac": True,
                    "has_heating": True,
                    "has_parking": index % 6 == 0,
                    "has_accessible_entry": index % 4 != 0,
                    "allows_laptop": True,
                    "min_spend_try": min_spend,
                    "has_food": index % 2 == 0,
                    "has_alcohol": index % 7 == 0,
                    "pet_friendly": index % 3 == 0,
                },
                "hours": [
                    (0, "08:00", "22:00"),
                    (1, "08:00", "22:00"),
                    (2, "08:00", "22:00"),
                    (3, "08:00", "22:00"),
                    (4, "08:00", "23:00"),
                    (5, "09:00", "23:00"),
                    (6, "09:00", "22:00"),
                ],
                "images": [
                    IMAGE_POOL[index % len(IMAGE_POOL)],
                    IMAGE_POOL[(index + 2) % len(IMAGE_POOL)],
                ],
                "seats": seats,
            }
        )

    return generated


def _build_generated_cafes(start_index: int, target_count: int) -> list[dict]:
    generated: list[dict] = []
    neighborhoods = ["moda", "besiktas-merkez", "cihangir"]
    noise_levels = ["silent", "quiet", "moderate", "loud"]
    outlet_access = ["all_seats", "some_seats", "rare"]
    seat_types = ["shared_table", "solo_desk", "bar", "sofa", "outdoor"]
    district_labels = {
        "moda": "Moda",
        "besiktas-merkez": "Besiktas",
        "cihangir": "Cihangir",
    }
    brand_pool = [
        "Starbuck Kafe",
        "Ashley Coffee",
        "Ayse Kahve",
        "Luna Brew",
        "Mavi Fincan",
        "Kuzey Kahve",
        "Rota Coffee",
        "Dingin Masa",
        "Mokka Lab",
        "Marin Coffee",
        "Ortak Masa",
        "Kahve Isligi",
        "Sokak Brew",
        "Brew Point",
        "Corner Bean",
        "Kahve Atolye",
    ]
    concept_pool = [
        "House",
        "Corner",
        "Roastery",
        "Study Lounge",
        "Cafe",
        "Nokta",
        "Mahalle",
        "Durak",
        "Bar",
        "Bahce",
        "Lokal",
        "Istasyon",
    ]
    seen_slugs = {item["slug"] for item in CAFES}

    for cafe_no in range(start_index, target_count + 1):
        neighborhood_slug = neighborhoods[(cafe_no - 1) % len(neighborhoods)]
        district_label = district_labels[neighborhood_slug]
        brand = brand_pool[(cafe_no - start_index) % len(brand_pool)]
        concept = concept_pool[((cafe_no - start_index) // len(brand_pool)) % len(concept_pool)]
        name = f"{brand} {concept} {district_label}"
        slug_base = _slugify(name) or f"cafe-{cafe_no}"
        slug = slug_base
        slug_suffix = 2
        while slug in seen_slugs:
            slug = f"{slug_base}-{slug_suffix}"
            slug_suffix += 1
        seen_slugs.add(slug)

        base_lat = 40.9750 + (((cafe_no * 7) % 45) / 10_000)
        base_lng = 29.0000 + (((cafe_no * 9) % 80) / 10_000)
        total_capacity = 24 + (cafe_no % 28)
        indoor_capacity = total_capacity - (cafe_no % 9)
        outdoor_capacity = max(total_capacity - indoor_capacity, 0)
        outlet_count = 6 + (cafe_no % 26)
        noise_level = noise_levels[cafe_no % len(noise_levels)]
        wifi_speed = 70 + ((cafe_no * 11) % 170)
        min_spend = float(80 + (cafe_no % 9) * 15)

        seats: list[tuple[str, int, int, bool, str]] = []
        for offset in range(3):
            seat_type = seat_types[(cafe_no + offset) % len(seat_types)]
            total = 6 + ((cafe_no + offset * 3) % 10)
            available = max(total - ((cafe_no + offset) % 4), 0)
            seats.append(
                (
                    seat_type,
                    total,
                    available,
                    (offset != 2),
                    f"{SEED_MARKER} seed seat {offset + 1}",
                )
            )

        generated.append(
            {
                "name": name,
                "slug": slug,
                "neighborhood_slug": neighborhood_slug,
                "owner_email": "admin@kahvesiz.local",
                "address": f"{district_label} Caddesi No:{10 + cafe_no}, Istanbul",
                "latitude": round(base_lat, 8),
                "longitude": round(base_lng, 8),
                "phone": f"+90 212 100 {cafe_no:02d} {((cafe_no * 3) % 100):02d}",
                "website": f"https://example.com/{slug}",
                "instagram": f"{_slugify(name)[:24]}",
                "google_maps_url": f"https://maps.google.com/?q={round(base_lat, 8)},{round(base_lng, 8)}",
                "status": "active",
                "total_capacity": total_capacity,
                "indoor_capacity": indoor_capacity,
                "outdoor_capacity": outdoor_capacity,
                "amenity": {
                    "wifi_available": True,
                    "wifi_speed_mbps": wifi_speed,
                    "outlet_count": outlet_count,
                    "outlet_accessibility": outlet_access[cafe_no % len(outlet_access)],
                    "noise_level": noise_level,
                    "has_natural_light": cafe_no % 2 == 0,
                    "has_ac": True,
                    "has_heating": True,
                    "has_parking": cafe_no % 5 == 0,
                    "has_accessible_entry": cafe_no % 3 != 0,
                    "allows_laptop": True,
                    "min_spend_try": min_spend,
                    "has_food": cafe_no % 2 == 0,
                    "has_alcohol": cafe_no % 7 == 0,
                    "pet_friendly": cafe_no % 4 == 0,
                },
                "hours": [
                    (0, "08:00", "22:00"),
                    (1, "08:00", "22:00"),
                    (2, "08:00", "22:00"),
                    (3, "08:00", "22:00"),
                    (4, "08:00", "23:00"),
                    (5, "09:00", "23:00"),
                    (6, "09:00", "22:00"),
                ],
                "images": [
                    IMAGE_POOL[cafe_no % len(IMAGE_POOL)],
                    IMAGE_POOL[(cafe_no + 2) % len(IMAGE_POOL)],
                ],
                "seats": seats,
            }
        )

    return generated


internet_source_rows = _load_internet_cafe_source()
if len(CAFES) < TARGET_CAFE_COUNT and internet_source_rows:
    CAFES.extend(_build_cafes_from_internet_source(internet_source_rows, TARGET_CAFE_COUNT - len(CAFES)))

if len(CAFES) < TARGET_CAFE_COUNT:
    CAFES.extend(_build_generated_cafes(start_index=len(CAFES) + 1, target_count=TARGET_CAFE_COUNT))


BOOKMARKS = [
    ("zeynep@kahvesiz.local", "northlight-study-cafe"),
    ("mert@kahvesiz.local", "monk-brew-lab"),
    ("ayse@kahvesiz.local", "monk-brew-lab"),
]


REVIEW_TEMPLATES = [
    ("Calismaya uygun", "Masa duzeni ve priz erisimi gun boyu calismaya uygundu."),
    ("Wi-Fi performansi iyi", "Baglanti stabildi, goruntulu toplantida kopma olmadi."),
    ("Sessiz saatler verimli", "Ozellikle sabah saatlerinde odaklanmak kolay oluyor."),
    ("Genel deneyim basarili", "Calisanlar ilgili, ortam temiz ve duzenliydi."),
    ("Tekrar gelirim", "Konum kolay, kahve kalitesi ve calisma kosullari dengeli."),
]


def pick_pg_url(explicit_url: str | None) -> str:
    for candidate in (
        explicit_url,
        os.getenv("DATABASE_URL"),
        os.getenv("DATABASE_URL_DEV"),
        os.getenv("DATABASE_URL_PROD"),
    ):
        if candidate:
            return candidate.replace("postgresql+asyncpg://", "postgresql://", 1)
    raise ValueError("PostgreSQL URL bulunamadi. --pg-url verin veya DATABASE_URL[_DEV] ayarlayin.")


def assert_safe_environment(pg_url: str, force: bool) -> None:
    env = (os.getenv("ENVIRONMENT") or os.getenv("FLASK_ENV") or "development").strip().lower()
    if force:
        return
    if env in {"production", "prod"}:
        raise RuntimeError("Production ortaminda seed calismaz. Gerekirse --force kullanin.")
    if "db-prod" in pg_url or "production" in pg_url:
        raise RuntimeError("Prod benzeri DATABASE_URL algilandi. Gerekirse --force kullanin.")


def upsert_user(cur, payload: dict) -> str:
    now = datetime.now(timezone.utc)
    cur.execute(
        """
        INSERT INTO users (
            email, username, display_name, role, is_active,
            email_verified_at, created_at, updated_at
        )
        VALUES (%s, %s, %s, %s, true, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE
        SET
            username = EXCLUDED.username,
            display_name = EXCLUDED.display_name,
            role = EXCLUDED.role,
            is_active = true,
            updated_at = EXCLUDED.updated_at
        RETURNING id::text
        """,
        (
            payload["email"],
            payload["username"],
            payload["display_name"],
            payload["role"],
            now,
            now,
            now,
        ),
    )
    user_id = str(cur.fetchone()[0])

    # Keep one PII row per user in dev.
    cur.execute(
        """
        UPDATE pii.user_pii
        SET
            full_name = %s,
            city = %s,
            country_code = 'TR',
            consent_given_at = %s,
            consent_version = 'dev-seed-v1',
            updated_at = now()
        WHERE user_id = %s
        """,
        (payload["display_name"], payload["city"], now, user_id),
    )
    if cur.rowcount == 0:
        cur.execute(
            """
            INSERT INTO pii.user_pii (
                user_id, full_name, city, country_code,
                consent_given_at, consent_version, created_at, updated_at
            )
            VALUES (%s, %s, %s, 'TR', %s, 'dev-seed-v1', now(), now())
            """,
            (user_id, payload["display_name"], payload["city"], now),
        )
    return user_id


def upsert_neighborhood(cur, payload: dict) -> str:
    cur.execute(
        """
        INSERT INTO neighborhoods (name, city, district, slug, is_active, created_at)
        VALUES (%s, %s, %s, %s, true, now())
        ON CONFLICT (slug) DO UPDATE
        SET
            name = EXCLUDED.name,
            city = EXCLUDED.city,
            district = EXCLUDED.district,
            is_active = true
        RETURNING id::text
        """,
        (payload["name"], payload["city"], payload["district"], payload["slug"]),
    )
    return str(cur.fetchone()[0])


def upsert_cafe(cur, payload: dict, neighborhood_id: str, owner_id: str) -> str:
    now = datetime.now(timezone.utc)
    description = f"{payload['name']} için geliştirme ortamı örnek verisi."
    cur.execute(
        """
        INSERT INTO cafes (
            owner_id, neighborhood_id, name, slug, description, address,
            latitude, longitude, phone, website, instagram, google_maps_url,
            is_verified, is_active, status,
            total_capacity, indoor_capacity, outdoor_capacity,
            created_at, updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            true, true, %s,
            %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (slug) DO UPDATE
        SET
            owner_id = EXCLUDED.owner_id,
            neighborhood_id = EXCLUDED.neighborhood_id,
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            address = EXCLUDED.address,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            phone = EXCLUDED.phone,
            website = EXCLUDED.website,
            instagram = EXCLUDED.instagram,
            google_maps_url = EXCLUDED.google_maps_url,
            is_verified = EXCLUDED.is_verified,
            is_active = EXCLUDED.is_active,
            status = EXCLUDED.status,
            total_capacity = EXCLUDED.total_capacity,
            indoor_capacity = EXCLUDED.indoor_capacity,
            outdoor_capacity = EXCLUDED.outdoor_capacity,
            updated_at = EXCLUDED.updated_at
        RETURNING id::text
        """,
        (
            owner_id,
            neighborhood_id,
            payload["name"],
            payload["slug"],
            description,
            payload["address"],
            payload["latitude"],
            payload["longitude"],
            payload["phone"],
            payload["website"],
            payload.get("instagram"),
            payload["google_maps_url"],
            payload["status"],
            payload["total_capacity"],
            payload["indoor_capacity"],
            payload["outdoor_capacity"],
            now,
            now,
        ),
    )
    return str(cur.fetchone()[0])


def refresh_cafe_seed_children(cur, cafe_id: str, payload: dict) -> None:
    a = payload["amenity"]
    cur.execute(
        """
        INSERT INTO cafe_amenities (
            cafe_id, wifi_available, wifi_speed_mbps, outlet_count, outlet_accessibility, noise_level,
            has_natural_light, has_ac, has_heating, has_parking, has_accessible_entry,
            allows_laptop, min_spend_try, has_food, has_alcohol, pet_friendly, updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, now()
        )
        ON CONFLICT (cafe_id) DO UPDATE
        SET
            wifi_available = EXCLUDED.wifi_available,
            wifi_speed_mbps = EXCLUDED.wifi_speed_mbps,
            outlet_count = EXCLUDED.outlet_count,
            outlet_accessibility = EXCLUDED.outlet_accessibility,
            noise_level = EXCLUDED.noise_level,
            has_natural_light = EXCLUDED.has_natural_light,
            has_ac = EXCLUDED.has_ac,
            has_heating = EXCLUDED.has_heating,
            has_parking = EXCLUDED.has_parking,
            has_accessible_entry = EXCLUDED.has_accessible_entry,
            allows_laptop = EXCLUDED.allows_laptop,
            min_spend_try = EXCLUDED.min_spend_try,
            has_food = EXCLUDED.has_food,
            has_alcohol = EXCLUDED.has_alcohol,
            pet_friendly = EXCLUDED.pet_friendly,
            updated_at = now()
        """,
        (
            cafe_id,
            a["wifi_available"],
            a["wifi_speed_mbps"],
            a["outlet_count"],
            a["outlet_accessibility"],
            a["noise_level"],
            a["has_natural_light"],
            a["has_ac"],
            a["has_heating"],
            a["has_parking"],
            a["has_accessible_entry"],
            a["allows_laptop"],
            a["min_spend_try"],
            a["has_food"],
            a["has_alcohol"],
            a["pet_friendly"],
        ),
    )

    cur.execute("DELETE FROM cafe_hours WHERE cafe_id = %s", (cafe_id,))
    for day_of_week, opens_at, closes_at in payload["hours"]:
        cur.execute(
            """
            INSERT INTO cafe_hours (cafe_id, day_of_week, opens_at, closes_at, is_closed)
            VALUES (%s, %s, %s::time, %s::time, false)
            ON CONFLICT (cafe_id, day_of_week) DO UPDATE
            SET opens_at = EXCLUDED.opens_at, closes_at = EXCLUDED.closes_at, is_closed = false
            """,
            (cafe_id, day_of_week, opens_at, closes_at),
        )

    cur.execute(
        "DELETE FROM cafe_images WHERE cafe_id = %s AND alt_text ILIKE %s",
        (cafe_id, f"{SEED_MARKER}%"),
    )
    for index, image_url in enumerate(payload["images"]):
        cur.execute(
            """
            INSERT INTO cafe_images (cafe_id, uploaded_by, url, alt_text, is_primary, sort_order, created_at)
            VALUES (%s, NULL, %s, %s, %s, %s, now())
            """,
            (
                cafe_id,
                image_url,
                f"{SEED_MARKER} {payload['name']} image {index + 1}",
                index == 0,
                index,
            ),
        )

    cur.execute(
        "DELETE FROM cafe_seats WHERE cafe_id = %s AND notes ILIKE %s",
        (cafe_id, f"{SEED_MARKER}%"),
    )
    for seat_type, total_count, available_count, has_outlet, notes in payload["seats"]:
        cur.execute(
            """
            INSERT INTO cafe_seats (cafe_id, seat_type, total_count, available_count, has_outlet, notes, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, now())
            """,
            (cafe_id, seat_type, total_count, available_count, has_outlet, notes),
        )


def seed_reviews(cur, user_ids: dict[str, str], cafe_ids: dict[str, str]) -> None:
    rng = random.Random(20260314)
    reviewer_emails = [email for email in sorted(user_ids.keys()) if email != "admin@kahvesiz.local"]
    if not reviewer_emails:
        return

    cafe_id_values = list(cafe_ids.values())
    cur.execute(
        """
        DELETE FROM review_votes rv
        USING reviews r
        WHERE rv.review_id = r.id
          AND r.cafe_id = ANY(%s::uuid[])
        """,
        (cafe_id_values,),
    )
    cur.execute(
        "DELETE FROM reviews WHERE cafe_id = ANY(%s::uuid[])",
        (cafe_id_values,),
    )

    created_reviews: list[tuple[str, str]] = []
    cafe_slugs = sorted(cafe_ids.keys())
    for cafe_index, cafe_slug in enumerate(cafe_slugs):
        cafe_id = cafe_ids[cafe_slug]
        review_count = rng.randint(1, 10)
        picked_reviewers = rng.sample(reviewer_emails, k=min(review_count, len(reviewer_emails)))

        for review_index, reviewer_email in enumerate(picked_reviewers):
            user_id = user_ids[reviewer_email]
            template_title, template_body = REVIEW_TEMPLATES[(cafe_index + review_index) % len(REVIEW_TEMPLATES)]
            rating = rng.randint(3, 5)
            visited = date(
                2026,
                (cafe_index % 12) + 1,
                ((review_index * 3 + cafe_index) % 28) + 1,
            )

            cur.execute(
                """
                INSERT INTO reviews (
                    user_id, cafe_id, rating, title, body,
                    noise_rating, wifi_rating, outlet_rating, visited_at,
                    is_verified_visit, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true, now(), now())
                ON CONFLICT (user_id, cafe_id) DO UPDATE
                SET
                    rating = EXCLUDED.rating,
                    title = EXCLUDED.title,
                    body = EXCLUDED.body,
                    noise_rating = EXCLUDED.noise_rating,
                    wifi_rating = EXCLUDED.wifi_rating,
                    outlet_rating = EXCLUDED.outlet_rating,
                    visited_at = EXCLUDED.visited_at,
                    is_verified_visit = EXCLUDED.is_verified_visit,
                    deleted_at = NULL,
                    updated_at = now()
                RETURNING id::text
                """,
                (
                    user_id,
                    cafe_id,
                    rating,
                    template_title,
                    template_body,
                    rng.randint(2, 5),
                    rng.randint(3, 5),
                    rng.randint(2, 5),
                    visited,
                ),
            )
            review_id = str(cur.fetchone()[0])
            created_reviews.append((review_id, reviewer_email))

    for review_id, author_email in created_reviews:
        voter_pool = [email for email in reviewer_emails if email != author_email]
        if not voter_pool:
            continue
        vote_count = rng.randint(0, min(4, len(voter_pool)))
        for voter_email in rng.sample(voter_pool, k=vote_count):
            cur.execute(
                """
                INSERT INTO review_votes (review_id, user_id, vote, created_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (review_id, user_id) DO UPDATE
                SET vote = EXCLUDED.vote
                """,
                (
                    review_id,
                    user_ids[voter_email],
                    "helpful" if rng.random() < 0.85 else "unhelpful",
                ),
            )


def seed_bookmarks(cur, user_ids: dict[str, str], cafe_ids: dict[str, str]) -> None:
    for user_email, cafe_slug in BOOKMARKS:
        cur.execute(
            """
            INSERT INTO bookmarks (user_id, cafe_id, created_at)
            VALUES (%s, %s, now())
            ON CONFLICT (user_id, cafe_id) DO NOTHING
            """,
            (user_ids[user_email], cafe_ids[cafe_slug]),
        )


def prune_legacy_seed_cafes(cur, keep_slugs: list[str]) -> None:
    cur.execute(
        """
        DELETE FROM cafes
        WHERE slug LIKE 'seed-study-cafe-%%'
          AND NOT (slug = ANY(%s))
        """,
        (keep_slugs,),
    )


def prune_non_seed_cafes(cur, keep_slugs: list[str]) -> None:
    cur.execute(
        """
        DELETE FROM cafes
        WHERE NOT (slug = ANY(%s))
        """,
        (keep_slugs,),
    )


def run_seed(pg_url: str, with_reviews: bool, dry_run: bool) -> None:
    conn = psycopg2.connect(pg_url)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            user_ids: dict[str, str] = {}
            neighborhood_ids: dict[str, str] = {}
            cafe_ids: dict[str, str] = {}

            for payload in USERS:
                user_ids[payload["email"]] = upsert_user(cur, payload)

            for payload in NEIGHBORHOODS:
                neighborhood_ids[payload["slug"]] = upsert_neighborhood(cur, payload)

            keep_slugs = [payload["slug"] for payload in CAFES]
            prune_legacy_seed_cafes(cur, keep_slugs)
            prune_non_seed_cafes(cur, keep_slugs)

            for payload in CAFES:
                cafe_id = upsert_cafe(
                    cur,
                    payload=payload,
                    neighborhood_id=neighborhood_ids[payload["neighborhood_slug"]],
                    owner_id=user_ids[payload["owner_email"]],
                )
                cafe_ids[payload["slug"]] = cafe_id
                refresh_cafe_seed_children(cur, cafe_id, payload)

            seed_bookmarks(cur, user_ids, cafe_ids)
            if with_reviews:
                seed_reviews(cur, user_ids, cafe_ids)

            if dry_run:
                conn.rollback()
            else:
                conn.commit()

    finally:
        conn.close()


def database_has_any_data(pg_url: str) -> bool:
    conn = psycopg2.connect(pg_url)
    try:
        with conn.cursor() as cur:
            for table_name in ("users", "neighborhoods", "cafes", "reviews", "bookmarks"):
                cur.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                if cur.fetchone() is not None:
                    return True
        return False
    finally:
        conn.close()


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed development data for PostgreSQL.")
    parser.add_argument("--pg-url", default=None, help="PostgreSQL URL (optional).")
    parser.add_argument("--force", action="store_true", help="Bypass production safety checks.")
    parser.add_argument("--dry-run", action="store_true", help="Execute and rollback.")
    parser.add_argument(
        "--without-reviews",
        action="store_true",
        help="Skip review and vote seeding.",
    )
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="Sadece veritabani bossa seed calistir.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    try:
        pg_url = pick_pg_url(args.pg_url)
        assert_safe_environment(pg_url, force=bool(args.force))
        if args.if_empty and database_has_any_data(pg_url):
            print("[ok] veritabani bos degil, seed atlandi (--if-empty).")
            return 0
        run_seed(
            pg_url=pg_url,
            with_reviews=not bool(args.without_reviews),
            dry_run=bool(args.dry_run),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[error] seed failed: {exc}")
        return 1

    mode = "dry-run" if args.dry_run else "write"
    reviews = "off" if args.without_reviews else "on"
    print(f"[ok] seed completed ({mode}, reviews={reviews})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
