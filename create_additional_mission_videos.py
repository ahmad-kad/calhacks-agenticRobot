#!/usr/bin/env python3
"""
Create Additional Mission Videos for MERLIN
Generates various mission scenarios showcasing different capabilities:
- Multi-object pickup and sorting
- Obstacle avoidance and navigation
- Precision placement tasks
- Sequential task execution
- Error recovery and adaptation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from docker_3d_robot_demo import Robot3DSimulator
import time

def create_multi_object_sorting_video():
    """Create a video showing multi-object pickup and sorting mission."""
    print("🎬 Creating Multi-Object Sorting Mission Video...")
    
    # Create simulator
    simulator = Robot3DSimulator(output_dir="/Users/ahmadkaddoura/calhacks/Data")
    
    # Mission parameters - sort objects by color
    mission_prompt = "Sort all objects by color: red to zone A, green to zone B, blue to zone C"
    target_objects = ["red_cube", "green_sphere", "blue_block"]
    sorting_zones = {
        "red": [1.0, 1.0],
        "green": [3.0, 1.0], 
        "blue": [1.0, 3.0]
    }
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create subplots
    ax_main = fig.add_subplot(2, 3, (1, 4), projection='3d')  # Main 3D view
    ax_prompt = fig.add_subplot(2, 3, 2)  # Prompt display
    ax_detection = fig.add_subplot(2, 3, 3)  # Object detection
    ax_progress = fig.add_subplot(2, 3, 5)  # Mission progress
    ax_status = fig.add_subplot(2, 3, 6)  # Robot status
    
    # Mission phases for sorting
    phases = [
        {
            "name": "Environment Scan", 
            "duration": 2, 
            "robot_pos": [2.5, 2.5], 
            "gripper_open": True,
            "description": "Scanning for objects to sort",
            "detected_objects": [
                {"name": "red_cube", "position": [2.0, 2.0], "color": "red", "confidence": 94},
                {"name": "green_sphere", "position": [3.0, 2.5], "color": "green", "confidence": 91},
                {"name": "blue_block", "position": [2.5, 3.0], "color": "blue", "confidence": 89}
            ],
            "target_info": "Found 3 objects to sort",
            "current_object": None
        },
        {
            "name": "Pick Red Cube", 
            "duration": 3, 
            "robot_pos": [2.0, 2.0], 
            "gripper_open": False,
            "description": "Picking up red cube",
            "detected_objects": [],
            "target_info": "Red cube grasped",
            "current_object": "red_cube"
        },
        {
            "name": "Sort Red to Zone A", 
            "duration": 3, 
            "robot_pos": sorting_zones["red"], 
            "gripper_open": True,
            "description": "Placing red cube in zone A",
            "detected_objects": [],
            "target_info": "Red cube sorted to zone A",
            "current_object": None
        },
        {
            "name": "Pick Green Sphere", 
            "duration": 3, 
            "robot_pos": [3.0, 2.5], 
            "gripper_open": False,
            "description": "Picking up green sphere",
            "detected_objects": [],
            "target_info": "Green sphere grasped",
            "current_object": "green_sphere"
        },
        {
            "name": "Sort Green to Zone B", 
            "duration": 3, 
            "robot_pos": sorting_zones["green"], 
            "gripper_open": True,
            "description": "Placing green sphere in zone B",
            "detected_objects": [],
            "target_info": "Green sphere sorted to zone B",
            "current_object": None
        },
        {
            "name": "Pick Blue Block", 
            "duration": 3, 
            "robot_pos": [2.5, 3.0], 
            "gripper_open": False,
            "description": "Picking up blue block",
            "detected_objects": [],
            "target_info": "Blue block grasped",
            "current_object": "blue_block"
        },
        {
            "name": "Sort Blue to Zone C", 
            "duration": 3, 
            "robot_pos": sorting_zones["blue"], 
            "gripper_open": True,
            "description": "Placing blue block in zone C",
            "detected_objects": [],
            "target_info": "All objects sorted successfully!",
            "current_object": None
        }
    ]
    
    # Calculate frame data
    frame_data = []
    current_time = 0
    fps = 2
    
    for phase in phases:
        phase_frames = int(phase["duration"] * fps)
        for i in range(phase_frames):
            progress = i / phase_frames if phase_frames > 0 else 0
            
            # Interpolate robot position for movement phases
            if "Pick" in phase["name"] and phase["current_object"]:
                # Move to object
                if phase["current_object"] == "red_cube":
                    start_pos = [2.5, 2.5]
                    end_pos = [2.0, 2.0]
                elif phase["current_object"] == "green_sphere":
                    start_pos = sorting_zones["red"]
                    end_pos = [3.0, 2.5]
                elif phase["current_object"] == "blue_block":
                    start_pos = sorting_zones["green"]
                    end_pos = [2.5, 3.0]
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            elif "Sort" in phase["name"] and phase["current_object"]:
                # Move to sorting zone
                if phase["current_object"] == "red_cube":
                    start_pos = [2.0, 2.0]
                    end_pos = sorting_zones["red"]
                elif phase["current_object"] == "green_sphere":
                    start_pos = [3.0, 2.5]
                    end_pos = sorting_zones["green"]
                elif phase["current_object"] == "blue_block":
                    start_pos = [2.5, 3.0]
                    end_pos = sorting_zones["blue"]
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            else:
                robot_pos = phase["robot_pos"]
            
            # Update object position if being held
            if phase["current_object"] and not phase["gripper_open"]:
                gripper_offset = 0.3
                gripper_pos = [
                    robot_pos[0] + gripper_offset * np.cos(progress * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(progress * 2 * np.pi),
                    0.0
                ]
                simulator.objects[phase["current_object"]]['position'] = np.array(gripper_pos)
                simulator.held_object = phase["current_object"]
            else:
                simulator.held_object = None
            
            frame_data.append({
                "time": current_time,
                "phase": phase["name"],
                "robot_pos": robot_pos,
                "gripper_open": phase["gripper_open"],
                "progress": progress,
                "description": phase["description"],
                "detected_objects": phase["detected_objects"],
                "target_info": phase["target_info"],
                "current_object": phase["current_object"]
            })
            
            current_time += 1/fps
    
    def animate(frame):
        """Animation function for multi-object sorting."""
        # Clear all subplots
        ax_main.clear()
        ax_prompt.clear()
        ax_detection.clear()
        ax_progress.clear()
        ax_status.clear()
        
        if frame < len(frame_data):
            data = frame_data[frame]
            
            # Main 3D view
            ax_main.set_xlim(0, 5)
            ax_main.set_ylim(0, 5)
            ax_main.set_zlim(0, 1.0)
            ax_main.set_xlabel('X Position (meters)')
            ax_main.set_ylabel('Y Position (meters)')
            ax_main.set_zlabel('Z Position (meters)')
            ax_main.set_title(f'MERLIN: {data["phase"]} - {data["time"]:.1f}s', fontsize=12, fontweight='bold')
            
            # Draw ground plane grid
            x = np.linspace(0, 5, 6)
            y = np.linspace(0, 5, 6)
            for i in range(len(x)):
                ax_main.plot([x[i], x[i]], [0, 5], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            for i in range(len(y)):
                ax_main.plot([0, 5], [y[i], y[i]], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            
            # Draw sorting zones
            for color, pos in sorting_zones.items():
                zone_color = color
                theta = np.linspace(0, 2*np.pi, 30)
                x_circle = pos[0] + 0.3 * np.cos(theta)
                y_circle = pos[1] + 0.3 * np.sin(theta)
                z_circle = np.zeros_like(theta)
                ax_main.plot(x_circle, y_circle, z_circle, color=zone_color, linewidth=3, alpha=0.7, 
                           linestyle='--', label=f'Zone {color.upper()}')
            
            # Draw robot
            robot_pos = data["robot_pos"]
            ax_main.scatter(robot_pos[0], robot_pos[1], 0.1, color='blue', s=200, marker='s', label='Robot')
            
            # Draw gripper
            gripper_color = 'green' if data["gripper_open"] else 'red'
            gripper_pos = [robot_pos[0] + 0.3, robot_pos[1], 0.1]
            ax_main.scatter(gripper_pos[0], gripper_pos[1], 0.1, color=gripper_color, s=100, marker='^', label='Gripper')
            
            # Draw objects
            for name, obj in simulator.objects.items():
                if name != simulator.held_object:
                    pos = obj['position']
                    color = obj['color']
                    ax_main.scatter(pos[0], pos[1], pos[2], color=color, s=200, marker='s', alpha=0.8, 
                                  label=name.replace('_', ' ').title())
            
            # Draw held object
            if simulator.held_object:
                held_obj = simulator.objects[simulator.held_object]
                gripper_offset = 0.3
                held_pos = [
                    robot_pos[0] + gripper_offset * np.cos(data["progress"] * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(data["progress"] * 2 * np.pi),
                    0.0
                ]
                ax_main.scatter(held_pos[0], held_pos[1], held_pos[2], 
                              color=held_obj['color'], s=300, marker='s', alpha=0.9,
                              edgecolors='yellow', linewidth=2,
                              label=f'Holding {simulator.held_object.replace("_", " ").title()}')
            
            # Prompt display
            ax_prompt.set_xlim(0, 1)
            ax_prompt.set_ylim(0, 1)
            ax_prompt.axis('off')
            ax_prompt.set_title('Sorting Mission', fontsize=12, fontweight='bold')
            ax_prompt.text(0.5, 0.8, f'"{mission_prompt}"', ha='center', va='center', 
                          fontsize=12, fontweight='bold', color='#58a6ff',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#161B22', alpha=0.8))
            ax_prompt.text(0.5, 0.5, 'Sorting Zones:', ha='center', va='center', 
                          fontsize=11, color='#e6edf3')
            ax_prompt.text(0.5, 0.3, 'A: Red (1,1)  B: Green (3,1)  C: Blue (1,3)', ha='center', va='center', 
                          fontsize=10, color='#7d8590')
            
            # Object detection display
            ax_detection.set_xlim(0, 1)
            ax_detection.set_ylim(0, 1)
            ax_detection.axis('off')
            ax_detection.set_title('Sorting Progress', fontsize=12, fontweight='bold')
            
            if data["current_object"]:
                ax_detection.text(0.5, 0.7, f'Currently handling:', ha='center', va='center', 
                                fontsize=11, color='#f59e0b', fontweight='bold')
                ax_detection.text(0.5, 0.5, f'{data["current_object"].replace("_", " ").title()}', 
                                ha='center', va='center', fontsize=14, color='#10b981', fontweight='bold')
            else:
                ax_detection.text(0.5, 0.6, 'Ready for next object', ha='center', va='center', 
                                fontsize=12, color='#7d8590')
            
            # Mission progress
            ax_progress.set_xlim(0, 1)
            ax_progress.set_ylim(0, 1)
            ax_progress.axis('off')
            ax_progress.set_title('Mission Progress', fontsize=12, fontweight='bold')
            
            phase_names = ["Environment Scan", "Pick Red Cube", "Sort Red to Zone A", "Pick Green Sphere", 
                          "Sort Green to Zone B", "Pick Blue Block", "Sort Blue to Zone C"]
            current_phase_idx = phase_names.index(data["phase"]) if data["phase"] in phase_names else 0
            
            for i, phase_name in enumerate(phase_names):
                if i <= current_phase_idx:
                    color = '#10b981' if i == current_phase_idx else '#58a6ff'
                    marker = '●' if i == current_phase_idx else '✓'
                else:
                    color = '#6b7280'
                    marker = '○'
                
                y_pos = 0.8 - i * 0.1
                ax_progress.text(0.1, y_pos, f'{marker} {phase_name}', 
                               fontsize=9, color=color, fontweight='bold')
            
            # Robot status
            ax_status.set_xlim(0, 1)
            ax_status.set_ylim(0, 1)
            ax_status.axis('off')
            ax_status.set_title('Robot Status', fontsize=12, fontweight='bold')
            
            gripper_status = "OPEN" if data["gripper_open"] else "CLOSED"
            gripper_color = '#10b981' if data["gripper_open"] else '#ef4444'
            
            ax_status.text(0.1, 0.8, f'Position: [{robot_pos[0]:.1f}, {robot_pos[1]:.1f}]', 
                         fontsize=10, color='#e6edf3')
            ax_status.text(0.1, 0.6, f'Gripper: {gripper_status}', 
                         fontsize=10, color=gripper_color, fontweight='bold')
            ax_status.text(0.1, 0.4, f'Progress: {data["progress"]*100:.0f}%', 
                         fontsize=10, color='#f59e0b')
            ax_status.text(0.1, 0.2, data["target_info"], 
                         fontsize=9, color='#7d8590')
    
    # Create animation
    total_frames = len(frame_data)
    anim = animation.FuncAnimation(fig, animate, frames=total_frames, interval=1000/fps, repeat=True)
    
    # Save as video
    print("💾 Saving multi-object sorting video...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='MERLIN'), bitrate=1800)
    
    try:
        anim.save('Data/videos/merlin_multi_object_sorting.mp4', writer=writer)
        print("✅ Multi-object sorting video saved as merlin_multi_object_sorting.mp4")
    except Exception as e:
        print(f"⚠️ Could not save video (ffmpeg not available): {e}")
        print("💡 Saving as GIF instead...")
        try:
            anim.save('Data/videos/merlin_multi_object_sorting.gif', writer='pillow', fps=fps)
            print("✅ Multi-object sorting video saved as merlin_multi_object_sorting.gif")
        except Exception as e2:
            print(f"⚠️ Could not save GIF either: {e2}")
            print("💡 Saving individual frames instead...")
            # Save individual frames
            for i in range(min(20, total_frames)):  # Save first 20 frames
                animate(i)
                plt.savefig(f'Data/videos/sorting_frame_{i:03d}.png', dpi=150, bbox_inches='tight')
            print("✅ Individual sorting frames saved")
    
    plt.close()

def create_obstacle_avoidance_video():
    """Create a video showing obstacle avoidance and navigation."""
    print("🎬 Creating Obstacle Avoidance Mission Video...")
    
    # Create simulator
    simulator = Robot3DSimulator(output_dir="/Users/ahmadkaddoura/calhacks/Data")
    
    # Mission parameters - navigate around obstacles
    mission_prompt = "Navigate to the red cube while avoiding obstacles"
    target_object = "red_cube"
    obstacles = [
        {"name": "obstacle_1", "position": [2.0, 2.0], "size": 0.5},
        {"name": "obstacle_2", "position": [3.0, 1.5], "size": 0.4},
        {"name": "obstacle_3", "position": [1.5, 3.0], "size": 0.6}
    ]
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create subplots
    ax_main = fig.add_subplot(2, 3, (1, 4), projection='3d')  # Main 3D view
    ax_prompt = fig.add_subplot(2, 3, 2)  # Prompt display
    ax_detection = fig.add_subplot(2, 3, 3)  # Path planning
    ax_progress = fig.add_subplot(2, 3, 5)  # Mission progress
    ax_status = fig.add_subplot(2, 3, 6)  # Robot status
    
    # Mission phases for obstacle avoidance
    phases = [
        {
            "name": "Environment Mapping", 
            "duration": 2, 
            "robot_pos": [0.5, 0.5], 
            "gripper_open": True,
            "description": "Mapping environment and obstacles",
            "detected_objects": [
                {"name": "red_cube", "position": [4.0, 4.0], "color": "red", "confidence": 95}
            ],
            "target_info": "Target identified: red cube at [4,4]",
            "path_points": []
        },
        {
            "name": "Path Planning", 
            "duration": 2, 
            "robot_pos": [0.5, 0.5], 
            "gripper_open": True,
            "description": "Planning safe path around obstacles",
            "detected_objects": [],
            "target_info": "Calculating optimal route",
            "path_points": [[0.5, 0.5], [1.0, 1.0], [2.5, 1.2], [3.5, 2.0], [4.0, 4.0]]
        },
        {
            "name": "Navigate Segment 1", 
            "duration": 3, 
            "robot_pos": [1.0, 1.0], 
            "gripper_open": True,
            "description": "Moving to first waypoint",
            "detected_objects": [],
            "target_info": "Avoiding obstacle 1",
            "path_points": [[0.5, 0.5], [1.0, 1.0], [2.5, 1.2], [3.5, 2.0], [4.0, 4.0]]
        },
        {
            "name": "Navigate Segment 2", 
            "duration": 3, 
            "robot_pos": [2.5, 1.2], 
            "gripper_open": True,
            "description": "Moving to second waypoint",
            "detected_objects": [],
            "target_info": "Avoiding obstacle 2",
            "path_points": [[0.5, 0.5], [1.0, 1.0], [2.5, 1.2], [3.5, 2.0], [4.0, 4.0]]
        },
        {
            "name": "Navigate Segment 3", 
            "duration": 3, 
            "robot_pos": [3.5, 2.0], 
            "gripper_open": True,
            "description": "Moving to third waypoint",
            "detected_objects": [],
            "target_info": "Avoiding obstacle 3",
            "path_points": [[0.5, 0.5], [1.0, 1.0], [2.5, 1.2], [3.5, 2.0], [4.0, 4.0]]
        },
        {
            "name": "Approach Target", 
            "duration": 2, 
            "robot_pos": [4.0, 4.0], 
            "gripper_open": True,
            "description": "Approaching target object",
            "detected_objects": [
                {"name": "red_cube", "position": [4.0, 4.0], "color": "red", "confidence": 95}
            ],
            "target_info": "Target reached successfully!",
            "path_points": [[0.5, 0.5], [1.0, 1.0], [2.5, 1.2], [3.5, 2.0], [4.0, 4.0]]
        }
    ]
    
    # Calculate frame data
    frame_data = []
    current_time = 0
    fps = 2
    
    for phase in phases:
        phase_frames = int(phase["duration"] * fps)
        for i in range(phase_frames):
            progress = i / phase_frames if phase_frames > 0 else 0
            
            # Interpolate robot position for movement phases
            if "Navigate" in phase["name"]:
                path_points = phase["path_points"]
                if len(path_points) >= 2:
                    # Calculate which segment we're in
                    segment_idx = 0
                    if "Segment 1" in phase["name"]:
                        segment_idx = 0
                    elif "Segment 2" in phase["name"]:
                        segment_idx = 1
                    elif "Segment 3" in phase["name"]:
                        segment_idx = 2
                    
                    if segment_idx < len(path_points) - 1:
                        start_pos = path_points[segment_idx]
                        end_pos = path_points[segment_idx + 1]
                        robot_pos = [
                            start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                            start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                        ]
                    else:
                        robot_pos = phase["robot_pos"]
                else:
                    robot_pos = phase["robot_pos"]
            else:
                robot_pos = phase["robot_pos"]
            
            frame_data.append({
                "time": current_time,
                "phase": phase["name"],
                "robot_pos": robot_pos,
                "gripper_open": phase["gripper_open"],
                "progress": progress,
                "description": phase["description"],
                "detected_objects": phase["detected_objects"],
                "target_info": phase["target_info"],
                "path_points": phase["path_points"]
            })
            
            current_time += 1/fps
    
    def animate(frame):
        """Animation function for obstacle avoidance."""
        # Clear all subplots
        ax_main.clear()
        ax_prompt.clear()
        ax_detection.clear()
        ax_progress.clear()
        ax_status.clear()
        
        if frame < len(frame_data):
            data = frame_data[frame]
            
            # Main 3D view
            ax_main.set_xlim(0, 5)
            ax_main.set_ylim(0, 5)
            ax_main.set_zlim(0, 1.0)
            ax_main.set_xlabel('X Position (meters)')
            ax_main.set_ylabel('Y Position (meters)')
            ax_main.set_zlabel('Z Position (meters)')
            ax_main.set_title(f'MERLIN: {data["phase"]} - {data["time"]:.1f}s', fontsize=12, fontweight='bold')
            
            # Draw ground plane grid
            x = np.linspace(0, 5, 6)
            y = np.linspace(0, 5, 6)
            for i in range(len(x)):
                ax_main.plot([x[i], x[i]], [0, 5], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            for i in range(len(y)):
                ax_main.plot([0, 5], [y[i], y[i]], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            
            # Draw obstacles
            for obstacle in obstacles:
                pos = obstacle["position"]
                size = obstacle["size"]
                # Draw obstacle as a cylinder
                theta = np.linspace(0, 2*np.pi, 30)
                x_circle = pos[0] + size/2 * np.cos(theta)
                y_circle = pos[1] + size/2 * np.sin(theta)
                z_circle = np.zeros_like(theta)
                ax_main.plot(x_circle, y_circle, z_circle, 'r-', linewidth=3, alpha=0.8, 
                           label='Obstacle')
                # Draw top of cylinder
                ax_main.plot(x_circle, y_circle, np.ones_like(theta) * 0.5, 'r-', linewidth=3, alpha=0.8)
            
            # Draw planned path
            if data["path_points"] and len(data["path_points"]) > 1:
                path_x = [p[0] for p in data["path_points"]]
                path_y = [p[1] for p in data["path_points"]]
                path_z = np.zeros_like(path_x)
                ax_main.plot(path_x, path_y, path_z, 'g--', linewidth=2, alpha=0.7, label='Planned Path')
                
                # Draw waypoints
                for i, point in enumerate(data["path_points"]):
                    if i == 0:
                        ax_main.scatter(point[0], point[1], 0.0, color='blue', s=100, marker='s', label='Start')
                    elif i == len(data["path_points"]) - 1:
                        ax_main.scatter(point[0], point[1], 0.0, color='red', s=100, marker='s', label='Goal')
                    else:
                        ax_main.scatter(point[0], point[1], 0.0, color='yellow', s=50, marker='o', alpha=0.7)
            
            # Draw robot
            robot_pos = data["robot_pos"]
            ax_main.scatter(robot_pos[0], robot_pos[1], 0.1, color='blue', s=200, marker='s', label='Robot')
            
            # Draw gripper
            gripper_color = 'green' if data["gripper_open"] else 'red'
            gripper_pos = [robot_pos[0] + 0.3, robot_pos[1], 0.1]
            ax_main.scatter(gripper_pos[0], gripper_pos[1], 0.1, color=gripper_color, s=100, marker='^', label='Gripper')
            
            # Draw target object
            for obj in data["detected_objects"]:
                pos = obj["position"]
                color = obj["color"]
                ax_main.scatter(pos[0], pos[1], 0.0, color=color, s=200, marker='s', alpha=0.8, 
                              label=obj["name"].replace('_', ' ').title())
            
            # Prompt display
            ax_prompt.set_xlim(0, 1)
            ax_prompt.set_ylim(0, 1)
            ax_prompt.axis('off')
            ax_prompt.set_title('Navigation Mission', fontsize=12, fontweight='bold')
            ax_prompt.text(0.5, 0.8, f'"{mission_prompt}"', ha='center', va='center', 
                          fontsize=12, fontweight='bold', color='#58a6ff',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#161B22', alpha=0.8))
            ax_prompt.text(0.5, 0.5, 'Obstacles detected:', ha='center', va='center', 
                          fontsize=11, color='#e6edf3')
            ax_prompt.text(0.5, 0.3, f'{len(obstacles)} obstacles', ha='center', va='center', 
                          fontsize=10, color='#ef4444')
            
            # Path planning display
            ax_detection.set_xlim(0, 1)
            ax_detection.set_ylim(0, 1)
            ax_detection.axis('off')
            ax_detection.set_title('Path Planning', fontsize=12, fontweight='bold')
            
            if data["path_points"]:
                ax_detection.text(0.5, 0.7, f'Waypoints: {len(data["path_points"])}', ha='center', va='center', 
                                fontsize=11, color='#10b981', fontweight='bold')
                ax_detection.text(0.5, 0.5, f'Distance: {len(data["path_points"])-1} segments', ha='center', va='center', 
                                fontsize=10, color='#e6edf3')
            else:
                ax_detection.text(0.5, 0.6, 'Planning path...', ha='center', va='center', 
                                fontsize=12, color='#7d8590')
            
            # Mission progress
            ax_progress.set_xlim(0, 1)
            ax_progress.set_ylim(0, 1)
            ax_progress.axis('off')
            ax_progress.set_title('Mission Progress', fontsize=12, fontweight='bold')
            
            phase_names = ["Environment Mapping", "Path Planning", "Navigate Segment 1", 
                          "Navigate Segment 2", "Navigate Segment 3", "Approach Target"]
            current_phase_idx = phase_names.index(data["phase"]) if data["phase"] in phase_names else 0
            
            for i, phase_name in enumerate(phase_names):
                if i <= current_phase_idx:
                    color = '#10b981' if i == current_phase_idx else '#58a6ff'
                    marker = '●' if i == current_phase_idx else '✓'
                else:
                    color = '#6b7280'
                    marker = '○'
                
                y_pos = 0.8 - i * 0.12
                ax_progress.text(0.1, y_pos, f'{marker} {phase_name}', 
                               fontsize=9, color=color, fontweight='bold')
            
            # Robot status
            ax_status.set_xlim(0, 1)
            ax_status.set_ylim(0, 1)
            ax_status.axis('off')
            ax_status.set_title('Robot Status', fontsize=12, fontweight='bold')
            
            gripper_status = "OPEN" if data["gripper_open"] else "CLOSED"
            gripper_color = '#10b981' if data["gripper_open"] else '#ef4444'
            
            ax_status.text(0.1, 0.8, f'Position: [{robot_pos[0]:.1f}, {robot_pos[1]:.1f}]', 
                         fontsize=10, color='#e6edf3')
            ax_status.text(0.1, 0.6, f'Gripper: {gripper_status}', 
                         fontsize=10, color=gripper_color, fontweight='bold')
            ax_status.text(0.1, 0.4, f'Progress: {data["progress"]*100:.0f}%', 
                         fontsize=10, color='#f59e0b')
            ax_status.text(0.1, 0.2, data["target_info"], 
                         fontsize=9, color='#7d8590')
    
    # Create animation
    total_frames = len(frame_data)
    anim = animation.FuncAnimation(fig, animate, frames=total_frames, interval=1000/fps, repeat=True)
    
    # Save as video
    print("💾 Saving obstacle avoidance video...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='MERLIN'), bitrate=1800)
    
    try:
        anim.save('Data/videos/merlin_obstacle_avoidance.mp4', writer=writer)
        print("✅ Obstacle avoidance video saved as merlin_obstacle_avoidance.mp4")
    except Exception as e:
        print(f"⚠️ Could not save video (ffmpeg not available): {e}")
        print("💡 Saving as GIF instead...")
        try:
            anim.save('Data/videos/merlin_obstacle_avoidance.gif', writer='pillow', fps=fps)
            print("✅ Obstacle avoidance video saved as merlin_obstacle_avoidance.gif")
        except Exception as e2:
            print(f"⚠️ Could not save GIF either: {e2}")
            print("💡 Saving individual frames instead...")
            # Save individual frames
            for i in range(min(20, total_frames)):  # Save first 20 frames
                animate(i)
                plt.savefig(f'Data/videos/obstacle_frame_{i:03d}.png', dpi=150, bbox_inches='tight')
            print("✅ Individual obstacle avoidance frames saved")
    
    plt.close()

def create_precision_placement_video():
    """Create a video showing precision placement tasks."""
    print("🎬 Creating Precision Placement Mission Video...")
    
    # Create simulator
    simulator = Robot3DSimulator(output_dir="/Users/ahmadkaddoura/calhacks/Data")
    
    # Mission parameters - precise placement
    mission_prompt = "Place the blue block precisely in the center of the target zone"
    target_object = "blue_block"
    target_zone = [2.5, 2.5]
    precision_threshold = 0.1
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create subplots
    ax_main = fig.add_subplot(2, 3, (1, 4), projection='3d')  # Main 3D view
    ax_prompt = fig.add_subplot(2, 3, 2)  # Prompt display
    ax_detection = fig.add_subplot(2, 3, 3)  # Precision display
    ax_progress = fig.add_subplot(2, 3, 5)  # Mission progress
    ax_status = fig.add_subplot(2, 3, 6)  # Robot status
    
    # Mission phases for precision placement
    phases = [
        {
            "name": "Target Identification", 
            "duration": 2, 
            "robot_pos": [1.0, 1.0], 
            "gripper_open": True,
            "description": "Identifying target object and zone",
            "detected_objects": [
                {"name": "blue_block", "position": [1.5, 1.5], "color": "blue", "confidence": 97}
            ],
            "target_info": "Target: blue block at [1.5, 1.5]",
            "precision_error": 0.0
        },
        {
            "name": "Approach Target", 
            "duration": 3, 
            "robot_pos": [1.5, 1.5], 
            "gripper_open": True,
            "description": "Approaching target object",
            "detected_objects": [
                {"name": "blue_block", "position": [1.5, 1.5], "color": "blue", "confidence": 97}
            ],
            "target_info": "Positioning for precise grasp",
            "precision_error": 0.0
        },
        {
            "name": "Precise Grasp", 
            "duration": 2, 
            "robot_pos": [1.5, 1.5], 
            "gripper_open": False,
            "description": "Grasping with precision",
            "detected_objects": [],
            "target_info": "Object grasped precisely",
            "precision_error": 0.0
        },
        {
            "name": "Navigate to Zone", 
            "duration": 3, 
            "robot_pos": target_zone, 
            "gripper_open": False,
            "description": "Moving to target zone",
            "detected_objects": [],
            "target_info": "Approaching target zone",
            "precision_error": 0.0
        },
        {
            "name": "Precision Alignment", 
            "duration": 2, 
            "robot_pos": target_zone, 
            "gripper_open": False,
            "description": "Fine-tuning position",
            "detected_objects": [],
            "target_info": "Aligning for precise placement",
            "precision_error": 0.05
        },
        {
            "name": "Precise Placement", 
            "duration": 1, 
            "robot_pos": target_zone, 
            "gripper_open": True,
            "description": "Placing with precision",
            "detected_objects": [],
            "target_info": "Placement successful!",
            "precision_error": 0.02
        }
    ]
    
    # Calculate frame data
    frame_data = []
    current_time = 0
    fps = 2
    
    for phase in phases:
        phase_frames = int(phase["duration"] * fps)
        for i in range(phase_frames):
            progress = i / phase_frames if phase_frames > 0 else 0
            
            # Interpolate robot position for movement phases
            if phase["name"] == "Approach Target":
                start_pos = [1.0, 1.0]
                end_pos = [1.5, 1.5]
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            elif phase["name"] == "Navigate to Zone":
                start_pos = [1.5, 1.5]
                end_pos = target_zone
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            else:
                robot_pos = phase["robot_pos"]
            
            # Update object position if being held
            if phase["name"] in ["Precise Grasp", "Navigate to Zone", "Precision Alignment"] and not phase["gripper_open"]:
                gripper_offset = 0.3
                gripper_pos = [
                    robot_pos[0] + gripper_offset * np.cos(progress * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(progress * 2 * np.pi),
                    0.0
                ]
                simulator.objects[target_object]['position'] = np.array(gripper_pos)
                simulator.held_object = target_object
            else:
                simulator.held_object = None
            
            frame_data.append({
                "time": current_time,
                "phase": phase["name"],
                "robot_pos": robot_pos,
                "gripper_open": phase["gripper_open"],
                "progress": progress,
                "description": phase["description"],
                "detected_objects": phase["detected_objects"],
                "target_info": phase["target_info"],
                "precision_error": phase["precision_error"]
            })
            
            current_time += 1/fps
    
    def animate(frame):
        """Animation function for precision placement."""
        # Clear all subplots
        ax_main.clear()
        ax_prompt.clear()
        ax_detection.clear()
        ax_progress.clear()
        ax_status.clear()
        
        if frame < len(frame_data):
            data = frame_data[frame]
            
            # Main 3D view
            ax_main.set_xlim(0, 5)
            ax_main.set_ylim(0, 5)
            ax_main.set_zlim(0, 1.0)
            ax_main.set_xlabel('X Position (meters)')
            ax_main.set_ylabel('Y Position (meters)')
            ax_main.set_zlabel('Z Position (meters)')
            ax_main.set_title(f'MERLIN: {data["phase"]} - {data["time"]:.1f}s', fontsize=12, fontweight='bold')
            
            # Draw ground plane grid
            x = np.linspace(0, 5, 6)
            y = np.linspace(0, 5, 6)
            for i in range(len(x)):
                ax_main.plot([x[i], x[i]], [0, 5], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            for i in range(len(y)):
                ax_main.plot([0, 5], [y[i], y[i]], [0, 0], 'k-', alpha=0.2, linewidth=0.5)
            
            # Draw target zone
            zone_color = 'green' if data["precision_error"] < precision_threshold else 'yellow'
            theta = np.linspace(0, 2*np.pi, 30)
            x_circle = target_zone[0] + precision_threshold * np.cos(theta)
            y_circle = target_zone[1] + precision_threshold * np.sin(theta)
            z_circle = np.zeros_like(theta)
            ax_main.plot(x_circle, y_circle, z_circle, color=zone_color, linewidth=3, alpha=0.8, 
                       linestyle='--', label='Target Zone')
            
            # Draw robot
            robot_pos = data["robot_pos"]
            ax_main.scatter(robot_pos[0], robot_pos[1], 0.1, color='blue', s=200, marker='s', label='Robot')
            
            # Draw gripper
            gripper_color = 'green' if data["gripper_open"] else 'red'
            gripper_pos = [robot_pos[0] + 0.3, robot_pos[1], 0.1]
            ax_main.scatter(gripper_pos[0], gripper_pos[1], 0.1, color=gripper_color, s=100, marker='^', label='Gripper')
            
            # Draw objects
            for obj in data["detected_objects"]:
                pos = obj["position"]
                color = obj["color"]
                ax_main.scatter(pos[0], pos[1], 0.0, color=color, s=200, marker='s', alpha=0.8, 
                              label=obj["name"].replace('_', ' ').title())
            
            # Draw held object
            if simulator.held_object:
                held_obj = simulator.objects[simulator.held_object]
                gripper_offset = 0.3
                held_pos = [
                    robot_pos[0] + gripper_offset * np.cos(data["progress"] * 2 * np.pi),
                    robot_pos[1] + gripper_offset * np.sin(data["progress"] * 2 * np.pi),
                    0.0
                ]
                ax_main.scatter(held_pos[0], held_pos[1], held_pos[2], 
                              color=held_obj['color'], s=300, marker='s', alpha=0.9,
                              edgecolors='yellow', linewidth=2,
                              label=f'Holding {simulator.held_object.replace("_", " ").title()}')
            
            # Prompt display
            ax_prompt.set_xlim(0, 1)
            ax_prompt.set_ylim(0, 1)
            ax_prompt.axis('off')
            ax_prompt.set_title('Precision Mission', fontsize=12, fontweight='bold')
            ax_prompt.text(0.5, 0.8, f'"{mission_prompt}"', ha='center', va='center', 
                          fontsize=12, fontweight='bold', color='#58a6ff',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#161B22', alpha=0.8))
            ax_prompt.text(0.5, 0.5, 'Target Zone:', ha='center', va='center', 
                          fontsize=11, color='#e6edf3')
            ax_prompt.text(0.5, 0.3, f'Center: {target_zone}', ha='center', va='center', 
                          fontsize=10, color='#10b981')
            
            # Precision display
            ax_detection.set_xlim(0, 1)
            ax_detection.set_ylim(0, 1)
            ax_detection.axis('off')
            ax_detection.set_title('Precision Metrics', fontsize=12, fontweight='bold')
            
            precision_status = "EXCELLENT" if data["precision_error"] < 0.05 else "GOOD" if data["precision_error"] < 0.1 else "NEEDS IMPROVEMENT"
            precision_color = '#10b981' if data["precision_error"] < 0.05 else '#f59e0b' if data["precision_error"] < 0.1 else '#ef4444'
            
            ax_detection.text(0.5, 0.7, f'Error: {data["precision_error"]:.3f}m', ha='center', va='center', 
                            fontsize=12, color=precision_color, fontweight='bold')
            ax_detection.text(0.5, 0.5, f'Status: {precision_status}', ha='center', va='center', 
                            fontsize=11, color=precision_color)
            ax_detection.text(0.5, 0.3, f'Threshold: {precision_threshold}m', ha='center', va='center', 
                            fontsize=10, color='#7d8590')
            
            # Mission progress
            ax_progress.set_xlim(0, 1)
            ax_progress.set_ylim(0, 1)
            ax_progress.axis('off')
            ax_progress.set_title('Mission Progress', fontsize=12, fontweight='bold')
            
            phase_names = ["Target Identification", "Approach Target", "Precise Grasp", 
                          "Navigate to Zone", "Precision Alignment", "Precise Placement"]
            current_phase_idx = phase_names.index(data["phase"]) if data["phase"] in phase_names else 0
            
            for i, phase_name in enumerate(phase_names):
                if i <= current_phase_idx:
                    color = '#10b981' if i == current_phase_idx else '#58a6ff'
                    marker = '●' if i == current_phase_idx else '✓'
                else:
                    color = '#6b7280'
                    marker = '○'
                
                y_pos = 0.8 - i * 0.12
                ax_progress.text(0.1, y_pos, f'{marker} {phase_name}', 
                               fontsize=9, color=color, fontweight='bold')
            
            # Robot status
            ax_status.set_xlim(0, 1)
            ax_status.set_ylim(0, 1)
            ax_status.axis('off')
            ax_status.set_title('Robot Status', fontsize=12, fontweight='bold')
            
            gripper_status = "OPEN" if data["gripper_open"] else "CLOSED"
            gripper_color = '#10b981' if data["gripper_open"] else '#ef4444'
            
            ax_status.text(0.1, 0.8, f'Position: [{robot_pos[0]:.1f}, {robot_pos[1]:.1f}]', 
                         fontsize=10, color='#e6edf3')
            ax_status.text(0.1, 0.6, f'Gripper: {gripper_status}', 
                         fontsize=10, color=gripper_color, fontweight='bold')
            ax_status.text(0.1, 0.4, f'Progress: {data["progress"]*100:.0f}%', 
                         fontsize=10, color='#f59e0b')
            ax_status.text(0.1, 0.2, data["target_info"], 
                         fontsize=9, color='#7d8590')
    
    # Create animation
    total_frames = len(frame_data)
    anim = animation.FuncAnimation(fig, animate, frames=total_frames, interval=1000/fps, repeat=True)
    
    # Save as video
    print("💾 Saving precision placement video...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='MERLIN'), bitrate=1800)
    
    try:
        anim.save('Data/videos/merlin_precision_placement.mp4', writer=writer)
        print("✅ Precision placement video saved as merlin_precision_placement.mp4")
    except Exception as e:
        print(f"⚠️ Could not save video (ffmpeg not available): {e}")
        print("💡 Saving as GIF instead...")
        try:
            anim.save('Data/videos/merlin_precision_placement.gif', writer='pillow', fps=fps)
            print("✅ Precision placement video saved as merlin_precision_placement.gif")
        except Exception as e2:
            print(f"⚠️ Could not save GIF either: {e2}")
            print("💡 Saving individual frames instead...")
            # Save individual frames
            for i in range(min(20, total_frames)):  # Save first 20 frames
                animate(i)
                plt.savefig(f'Data/videos/precision_frame_{i:03d}.png', dpi=150, bbox_inches='tight')
            print("✅ Individual precision placement frames saved")
    
    plt.close()

def main():
    """Create additional mission videos."""
    print("🎬 Starting Additional MERLIN Mission Video Creation")
    print("=" * 60)
    
    # Create output directory
    os.makedirs('Data/videos', exist_ok=True)
    
    try:
        create_multi_object_sorting_video()
        create_obstacle_avoidance_video()
        create_precision_placement_video()
        
        print("\n🎉 Additional mission videos created successfully!")
        print("📁 Output directory: Data/videos/")
        print("\nGenerated files:")
        print("  • merlin_multi_object_sorting.mp4 (multi-object sorting mission)")
        print("  • merlin_obstacle_avoidance.mp4 (obstacle avoidance mission)")
        print("  • merlin_precision_placement.mp4 (precision placement mission)")
        
    except Exception as e:
        print(f"\n💥 Error creating additional mission videos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
