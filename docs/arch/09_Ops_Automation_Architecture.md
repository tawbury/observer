# Observer Architecture

**Version:** v1.0.0  
**Status:** Consolidated Architecture Specification  
**Consolidation Date:** 2026-01-09  
**Scope:** Current Observer implementation and validated behavior

---

## 0. Document Status

### 0.1 Purpose

This document consolidates all Observer-related architecture documents into a single Source of Truth (SSoT) for the QTS Observer system.

### 0.2 Source Documents

**Core/Canonical Sources (Merged):**
- QTS_Observer_Contract.md v1.0.0
- QTS_Observer_Core_Architecture.md v1.0.0

**Phase & Decision Documents (Summarized):**
- QTS_Ob_Phase_5_Scope.md
- QTS_Ob_Phase_5_Contracts.md
- QTS_Ob_Phase_5_Implementation.md
- QTS_Ob_Phase_10_Market Ob&Log.md
- QTS_Ob_Phase_11_A&D_Pipeline.md
- QTS_Ob_Phase_12~15 기준문서.md
- QTS_Ob_Phase_14.md
- QTS_Ob_Phase_14_End.md
- QTS_Ob_Phase_15_Architecture.md
- QTS_Ob_Phase_15_Start.md
- QTS_Ob_Phase_15_End.md
- QTS_Ob_검증 체크리스트.md

### 0.3 What This Document Does NOT Include

This document does NOT include:
- Future extension designs (see §10 Deferred Designs)
- Session/execution boundary documents
- Implementation guides or code-level details
- QTS integration runtime binding (see Reference Documents)
- Adaptive/high-frequency snapshot behavior (design-only, not implemented)

---

## 1. Observer Role & Responsibility

### 1.1 Purpose

Observer-Core is a **judgment-free observation and recording system** within QTS.

Primary purpose:
- Observe market and system events
- Record observation state as snapshots
- Store observations without interpretation or decision-making

### 1.2 Position Declaration

Observer-Core is designed as a **QTS-Compatible Independent Data Producer**:
- Can run standalone or integrated within QTS
- Does not depend on QTS strategy, execution, or risk engines
- Maintains data compatibility regardless of execution mode

### 1.3 Primary Use Case Priority

While Observer maintains a general-purpose structure, the **primary design priority is scalp strategy operation**:
- High-frequency decision data collection
- Frequent judgment, blocking, and non-execution state recording
- Post-hoc reconstruction capability for scalp trading decisions

### 1.4 Ownership Boundaries

Observer-Core is responsible for:
- Receiving ObservationSnapshot structures
- Creating PatternRecord wrappers
- Maintaining empty tag/label slots
- Dispatching records to EventBus
- Ensuring data contract compliance

### 1.5 Explicit Non-Responsibilities

Observer-Core does NOT and will NOT:
- Make strategy judgments
- Evaluate conditions
- Make trading decisions
- Manage position state
- Approve risk
- Generate learning labels
- Create regime classifications
- Generate condition tags
- Generate outcome labels
- Modify or correct input data
- Normalize or transform data
- Calculate indicators
- Intervene in ETEDA pipeline

**Contract Violation:** Any implementation that performs these actions violates the Observer contract.

---

## 2. Position in QTS Architecture

### 2.1 Relationship to ETEDA Pipeline

Observer operates **outside and before** the ETEDA pipeline:

```
[Real World Data]
    ↓
[Observer] ← Phase 15 position
    ↓
[Extract]
    ↓
[Transform]
    ↓
[Evaluate]
    ↓
[Decide]
    ↓
[Act]
```

Observer is NOT:
- Part of the strategy system
- Part of the engine pipeline
- Part of broker execution

Observer is:
- A pre-stage device that makes real-world data observable

### 2.2 Relationship to Ops Layer

Observer is positioned within the Ops Layer as a **data collection infrastructure component**.

Observer does NOT:
- Own scheduling or triggering
- Control execution flow
- Manage automation policies

### 2.3 Data Flow Position

Observer sits at the ingress boundary:

```
External/QTS Event
 → ObservationSnapshot
 → Observer
 → PatternRecord
 → EventBus
 → Sink
 → Data Asset (jsonl)
```

Each stage is isolated and does not reference internal state of other stages.

---

## 3. Core Components

### 3.1 Observer Component

**Responsibility:**
- Receive ObservationSnapshot
- Create PatternRecord structure
- Maintain empty tag/label slots
- Dispatch to EventBus

**Boundaries:**
- Does NOT create regime classifications
- Does NOT generate condition judgments
- Does NOT generate outcome labels
- Does NOT modify snapshot content

**Implementation Status:** Implemented

### 3.2 EventBus Component

**Responsibility:**
- Fan-out PatternRecord to registered Sinks
- Isolate individual Sink failures from overall flow

**Boundaries:**
- Does NOT receive external events
- Does NOT connect to broker APIs
- Does NOT normalize data
- Does NOT determine retry policies

**Implementation Status:** Implemented

### 3.3 Sink Component

**Responsibility:**
- Write PatternRecord to persistent storage
- Follow append-only recording rules
- Comply with path and format rules

