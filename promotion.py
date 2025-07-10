import sqlite3
import os
import queue
import time
from ranks import get_rank_name, get_rank_title_path, get_small_insignia_path
from logger import log
from helpers import is_il2_running
from config import POLL_INTERVAL, LOCALE_MAP, CEREMONY_MAP, RESOURCE_PATH

def get_latest_event_year(conn, pid: int) -> int:
    cur = conn.cursor()
    cur.execute("SELECT date FROM event WHERE pilotId=? ORDER BY date DESC LIMIT 1", (pid,))
    row = cur.fetchone()
    return int(row[0][:4]) if row else 1941# --- Check all pilots (per-country ceilings + debug logging) --------------
    
def check_all_pilots(
    conn,
    thresholds,
    max_ranks,
    language,
    insignia_base,
    campaign_country,
    mission_squadron,
    squadron_country_map,
    last_date
):
    """
    Promotions now obey per-country ceilings:
      - squadron_country_map: { squadronId: countryCode, ... }
      - max_ranks:            { "101": 10, "102":13, ... }
    """
    ai_notifications = []
    player_notify    = None
    cur = conn.cursor()

    # NEW: Find active player for this campaign/squadron
    active_player_id = get_active_player_id(conn, mission_squadron)

    # fetch all pilots
    cur.execute("""
        SELECT
            id,
            name,
            lastName,
            rankId,
            pcp,
            sorties,
            goodSorties,
            description,
            personageId,
            squadronId
          FROM pilot
    """)
    for (
        pid, first, last, raw_rank, raw_pcp,
        raw_sorties, raw_good, desc, person, pilot_sq
    ) in cur.fetchall():
        is_player = (pid == active_player_id)
        # Parse numeric fields up‐front
        try:
            r = int(raw_rank)
        except:
            r = 0
        try:
            p = float(raw_pcp)
        except:
            p = 0.0
        s = int(raw_sorties)
        g = int(raw_good)

        # Determine this pilot’s ceiling
        pilot_country = squadron_country_map.get(pilot_sq, campaign_country)
        ceiling       = max_ranks.get(str(pilot_country), 5)

        log(f"Pilot {pid}: squadron={pilot_sq}, "
            f"country={pilot_country}, current_rank={r}, "
            f"max_allowed_rank={ceiling}")

        # Try to promote if in [5 .. ceiling-1]
        if 4 <= r < ceiling:
            nr = try_promote(conn, pid, r, p, s, g, thresholds, last_date, is_player=is_player)
        else:
            nr = r

        if nr != r:
            # Player pilot check: must match active_player_id!
            if is_player:
                log(f"Treating pilot {pid} as active player for this mission.")
                # real player for this campaign
                if "birthCountryInfo=" in desc:
                    try:
                        display_country = int(desc.split("birthCountryInfo=")[1].split("&")[0])
                    except:
                        display_country = pilot_country
                else:
                    display_country = pilot_country

                year = get_latest_event_year(conn, pid) if display_country == 101 else 1941
                big_ins, title = get_rank_title_path(
                    display_country, nr, year, insignia_base, LOCALE_MAP[language]
                )
                ceremony = os.path.join(
                    RESOURCE_PATH,
                    CEREMONY_MAP.get(display_country, "")
                )
                player_notify = (
                    "player", ceremony, big_ins, title, language,
                    display_country, first, last, r, nr, last_date  
                )


            # AI pilot (not the player)
            else:
                display_country = pilot_country
                year = get_latest_event_year(conn, pid) if display_country == 101 else 1941

                if pilot_sq == mission_squadron:
                    full_name = f"{first} {last}".strip()
                    before_ins = get_small_insignia_path(
                        display_country, nr - 1, year, insignia_base
                    )
                    after_ins  = get_small_insignia_path(
                        display_country, nr, year, insignia_base
                    )
                    _, title = get_rank_title_path(
                        display_country, nr, year,
                        insignia_base,
                        LOCALE_MAP[language]
                    )
                    ai_notifications.append(
                        ("ai", full_name, before_ins, after_ins, title, language)
                    )
                # AI in other squadrons: silent

    # enqueue AI first, then the player
    for note in ai_notifications:
        popup_queue.put(note)
    if player_notify:
        log(f"Enqueuing player promotion notification for pilot {active_player_id}")
        popup_queue.put(player_notify)
        
