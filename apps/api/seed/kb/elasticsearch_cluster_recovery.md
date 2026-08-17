# Elasticsearch and Search Index Cluster Recovery

## 1. System Architecture
The Search Index service operates a 5-node Elasticsearch cluster managing user catalogs, incident logs, and searchable text documents.

## 2. Diagnosing Cluster Health
Check cluster status using the REST API:
`curl -X GET "http://elasticsearch-prod:9200/_cluster/health?pretty"`

- **Green**: All primary and replica shards are allocated.
- **Yellow**: All primary shards are active, but some replicas are unassigned.
- **Red**: At least one primary shard is missing or corrupted. System searches will return partial or failed results.

## 3. Resolving Out-of-Memory (OOM) and JVM Heap Pressure
When cluster status degrades to RED due to memory exhaustion:
1. Identify high-heap nodes:
   `curl -X GET "http://elasticsearch-prod:9200/_cat/nodes?v&h=name,heap.percent,ram.percent,cpu"`.
2. Clear fielddata caches on overloaded nodes:
   `curl -X POST "http://elasticsearch-prod:9200/_cache/clear?fielddata=true"`.
3. If a node is crash looping, increase JVM heap limit from 4GB to 8GB (ensuring `ES_JAVA_OPTS="-Xms8g -Xmx8g"` does not exceed 50% of total host RAM).
4. Trigger unassigned shard reroute:
   `curl -X POST "http://elasticsearch-prod:9200/_cluster/reroute?retry_failed=true"`.
