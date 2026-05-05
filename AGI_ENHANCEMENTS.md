# Vision AGI Enhancement Documentation

## Overview

Vision has been enhanced with **Autonomous General Intelligence (AGI) capabilities** through two new cognitive modules:

1. **`elite_goals.py`** — Autonomous Goal Management System
2. **`elite_world.py`** — World Model & State Understanding

These modules integrate with the existing `elite_brain.py` cognitive layer to create a more capable, autonomous AI operator.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      VISION AGI STACK                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ elite_brain  │  │ elite_goals  │  │    elite_world       │  │
│  │              │  │              │  │                      │  │
│  │ • Semantic   │  │ • Goal Graph │  │ • Entity Registry    │  │
│  │   Memory     │  │ • Planning   │  │ • Observation Buffer │  │
│  │ • Tree of    │  │ • Intention  │  │ • State Inference    │  │
│  │   Thoughts   │  │   Stack      │  │ • Prediction Engine  │  │
│  │ • MetaCritic │  │ • Achievement│  │ • Spatial Memory     │  │
│  │ • Self-      │  │   Log        │  │                      │  │
│  │   Evolution  │  │              │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                    │               │
│         └─────────────────┴────────────────────┘               │
│                           │                                      │
│                    ┌──────┴──────┐                               │
│                    │live_chat_app │                               │
│                    │  (FastAPI)   │                               │
│                    └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Details

### 1. elite_goals.py — Goal Management

#### Key Components

**GoalGraph**
- Hierarchical goal decomposition (parent/child relationships)
- Goal lifecycle management (PENDING → ACTIVE → COMPLETED/FAILED)
- Automatic parent completion when all subgoals complete
- Persistent storage in `.brain/goals/goals.json`

**PlanEngine**
- LLM-powered plan generation from goals
- Step-by-step plan execution with tool integration
- Dependency tracking between steps
- Plan success/failure tracking

**IntentionStack**
- Manages active context and context switching
- Stack-based intention tracking
- Supports nested goal pursuit

**GoalManager** (Main Facade)
- Unified interface for all goal operations
- Autonomous goal pursuit loop
- Background task management

#### Goal Priorities

```python
class GoalPriority(Enum):
    CRITICAL = 5   # Must complete immediately
    HIGH = 4       # Important, prioritize
    MEDIUM = 3     # Normal priority
    LOW = 2        # Can defer
    BACKGROUND = 1 # Fill-in work
```

#### Goal Status Flow

```
PENDING → ACTIVE → COMPLETED
   ↓         ↓
BLOCKED   FAILED
   ↓
ABANDONED
```

#### Usage Examples

```python
from elite_goals import get_goal_manager, GoalPriority

# Get the singleton manager
goal_mgr = get_goal_manager()

# Create a goal
goal = await goal_mgr.create_goal(
    description="Organize desktop files",
    priority="MEDIUM",
    auto_decompose=True  # Automatically create subgoals
)

# Pursue a goal immediately
success = await goal_mgr.pursue_goal(goal.uid)

# Start autonomous goal pursuit
goal_mgr.start_autonomous_loop()

# Check status
status = goal_mgr.get_status()
# Returns: {
#     "total_goals": 10,
#     "active": 2,
#     "pending": 5,
#     "intention_stack_depth": 1,
#     "current_intention": "Current: pursue_goal | Stack depth: 0"
# }
```

---

### 2. elite_world.py — World Model

#### Key Components

**EntityRegistry**
- Tracks all entities in the environment
- Types: WINDOW, PROCESS, FILE, APPLICATION, DEVICE, CONCEPT, TASK
- State tracking: UNKNOWN, ACTIVE, INACTIVE, BUSY, ERROR, COMPLETED
- Relationship tracking between entities
- Persistent storage in `.brain/world/entities.json`

**ObservationBuffer**
- Rolling buffer of recent observations
- Automatic fact extraction via LLM
- Source tracking (screenshot, tool_result, user_input, etc.)

**StateInference**
- Infers high-level situations from observations
- Anomaly detection
- Current situation summarization

**PredictionEngine**
- Generates predictions about future states
- Confidence scoring
- Prediction fulfillment tracking

**SpatialMemory**
- Remembers locations and layouts
- Nearest-neighbor queries
- Desktop/application layout memory