# --- Promotion logic ---
#def try_promote(conn, pid, rank, pcp, sorties, good, thresholds):
#    p = float(pcp); s = int(sorties); g = int(good)
#    failure = (s - g) / s if s > 0 else 1.0
#    idx = rank - 4
#    if not (0 <= idx < len(thresholds)):
#        return rank
#    pr, sr, fr = thresholds[idx]
#    log(f"Pilot {pid}: PCP={p}, sorties={s}, good={g}, failure={failure:.3f}, thr=({pr},{sr},{fr})")
#    if p >= pr or (s >= sr and failure <= fr):
#        nr = rank + 1
#        conn.execute("UPDATE pilot SET rankId=? WHERE id= ?", (nr, pid))
#        conn.commit()
#        log(f"Auto-promoted {pid}: {rank} -> {nr}")
#        return nr
#    return rank

def try_promote(conn, pid, rank, pcp, sorties, good, thresholds, current_date_str, is_player=True):
    from datetime import datetime
    import random

    p = float(pcp)
    s = int(sorties)
    g = int(good)
    failure = (s - g) / s if s > 0 else 1.0
    idx = rank - 4

    if not (0 <= idx < len(thresholds)):
        return rank

    pr, sr, fr = thresholds[idx]
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")

    if not (p >= pr or (s >= sr and failure <= fr)):
        log(f"Pilot {pid} does not meet threshold for rank {rank + 1}")
        return rank

    # === AI PILOT LOGIC ===
    if not is_player:
        promote_to = rank + 1
        conn.execute("UPDATE pilot SET rankId=? WHERE id=?", (promote_to, pid))
        conn.commit()
        log(f"[AI] Pilot {pid} promoted to rank {promote_to} (auto)")
        return promote_to

    # === PLAYER PILOT LOGIC ===
    cur = conn.cursor()
    cur.execute("""
        SELECT last_attempt, last_success, fail_count
        FROM promotion_attempts
        WHERE pilotId = ?
    """, (pid,))
    row = cur.fetchone()

    last_attempt_date = None
    last_success = None
    fail_count = 0

    if row:
        last_attempt_date = datetime.strptime(row[0], "%Y-%m-%d")
        last_success = row[1]
        fail_count = row[2] or 0

        if last_success == 0:
            days_since = (current_date - last_attempt_date).days
            if days_since < 2:
                log(f"Pilot {pid} in cooldown period ({days_since} days since last attempt).")
                return rank

    base_chance = 0.9 - (0.05 * idx)
    chance = max(base_chance, 0.25)

    # Forced promotion after 3 failed attempts
    if fail_count >= 3:
        promote_to = rank + 1
        conn.execute("UPDATE pilot SET rankId=? WHERE id=?", (promote_to, pid))
        cur.execute("""
            INSERT INTO promotion_attempts (pilotId, last_attempt, last_success, fail_count)
            VALUES (?, ?, 1, 0)
            ON CONFLICT(pilotId) DO UPDATE SET last_attempt=excluded.last_attempt,
                                               last_success=1,
                                               fail_count=0
        """, (pid, current_date_str))
        conn.commit()
        log(f"[PLAYER] Pilot {pid} forced promotion to {promote_to} after {fail_count} failures.")
        return promote_to

    # Chance-based promotion
    roll = random.random()
    log(f"[PLAYER] Pilot {pid}: roll={roll:.3f}, chance={chance:.3f} for rank {rank + 1}")

    if roll <= chance:
        promote_to = rank + 1
        conn.execute("UPDATE pilot SET rankId=? WHERE id=?", (promote_to, pid))
        cur.execute("""
            INSERT INTO promotion_attempts (pilotId, last_attempt, last_success, fail_count)
            VALUES (?, ?, 1, 0)
            ON CONFLICT(pilotId) DO UPDATE SET last_attempt=excluded.last_attempt,
                                               last_success=1,
                                               fail_count=0
        """, (pid, current_date_str))
        conn.commit()
        log(f"[PLAYER] Pilot {pid} promoted to rank {promote_to}")
        return promote_to
    else:
        fail_count += 1
        cur.execute("""
            INSERT INTO promotion_attempts (pilotId, last_attempt, last_success, fail_count)
            VALUES (?, ?, 0, ?)
            ON CONFLICT(pilotId) DO UPDATE SET last_attempt=excluded.last_attempt,
                                               last_success=0,
                                               fail_count=excluded.fail_count
        """, (pid, current_date_str, fail_count))
        conn.commit()
        log(f"[PLAYER] Pilot {pid} failed promotion. Fail count now {fail_count}")
        return rank


    
