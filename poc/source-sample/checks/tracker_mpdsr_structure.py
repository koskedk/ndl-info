#!/usr/bin/env python3
"""Reads how the death programmes are set up on the KHIS tracker (DHIS2): definitions and totals only.

It answers what the tracker bridge brief (poc/MPDSR-TRACKER-BRIDGE.md) needs to know:
  1. the system: DHIS2 version, and what the account may see
  2. the programmes for deaths: stages, data elements, option sets, tracked entity attributes
  3. the places: the Master Facility List's facilities, found by MFL code
  4. totals: enrolments and events per programme, stage, facility and month
  5. personal fields: the attributes and data elements that name or identify someone, or are free text

It never reads a case's attribute values or an event's answers, and it never prints the user name.
Read-only: every call is a GET.

Settings, in poc/.env:  HIS_TRACKER_URL, HIS_TRACKER_USERNAME, HIS_TRACKER_PASSWORD

    uv run python checks/tracker_mpdsr_structure.py
    uv run python checks/tracker_mpdsr_structure.py --settings HIS_KENYA --no-totals   # same reads on KHIS
    uv run python checks/tracker_mpdsr_structure.py --match 'death|mpdsr|mortality' --no-totals   # a wider look

Writes:
  checks/tracker_mpdsr_structure.json   the definitions and totals (no personal data in it)
  tracker-fields-restricted.csv         the fields that must never reach silver or gold, made by rule from step 5
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import time
import urllib.parse
from collections import Counter
from pathlib import Path

from dotenv import dotenv_values

HERE = Path(__file__).resolve().parent
POC = HERE.parent.parent
# The forms to stage: a notification and a review for maternal, neonatal and perinatal deaths, and the two community
# forms for maternal deaths. The maternal, community and perinatal ones are what the analysts' own pipeline stages
# (mpdsr.py and pdsr.py of the KHIS MNH project); the neonatal ones are added for the neonatal mortality indicator.
MATCH = r"death (notification|review) form rev 2025|community maternal death"
# The analysts' short name for each form, kept so their SQL can be carried over. NDN and NDR are ours.
PROGRAM_KEYS = {"orgIzwnrwEG": "MDN_2025", "m6U01IixAdW": "MDR", "gsV6ZGGQSqK": "C_MDN", "IOaRQKgCrPO": "C_MD_VA",
                "TcVXzAKCVdU": "PDN", "qjk3GCpkIoa": "PDR", "z9p4TifTD9m": "NDN", "YwtPT5i5ccz": "NDR"}
# Typed-text fields that are not personal: they tie a notification to its review, or name the facility by code
KEEP = {"AvLykgDSa8f": "MPDSR Case ID", "vobAuF9as7h": "MPDSR Review Event ID", "yHgODPqdWcB": "KMHFL code"}
# A field that names or identifies someone, by what it is called
IDENTIFYING = (r"\bnames?\b|surname|first name|last name|middle name|phone|telephone|mobile|e-?mail|address|village|"
               r"estate|landmark|next of kin|\bnok\b|national id|\bid (?:no|number)\b|id number|passport|"
               r"birth cert|huduma|alien|\bupi\b|\bcr (?:no|number)\b|client registry|inpatient (?:no|number)|"
               r"\bip (?:no|number)\b|\bop (?:no|number)\b|outpatient (?:no|number)|serial|household|guardian|husband|spouse")
# A field that can hold anything typed, by its value type (when it has no list of options)
FREE_TEXT = {"TEXT", "LONG_TEXT", "EMAIL", "PHONE_NUMBER", "USERNAME", "URL", "FILE_RESOURCE", "IMAGE", "COORDINATE",
             "LETTER"}


def say(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


class Dhis2:
    """GET-only client, through curl. The sign-in is handed to curl on standard input: it is never on the command
    line and never printed. curl is used because the site's Cloudflare refuses Python's own client (error 1010)."""

    def __init__(self, url, user, password):
        self.base = url.rstrip("/")
        if not self.base.endswith("/api"):
            self.base += "/api"
        if not shutil.which("curl"):
            raise SystemExit("curl is not installed, and this script reads the tracker through it.")
        quoted = f"{user}:{password}".replace("\\", "\\\\").replace('"', '\\"')
        self._signin = f'user = "{quoted}"\n'
        self.calls = 0

    def get(self, path, tries=3, **params):
        query = urllib.parse.urlencode([(k, v) for k, v in params.items() if v is not None], doseq=True)
        url = f"{self.base}/{path}" + (f"?{query}" if query else "")
        config = (f'url = "{url}"\n' + self._signin + 'header = "Accept: application/json"\n'
                  'silent\nshow-error\ngloboff\nmax-time = 180\nwrite-out = "\\n%{http_code}"\n')
        last = None
        for attempt in range(tries):
            self.calls += 1
            done = subprocess.run(["curl", "--config", "-"], input=config, capture_output=True, text=True)
            body, _, status = done.stdout.rpartition("\n")
            if done.returncode == 0 and status == "200":
                return json.loads(body)
            if status == "401":
                raise SystemExit("The server refused the sign-in (401). Check the user name and password in poc/.env.")
            if status == "403" and "1010" in body and "cloudflare" in body.lower():
                raise SystemExit("Cloudflare refused this client before the sign-in was looked at (error 1010). "
                                 "Nothing was read. Ask DHA how API clients are meant to reach this server.")
            if status in ("403", "404", "409"):
                raise LookupError(f"{status} on {path}")
            last = f"HTTP {status}" if done.returncode == 0 else f"curl error {done.returncode}"
            time.sleep(3 * (attempt + 1))
        raise SystemExit(f"Could not reach {path} after {tries} tries ({last}). Is the address right, and is a VPN needed?")


def month_list(first):
    year, month = (int(part) for part in first.split("-"))
    now = time.localtime()
    out = []
    while (year, month) <= (now.tm_year, now.tm_mon):
        out.append(f"{year}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def paged(api, path, key, **params):
    """Every row of a tracker listing, a page at a time. Works with both shapes DHIS2 has used for paging."""
    page, rows = 1, []
    while True:
        answer = api.get(path, page=page, pageSize=1000, **params)
        chunk = answer.get(key) or answer.get("instances") or []
        rows += chunk
        if len(chunk) < 1000:
            return rows
        page += 1


def kind_of(name, value_type, has_options):
    """Why a field is personal, or None."""
    if re.search(IDENTIFYING, name or "", re.I):
        return "identifies a person"
    if value_type in FREE_TEXT and not has_options:
        return "free text"
    return None


def main():
    ap = argparse.ArgumentParser(description="Structure of the death programmes on the KHIS tracker")
    ap.add_argument("--settings", default="HIS_TRACKER", help="start of the three setting names in poc/.env")
    ap.add_argument("--match", default=MATCH, help="words that mark a death programme, as a regular expression")
    ap.add_argument("--from", dest="first", default="2025-07", help="first month for the totals (default 2025-07)")
    ap.add_argument("--no-totals", action="store_true", help="definitions only: skip step 4")
    ap.add_argument("--out", default=str(HERE / "tracker_mpdsr_structure.json"))
    ap.add_argument("--restricted", default=str(HERE.parent / "tracker-fields-restricted.csv"),
                    help="where to write the list of fields that must never reach silver or gold")
    a = ap.parse_args()

    env = dotenv_values(POC / ".env")
    names = [f"{a.settings}_{part}" for part in ("URL", "USERNAME", "PASSWORD")]
    missing = [name for name in names if not env.get(name)]
    if missing:
        raise SystemExit("Add to poc/.env first: " + ", ".join(missing))
    api = Dhis2(*(env[name] for name in names))
    host = urllib.parse.urlparse(api.base).netloc
    found = {"host": host, "read_on": time.strftime("%Y-%m-%d %H:%M")}

    # ------------------------------------------------------------------ 1. the system
    say(f"step 1 of 5: the system at {host}")
    try:
        info = api.get("system/info")
    except LookupError as error:
        say(f"   the version is not readable with this account ({error})")
        info = {}
    try:
        me = api.get("me", fields="authorities,organisationUnits[level],dataViewOrganisationUnits[level],"
                                  "teiSearchOrganisationUnits[level]")
    except LookupError as error:
        raise SystemExit(f"The server refused this account's own details ({error}), so nothing else will be readable. "
                         "Nothing was read. The sign-in was accepted, so the cause is the account's rights, the network, "
                         "or the server refusing this kind of client.")
    authorities = set(me.get("authorities") or [])
    levels = lambda key: sorted({unit.get("level") for unit in me.get(key) or []})
    found["system"] = {"version": info.get("version"), "server_date": (info.get("serverDate") or "")[:10],
                       "superuser": "ALL" in authorities, "authorities": len(authorities),
                       "capture_levels": levels("organisationUnits"), "view_levels": levels("dataViewOrganisationUnits"),
                       "search_levels": levels("teiSearchOrganisationUnits")}
    say(f"   DHIS2 {info.get('version')} | account: {len(authorities)} authorities"
        f"{' (superuser)' if 'ALL' in authorities else ''} | capture at levels {levels('organisationUnits')}, "
        f"view {levels('dataViewOrganisationUnits')}, search {levels('teiSearchOrganisationUnits')}")

    # ------------------------------------------------------------------ 2. the programmes
    say("step 2 of 5: the programmes")
    programs = api.get("programs", paging="false", fields=(
        "id,name,shortName,programType,lastUpdated,trackedEntityType[id,name],access[data[read,write]],"
        "programTrackedEntityAttributes[mandatory,searchable,trackedEntityAttribute[id,name,valueType,unique,"
        "confidential,optionSet[id,name]]],"
        "programStages[id,name,repeatable,sortOrder,programStageDataElements[compulsory,"
        "dataElement[id,name,valueType,optionSet[id,name,options[code,name]]]]]")).get("programs", [])
    found["all_programmes"] = sorted([p["name"], p.get("programType")] for p in programs)
    say(f"   {len(programs)} programmes the account can see:")
    for name, kind in found["all_programmes"]:
        say(f"     {'tracker' if kind == 'WITH_REGISTRATION' else 'event  '}  {name}")
    chosen = [p for p in programs if re.search(a.match, p["name"], re.I)]
    say(f"   {len(chosen)} match '{a.match}'")
    found["programmes"] = []
    for p in sorted(chosen, key=lambda p: p["name"]):
        attributes = [{"id": x["trackedEntityAttribute"]["id"], "name": x["trackedEntityAttribute"]["name"],
                       "value_type": x["trackedEntityAttribute"].get("valueType"),
                       "unique": x["trackedEntityAttribute"].get("unique", False),
                       "confidential": x["trackedEntityAttribute"].get("confidential", False),
                       "option_set": (x["trackedEntityAttribute"].get("optionSet") or {}).get("name"),
                       "mandatory": x.get("mandatory", False), "searchable": x.get("searchable", False)}
                      for x in p.get("programTrackedEntityAttributes") or []]
        stages = []
        for s in sorted(p.get("programStages") or [], key=lambda s: s.get("sortOrder") or 0):
            elements = [{"id": x["dataElement"]["id"], "name": x["dataElement"]["name"],
                         "value_type": x["dataElement"].get("valueType"), "compulsory": x.get("compulsory", False),
                         "option_set": (x["dataElement"].get("optionSet") or {}).get("name"),
                         "options": [[o.get("code"), o.get("name")]
                                     for o in (x["dataElement"].get("optionSet") or {}).get("options") or []]}
                        for x in s.get("programStageDataElements") or []]
            stages.append({"id": s["id"], "name": s["name"], "repeatable": s.get("repeatable", False),
                           "data_elements": elements})
        tracker = p.get("programType") == "WITH_REGISTRATION"
        found["programmes"].append({
            "id": p["id"], "key": PROGRAM_KEYS.get(p["id"], ""), "name": p["name"].strip(), "tracker": tracker, "last_updated": (p.get("lastUpdated") or "")[:10],
            "tracked_entity_type": (p.get("trackedEntityType") or {}).get("name"),
            "can_read_data": ((p.get("access") or {}).get("data") or {}).get("read"),
            "can_write_data": ((p.get("access") or {}).get("data") or {}).get("write"),
            "attributes": attributes, "stages": stages})
        say(f"   {p['name']}  [{p['id']}]  {'tracker' if tracker else 'event'} programme"
            f" | data read: {found['programmes'][-1]['can_read_data']}, write: {found['programmes'][-1]['can_write_data']}")
        if tracker:
            say(f"      entity: {found['programmes'][-1]['tracked_entity_type']} | {len(attributes)} attributes")
        for s in stages:
            with_options = sum(1 for e in s["data_elements"] if e["option_set"])
            say(f"      stage: {s['name']}  [{s['id']}]{' (repeatable)' if s['repeatable'] else ''}"
                f" | {len(s['data_elements'])} data elements, {with_options} with a list of options")

    # ------------------------------------------------------------------ 3. the places
    say("step 3 of 5: the places, by MFL code from the Master Facility List")
    with open(POC / "transform" / "seeds" / "master_facility_list.csv", newline="") as f:
        listed = {row["mfl_code"]: row["facility_name"] for row in csv.DictReader(f)}
    units = api.get("organisationUnits", paging="false", filter=f"code:in:[{','.join(listed)}]",
                    fields="id,code,name,level,path").get("organisationUnits", [])
    found["places"] = sorted(({"mfl_code": u["code"], "id": u["id"], "name": u["name"], "level": u.get("level"),
                               "path": u.get("path")} for u in units), key=lambda u: u["mfl_code"])
    for u in found["places"]:
        say(f"   {u['mfl_code']}  {u['id']}  level {u['level']}  {u['name']}")
    for code in sorted(set(listed) - {u["code"] for u in units}):
        say(f"   {code}  NOT FOUND on the tracker ({listed[code]})")

    # ------------------------------------------------------------------ 4. totals
    found["totals"] = []
    if a.no_totals:
        say("step 4 of 5: totals skipped (--no-totals)")
    else:
        months = month_list(a.first)
        say(f"step 4 of 5: totals per programme, stage, facility and month, {months[0]} to {months[-1]}")
        stage_name = {s["id"]: s["name"] for p in found["programmes"] for s in p["stages"]}
        for p in found["programmes"]:
            for scope, label in (("ACCESSIBLE", "all places the account can reach"),):
                try:
                    answer = api.get("tracker/events", program=p["id"], ouMode=scope, fields="event", pageSize=1,
                                     totalPages="true")
                    total = answer.get("total", (answer.get("pager") or {}).get("total"))
                    say(f"   {p['name']}: {total} events in {label}")
                    found["totals"].append({"programme": p["name"], "scope": scope, "events": total})
                except LookupError as error:
                    say(f"   {p['name']}: no total for {label} ({error})")
            for n, u in enumerate(found["places"], 1):
                row = {"programme": p["name"], "mfl_code": u["mfl_code"], "facility": u["name"]}
                try:
                    events = paged(api, "tracker/events", "events", program=p["id"], orgUnit=u["id"], ouMode="SELECTED",
                                   occurredAfter=f"{months[0]}-01", fields="event,programStage,occurredAt,status")
                except LookupError as error:
                    say(f"   {p['name']} | {n} of {len(found['places'])} {u['name']}: events not readable ({error})")
                    continue
                by = Counter((stage_name.get(e.get("programStage"), e.get("programStage")), (e.get("occurredAt") or "")[:7])
                             for e in events)
                row["events"] = [{"stage": s, "month": m, "events": c} for (s, m), c in sorted(by.items())]
                if p["tracker"]:
                    try:
                        enrolments = paged(api, "tracker/enrollments", "enrollments", program=p["id"], orgUnit=u["id"],
                                           ouMode="SELECTED", enrolledAfter=f"{months[0]}-01",
                                           fields="enrollment,enrolledAt,status")
                        em = Counter((e.get("enrolledAt") or "")[:7] for e in enrolments)
                        row["enrolments"] = [{"month": m, "enrolments": c} for m, c in sorted(em.items())]
                    except LookupError as error:
                        row["enrolments_error"] = str(error)
                found["totals"].append(row)
                per_stage = Counter()
                for (s, _), c in by.items():
                    per_stage[s] += c
                say(f"   {p['name']} | {n} of {len(found['places'])} {u['name']}: {len(events)} events"
                    + (f", {sum(x['enrolments'] for x in row.get('enrolments', []))} enrolments" if p["tracker"] else "")
                    + (" | " + "; ".join(f"{s}: {c}" for s, c in sorted(per_stage.items())) if per_stage else ""))

    # ------------------------------------------------------------------ 5. personal fields
    say("step 5 of 5: fields that name or identify someone, or are free text")
    found["personal_fields"] = []
    for p in found["programmes"]:
        for x in p["attributes"]:
            why = "marked confidential" if x["confidential"] else kind_of(x["name"], x["value_type"], bool(x["option_set"]))
            if x["unique"] and not why:
                why = "unique identifier"
            if why:
                found["personal_fields"].append({"programme": p["name"], "where": "attribute", "id": x["id"],
                                                 "name": x["name"], "value_type": x["value_type"], "why": why})
        for s in p["stages"]:
            for x in s["data_elements"]:
                why = None if x["id"] in KEEP else kind_of(x["name"], x["value_type"], bool(x["option_set"]))
                if why:
                    found["personal_fields"].append({"programme": p["name"], "programme_id": p["id"],
                                                     "where": f"stage: {s['name']}", "id": x["id"],
                                                     "name": x["name"], "value_type": x["value_type"], "why": why})
    for (programme, why), count in sorted(Counter((x["programme"], x["why"]) for x in found["personal_fields"]).items()):
        say(f"   {programme}: {count} fields, {why}")

    Path(a.out).write_text(json.dumps(found, indent=1, ensure_ascii=False))
    with open(a.restricted, "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["program_key", "program_id", "program", "data_element_id", "data_element", "value_type", "why"])
        for x in found["personal_fields"]:
            if x["where"] != "attribute":
                out.writerow([PROGRAM_KEYS.get(x["programme_id"], ""), x["programme_id"], x["programme"].strip(), x["id"],
                              x["name"], x["value_type"], x["why"]])
    say(f"done: {api.calls} calls, all read-only. Definitions and totals written to {a.out}")
    say(f"      fields that must never reach silver or gold written to {a.restricted}")


if __name__ == "__main__":
    main()
