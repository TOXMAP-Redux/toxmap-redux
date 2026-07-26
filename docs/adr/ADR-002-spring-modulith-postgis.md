# ADR-002: Java · Spring Modulith · PostGIS · React/MapLibre

| Field | Value |
|-------|-------|
| **ID** | ADR-002 |
| **Title** | Spring Modulith + PostGIS + React/MapLibre as Platform-Oriented Architecture |
| **Date** | 2026-07-15 |
| **Status** | **Rejected — Superseded by [ADR-001](ADR-001-fastapi-postgis-react.md)** |
| **Deciders** | Architecture Review |
| **NLM Sources** | [PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/) · [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/) · [UCD Usability Study 2011](https://dpcpsi.nih.gov/sites/g/files/mnhszr346/files/FR508_10-4004_NLM_11-03-11.pdf) |
| **Supersedes** | — |
| **Superseded by** | [ADR-001](ADR-001-fastapi-postgis-react.md) (2026-07-16) |

---

## Context

Same context as [ADR-001](ADR-001-fastapi-postgis-react.md). Per NLM peer-reviewed sources ([PMC2703818](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2703818/), [PMC4251466](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4251466/)), the original TOXMAP was itself a **Java + Apache Struts** application (2004–2012), making Spring Boot a natural evolution of that lineage. The original also integrated multiple independent data domains: TRI, Superfund/NPL, U.S. Census demographics, Canadian NPRI, nuclear plant locations, and congressional districts — a multi-module structure that aligns strongly with Spring Modulith's design philosophy.

This ADR is evaluated for teams with strong Java expertise or anticipating growth into a broader environmental data platform (e.g., adding EPA ECHO, ATSDR CERCLIS, or EJScreen modules in the future).

The driving question: **Does the structure discipline of Spring Modulith justify its additional weight for a geospatial read-heavy application with multiple data domains?**

---

## Decision

**If adopted, the following stack would be used:**

```
Backend:           Java 21 + Spring Boot 3.3 + Spring Modulith 1.2
Geospatial ORM:    Hibernate Spatial 6.x + JTS Topology Suite
Database:          PostgreSQL 16 + PostGIS 3.4
Data Ingestion:    Spring Batch 5 (CSV → PostGIS ETL)
Frontend:          React 18 + MapLibre GL JS (via react-map-gl)
Map Tiles:         Protomaps (self-hosted PMTiles) or OpenFreeMap
Charts:            Recharts
Build:             Gradle 8 (Kotlin DSL)
Containerization:  Docker + Docker Compose
CI/CD:             GitHub Actions
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser Client                        │
│  React 18 · MapLibre GL · react-map-gl · Recharts           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS (REST/JSON)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Spring Boot 3.3 Application                     │
│          (Spring Modulith — enforced module boundaries)      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Module: facility                                       │ │
│  │  FacilityController → FacilityService                  │ │
│  │  → FacilityRepository (Spring Data JPA + Hibernate Geo)│ │
│  └─────────────────────────┬──────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Module: chemical                                       │ │
│  │  ChemicalController → ChemicalService                  │ │
│  │  → ChemicalRepository                                  │ │
│  └─────────────────────────┬──────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Module: release                                        │ │
│  │  ReleaseController → ReleaseService                    │ │
│  │  → ReleaseRepository                                   │ │
│  └─────────────────────────┬──────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Module: ingestion                                      │ │
│  │  Spring Batch Jobs: TriCsvImportJob                     │ │
│  │  ItemReader → ItemProcessor → JdbcBatchItemWriter       │ │
│  └─────────────────────────┬──────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Module: export                                         │ │
│  │  ExportController → CsvStreamingService                │ │
│  └─────────────────────────┬──────────────────────────────┘ │
└─────────────────────────────┼───────────────────────────────┘
                              │ JDBC (HikariCP)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL 16 + PostGIS 3.4                     │
│  (Same schema as ADR-001)                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Structure (Spring Modulith)

```
src/main/java/com/example/toxmap/
├── ToxmapApplication.java
├── facility/                          ← TRI facilities module
│   ├── Facility.java                  # @Entity with Point geometry (JTS)
│   ├── FacilityRepository.java        # Spring Data JPA + Hibernate Spatial
│   ├── FacilityService.java
│   └── FacilityController.java
├── chemical/                          ← TRI chemicals module
│   ├── Chemical.java
│   ├── ChemicalRepository.java        # auto-complete search queries
│   ├── ChemicalService.java
│   └── ChemicalController.java
├── release/                           ← TRI release events module
│   ├── ReleaseEvent.java              # medium breakdown: air/water/land/underground
│   ├── ReleaseRepository.java         # 15-year trend queries
│   ├── ReleaseService.java
│   └── ReleaseController.java
├── superfund/                         ← Superfund/NPL module (NLM 2006 enhancement)
│   ├── SuperfundSite.java             # HRS score, status, contaminants[]
│   ├── SuperfundRepository.java
│   ├── SuperfundService.java
│   └── SuperfundController.java
├── demographics/                      ← Census demographics module (NLM 2006-2013)
│   ├── CensusCounty.java              # MultiPolygon geometry, income/age/pop
│   ├── CensusCountyRepository.java
│   ├── DemographicsService.java
│   └── DemographicsController.java
├── layers/                            ← Optional overlay layers (NLM 2013 redesign)
│   ├── NuclearPlant.java
│   ├── Nprifacility.java              # Canadian NPRI
│   ├── LayerRepository.java
│   └── LayerController.java
├── ingestion/                         ← ETL module (internal — not exposed as API)
│   ├── TriCsvImportJobConfig.java     # Spring Batch: TRI CSV
│   ├── SuperfundImportJobConfig.java  # Spring Batch: NPL sites
│   ├── CensusImportJobConfig.java     # Spring Batch: Census TIGER
│   ├── TriRecordProcessor.java
│   └── TriRecordFieldSetMapper.java
└── export/                            ← CSV streaming export module
    ├── ExportController.java
    └── CsvStreamingService.java
```

**Spring Modulith enforces:**
- Each domain (facility, superfund, demographics, layers) has hard module boundaries
- `ingestion` is internal — no other module can import its implementation
- Module integration tests via `@ApplicationModuleTest`
- Architecture verification at test time (no hidden cycles)
- This multi-domain structure is the **primary argument for ADR-002 over ADR-001** — it mirrors the multi-data-source design of the original NLM TOXMAP

---

## Key Implementation Patterns

### Geospatial Entity (Hibernate Spatial + JTS)

```java
import org.locationtech.jts.geom.Point;
import org.hibernate.annotations.Type;

@Entity
@Table(name = "facilities")
public class Facility {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tri_facility_id", unique = true, nullable = false)
    private String triFacilityId;

    @Column(name = "location", columnDefinition = "GEOMETRY(POINT,4326)")
    private Point location;   // org.locationtech.jts.geom.Point

    // ... other fields
}
```

### Geospatial Repository Query (JPQL + PostGIS function)

```java
public interface FacilityRepository extends JpaRepository<Facility, Long> {

    @Query(value = """
        SELECT f FROM Facility f
        WHERE function('ST_DWithin',
            function('ST_Transform', f.location, 3857),
            function('ST_Transform', function('ST_GeomFromText', :wkt, 4326), 3857),
            :radiusMeters) = true
        """)
    List<Facility> findWithinRadius(
        @Param("wkt") String pointWkt,
        @Param("radiusMeters") double radiusMeters
    );
}
```

### Spring Batch TRI CSV Import

```java
@Configuration
public class TriCsvImportJobConfig {

    @Bean
    public Job triImportJob(JobRepository repo, Step triImportStep) {
        return new JobBuilder("triImportJob", repo)
            .start(triImportStep)
            .build();
    }

    @Bean
    public Step triImportStep(JobRepository repo,
                              PlatformTransactionManager txMgr,
                              FlatFileItemReader<TriRecord> reader,
                              TriRecordProcessor processor,
                              JdbcBatchItemWriter<Facility> writer) {
        return new StepBuilder("triImportStep", repo)
            .<TriRecord, Facility>chunk(500, txMgr)
            .reader(reader)
            .processor(processor)
            .writer(writer)
            .build();
    }

    @Bean
    public FlatFileItemReader<TriRecord> triCsvReader(@Value("${tri.csv.path}") Resource csv) {
        return new FlatFileItemReaderBuilder<TriRecord>()
            .name("triCsvReader")
            .resource(csv)
            .linesToSkip(1)
            .delimited()
            .names(TriRecord.FIELD_NAMES)
            .fieldSetMapper(new TriRecordFieldSetMapper())
            .build();
    }
}
```

---

## Gradle Dependencies

```kotlin
// build.gradle.kts
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.modulith:spring-modulith-starter-core")
    implementation("org.springframework.batch:spring-batch-core")

    // PostGIS / Hibernate Spatial
    implementation("org.hibernate.orm:hibernate-spatial")
    implementation("org.locationtech.jts:jts-core:1.19.0")
    runtimeOnly("org.postgresql:postgresql")

    // API docs
    implementation("org.springdoc:springdoc-openapi-starter-webmvc-ui:2.5.0")

    // Spring Modulith test support
    testImplementation("org.springframework.modulith:spring-modulith-starter-test")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.batch:spring-batch-test")
}
```

---

## Consequences

### Positive

- **Enforced module boundaries** — Spring Modulith verifies no illegal cross-module dependencies at compile/test time; critical if this platform expands (e.g., adding ECHO, CERCLIS, or EJScreen modules)
- **Spring Batch for ETL** — production-grade job execution with restart/retry, chunk processing, and job history; handles large TRI CSV files robustly
- **JVM performance** — Spring Boot with virtual threads (Java 21 Loom) provides excellent throughput for concurrent API requests
- **Mature ecosystem** — Spring Data JPA, Spring Security, Spring Boot Actuator are battle-tested for production deployments
- **Type safety** — Java's type system catches more errors at compile time; valuable for complex data transformations

### Negative

- **Heavier boilerplate** — a single endpoint requires Controller + Service + Repository + Entity + DTO + Mapper; significantly more code than FastAPI
- **Java geospatial tooling is verbose** — JTS `Point` manipulation requires more code than geopandas; GeoJSON serialization requires custom Jackson config
- **Spring Batch complexity** — for a periodic CSV ingest job, Spring Batch is arguably over-engineered; pandas + SQLAlchemy achieves the same in fewer lines
- **Slower prototyping** — Java compile-run cycle slower than Python; higher barrier for open-source contributors unfamiliar with Spring
- **No native pandas equivalent** — complex data cleaning (TRI data has many null/invalid coordinates) is more natural in Python

## Zero-Budget Hosting Compatibility (ADR-004)

> **Short answer: No — the $0 budget constraint makes ADR-002 harder, not easier.**

The zero-budget hosting strategy in [ADR-004](ADR-004-zero-budget-hosting.md) defines three deployment options. Here is how Spring Modulith fares against each:

### Option A: Static-First (Cloudflare Pages + DuckDB WASM) — Backend-Agnostic

Option A **eliminates the backend entirely** for production — neither Spring Modulith nor FastAPI runs in production. Both are equal here. The data pipeline still runs as a Python script in GitHub Actions regardless of backend choice, because geopandas/pandas is the correct tool for TRI CSV processing.

**Verdict for Option A: Draw.** ADR-001 still wins overall because the Python ingestion pipeline is required anyway — there is no benefit to adding a Java backend that isn't used in production.

### Option B: Fly.io Free Tier — Spring Boot Fails the RAM Test

Fly.io's free tier provides **256 MB RAM per VM**. This is the hard constraint:

| Runtime | Idle RAM | Under Load | Fits 256 MB? |
|---------|---------|------------|-------------|
| FastAPI + uvicorn (Python) | ~60 MB | ~120 MB | ✅ Comfortable |
| Spring Boot 3.x (JVM, standard) | ~280 MB | ~450 MB | ❌ Exceeds limit |
| Spring Boot 3.x + GraalVM native image | ~90 MB | ~160 MB | ✅ Possible — but complex |

**Standard Spring Modulith will OOM-kill on Fly.io's free 256 MB VM.** The JVM alone consumes more than the free tier allows before the application even handles a request.

The only escape is **GraalVM native compilation** — which compiles the Spring app to a platform-specific binary at build time, eliminating JVM overhead. But this creates significant new problems:
- Hibernate Spatial's reflection-heavy internals require extensive GraalVM `reflect-config.json` hints
- Native compilation breaks if any dependency uses runtime reflection not declared at build time
- Build time: ~10–15 minutes per compile (consumes GitHub Actions free minutes)
- Debugging native images requires specialist knowledge
- Spring Modulith's module verification uses reflection — needs explicit native config

**Verdict for Option B: ADR-001 (FastAPI) is the correct choice.** FastAPI runs comfortably within 256 MB. Spring Modulith with standard JVM does not. GraalVM native is theoretically possible but adds weeks of configuration work for no functional benefit over FastAPI.

### Option C: Docker Compose Localhost — Both Work Fine

No RAM constraints on a developer machine. Both stacks run without issue.

**Verdict for Option C: Draw.**

### Summary

| ADR-004 Option | ADR-001 (FastAPI) | ADR-002 (Spring Modulith) |
|----------------|------------------|--------------------------|
| A — Static + DuckDB WASM | ✅ | ✅ (draw; Python pipeline needed anyway) |
| B — Fly.io + Supabase | ✅ Fits 256 MB | ❌ OOMs (needs GraalVM native = weeks of work) |
| C — Docker Compose | ✅ | ✅ (draw) |

**The $0 budget constraint reinforces ADR-001, not ADR-002.**

---

## When to Choose This ADR Over ADR-001

| Condition | Prefer ADR-002 |
|-----------|---------------|
| Team is exclusively Java | ✅ |
| Platform expected to grow to 5+ data domains (TRI + ECHO + CERCLIS + EJScreen + ...) | ✅ |
| Enterprise deployment requiring Spring Security + Spring Boot Actuator out of the box | ✅ |
| Contribution pool is Java-heavy (e.g., enterprise open-source project) | ✅ |
| **Budget is $0 and Option B (Fly.io) is the deployment target** | ❌ Spring JVM OOMs at 256 MB |
| **Budget is $0 and Option A (static) is the deployment target** | ❌ Python pipeline needed anyway |
| Team prioritizes fast prototyping and geospatial data wrangling | ❌ (use ADR-001) |
| Team is Python-fluent | ❌ (use ADR-001) |

---

## Alternatives Considered

- **[ADR-001](ADR-001-fastapi-postgis-react.md)** (FastAPI): Preferred for geospatial-heavy, fast-iteration use cases
- **Micronaut + GraalVM**: Lower cold start; rejected due to smaller community and limited Hibernate Spatial support
- **Quarkus + Panache**: More ergonomic than Spring for REST; rejected due to less mature spatial extension support

---

## Review Checklist

- [ ] Spring Modulith module graph verified clean (no cycles)
- [ ] Hibernate Spatial `ST_DWithin` query benchmarked on 90K facilities
- [ ] Spring Batch job tested against full 2022 TRI CSV (restart/retry scenarios)
- [ ] `@ApplicationModuleTest` coverage for `facility`, `release`, `ingestion` modules
- [ ] ADR reviewed by at least two contributors before status → Accepted