def get_active_player_id(conn, mission_squadron):
    """
    Returns the id of the *real player* pilot in the current mission's squadron,
    preferring the one with most recent mission activity.
    Logs candidates and selected id for debug.
    """
    cur = conn.cursor()
    # Find all possible player pilots in this squadron
    cur.execute("""
        SELECT id FROM pilot
        WHERE personageId <> '' AND squadronId = ?
    """, (mission_squadron,))
    candidates = [row[0] for row in cur.fetchall()]
    log(f"Possible player candidates in squadron {mission_squadron}: {candidates}")

    if not candidates:
        log("No active player found for this squadron.")
        return None

    # Get the latest mission for this squadron
    cur.execute("""
        SELECT id FROM mission
        WHERE squadronId = ?
        ORDER BY id DESC
        LIMIT 1
    """, (mission_squadron,))
    mission_row = cur.fetchone()
    latest_mission_id = mission_row[0] if mission_row else None

    # Prefer the candidate who has an event in the latest mission
    if latest_mission_id:
        for pid in sorted(candidates, reverse=True):  # Prefer higher id if multiple
            cur.execute("""
                SELECT 1 FROM event WHERE pilotId = ? AND missionId = ? LIMIT 1
            """, (pid, latest_mission_id))
            if cur.fetchone():
                log(f"Selected active player id: {pid} (has event in latest mission {latest_mission_id})")
                return pid

    # Fallback: highest id as before
    selected_pid = max(candidates)
    log(f"Selected active player id: {selected_pid} (fallback to highest id)")
    return selected_pid

# --- Monitor DB ---
def monitor_db(db_path, thresholds, max_ranks, language, insignia_base):
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # 1) Build a full squadron→country map up front
    cur.execute("SELECT id, configID FROM squadron")
    squadron_country = { row[0]: row[1] // 1000 for row in cur.fetchall() }
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS promotion_attempts (
        pilotId INTEGER PRIMARY KEY,
        last_attempt TEXT,
        last_success INTEGER,
        fail_count INTEGER DEFAULT 0
    )
""")

    # Prime with last seen mission
    cur.execute("SELECT id, date FROM mission ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    last_mid, last_date = (row[0], row[1]) if row else (0, None)
    conn.close()
    log(f"Starting mission monitor from id {last_mid}, date {last_date}")

    while True:
        if not is_il2_running():
            log("IL-2 closed – stopping monitor")
            return

        try:
            conn = sqlite3.connect(db_path)
            cur  = conn.cursor()
            
            # 1) Always rebuild the squadron→country map here
            cur.execute("SELECT id, configID FROM squadron")
            squadron_country = {
                row[0]: row[1] // 1000
                for row in cur.fetchall()
            }

            # Fetch any new missions
            cur.execute(
                "SELECT id, date, squadronId FROM mission WHERE id>? ORDER BY id ASC",
                (last_mid,)
            )
            for mid, date_str, squadron_id in cur.fetchall():
                log(f"=== Mission Start: {mid} ({date_str}) ===")
                last_mid = mid
                if date_str != last_date:
                    last_date = date_str

                    # 2) Determine this mission’s “player” country (unchanged)
                    campaign_country = 201
                    if squadron_id is not None:
                        cur.execute(
                            "SELECT description FROM pilot "
                            "WHERE personageId<>'' AND description LIKE ? LIMIT 1",
                            (f"%startSquadronInfo={squadron_id}%",)
                        )
                        p_row = cur.fetchone()
                        if p_row and "birthCountryInfo=" in p_row[0]:
                            try:
                                campaign_country = int(
                                    p_row[0].split("birthCountryInfo=")[1].split("&")[0]
                                )
                            except:
                                log(f"Failed parsing player country for sq {squadron_id}; using {campaign_country}")

                    # 3) Call promotions, passing the full map
                    check_all_pilots(
                        conn,
                        thresholds,
                        max_ranks,
                        language,
                        insignia_base,
                        campaign_country,
                        squadron_id,
                        squadron_country,
                        last_date 
                    )
                    
        except Exception as e:
            log(f"Monitor error: {e}")
        finally:
            conn.close()

        time.sleep(POLL_INTERVAL)