**WorldModel** (Main Facade)
- Unified interface for world operations
- Background update loop
- Situation awareness

#### Entity Types

```python
class EntityType(Enum):
    WINDOW        # UI windows
    PROCESS       # Running processes
    FILE          # Files and documents
    APPLICATION   # Installed apps
    DEVICE        # Hardware devices
    CONCEPT       # Abstract concepts
    TASK          # Ongoing tasks
```

#### Usage Examples

```python
from elite_world import get_world_model, EntityType, EntityState

# Get the singleton model
world = get_world_model()

# Register an entity
chrome = world.register_entity(
    name="Chrome",
    entity_type=EntityType.APPLICATION,
    state=EntityState.ACTIVE,
    attributes={"url": "https://example.com"}
)

# Update entity state
world.update_entity_state(chrome.uid, EntityState.BUSY, "Loading page...")

# Make an observation
obs = await world.observe(
    content="Desktop shows 5 open windows",
    source="screenshot",
    entities_involved=[chrome.uid]
)

# Get situation summary
situation = await world.get_situation_summary()
# Returns: "User is working with multiple browser windows open"

# Generate prediction
prediction = await world.generate_prediction("User workflow")
# Returns prediction with confidence score

# Check status
status = world.get_status()
# Returns: {
#     "entities": 25,
#     "active_entities": 8,
#     "observations": 150,
#     "predictions": 5,
#     "locations": 12,
#     "current_situation": "User browsing documentation"
# }
```

---

## API Endpoints

### AGI Status

```http
GET /api/agi/status
```

Returns status of all AGI cognitive modules.

**Response:**
```json
{
  "goals": {
    "total_goals": 10,
    "active": 2,
    "pending": 5,
    "intention_stack_depth": 1,
    "current_intention": "Current: pursue_goal"
  },
  "world": {
    "entities": 25,
    "active_entities": 8,
    "observations": 150,
    "predictions": 5,
    "current_situation": "User working with code editor"
  },
  "brain": { /* existing brain status */ }
}
```

### Create Goal

```http
POST /api/agi/goals
Content-Type: application/json

{
  "description": "Organize desktop files by type",
  "priority": "MEDIUM",
  "auto_decompose": true
}
```

**Response:**
```json
{
  "uid": "goal_1234567890_1234",
  "description": "Organize desktop files by type",
  "status": "PENDING",
  "priority": "MEDIUM"
}
```

### List Goals

```http
GET /api/agi/goals
```

**Response:**
```json
{
  "goals": [
    {
      "uid": "goal_1234567890_1234",
      "description": "Organize desktop files",
      "status": "PENDING",
      "priority": "MEDIUM",
      "parent_uid": null,
      "subgoal_count": 3
    }
  ]
}
```

### Pursue Goal

```http
POST /api/agi/goals/{goal_uid}/pursue
```

**Response:**
```json
{
  "success": true,
  "goal_uid": "goal_1234567890_1234"
}
```

### Add Observation

```http
POST /api/agi/observe
Content-Type: application/json

{
  "content": "Desktop shows multiple file icons",
  "source": "screenshot",
  "entities_involved": ["entity_application_1234"]
}
```

**Response:**
```json
{
  "uid": "obs_1234567890_1234",
  "timestamp": 1714392000.0,
  "inferred_facts": [
    "User has files on desktop",
    "Files appear to be documents"
  ]
}
```

### Get Situation

```http
GET /api/agi/situation
```

**Response:**
```json
{
  "situation": "User is organizing files on desktop",
  "entities": 25,
  "observations": 150
}
```

### Generate Prediction

```http
POST /api/agi/predict
Content-Type: application/json

{
  "context": "File organization workflow"
}
```

**Response:**
```json
{
  "uid": "pred_1234567890_1234",
  "description": "User will likely create folders for different file types",
  "confidence": 0.75,
  "expected_by": 1714392060.0
}
```

---

## WebSocket Protocol Extensions

### Client → Server Messages

**Create Goal:**
```json
{
  "type": "agi_create_goal",
  "description": "Organize desktop files",
  "priority": "MEDIUM"
}
```

**Pursue Goal:**
```json
{
  "type": "agi_pursue_goal",
  "goal_uid": "goal_1234567890_1234"
}
```

**Get Status:**
```json
{
  "type": "agi_get_status"
}
```

