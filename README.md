# 🚗 TESLA – Autonomous Driving Simulator (Python + Pygame)

A **Tesla-inspired autonomous driving simulator** built with Python & Pygame featuring AI that combines **Prolog-based safety logic**, **Minimax decision-making**, and **persistent learning**.  
The agent improves over time by remembering danger zones and avoiding past crash patterns.

---

## 🧠 Overview

The simulator models an autonomous vehicle navigating a multi-lane environment with:
- Traffic cars
- Pedestrian crossings
- Static obstacles (cones, barriers, broken vehicles)

The AI follows a structured pipeline:
1. Sensor interpretation
2. Safety logic (Prolog-style rules)
3. Strategy evaluation (Minimax)
4. Experience-based learning (JSON memory)

Result: Over multiple runs the agent becomes **safer & more efficient**.

---

## 📚 Core Features

### 🟣 Visual & UI
- Tesla-style futuristic UI
- Animated road & traffic
- Pedestrian crossings with indicators
- Dashboard with speed, radar, AI status

### 🚦 Environment
- Multi-lane road system
- Traffic cars with lane-aware behavior
- Pedestrian-first right-of-way
- Static obstacles & intersections

### 🤖 AI Intelligence
- **Sensors**: distance, lanes, pedestrians, speed
- **Prolog Rules** for safety (emergency braking, safe distance)
- **Minimax** for evaluating lane switching, braking, acceleration
- **Memory System**:
  - Stores crash zones (`memory.json`)
  - Avoids past danger lanes
  - Tracks skill progression → Learning → Skilled → Expert

---

## 🧩 Learning Summary

The car logs crashes as:
{ lane: X, position: Y }

yaml
Copy code
stored in `ai/memory.json`.

On next runs the agent:
✔ avoids those lanes  
✔ brakes earlier  
✔ becomes safer automatically  

Learning is **persistent across sessions**.

---

## 🎮 Controls

| Key   | Action                      |
|-------|-----------------------------|
| SPACE | Pause / Resume              |
| S     | Toggle Sensors              |
| D     | Toggle Debug Info           |
| R     | Reset Simulation            |
| ESC   | Quit                        |

---

## 📂 Project Structure

TESLA/
├── main.py
├── config.py
│
├── ai/
│ ├── tesla_brain.py
│ ├── sensors.py
│ ├── prolog_engine.py
│ ├── prolog_rules.pl
│ └── memory.json
│
├── environment/
│ ├── map_builder.py
│ ├── traffic.py
│ ├── obstacles.py
│ ├── pedestrians.py
│ └── pedestrian_crossing.py
│
└── ui/
├── dashboard.py
├── animations.py
├── start_screen.py
└── environment_editor.py

yaml
Copy code

---

## ⚙️ Technologies

- Python  
- Pygame  
- Prolog-style logic inference  
- Minimax algorithm  
- JSON persistent memory  

---

## ✨ Recent Improvements (Dec 2025)

- Speed cap at **85 MPH**
- Smooth ABS-style acceleration/braking
- Better traffic spawning & lane switching
- Pedestrian crossing indicators (no traffic lights)
- Tesla animated start UI
- Custom scenario editor
- Improved dashboard & color palette

---

## 👨‍💻 Credits

**TESLA – Autonomous Driving Simulator**  
Showcases:
- Safety-first autonomous logic  
- Experience-based learning  
- Strategic decision making  
- Clean UI + simulation design

Built with curiosity, experimentation, and respect for real-world autonomous systems.