**Boundaries:**
- Does NOT modify PatternRecord content
- Does NOT determine storage policies (defined by Contract)

**Implementation Status:** Implemented (JsonlFileSink)

### 3.4 PatternRecord (Data Unit)

**Responsibility:**
- Wrap ObservationSnapshot without modification
- Provide slots for future tagging/labeling
- Maintain metadata for tracking

**Boundaries:**
- Does NOT compute tags or labels
- Does NOT modify snapshot fields

**Implementation Status:** Implemented

---

## 4. Snapshot Architecture

### 4.1 Snapshot Definition

ObservationSnapshot is the **minimum observation unit** that records market or system state at a specific point in time without judgment.

Structure:
```
ObservationSnapshot
 ├─ Meta (timestamp, session_id, run_id, mode, observer_version)
 ├─ Context (source, stage, symbol, market)
 ├─ Observation (inputs, computed, state)
 └─ Trace (schema_version, config_snapshot, notes)
```

### 4.2 Snapshot Creation Responsibility

**Observer does NOT create snapshots.**

Snapshot creation is external to Observer-Core:
- QTS internal modules
- Broker adapters
- Simulators
- External collection systems

Observer assumes snapshots already satisfy contract structure when received.

### 4.3 Trigger Model

**Currently Implemented:**
- Periodic snapshots: Fixed interval (default 1.0 second)
- Event-driven snapshots: Market data events, tick events

**Explicitly NOT Implemented:**
- Adaptive frequency based on market conditions
- High-frequency mode switching (e.g., 0.5s intervals)
- SCALP-event-triggered frequency changes
- Conditional snapshot cadence adjustment

### 4.4 Frequency Behavior

**Fixed Behavior:**
- Default: 1.0 second intervals
- Configurable via `interval_sec` parameter
- No conditional frequency changes in current implementation

**Unsupported Behaviors:**
- Dynamic interval adjustment
- Event-based frequency switching
- Strategy-mode-dependent snapshot rates

### 4.5 Storage & Determinism

**Storage Mechanism:** File-based (JSONL)

**Storage Location:** 
```
<PROJECT_ROOT>/data/observer/
```
- Path is execution-location-independent
- Determined by `paths.py` (single SSoT)

**Storage Rules:**
- Append-only (no overwrites)
- 1 line = 1 PatternRecord
- UTF-8 encoding
- No ordering guarantees for parallel writes

**Determinism:** Explicit and deterministic
- Snapshot behavior is code-explicit
- No implicit or inferred logic
- All trigger conditions are documented

---

## 5. Execution & Control Flow

### 5.1 How Observer Runs

Observer lifecycle:
1. `start()` - Begin observation
2. `on_snapshot(snapshot)` - Process incoming snapshots
3. Validation → Guard → PatternRecord creation → Enrichment → EventBus dispatch
4. `stop()` - End observation

### 5.2 Snapshot Processing Flow

For each snapshot:
1. **Validation** - Check contract compliance
2. **Guard** - Apply safety checks
3. **PatternRecord Assembly** - Wrap snapshot with empty slots
4. **Enrichment** - Add metadata namespaces (Phase 4)
5. **Dispatch** - Send to EventBus

### 5.3 What Observer Never Triggers

Observer does NOT trigger:
- Trading execution
- Strategy evaluation
- Risk assessment
- Position management
- External system calls
- ETEDA pipeline steps

### 5.4 Runtime Modes

**Supported Modes:**
- DEV
- PROD

**Mode Purpose:**
- Log level control
- metadata.mode value recording
- Operational/test data distinction

**Mode Does NOT Change:**
- Data structure
- Storage path
- File format
- Contract rules

---

## 6. Safety, Validation & Guardrails

### 6.1 Existing Safeguards

**Validation Layer (Phase 3):**
- Snapshot meta required fields check
- Snapshot context required fields check
- Observation structure validation
- NaN/Inf blocking in numeric values

**Guard Layer (Phase 3):**
- Snapshot blocking based on validation results
- Safety decision logging
- Allow/block determination

**Enrichment Layer (Phase 4):**
- Quality tagging (neutral indicators only)
- Interpretation metadata (summary hints)
- Schema versioning metadata

### 6.2 What Is Intentionally Absent

Observer does NOT implement:
- Automatic recovery
- Retry policies
- Data correction
- Value imputation
- Missing data handling beyond blocking

### 6.3 Error Handling Policy

**Observer Internal Errors:** Execution halt

**Sink Errors:** Log and continue (failure isolation)

**Data Errors:** Ignore snapshot (optional blocking)

---

## 7. Configuration & Schema Dependency

### 7.1 Config Inputs

Observer receives configuration for:
- Session ID
- Runtime mode (DEV/PROD)
- EventBus sink configuration
- Validator/Guard/Enricher instances (optional)

Observer does NOT:
- Load strategy configurations
- Access trading parameters
- Modify system-wide settings

### 7.2 Schema Enforcement

Observer operates within Schema Engine-defined fields:
- Snapshot structure follows schema contract
- No ad-hoc field creation
- Schema version tracking in metadata

### 7.3 Failure Behavior

