# 🚗 TESLA – Autonomous Driving Simulator (Python + Pygame)

A **Tesla-inspired autonomous driving simulator** built with Python & Pygame featuring AI that combines **Prolog-based safety logic**, **Minimax decision-making**, and **persistent learning**.  
The agent improves over time by remembering danger zones and avoiding past crash patterns.

### 🌐 Play Online / Test in Browser
You can run and test the simulator directly in your browser without installing anything! 
👉 **[Click here to play the Web Version](https://i-anasop.github.io/Tesla/)**

*(Note: The first load might take a few seconds as the Pygame WebAssembly environment is initialized).*

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

```

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

```

---

## ⚙️ Technologies

- Python  
- Pygame  
- Prolog-style logic inference  
- Minimax algorithm  
- JSON persistent memory  

---

## 💡 Credits

Built by **Anas** with dedication, curiosity, and a respect for real-world autonomous systems.

---

## ⚖️ License & Reuse

This project is **open for learning and modification**.
Feel free to fork, remix, or improve it, just credit the original author.
If you wanna check this project video, check my Linkedin Post.

---

📬 _Have feedback or want to contribute? Let’s connect!_
## 🔗 Connect With Me

- [LinkedIn](https://www.linkedin.com/in/m-ianas/)
