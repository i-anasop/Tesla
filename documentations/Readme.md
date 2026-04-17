# TESLA – Autonomous Driving Simulator

A professional **Tesla-inspired autonomous driving simulator** built with **Python and Pygame**, featuring an intelligent AI agent that combines **Prolog-based safety reasoning**, **Minimax decision-making**, and a **persistent learning system**.  
The simulator emphasizes safety, realism, and continuous improvement through experience.

---

## Overview

This project simulates an autonomous vehicle navigating a multi-lane road environment with traffic, pedestrians, and static obstacles.  
The AI agent makes driving decisions using a structured pipeline:

- Logical safety constraints (Prolog rules)
- Strategic action evaluation (Minimax)
- Memory-based learning from past failures

Over time, the agent becomes **safer and more efficient** by remembering where it previously failed.

---

## Does the Tesla Agent Learn?

**Yes — learning is an active and core component of this project.**

### How Learning Works

1. **Memory System**
   - The agent stores driving experience in a persistent file: `ai/memory.json`
   - Memory is retained across simulation runs.

2. **Danger Zone Identification**
   - When a crash occurs, the agent records:
     - Lane number
     - Approximate position (distance)
   - Example: “Lane 2 at 5 km is dangerous.”

3. **Future Avoidance**
   - Before changing lanes or accelerating, the AI checks memory.
   - If a planned action leads into a known danger zone, the agent:
     - Avoids the lane
     - Brakes
     - Or stays in its current lane

4. **Skill Tracking**
   - The agent tracks:
     - Cars safely passed
     - Crashes avoided
   - Skill levels evolve over time:
     - **Learning → Skilled → Expert**

**Result:**  
The more the simulation runs, the safer and smarter the driver becomes.

---

## Core Features

### Visual Design
- Tesla-inspired futuristic UI
- Smooth animations and camera motion
- Curved roads, zebra crossings, intersections
- Tesla Model 3–style top-down vehicle
- Professional dashboard overlay:
  - Speed gauge
  - Mini radar
  - AI status indicators

### Traffic & Environment
- Multi-lane road system
- Pre-existing traffic vehicles
- Lane-aware traffic behavior
- Pedestrian crossings with animated indicators
- Static obstacles:
  - Cones
  - Barriers
  - Broken-down cars
- Pedestrian-first safety enforcement (all vehicles stop)

---

## AI Intelligence System

### Decision Pipeline

1. **Sensors**
   - LIDAR-like distance sensing
   - Lane detection
   - Vehicle speed detection
   - Pedestrian awareness

2. **Prolog Safety Rules (Critical Layer)**
   - Logic-based reasoning
   - Emergency braking overrides all actions
   - Distance-based collision constraints
   - Pedestrian right-of-way enforcement

3. **Minimax Evaluation**
   - Scores multiple possible actions
   - Optimizes safety and progress
   - Evaluates lane switching, braking, and acceleration

4. **Experience Memory**
   - Consults past crashes and safe paths
   - Avoids known danger zones

5. **Final Action Execution**
   - Best safe action is applied to the vehicle

---

## Learning Mechanism Summary

The AI improves through:
- Crash-based experience recording
- Pattern recognition in lanes and traffic flow
- Memory-guided decision-making
- Cross-session persistence using JSON

This is **experience-based learning**, not hardcoded behavior.

---

## Controls

| Key   | Action                   |
|-------|-------------------------|
| SPACE | Pause / Resume           |
| S     | Toggle sensor visualization |
| D     | Toggle debug information |
| R     | Reset simulation         |
| ESC   | Quit                     |

---

## Project Structure

TESLA/
├── main.py # Entry point & main loop
├── config.py # Global configuration
│
├── ai/
│ ├── tesla_brain.py # Core AI logic (Prolog + Minimax + Learning)
│ ├── sensors.py # Sensor simulation
│ ├── prolog_engine.py # Prolog inference engine
│ ├── prolog_rules.pl # Safety & decision rules
│ └── memory.json # Persistent experience memory
│
├── environment/
│ ├── map_builder.py # Roads, lanes, crossings
│ ├── traffic.py # Traffic vehicle behavior
│ ├── obstacles.py # Static obstacles
│ ├── pedestrians.py # Pedestrian movement logic
│ └── pedestrian_crossing.py # Crossing indicators
│
├── ui/
│ ├── dashboard.py # HUD and gauges
│ ├── animations.py # Visual effects & particles
│ ├── start_screen.py # Loading / menu screen
│ └── environment_editor.py# Custom scenario editor
│
└── README.md # Project documentation

## Key Configuration (config.py)

```python
# Speed Limits
CAR_MAX_SPEED = 5.5          # Internal speed
MAX_SPEED_MPH = 85           # Display limit

# Smooth Motion
CAR_ACCELERATION = 0.08
CAR_DECELERATION = 0.12

# Traffic Spawning
TRAFFIC_MIN_SPAWN_DISTANCE = 250
TRAFFIC_SPAWN_AHEAD_DISTANCE = 400
MAX_TRAFFIC_CARS = 6

## Recent Enhancements (December 2025)

Speed capped at 85 MPH
Smooth acceleration and braking curves
Improved traffic spawning (no overlap)
Lane switching for slow and halted vehicles
Pedestrian crossing indicators (replaced traffic lights)
Tesla-style animated start screen
Environment editor for custom scenarios
Enhanced dashboard UI and color palette

# Technologies Used

Python
Pygame
Prolog-style Logic Programming
Minimax Decision Algorithm
JSON-based Persistent Memory

# Credits

TESLA – Autonomous Driving Simulator
An AI-powered simulation demonstrating:
Logical reasoning
Experience-based learning
Safety-first autonomous decision making
Clean UI/UX design