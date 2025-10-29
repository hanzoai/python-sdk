# Copyright 2025 Zoo Labs Foundation Inc. and the Gym team.
#
# Experience Manager for Training-Free GRPO
# Based on Tencent youtu-agent: https://arxiv.org/abs/2510.08191v1
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, List, Literal
import json
from pathlib import Path

Operation = Literal["add", "delete", "modify", "merge", "keep"]


class ExperienceManager:
    """Manages the experience library E for Training-Free GRPO.
    
    The experience library stores generalizable strategic insights extracted
    from trajectory groups. Each experience is a concise (≤32 words) natural
    language statement that guides future problem-solving.
    
    Example experiences:
    - "When solving equations, verify solutions by substitution to catch errors."
    - "For optimization problems, check boundary conditions before applying calculus."
    - "In probability, use conditional probability when events are dependent."
    """

    def __init__(self, checkpoint_path: str = None):
        """Initialize experience manager.
        
        Args:
            checkpoint_path: Path to load/save experiences (JSON format)
        """
        self.experiences: Dict[str, str] = {}
        self._next_id = 0
        self.checkpoint_path = checkpoint_path

        if checkpoint_path and Path(checkpoint_path).exists():
            self.load(checkpoint_path)

    def add(self, experience: str) -> str:
        """Add new experience, return assigned ID.
        
        Args:
            experience: Natural language experience statement (≤32 words)
            
        Returns:
            exp_id: Assigned experience ID (format: "G{N}")
        """
        exp_id = f"G{self._next_id}"
        self.experiences[exp_id] = experience
        self._next_id += 1
        return exp_id

    def delete(self, exp_id: str) -> bool:
        """Delete experience by ID.
        
        Args:
            exp_id: Experience ID to delete
            
        Returns:
            success: True if deleted, False if ID not found
        """
        if exp_id in self.experiences:
            del self.experiences[exp_id]
            return True
        return False

    def modify(self, exp_id: str, new_experience: str) -> bool:
        """Modify existing experience.
        
        Args:
            exp_id: Experience ID to modify
            new_experience: New experience text
            
        Returns:
            success: True if modified, False if ID not found
        """
        if exp_id in self.experiences:
            self.experiences[exp_id] = new_experience
            return True
        return False

    def merge(self, exp_ids: List[str], merged_experience: str) -> str:
        """Merge multiple experiences into one.
        
        Deletes the original experiences and creates a new merged one.
        
        Args:
            exp_ids: List of experience IDs to merge
            merged_experience: Merged experience text
            
        Returns:
            new_exp_id: ID of the newly created merged experience
        """
        # Delete old experiences
        for exp_id in exp_ids:
            self.delete(exp_id)
        # Add merged experience
        return self.add(merged_experience)

    def apply_operations(self, operations: List[Dict]) -> None:
        """Apply batch of operations from LLM.
        
        This is the main interface for updating the experience library based
        on LLM-extracted semantic advantages.
        
        Args:
            operations: List of operation dictionaries with keys:
                - "option": One of ["add", "modify", "delete", "merge", "keep"]
                - "experience": New/modified experience text (for add/modify/merge)
                - "modified_from": Original experience ID (for modify)
                - "delete_id": Experience ID to delete (for delete)
                - "merged_from": List of experience IDs to merge (for merge)
                
        Example:
            operations = [
                {"option": "add", "experience": "When solving..."},
                {"option": "modify", "experience": "Updated...", "modified_from": "G17"},
                {"option": "delete", "delete_id": "G5"},
                {"option": "merge", "experience": "Merged...", "merged_from": ["G1", "G3"]}
            ]
        """
        for op in operations:
            option = op.get("option", "keep")

            if option == "add":
                self.add(op["experience"])

            elif option == "delete":
                self.delete(op["delete_id"])

            elif option == "modify":
                self.modify(op["modified_from"], op["experience"])

            elif option == "merge":
                self.merge(op["merged_from"], op["experience"])
                
            # "keep" option does nothing

    def format_for_prompt(self) -> str:
        """Format experiences for injection into prompts.
        
        Returns:
            formatted: Multi-line string with numbered experiences
            
        Example output:
            [G0]. When solving equations, verify solutions by substitution.
            [G1]. For optimization, check boundary conditions first.
            [G2]. In probability, use conditional probability when dependent.
        """
        if not self.experiences:
            return "None"

        formatted = []
        for exp_id, exp_text in self.experiences.items():
            formatted.append(f"[{exp_id}]. {exp_text}")

        return "\n".join(formatted)

    def save(self, path: str) -> None:
        """Save experiences to JSON file.
        
        Args:
            path: Output file path
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump({
                "experiences": self.experiences,
                "next_id": self._next_id
            }, f, indent=2)

    def load(self, path: str) -> None:
        """Load experiences from JSON file.
        
        Args:
            path: Input file path
        """
        with open(path) as f:
            data = json.load(f)
            self.experiences = data["experiences"]
            self._next_id = data["next_id"]

    def __len__(self) -> int:
        """Return number of experiences in library."""
        return len(self.experiences)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ExperienceManager({len(self)} experiences)"
