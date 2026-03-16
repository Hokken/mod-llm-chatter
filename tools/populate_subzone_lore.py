#!/usr/bin/env python3
"""
Populate subzone_lore.json descriptions using LLM.

Reads the JSON file, finds entries with empty descriptions,
calls an LLM to generate lore-appropriate descriptions, and
writes results back. Can be resumed — skips already-populated
entries.

Usage:
    python populate_subzone_lore.py \
        --provider anthropic \
        --api-key sk-ant-xxx \
        --model claude-haiku-4-5-20251001

    python populate_subzone_lore.py \
        --provider openai \
        --api-key sk-xxx \
        --model gpt-4o-mini
"""

import argparse
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "subzone_lore.json")
# In Docker, /app is read-only. Write to /tmp and
# copy back to host after completion.
OUTPUT_PATH = os.environ.get(
    "LORE_OUTPUT_PATH", JSON_PATH
)

SYSTEM_PROMPT = (
    "You are a World of Warcraft lore expert "
    "specializing in WotLK 3.3.5a. You write "
    "short, evocative descriptions of locations "
    "in Azeroth. Your tone is atmospheric and "
    "lore-grounded — like a well-traveled "
    "adventurer describing a place they know "
    "well. Never reference game mechanics, "
    "player levels, quest hubs, or UI elements. "
    "Write as if the place is real."
)


def build_prompt(zone_name, subzone_name, is_parent):
    """Build the prompt for a zone or subzone."""
    if is_parent:
        return (
            f"World of Warcraft: Wrath of the Lich "
            f"King (3.3.5a).\n\n"
            f"Write a 2-3 sentence lore description "
            f"of {zone_name}. Capture the atmosphere, "
            f"the landscape, who lives there, and any "
            f"notable history or dangers. Write in a "
            f"rich roleplay tone — as if a seasoned "
            f"traveler is describing the region to a "
            f"companion. Do not mention game mechanics "
            f"or player activities.\n\n"
            f"Respond with ONLY the description text, "
            f"nothing else."
        )
    else:
        return (
            f"World of Warcraft: Wrath of the Lich "
            f"King (3.3.5a).\n\n"
            f"{subzone_name} is an area within "
            f"{zone_name}.\n\n"
            f"Write a 1-2 sentence lore description "
            f"of {subzone_name}. Capture what makes "
            f"this specific place distinct — its "
            f"atmosphere, inhabitants, landmarks, or "
            f"history. Write in a rich roleplay tone "
            f"— as if an adventurer is remarking on "
            f"arriving there. Do not mention game "
            f"mechanics, quests, or player activities."
            f"\n\nRespond with ONLY the description "
            f"text, nothing else."
        )


