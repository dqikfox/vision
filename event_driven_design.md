# Event-Driven Model Playground Design

## Concept
Instead of a linear chain, we treat each model as an **Agent**. Each agent has:
1.  **Identity**: Name, Provider, and Model.
2.  **Personality**: A System Prompt defining how it behaves.
3.  **Routing Rule**: A "Target" agent it should send its response to.

## Architecture
- **Message Broker**: A central coordinator that receives a message from Agent A, identifies Agent A's target (Agent B), and triggers Agent B's inference.
- **Conversation State**: Maintains the history of messages between agents.
- **Trigger**: An initial "User Message" kicks off the first agent, which then triggers the next based on the rules.

## Data Structure
```json
{
  "agents": [
    { "id": "A", "name": "Researcher", "provider": "ollama", "model": "qwen2.5", "target": "B" },
    { "id": "B", "name": "Critic", "provider": "openai", "model": "gpt-4o", "target": "A" }
  ]
}
```
In this example, Agent A and B will loop indefinitely (or until a limit) conversing with each other.
