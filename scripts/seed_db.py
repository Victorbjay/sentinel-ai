import asyncio
import csv
import json
from pathlib import Path
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models.verified_fact import VerifiedFact
from app.services.embeddings import generate_embedding


async def _upsert_fact(session, item: dict) -> str:
    embedding = generate_embedding(
        f"{item['topic']}: {item['claim_summary']}. {item['official_fact']}"
    )
    existing = (
        await session.scalars(
            select(VerifiedFact).where(
                VerifiedFact.topic == item["topic"],
                VerifiedFact.claim_summary == item["claim_summary"],
            )
        )
    ).first()

    if existing:
        existing.official_fact = item["official_fact"]
        existing.official_source = item["official_source"]
        existing.source_url = item.get("source_url")
        existing.embedding = embedding
        return "updated"

    fact = VerifiedFact(
        topic=item["topic"],
        claim_summary=item["claim_summary"],
        official_fact=item["official_fact"],
        official_source=item["official_source"],
        source_url=item.get("source_url"),
        embedding=embedding,
    )
    session.add(fact)
    return "created"


async def seed():
    print("[Seed] Initializing database and extensions...")
    await init_db()

    root_dir = Path(__file__).resolve().parent.parent
    inec_file = root_dir / "data" / "seeds" / "inec_verified_facts.json"
    faq_file = root_dir / "data" / "official" / "voter_info_faq_multilingual.csv"

    facts_to_load = []
    if inec_file.exists():
        with open(inec_file, "r", encoding="utf-8") as f:
            facts_to_load.extend(json.load(f))

    if faq_file.exists():
        with open(faq_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                facts_to_load.append({
                    "topic": f"Voter FAQ: {row['topic'].replace('_', ' ').title()}",
                    "claim_summary": row["en"],
                    "official_fact": f"{row['answer_en']} (Pidgin: {row['pcm_draft']})",
                    "official_source": f"Official #AI4Elections Multilingual Voter FAQ ({row['faq_id']})",
                    "source_url": "https://inecnigeria.org",
                })

    created_count = 0
    updated_count = 0

    async with AsyncSessionLocal() as session:
        for item in facts_to_load:
            status = await _upsert_fact(session, item)
            if status == "created":
                created_count += 1
            else:
                updated_count += 1
        await session.commit()
        print(
            f"[Seed] Completed! Created: {created_count}, Updated with semantic embeddings: {updated_count} (Total: {len(facts_to_load)})"
        )


if __name__ == "__main__":
    asyncio.run(seed())