**Validation Failure:** Snapshot blocked, logged, not recorded

**Guard Failure:** Snapshot blocked, logged, not recorded

**Sink Failure:** Logged, other sinks continue

**Schema Violation:** Snapshot rejected at validation

---

## 8. Observer Lifecycle & Phase Locks

### 8.1 Phase-Based Responsibility Locks

**Phase 3 Locks:**
- Validation rules frozen
- Guard decision logic frozen
- No tag/label generation

**Phase 4 Locks:**
- Enrichment metadata namespaces frozen
- Quality tagging rules frozen (neutral indicators only)
- Interpretation hints frozen (summary only)

**Phase 5 Locks:**
- Analysis/clustering moved to offline pipeline
- Observer does not perform pattern detection
- Dataset building is post-processing only

**Phase 15 Locks:**
- Real-time input integration validated
- Structure stability confirmed
- No further structural changes required

### 8.2 What Is Frozen After Phase 15

**Frozen Elements:**
- Observer component responsibilities
- Data flow architecture
- Snapshot contract structure
- Storage rules
- Validation/Guard boundaries

**Not Frozen:**
- Sink implementations (extensible)
- Enrichment metadata content (within namespaces)
- External snapshot generation methods

### 8.3 What Will Not Be Revisited

**Permanent Decisions:**
- Observer does not make trading decisions
- Observer does not generate tags/labels
- Observer does not modify snapshots
- Append-only storage model
- File-based data assets
- Contract-first design hierarchy

---

## 9. Explicit Non-Goals

Observer explicitly does NOT and will NOT:

**Strategy & Trading:**
- Strategy judgment
- Condition evaluation
- Trading decisions
- Position management
- Risk approval

**Data Processing:**
- Data normalization
- Value correction
- Missing data imputation
- Indicator calculation
- Signal generation

**System Integration:**
- ETEDA pipeline orchestration
- Broker execution
- Scheduling/triggering ownership
- Automatic recovery
- Retry policy management

**Tagging & Labeling:**
- Regime classification
- Condition tag generation
- Outcome label generation
- Pattern detection (moved to offline)

**Architecture Scope:**
- Strategy engine design
- Trading execution logic
- Risk management policies
- Learning model definition
- Report generation logic

---

## 10. Deferred Designs & Reference Documents

### 10.1 Design-Only / Future Phase Documents

**QTS_Observer_Scalp_Extension.md**
- **Status:** Design-only reference, NOT implemented
- **Content:** Adaptive snapshot behavior, high-frequency mode, event-driven frequency switching
- **Scope:** Future extension phase (not part of current architecture)
- **Important:** This document describes DEFERRED functionality that does NOT affect current Observer behavior

### 10.2 Reference Documents (Not Merged)

**QTS_Observer_Integration_Guide.md**
- Observer ↔ QTS integration guide
- Runtime binding reference
- Not part of core architecture definition

### 10.3 Excluded Documents

The following are NOT architecture documents:
- QTS_Observer_Start_Prompt.md (session boundary)
- QTS_OF_Observer_Minimum_Components.md (execution guide)

---

## 11. Extension Points

### 11.1 Allowed Extensions (v1.x)

**Permitted:**
- Additional Sink implementations (DB, Stream, Object Storage)
- Log Sink additions
- Metric collection Sink additions

**Not Permitted:**
- Observer internal logic extensions
- Tag/Label generation logic additions
- Snapshot structure modifications
- Contract rule changes

### 11.2 Standalone vs Integrated Execution

**Both modes supported:**
- Standalone: Observer-Core runs independently
- Integrated: Observer-Core runs within QTS

**Invariant across modes:**
- Identical PatternRecord structure
- Identical data contract
- Identical storage rules

---

## 12. Data Integrity Rules

All PatternRecord outputs must satisfy:

1. `snapshot` field always exists
2. `snapshot` internal fields are immutable
3. PatternRecord storage is append-only
4. Stored PatternRecords cannot be modified or deleted

**Violation Consequence:** Data automatically excluded from QTS learning/analysis.

---

## 13. Contract Hierarchy

**Priority Order:**
1. QTS_Observer_Contract.md (highest authority)
2. Observer_Architecture.md (this document)
3. Implementation code

**Rule:** Architecture cannot redefine or extend Contract. Contract violations invalidate Architecture.

---

## 14. Architecture Lock Declaration

This architecture is **LOCKED** as of Phase 15 completion.

**Lock Conditions Met:**
- QTS_Observer_Contract.md v1.0.0 confirmed
- Observer-Core v1.0.0 execution validated
- Real-time input integration verified
- Structure stability confirmed
- Architecture-Contract alignment verified

**Post-Lock Restrictions:**
- Component responsibility changes prohibited
- Data flow changes prohibited
- Contract-violating structures prohibited

---

## 15. Final Architecture Statement

> **Observer_Architecture.md is the Single Source of Truth (SSoT) for the QTS Observer system's component responsibilities, data flow, and operational boundaries.**

> **All implementations must follow this architecture while prioritizing the superior Contract document.**

> **Observer is a judgment-free, observation-only system that records state without interpretation, decision-making, or execution authority.**

---

**End of Document**
