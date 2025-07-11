# Unified License Analyzer: System Overview

## Purpose
This tool helps identify license compatibility and compliance risks in software, ML, and dataset reuse scenarios.

## Core Features
- Parses SPDX, RAIL, Creative Commons, and custom license metadata
- Models dependencies between software, models, datasets, and services
- Checks license compatibility and triggers based on reuse activity
- Generates conflict reports and compliance summaries

## Architecture

1. **YAML-based License Schema**
   - Captures permissions, restrictions, obligations, and compatibility

2. **Dependency Graph**
   - Nodes: components (software/model/data)
   - Edges: reuse relationships (train, fine-tune, embed)

3. **Checker Module**
   - Analyzes combinations for conflicts
   - Detects prohibited activities and relicensing violations

4. **Taxonomy**
   - Maps real-world ML/software activities to licensing terms (e.g., “train” → “modify”)

5. **Notebook / CLI Interface**
   - Loads real or synthetic examples and returns reports
