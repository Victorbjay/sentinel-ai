import asyncio
import json
from pathlib import Path
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models.verified_fact import VerifiedFact
from app.services.embeddings import generate_embedding


async def seed():
    print("[Seed] Initializing database and extensions...")
    await init_db()

    seed_file = Path(__file__).resolve().parent.parent / "data" / "seeds" / "inec_verified_facts.json"
    if not seed_file.exists():
        print(f"[Seed] Error: Seed file not found at {seed_file}")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        facts_data = json.load(f)

    created_count = 0
    updated_count = 0

    async with AsyncSessionLocal() as session:
        for item in facts_data:
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
                updated_count += 1
            else:
                fact = VerifiedFact(
                    topic=item["topic"],
                    claim_summary=item["claim_summary"],
                    official_fact=item["official_fact"],
                    official_source=item["official_source"],
                    source_url=item.get("source_url"),
                    embedding=embedding,
                )
                session.add(fact)
                created_count += 1

        await session.commit()
        print(
            f"[Seed] Completed! Created: {created_count}, Updated with semantic embeddings: {updated_count}"
        )


if __name__ == "__main__":
    asyncio.run(seed())
