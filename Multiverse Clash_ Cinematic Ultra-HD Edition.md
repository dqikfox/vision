# Multiverse Clash: Cinematic Ultra-HD Edition

The pinnacle of AI model playgrounds. An ultra-high-definition, cinematic experience where AI models are embodied by legendary chibi heroes with advanced game-engine animations and dynamic environmental effects.

## Prerequisites
- **Python 3.x**: Ensure Python is installed and in your PATH.
- **Ollama**: Must be running locally (http://localhost:11434).
- **API Keys**: Set environment variables for cloud providers:
  ```bash
  set OPENAI_API_KEY=your_key
  set ANTHROPIC_API_KEY=your_key
  ```
- **Dependencies**:
  ```bash
  pip install flask flask-cors requests openai anthropic
  ```

## How to Run
1. Open a terminal/command prompt in this directory (`C:\project\vision`).
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Features
- **Cinematic Character Animations**:
    - **Jump Attacks**: Heroes perform dramatic jump-and-strike animations when responding.
    - **Screen Shake & Impact**: Visual feedback for model "clashes" with dynamic screen shaking.
    - **Particle Systems**: Energy bursts and color-coded particle effects during character interactions.
    - **Ultra-Smooth Locomotion**: High-fidelity walking cycles with head-bobbing and rhythmic scaling.
- **Ultra-HD Visual Production**:
    - **Advanced Glassmorphism**: Enhanced translucent UI with deep multi-layered blurs and radiant glows.
    - **Dynamic Arena Effects**: Radial gradients and atmospheric lighting that reacts to character movements.
    - **High-Resolution Chibi Roster**: Professionally designed 3D-style assets for the ultimate visual appeal.
- **Intelligent Model Orchestration**:
    - **Seamless Multiverse Bridging**: Connect local Ollama models with cloud-based GPT-4 and Claude 3.5.
    - **Autonomous Event-Driven Logic**: Define complex, non-linear routing where heroes autonomously pass messages.
    - **Real-Time Cinematic Feedback**: Animated speech bubbles and "synchronizing" indicators for a professional feel.
- **Robust Professional Backend**:
    - **High-Performance Flask Core**: Optimized for low-latency model inference and reliable asset serving.
    - **Comprehensive Error Resilience**: Advanced handling for API timeouts and local service connectivity issues.

## Project Structure
- `app.py`: The main Flask server (includes the frontend UI).
- `MODEL_PLAYGROUND_README.md`: This file.
