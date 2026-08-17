# Kafka Stream and Telemetry Pipeline Troubleshooting

## 1. Architecture Overview
The Analytics Pipeline consumes high-throughput telemetry, audit events, and metric streams via Apache Kafka cluster `prod-kafka-cluster`.

## 2. Common Symptoms & Root Causes
- **Consumer Group Lag Spikes**: Occurs when downstream workers cannot process batch payloads quickly enough or database write locks throttle consumer progress.
- **Partition Rebalance Storms**: Triggered by pod OOM kills, network heartbeat timeouts (`max.poll.interval.ms` exceeded), or dynamic scaling flapping.
- **Dead Letter Queue (DLQ) Overflow**: Poison pill messages with malformed schema payloads failing deserialization repeatedly.

## 3. Step-by-Step Recovery Steps
1. **Check Consumer Group Lag**:
   `kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group analytics-telemetry-group`.
2. **Scale Consumer Replicas**:
   If partition count allows (e.g. 12 partitions with only 4 active pods), scale consumer fleet to match partition count:
   `kubectl scale deployment/analytics-consumer --replicas=12 -n production`.
3. **Handle Poison Pill Payloads**:
   If a malformed message is stalling partition progress, route it directly to the DLQ topic `analytics-dlq` and advance the consumer offset:
   `kafka-consumer-groups.sh --bootstrap-server kafka:9092 --group analytics-telemetry-group --reset-offsets --shift-by 1 --execute --topic telemetry-events`.
