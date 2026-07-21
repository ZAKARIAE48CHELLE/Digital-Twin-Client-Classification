import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from personas.persona_library import seed_default_personas

def main():
    print("Seeding OSMOS Persona Library into PostgreSQL...")
    seeded_count = seed_default_personas()
    print(f"[OK] Seeding complete: {seeded_count} personas upserted.")


if __name__ == "__main__":
    main()