def call_anthropic(client, model, prompt):
    """Call Anthropic API."""
    response = client.messages.create(
        model=model,
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def call_openai(client, model, prompt):
    """Call OpenAI API."""
    response = client.chat.completions.create(
        model=model,
        max_tokens=150,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Populate subzone lore descriptions"
    )
    parser.add_argument(
        "--provider", required=True,
        choices=["anthropic", "openai"],
        help="LLM provider"
    )
    parser.add_argument(
        "--api-key", required=True,
        help="API key"
    )
    parser.add_argument(
        "--model", default=None,
        help="Model name (default: provider's cheapest)"
    )
    parser.add_argument(
        "--parents-only", action="store_true",
        help="Only populate parent zone descriptions"
    )
    parser.add_argument(
        "--subzones-only", action="store_true",
        help="Only populate subzone descriptions"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print prompts without calling LLM"
    )
    parser.add_argument(
        "--save-every", type=int, default=20,
        help="Save JSON every N descriptions (default 20)"
    )
    args = parser.parse_args()

    # Default models
    if not args.model:
        if args.provider == "anthropic":
            args.model = "claude-haiku-4-5-20251001"
        else:
            args.model = "gpt-4o-mini"

    # Load JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    zones = data.get("zones", {})

    # Count work
    total_parents = 0
    total_subzones = 0
    skip_parents = 0
    skip_subzones = 0

    for zid, zdata in zones.items():
        if not args.subzones_only:
            if zdata.get("description", ""):
                skip_parents += 1
            total_parents += 1
        if not args.parents_only:
            for sid, sdata in zdata.get(
                "subzones", {}
            ).items():
                if sdata.get("description", ""):
                    skip_subzones += 1
                total_subzones += 1

    todo_parents = total_parents - skip_parents
    todo_subzones = total_subzones - skip_subzones
    todo_total = 0
    if not args.subzones_only:
        todo_total += todo_parents
    if not args.parents_only:
        todo_total += todo_subzones

    print(f"Zones: {total_parents} total, "
          f"{skip_parents} already done, "
          f"{todo_parents} to populate")
    print(f"Subzones: {total_subzones} total, "
          f"{skip_subzones} already done, "
          f"{todo_subzones} to populate")
    print(f"Total calls needed: {todo_total}")
    print(f"Provider: {args.provider}, "
          f"Model: {args.model}")
    print()

    if todo_total == 0:
        print("Nothing to do — all descriptions "
              "already populated!")
        return

    if args.dry_run:
        print("=== DRY RUN ===")
        count = 0
        for zid, zdata in zones.items():
            if not args.subzones_only:
                if not zdata.get("description", ""):
                    p = build_prompt(
                        zdata["name"], "", True)
                    print(f"\n[ZONE {zid}] "
                          f"{zdata['name']}:")
                    print(f"  {p[:120]}...")
                    count += 1
                    if count >= 5:
                        print(f"\n... and "
                              f"{todo_total - 5} more")
                        return
        return

    # Initialize client
    call_fn = None
    if args.provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(
            api_key=args.api_key)
        call_fn = lambda p: call_anthropic(
            client, args.model, p)
    else:
        from openai import OpenAI
        client = OpenAI(api_key=args.api_key)
        call_fn = lambda p: call_openai(
            client, args.model, p)

    # Process
    done = 0
    errors = 0
    start_time = time.time()

    def save_json():
        with open(OUTPUT_PATH, "w",
                  encoding="utf-8") as f:
            json.dump(data, f, indent=2,
                      ensure_ascii=False)

    # Parent zones first
    if not args.subzones_only:
        for zid, zdata in zones.items():
            if zdata.get("description", ""):
                continue
            zone_name = zdata["name"]
            prompt = build_prompt(
                zone_name, "", True)
            try:
                desc = call_fn(prompt)
                zdata["description"] = desc
                done += 1
                elapsed = time.time() - start_time
                rate = done / elapsed if elapsed else 0
                eta = ((todo_total - done) / rate
                       if rate else 0)
                print(f"[{done}/{todo_total}] "
                      f"ZONE {zone_name}: "
                      f"{desc[:60]}... "
                      f"({eta:.0f}s remaining)")
            except Exception as e:
                errors += 1
                print(f"[ERROR] ZONE {zone_name}: "
                      f"{e}")
                time.sleep(2)

            if done % args.save_every == 0:
                save_json()
                print(f"  (saved at {done})")

    # Subzones
    if not args.parents_only:
        for zid, zdata in zones.items():
            zone_name = zdata["name"]
            subzones = zdata.get("subzones", {})
            for sid, sdata in subzones.items():
                if sdata.get("description", ""):
                    continue
                sub_name = sdata["name"]
                prompt = build_prompt(
                    zone_name, sub_name, False)
                try:
                    desc = call_fn(prompt)
                    sdata["description"] = desc
                    done += 1
                    elapsed = (
                        time.time() - start_time)
                    rate = (done / elapsed
                            if elapsed else 0)
                    eta = ((todo_total - done) / rate
                           if rate else 0)
                    print(
                        f"[{done}/{todo_total}] "
                        f"{zone_name} > {sub_name}: "
                        f"{desc[:50]}... "
                        f"({eta:.0f}s remaining)")
                except Exception as e:
                    errors += 1
                    print(
                        f"[ERROR] {zone_name} > "
                        f"{sub_name}: {e}")
                    time.sleep(2)

                if done % args.save_every == 0:
                    save_json()
                    print(f"  (saved at {done})")

    # Final save
    save_json()
    elapsed = time.time() - start_time
    print(f"\nDone! {done} descriptions populated "
          f"in {elapsed:.0f}s, {errors} errors.")


if __name__ == "__main__":
    main()
