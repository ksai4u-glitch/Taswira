"""
Read the state results for the elections map from elections/raw/ and elections/story.json.

Each raw file is the "results by state" table as copied from its source (see raw/README.md),
one state per line. story.json says which column holds each candidate, which columns are the
other candidates and which (if any) is the total of valid votes. Standard library only.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

# Names in the raw tables -> ISO code of the state in history/geo/nga-states-2022.topojson.
STATES = {
    "Abia": "NG-AB", "Adamawa": "NG-AD", "Akwa Ibom": "NG-AK", "Anambra": "NG-AN", "Bauchi": "NG-BA",
    "Bayelsa": "NG-BY", "Benue": "NG-BE", "Borno": "NG-BO", "Cross River": "NG-CR", "Delta": "NG-DE",
    "Ebonyi": "NG-EB", "Edo": "NG-ED", "Ekiti": "NG-EK", "Enugu": "NG-EN", "FCT": "NG-FC", "Gombe": "NG-GO",
    "Imo": "NG-IM", "Jigawa": "NG-JI", "Kaduna": "NG-KD", "Kano": "NG-KN", "Katsina": "NG-KT",
    "Kebbi": "NG-KE", "Kogi": "NG-KO", "Kwara": "NG-KW", "Lagos": "NG-LA", "Nasarawa": "NG-NA",
    "Niger": "NG-NI", "Ogun": "NG-OG", "Ondo": "NG-ON", "Osun": "NG-OS", "Oyo": "NG-OY",
    "Plateau": "NG-PL", "Rivers": "NG-RI", "Sokoto": "NG-SO", "Taraba": "NG-TA", "Yobe": "NG-YO",
    "Zamfara": "NG-ZA",
}


def number(text):
    return int(text.strip().replace(",", "").replace("−", "-"))


def read_raw(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    sep = "\t" if name.endswith(".tsv") else "|"
    return [line.split(sep) for line in lines]


def state_results(election, corrections=()):
    """Return {iso: {"name", party: votes, ..., "others", "valid"}} for one election."""
    out = {}
    for row in read_raw(election["raw"]):
        name = row[0].strip()
        votes = {c["party"]: number(row[c["column"]]) for c in election["candidates"]}
        for c in corrections:
            if c["year"] == election["year"] and c["state"] == name:
                if votes[c["party"]] != c["from"]:
                    raise ValueError(f"correction for {name} {c['party']}: raw figure is not {c['from']}")
                votes[c["party"]] = c["to"]
        others = sum(number(row[i]) for i in election.get("others_columns", []))
        col = election.get("valid_column")
        valid = number(row[col]) if col else sum(votes.values()) + others
        out[STATES[name]] = dict(name=name, others=others, valid=valid, **votes)
    return out


def load(story=None):
    """Return the story with each election's "states" filled in."""
    if story is None:
        with open(os.path.join(HERE, "story.json"), encoding="utf-8") as f:
            story = json.load(f)
    for e in story["elections"]:
        e["states"] = state_results(e, story.get("corrections", []))
    return story
