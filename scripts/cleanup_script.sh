#!/bin/bash

# MercuraClone Workspace Cleanup Script
# This script documents the commands used to clean up the workspace

echo "Starting MercuraClone workspace cleanup..."

# Task 1: Consolidate Application Folders
echo "Task 1: Deleting redundant my-app folder..."
rm -rf my-app/

# Task 2: Root Directory De-Sprawl & Archiving
echo "Task 2: Creating archive and docs directories..."
mkdir -p archive docs

echo "Moving legacy research files to archive..."
mv CompetitorPDR.md archive/
mv FutureDevelopmentPlans.md archive/

echo "Moving technical documentation to docs..."
mv DEPLOYMENT_CHECKLIST.md docs/
mv DEPLOYMENT_FREE_OPTIONS.md docs/
mv QUICKSTART.md docs/
mv FILE_STRUCTURE.md docs/

echo "Consolidating README files..."
# The consolidated README_new.md has been created and will replace README.md
mv README_new.md README.md

# Task 3: Environment Cleanup
echo "Task 3: Consolidating environment files..."
# .env.example has been updated with consolidated content
rm env.template

echo "Workspace cleanup completed!"
echo ""
echo "Summary of Source of Truth locations:"
echo "====================================="
echo "Web Dashboard: frontend/src/"
echo "Browser Extension: frontend/src/chrome/"
echo "Backend API: app/"
echo "Documentation: docs/"
echo "Legacy Research: archive/"
echo "Environment Config: .env.example"
echo "Project Roadmap: MasterProjectRoadmap.md"
