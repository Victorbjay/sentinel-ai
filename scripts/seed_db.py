import asyncio
import json
from pathlib import Path
from app.core.database import AsyncSessionLocal, init_db
from app.models.verified_fact import VerifiedFact
from app.services.rag import generate_mock_or_deterministic_embedding


async def seed():
    print("[Seed] Initializing database and extensions...")
    await init_db()

    seed_file = Path(__file__).resolve().parent.parent / "data" / "seeds" / "inec_verified_facts.json"
    if not seed_file.exists():
        print(f"[Seed] Error: Seed file not found at {seed_file}")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        facts_data = json.load(f)

    async with AsyncSessionLocal() as session:
        for item in facts_data:
            embedding = generate_mock_or_deterministic_embedding(
                f"{item['topic']} {item['claim_summary']} {item['official_fact']}"
            )
            fact = VerifiedFact(
                topic=item["topic"],
                claim_summary=item["claim_summary"],
                official_fact=item["official_fact"],
                official_source=item["official_source"],
                source_url=item.get("source_url"),
                embedding=embedding,
            )
            session.add(fact)
        await session.commit()
        print(f"[Seed] Successfully seeded {len(facts_data)} verified electoral facts into pgvector!")


if __name__ == "__main__":
    asyncio.run(seed())
