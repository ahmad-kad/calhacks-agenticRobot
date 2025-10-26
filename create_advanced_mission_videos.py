#!/usr/bin/env python3
"""
Create Advanced Mission Videos for MERLIN
Generates advanced mission scenarios showcasing:
- Sequential task execution
- Error recovery and adaptation
- Complex multi-step workflows
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

def create_sequential_tasks_video():
    """Create a video showing sequential task execution."""
    print("🎬 Creating Sequential Tasks Mission Video...")
    
    # Create simulator
    simulator = Robot3DSimulator(output_dir="/Users/ahmadkaddoura/calhacks/Data")
    
    # Mission parameters - sequential tasks
    mission_prompt = "Complete these tasks in order: 1) Move red cube to zone A, 2) Move green sphere to zone B, 3) Move blue block to zone C"
    tasks = [
        {"object": "red_cube", "zone": [1.0, 1.0], "zone_name": "A"},
        {"object": "green_sphere", "zone": [3.0, 1.0], "zone_name": "B"},
        {"object": "blue_block", "zone": [1.0, 3.0], "zone_name": "C"}
    ]
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create subplots
    ax_main = fig.add_subplot(2, 3, (1, 4), projection='3d')  # Main 3D view
    ax_prompt = fig.add_subplot(2, 3, 2)  # Prompt display
    ax_detection = fig.add_subplot(2, 3, 3)  # Task progress
    ax_progress = fig.add_subplot(2, 3, 5)  # Mission progress
    ax_status = fig.add_subplot(2, 3, 6)  # Robot status
    
    # Mission phases for sequential tasks
    phases = [
        {
            "name": "Task Planning", 
            "duration": 2, 
            "robot_pos": [2.5, 2.5], 
            "gripper_open": True,
            "description": "Planning sequential task execution",
            "detected_objects": [
                {"name": "red_cube", "position": [2.0, 2.0], "color": "red", "confidence": 94},
                {"name": "green_sphere", "position": [3.0, 2.5], "color": "green", "confidence": 91},
                {"name": "blue_block", "position": [2.5, 3.0], "color": "blue", "confidence": 89}
            ],
            "target_info": "3 tasks planned",
            "current_task": None,
            "completed_tasks": []
        },
        {
            "name": "Task 1: Red Cube", 
            "duration": 4, 
            "robot_pos": [1.0, 1.0], 
            "gripper_open": True,
            "description": "Moving red cube to zone A",
            "detected_objects": [],
            "target_info": "Red cube delivered to zone A",
            "current_task": 0,
            "completed_tasks": []
        },
        {
            "name": "Task 2: Green Sphere", 
            "duration": 4, 
            "robot_pos": [3.0, 1.0], 
            "gripper_open": True,
            "description": "Moving green sphere to zone B",
            "detected_objects": [],
            "target_info": "Green sphere delivered to zone B",
            "current_task": 1,
            "completed_tasks": [0]
        },
        {
            "name": "Task 3: Blue Block", 
            "duration": 4, 
            "robot_pos": [1.0, 3.0], 
            "gripper_open": True,
            "description": "Moving blue block to zone C",
            "detected_objects": [],
            "target_info": "Blue block delivered to zone C",
            "current_task": 2,
            "completed_tasks": [0, 1]
        },
        {
            "name": "Mission Complete", 
            "duration": 2, 
            "robot_pos": [2.5, 2.5], 
            "gripper_open": True,
            "description": "All tasks completed successfully",
            "detected_objects": [],
            "target_info": "Sequential mission successful!",
            "current_task": None,
            "completed_tasks": [0, 1, 2]
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
            if phase["current_task"] is not None:
                task = tasks[phase["current_task"]]
                if "Task" in phase["name"]:
                    # Move to task zone
                    robot_pos = [
                        task["zone"][0] + (progress - 0.5) * 0.2,
                        task["zone"][1] + (progress - 0.5) * 0.2
                    ]
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
                "current_task": phase["current_task"],
                "completed_tasks": phase["completed_tasks"]
            })
            
            current_time += 1/fps
    
    def animate(frame):
        """Animation function for sequential tasks."""
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
            
            # Draw task zones
            zone_colors = ['red', 'green', 'blue']
            for i, task in enumerate(tasks):
                zone_color = zone_colors[i]
                pos = task["zone"]
                theta = np.linspace(0, 2*np.pi, 30)
                x_circle = pos[0] + 0.3 * np.cos(theta)
                y_circle = pos[1] + 0.3 * np.sin(theta)
                z_circle = np.zeros_like(theta)
                
                # Highlight current task zone
                if data["current_task"] == i:
                    ax_main.plot(x_circle, y_circle, z_circle, color=zone_color, linewidth=4, alpha=0.9, 
                               linestyle='-', label=f'Zone {task["zone_name"]} (CURRENT)')
                else:
                    ax_main.plot(x_circle, y_circle, z_circle, color=zone_color, linewidth=2, alpha=0.6, 
                               linestyle='--', label=f'Zone {task["zone_name"]}')
            
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
            
            # Prompt display
            ax_prompt.set_xlim(0, 1)
            ax_prompt.set_ylim(0, 1)
            ax_prompt.axis('off')
            ax_prompt.set_title('Sequential Mission', fontsize=12, fontweight='bold')
            ax_prompt.text(0.5, 0.8, f'"{mission_prompt}"', ha='center', va='center', 
                          fontsize=11, fontweight='bold', color='#58a6ff',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#161B22', alpha=0.8))
            ax_prompt.text(0.5, 0.5, 'Task Order:', ha='center', va='center', 
                          fontsize=11, color='#e6edf3')
            ax_prompt.text(0.5, 0.3, '1→A  2→B  3→C', ha='center', va='center', 
                          fontsize=10, color='#7d8590')
            
            # Task progress display
            ax_detection.set_xlim(0, 1)
            ax_detection.set_ylim(0, 1)
            ax_detection.axis('off')
            ax_detection.set_title('Task Progress', fontsize=12, fontweight='bold')
            
            if data["current_task"] is not None:
                task = tasks[data["current_task"]]
                ax_detection.text(0.5, 0.7, f'Current Task: {data["current_task"] + 1}', ha='center', va='center', 
                                fontsize=12, color='#f59e0b', fontweight='bold')
                ax_detection.text(0.5, 0.5, f'{task["object"].replace("_", " ").title()}', ha='center', va='center', 
                                fontsize=11, color='#10b981')
                ax_detection.text(0.5, 0.3, f'→ Zone {task["zone_name"]}', ha='center', va='center', 
                                fontsize=10, color='#e6edf3')
            else:
                ax_detection.text(0.5, 0.6, f'Completed: {len(data["completed_tasks"])}/3', ha='center', va='center', 
                                fontsize=12, color='#10b981', fontweight='bold')
            
            # Mission progress
            ax_progress.set_xlim(0, 1)
            ax_progress.set_ylim(0, 1)
            ax_progress.axis('off')
            ax_progress.set_title('Mission Progress', fontsize=12, fontweight='bold')
            
            phase_names = ["Task Planning", "Task 1: Red Cube", "Task 2: Green Sphere", 
                          "Task 3: Blue Block", "Mission Complete"]
            current_phase_idx = phase_names.index(data["phase"]) if data["phase"] in phase_names else 0
            
            for i, phase_name in enumerate(phase_names):
                if i <= current_phase_idx:
                    color = '#10b981' if i == current_phase_idx else '#58a6ff'
                    marker = '●' if i == current_phase_idx else '✓'
                else:
                    color = '#6b7280'
                    marker = '○'
                
                y_pos = 0.8 - i * 0.15
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
    print("💾 Saving sequential tasks video...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='MERLIN'), bitrate=1800)
    
    try:
        anim.save('Data/videos/merlin_sequential_tasks.mp4', writer=writer)
        print("✅ Sequential tasks video saved as merlin_sequential_tasks.mp4")
    except Exception as e:
        print(f"⚠️ Could not save video (ffmpeg not available): {e}")
        print("💡 Saving as GIF instead...")
        try:
            anim.save('Data/videos/merlin_sequential_tasks.gif', writer='pillow', fps=fps)
            print("✅ Sequential tasks video saved as merlin_sequential_tasks.gif")
        except Exception as e2:
            print(f"⚠️ Could not save GIF either: {e2}")
            print("💡 Saving individual frames instead...")
            # Save individual frames
            for i in range(min(20, total_frames)):  # Save first 20 frames
                animate(i)
                plt.savefig(f'Data/videos/sequential_frame_{i:03d}.png', dpi=150, bbox_inches='tight')
            print("✅ Individual sequential task frames saved")
    
    plt.close()

def create_error_recovery_video():
    """Create a video showing error recovery and adaptation."""
    print("🎬 Creating Error Recovery Mission Video...")
    
    # Create simulator
    simulator = Robot3DSimulator(output_dir="/Users/ahmadkaddoura/calhacks/Data")
    
    # Mission parameters - error recovery
    mission_prompt = "Pick up the red cube and place it in the target zone"
    target_object = "red_cube"
    target_zone = [3.0, 3.0]
    
    # Set up the figure with subplots
    fig = plt.figure(figsize=(16, 10))
    
    # Create subplots
    ax_main = fig.add_subplot(2, 3, (1, 4), projection='3d')  # Main 3D view
    ax_prompt = fig.add_subplot(2, 3, 2)  # Prompt display
    ax_detection = fig.add_subplot(2, 3, 3)  # Error status
    ax_progress = fig.add_subplot(2, 3, 5)  # Mission progress
    ax_status = fig.add_subplot(2, 3, 6)  # Robot status
    
    # Mission phases for error recovery
    phases = [
        {
            "name": "Initial Attempt", 
            "duration": 2, 
            "robot_pos": [1.0, 1.0], 
            "gripper_open": True,
            "description": "Attempting to pick up red cube",
            "detected_objects": [
                {"name": "red_cube", "position": [2.0, 2.0], "color": "red", "confidence": 94}
            ],
            "target_info": "Approaching target object",
            "error_status": "NONE",
            "recovery_attempts": 0
        },
        {
            "name": "Grasp Failed", 
            "duration": 1, 
            "robot_pos": [2.0, 2.0], 
            "gripper_open": True,
            "description": "Grasp attempt failed - object too heavy",
            "detected_objects": [
                {"name": "red_cube", "position": [2.0, 2.0], "color": "red", "confidence": 94}
            ],
            "target_info": "Error: Grasp failed",
            "error_status": "GRASP_FAILED",
            "recovery_attempts": 0
        },
        {
            "name": "Error Analysis", 
            "duration": 2, 
            "robot_pos": [2.0, 2.0], 
            "gripper_open": True,
            "description": "Analyzing error and planning recovery",
            "detected_objects": [
                {"name": "red_cube", "position": [2.0, 2.0], "color": "red", "confidence": 94}
            ],
            "target_info": "Recovery strategy: Adjust grip strength",
            "error_status": "ANALYZING",
            "recovery_attempts": 0
        },
        {
            "name": "Recovery Attempt 1", 
            "duration": 2, 
            "robot_pos": [2.0, 2.0], 
            "gripper_open": False,
            "description": "Recovery attempt with adjusted grip",
            "detected_objects": [],
            "target_info": "Recovery attempt 1/3",
            "error_status": "RECOVERING",
            "recovery_attempts": 1
        },
        {
            "name": "Recovery Success", 
            "duration": 1, 
            "robot_pos": [2.0, 2.0], 
            "gripper_open": False,
            "description": "Recovery successful - object grasped",
            "detected_objects": [],
            "target_info": "Object grasped successfully!",
            "error_status": "RECOVERED",
            "recovery_attempts": 1
        },
        {
            "name": "Transport to Target", 
            "duration": 3, 
            "robot_pos": target_zone, 
            "gripper_open": False,
            "description": "Transporting object to target zone",
            "detected_objects": [],
            "target_info": "Moving to target zone",
            "error_status": "NONE",
            "recovery_attempts": 1
        },
        {
            "name": "Mission Success", 
            "duration": 1, 
            "robot_pos": target_zone, 
            "gripper_open": True,
            "description": "Mission completed despite initial error",
            "detected_objects": [],
            "target_info": "Mission successful with recovery!",
            "error_status": "SUCCESS",
            "recovery_attempts": 1
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
            if phase["name"] == "Transport to Target":
                start_pos = [2.0, 2.0]
                end_pos = target_zone
                robot_pos = [
                    start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
                    start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                ]
            else:
                robot_pos = phase["robot_pos"]
            
            # Update object position if being held
            if phase["name"] in ["Recovery Attempt 1", "Recovery Success", "Transport to Target"] and not phase["gripper_open"]:
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
                "error_status": phase["error_status"],
                "recovery_attempts": phase["recovery_attempts"]
            })
            
            current_time += 1/fps
    
    def animate(frame):
        """Animation function for error recovery."""
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
            zone_color = 'green' if data["error_status"] == "SUCCESS" else 'yellow' if data["error_status"] == "RECOVERED" else 'red' if data["error_status"] in ["GRASP_FAILED", "ANALYZING"] else 'blue'
            theta = np.linspace(0, 2*np.pi, 30)
            x_circle = target_zone[0] + 0.3 * np.cos(theta)
            y_circle = target_zone[1] + 0.3 * np.sin(theta)
            z_circle = np.zeros_like(theta)
            ax_main.plot(x_circle, y_circle, z_circle, color=zone_color, linewidth=3, alpha=0.8, 
                       linestyle='--', label='Target Zone')
            
            # Draw robot
            robot_pos = data["robot_pos"]
            robot_color = 'red' if data["error_status"] in ["GRASP_FAILED", "ANALYZING"] else 'green' if data["error_status"] == "SUCCESS" else 'blue'
            ax_main.scatter(robot_pos[0], robot_pos[1], 0.1, color=robot_color, s=200, marker='s', label='Robot')
            
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
            ax_prompt.set_title('Error Recovery Mission', fontsize=12, fontweight='bold')
            ax_prompt.text(0.5, 0.8, f'"{mission_prompt}"', ha='center', va='center', 
                          fontsize=12, fontweight='bold', color='#58a6ff',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor='#161B22', alpha=0.8))
            ax_prompt.text(0.5, 0.5, 'Demonstrates:', ha='center', va='center', 
                          fontsize=11, color='#e6edf3')
            ax_prompt.text(0.5, 0.3, 'Error detection & recovery', ha='center', va='center', 
                          fontsize=10, color='#f59e0b')
            
            # Error status display
            ax_detection.set_xlim(0, 1)
            ax_detection.set_ylim(0, 1)
            ax_detection.axis('off')
            ax_detection.set_title('Error Status', fontsize=12, fontweight='bold')
            
            error_colors = {
                "NONE": '#10b981',
                "GRASP_FAILED": '#ef4444',
                "ANALYZING": '#f59e0b',
                "RECOVERING": '#3b82f6',
                "RECOVERED": '#10b981',
                "SUCCESS": '#10b981'
            }
            
            error_color = error_colors.get(data["error_status"], '#7d8590')
            ax_detection.text(0.5, 0.7, f'Status: {data["error_status"]}', ha='center', va='center', 
                            fontsize=12, color=error_color, fontweight='bold')
            
            if data["recovery_attempts"] > 0:
                ax_detection.text(0.5, 0.5, f'Recovery attempts: {data["recovery_attempts"]}', ha='center', va='center', 
                                fontsize=11, color='#e6edf3')
            
            # Mission progress
            ax_progress.set_xlim(0, 1)
            ax_progress.set_ylim(0, 1)
            ax_progress.axis('off')
            ax_progress.set_title('Mission Progress', fontsize=12, fontweight='bold')
            
            phase_names = ["Initial Attempt", "Grasp Failed", "Error Analysis", "Recovery Attempt 1", 
                          "Recovery Success", "Transport to Target", "Mission Success"]
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
                               fontsize=8, color=color, fontweight='bold')
            
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
    print("💾 Saving error recovery video...")
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=fps, metadata=dict(artist='MERLIN'), bitrate=1800)
    
    try:
        anim.save('Data/videos/merlin_error_recovery.mp4', writer=writer)
        print("✅ Error recovery video saved as merlin_error_recovery.mp4")
    except Exception as e:
        print(f"⚠️ Could not save video (ffmpeg not available): {e}")
        print("💡 Saving as GIF instead...")
        try:
            anim.save('Data/videos/merlin_error_recovery.gif', writer='pillow', fps=fps)
            print("✅ Error recovery video saved as merlin_error_recovery.gif")
        except Exception as e2:
            print(f"⚠️ Could not save GIF either: {e2}")
            print("💡 Saving individual frames instead...")
            # Save individual frames
            for i in range(min(20, total_frames)):  # Save first 20 frames
                animate(i)
                plt.savefig(f'Data/videos/recovery_frame_{i:03d}.png', dpi=150, bbox_inches='tight')
            print("✅ Individual error recovery frames saved")
    
    plt.close()

def main():
    """Create advanced mission videos."""
    print("🎬 Starting Advanced MERLIN Mission Video Creation")
    print("=" * 60)
    
    # Create output directory
    os.makedirs('Data/videos', exist_ok=True)
    
    try:
        create_sequential_tasks_video()
        create_error_recovery_video()
        
        print("\n🎉 Advanced mission videos created successfully!")
        print("📁 Output directory: Data/videos/")
        print("\nGenerated files:")
        print("  • merlin_sequential_tasks.mp4 (sequential task execution)")
        print("  • merlin_error_recovery.mp4 (error recovery and adaptation)")
        
    except Exception as e:
        print(f"\n💥 Error creating advanced mission videos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
