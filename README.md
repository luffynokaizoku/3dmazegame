# 🔥 GROUP 1 - Cube Maze Adventure PRO

Welcome to **Cube Maze Adventure PRO**, a thrilling 3D first-person maze exploration game developed using the Ursina Engine in Python! This README provides a comprehensive overview of the game, its features, how to install and run it, and the team behind its creation.

---

## 🌟 Game Overview

**Cube Maze Adventure PRO** plunges you into a world of procedurally generated 3D mazes. Your objective is to navigate the intricate cube labyrinth to reach a designated goal, all while evading a cunning monster that patrols the paths, chases intruders, and launches dangerous projectiles. The game offers an engaging experience with dynamic health management, intelligent enemy AI, and intuitive first-person controls.

> "Embark on an epic adventure through an ever-changing cubic labyrinth. Find your way to the goal, but beware of the monster lurking in the shadows!"

---

## 🔹 Core Features

* **Procedurally Generated 3D Mazes**: Experience unique challenges with each playthrough thanks to mazes generated dynamically using a recursive backtracking algorithm. The terrain features distinct wall heights and path levels.
* **First-Person Player Controller**: Enjoy seamless movement and exploration with a responsive first-person camera, walking, and jumping mechanics.
* **Dynamic Health System**: Monitor your health bar as you take damage from monster attacks, featuring a temporary invulnerability period to allow for tactical retreats.
* **Intelligent AI Monster**: Encounter a formidable opponent with varied behaviors:
    * **Patrol**: The monster intelligently patrols predefined paths (linear or sine wave) when no threat is perceived.
    * **Chase**: Detects the player within a specified vision range and actively pursues them.
    * **Projectile Attack**: Initiates a ranged attack by firing projectiles after a brief wind-up, complete with attack cooldowns.
* **Clear Goal Objective**: Your ultimate aim is to locate and reach the vibrant orange goal entity hidden within the maze to win the game.
* **Comprehensive Game States**: The game seamlessly transitions between:
    * **Main Menu**: Start a new game or exit the application.
    * **Playing**: Active gameplay, allowing for player movement and monster interaction.
    * **Paused**: Temporarily halts the game, offering options to resume or return to the main menu.
    * **Win/Lose Screens**: Displays appropriate messages and options to restart or go back to the main menu upon game completion.
* **Intuitive UI Management**: A clean and functional user interface for menus, health display, and game-over feedback.
* **Highly Configurable**: Easily adjust game parameters such as player speed, monster AI, maze dimensions, and entity colors through a centralized configuration class.

---

## 📁 Project Directory Structure

```
CubeMazeAdventurePRO/
├── gogogo.py             # Main game logic and Ursina application
└── README.md             # This file
```

---

## 🔧 Installation & Running the Game

### 1. Requirements

* Python 3.x
* Ursina Engine

### 2. Install Dependencies

If you don't have Ursina installed, open your terminal or command prompt and run:

```bash
pip install ursina
```

### 3. Launch the Game

Navigate to the directory where `gogogo.py` is saved in your terminal or command prompt and run:

```bash
python gogogo.py
```

---

## 🤏 Controls

* **WASD**: Move (Forward, Left, Backward, Right)
* **Spacebar**: Jump
* **Mouse**: Look around
* **Escape**:
    * From in-game: Pause/Unpause the game.
    * From Win/Lose screen: Return to Main Menu.
    * From Main Menu: Exit the application.

---

## 📊 Game Mechanics

### Player Health

* **Max Health**: Configurable, default 3 HP.
* **Damage**: Each monster projectile hit reduces health by 1.
* **Invulnerability**: Short period of invulnerability after taking damage.

### Monster Behavior

* **Vision Range**: Detects player within a configurable radius.
* **Attack Wind-up**: Visual cue (color change) and delay before firing a projectile.
* **Attack Cooldown**: Prevents rapid-fire attacks.

---

## 🏆 Project Team - GROUP 1 🔥

| Name | Roll Number |
| :--- | :---------- |
| **Sure. Sri Venkat Rama Surya** | 231FA04442 |
| **Sirigiri. Anand Prabhu Das** | 231FA04436 |
| **Reddy. Bala Raju** | 231FA04432 |

---

## 🙏 Acknowledgments

* Developed using the **Ursina Engine**.
* Special thanks to our mentors and peers for testing and feedback.

---

## 🚀 Future Improvements

* Additional monster types with unique abilities.
* More maze generation algorithms.
* Environmental hazards within the maze.
* Collectibles or score system.
* Improved visual effects and sounds.

---

## 💡 License

This project is for educational use and not intended for commercial distribution.

---

## 🚀 Ready to Explore?

Run `python gogogo.py` and embark on your cube maze adventure!

> "Every twist and turn holds a new challenge. Can you conquer the maze?"
