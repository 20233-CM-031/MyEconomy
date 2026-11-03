# ADR-0001: Start with a Modular Monolith

- **Status:** Accepted for initial implementation
- **Date:** 2026-11-03

## Context
The product vision spans multiple domains, but there is no deployed workload, independent team boundary or scale evidence yet. Premature microservices would add network failure modes, distributed transactions, deployment complexity and operational overhead before those costs are justified.

## Decision
Begin with one deployable backend organized as strict modules and inward-facing domain/application layers. Define explicit interfaces at module boundaries. Keep long-running external work behind durable jobs and an outbox once persistence is introduced.

## Consequences
**Positive:** easier local development, integration testing, transactional consistency, faster iteration and simpler deployment.
**Negative:** requires discipline to preserve module boundaries; one deployment shares a failure domain.
**Revisit when:** independent scaling, distinct team ownership, security isolation or reliability objectives justify extracting a module.
