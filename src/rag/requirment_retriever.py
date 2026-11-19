from src.loaders.dataset_loader import VendorVerdictDataset

from src.models.evidence_package import EvidencePackage, RetrievedChunk

from src.rag.queries import get_requirement_query

from src.rag.retriever import EvidenceRetriever


class RequirementRetriever:

    def __init__(
            self,
            dataset: VendorVerdictDataset,
            retriever: EvidenceRetriever
    ):
        self.dataset = dataset
        self.retriever = retriever


    def retrieve(
            self,
            case_id: str,
            requirment_id: str,
            top_k: int = 8,
    )-> EvidencePackage:
        # GET Authoritative requirment from
        # requirments.json
        requirement = self.dataset.get_requirement(requirment_id)

        # GET retrieval query
        query = get_requirement_query(requirment_id)

        # Retrieve extra candidates
        # because deduplication may remove some

        candidate_count = max(top_k * 2, 10)

        results = (
            self.retriever.search(
                case_id=case_id,
                query=query,
                top_k=candidate_count
            )
        )

        # Remove duplicate chunks and limit too many chunks
        # from the same page

        cleaned = (
            self._deduplicate(
                results,
                max_per_page=2
            )
        )


        # FInal top-k

        cleaned = cleaned[:top_k]

        # Convert to typed objects

        chunks = [
            RetrievedChunk(
                chunk_id=result['chunk_id'],
                page_id=result['metadata']['page_id'],
                text=result['text'],
                distance=result['distance'],
                metadata=result['metadata']
            )
            for result in cleaned
        ]

        # Unique Page IDs

        page_ids = list(
            dict.fromkeys(
                chunk.page_id
                for chunk in chunks
            )
        )

        # Build final EvidencePackage

        return EvidencePackage(
            case_id=case_id,
            requirement_id=requirment_id,
            requirement_title=requirement['title'],
            field_name=requirement['field'],
            rule_name=requirement['rule'],
            rule_params=requirement.get('params', {}),
            severity=requirement['severity'],
            query=query,
            chunks=chunks,
            page_ids=page_ids,
            evidence_count=len(chunks)
        )


    @staticmethod
    def _deduplicate(
        results: list[dict],
        max_per_page: int = 3
    ) -> list[dict]:
        seen_hashes = set()
        page_counts = {}
        deduplicated = []
        for result in results:
            metadata = (
                result.get('metadata', {})
            )
            page_id = metadata.get('page_id')
            content_hash = metadata.get("content_hash")
            # remove exact duplicate chunks
            if content_hash:
                if content_hash in seen_hashes:
                    continue
                seen_hashes.add(content_hash)

            # Limit Chunks from same page

            if page_id:
                current_count = (
                    page_counts.get(page_id, 0)
                )

                if current_count >= max_per_page:
                    continue
                page_counts[page_id] = current_count + 1
            deduplicated.append(result)

        return deduplicated