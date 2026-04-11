$ErrorActionPreference = "Stop"

$uri = if ($env:LOCAL_RAG_PORT) {
  "http://127.0.0.1:$($env:LOCAL_RAG_PORT)/health"
} else {
  "http://127.0.0.1:8010/health"
}

Invoke-WebRequest -UseBasicParsing -Uri $uri | Select-Object -ExpandProperty Content
