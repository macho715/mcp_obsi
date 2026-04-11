-- 5) embedding_index 적재
-- 가정: ingest.embedding_stage(search_doc_key, embedding_model,
--       embedding_version, content_sha256, embedding, is_active)
--       embedding type = vector(1536)
-- =========================================================

delete from ontology.embedding_index ei
using ontology.search_doc sd
join ingest.embedding_stage st
  on st.search_doc_key = sd.search_doc_key
where ei.search_doc_id = sd.search_doc_id;

insert into ontology.embedding_index (
  search_doc_id,
  embedding_model,
  embedding_version,
  content_sha256,
  embedding,
  is_active
)
select
  sd.search_doc_id,
  st.embedding_model,
  st.embedding_version,
  st.content_sha256,
  st.embedding,
  coalesce(st.is_active, true)
from ingest.embedding_stage st
join ontology.search_doc sd
  on sd.search_doc_key = st.search_doc_key;