**Add Observation:**
```json
{
  "type": "agi_observe",
  "content": "Desktop shows file icons",
  "source": "user_action"
}
```

### Server → Client Messages

**Goal Created:**
```json
{
  "type": "agi_goal_created",
  "uid": "goal_1234567890_1234",
  "description": "Organize desktop files",
  "status": "PENDING"
}
```

**Goal Pursued:**
```json
{
  "type": "agi_goal_pursued",
  "goal_uid": "goal_1234567890_1234",
  "success": true
}
```

**Status Update:**
```json
{
  "type": "agi_status",
  "goals": { /* goal status */ },
  "world": { /* world status */ }
}
```

**Observation:**
```json
{
  "type": "agi_observation",
  "uid": "obs_1234567890_1234",
  "inferred_facts": ["User has files on desktop"]
}
```

---

## Integration with Existing Systems

### Memory Integration

The AGI modules integrate with existing memory systems:

- **Semantic Memory**: Goals and world entities are embedded and retrievable
- **Episodic Memory**: Goal pursuit and observations are logged
- **Self-Evolution**: Learned patterns improve future goal planning

### Tool Integration

Goals can invoke Vision's existing tool ecosystem:

```python
# In elite_goals.py PlanEngine
result = await self._tool_executor("click", {"x": 100, "y": 200})
```

### LLM Integration

Both modules use the same LLM abstraction as the rest of Vision:

```python
# Wired during startup
brain_ai.wire_llm(_fast_completion)
goal_manager.set_llm(_fast_completion)
world_model.set_llm(_fast_completion)
```

---

## Configuration

### Environment Variables

No additional environment variables required. AGI modules use existing Vision configuration.

### Data Storage

```
.brain/
├── goals/
│   └── goals.json          # Persisted goals
└── world/
    └── entities.json       # Persisted entities
```

### Tunable Parameters

**elite_goals.py:**
```python
MAX_ACTIVE_GOALS = 5        # Concurrent goal pursuit limit
MAX_GOAL_DEPTH = 4          # Maximum goal hierarchy depth
PLAN_TIMEOUT_SECONDS = 300  # Plan execution timeout
INTENTION_STACK_SIZE = 10   # Maximum intention stack depth
```

**elite_world.py:**
```python
MAX_ENTITIES = 1000         # Maximum tracked entities
MAX_OBSERVATIONS = 500      # Observation buffer size
PREDICTION_HORIZON_SECONDS = 60  # Prediction time horizon
SPATIAL_MEMORY_SIZE = 100   # Spatial memory capacity
```

---

## Testing

Run the AGI module tests:

```bash
# Run all AGI tests
python -m pytest test_agi_modules.py -v

# Run specific test class
python -m pytest test_agi_modules.py::TestGoalGraph -v
python -m pytest test_agi_modules.py::TestWorldModel -v

# Run with coverage
python -m pytest test_agi_modules.py --cov=elite_goals --cov=elite_world -v
```

---

## Future Enhancements

### Phase 3: Advanced Planning

- [ ] Hierarchical Task Networks (HTN)
- [ ] Temporal planning with deadlines
- [ ] Resource-aware scheduling
- [ ] Multi-agent goal coordination

### Phase 4: Deep World Understanding

- [ ] Causal reasoning engine
- [ ] Counterfactual reasoning
- [ ] Theory of mind modeling
- [ ] Long-term pattern learning

### Phase 5: Self-Improvement

- [ ] Automatic goal generation from user patterns
- [ ] Strategy learning from successful plans
- [ ] Meta-learning for planning efficiency
- [ ] Autonomous capability expansion

---

## Troubleshooting

### Goals not persisting

Check `.brain/goals/` directory exists and is writable:
```bash
ls -la .brain/goals/
```

### World model not updating

Ensure background updates are started:
```python
world_model.start_background_updates()
```

### High memory usage

Adjust buffer sizes in configuration:
```python
MAX_ENTITIES = 500        # Reduce from 1000
MAX_OBSERVATIONS = 250    # Reduce from 500
```

---

## References

- `elite_brain.py` — Base cognitive architecture
- `elite_goals.py` — Goal management implementation
- `elite_world.py` — World model implementation
- `test_agi_modules.py` — Test suite
- `live_chat_app.py` — Integration point

---

**Last Updated**: April 29, 2026
**Version**: 1.0.0 (AGI Phase 2)
