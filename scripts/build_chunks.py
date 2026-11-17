import json

from src.config.settings import settings
from src.loaders.dataset_loader import VendorVerdictDataset
from src.services.validation_service import ValidationService
from src.services.chunking_service import ChunkingService


def main():
    dataset = VendorVerdictDataset().load()
    validation_service = ValidationService(dataset)
    chunking_service = ChunkingService(
        dataset=dataset,
        validation_service=validation_service
    )
    chunks = chunking_service.build_all_chunks()
    settings.output_dir_path.mkdir(
        parents=True,
        exist_ok=True
    )
    output_file = settings.output_dir_path / "chunks.jsonl"

    with open(output_file, "w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")

    print()
    print("="*60)
    print(
        "Vendor Verdict Chunk Build"
    )
    print("="*60)
    print(f"Chunks built: {len(chunks)}")
    print(f"Output file: {output_file}")

    if chunks:
        average = (
            sum(
                chunk.word_count
                for chunk in chunks
            ) / len(chunks)
        )
        print(f"Average words per chunk: {average:.2f}")


if __name__ == "__main__":
    main()