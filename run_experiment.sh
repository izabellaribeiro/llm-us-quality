#!/bin/bash

###############################################################################
# Experiment Reproduction Script
# 
# This script reproduces the LLM user story quality evaluation experiment.
# It evaluates user stories from 3 projects using 3 GPT models.
#
# Prerequisites:
#   - Python 3.8+
#   - Virtual environment with dependencies installed
#   - .env file with OpenAI API key
#
# Usage:
#   chmod +x run_experiment.sh
#   ./run_experiment.sh
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  LLM User Story Quality Evaluation - Experiment Runner    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Step 1: Check Prerequisites
###############################################################################

echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env file not found!${NC}"
    echo -e "${YELLOW}  Please create .env file with your OpenAI API key:${NC}"
    echo -e "${YELLOW}  API_KEY=your-api-key-here${NC}"
    exit 1
fi

# Check if API key is set
if ! grep -q "API_KEY=" .env; then
    echo -e "${RED}✗ API_KEY not found in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}✓ .env file found with API_KEY${NC}"

###############################################################################
# Step 2: Install Dependencies
###############################################################################

echo ""
echo -e "${YELLOW}[2/6] Installing dependencies...${NC}"

pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

###############################################################################
# Step 3: Verify Data Files
###############################################################################

echo ""
echo -e "${YELLOW}[3/6] Verifying data files...${NC}"

DATASETS=(
    "data/raw/g13-planningpoker.txt"
    "data/raw/g21-badcamp.txt"
    "data/raw/g28-zooniverse.txt"
)

for dataset in "${DATASETS[@]}"; do
    if [ ! -f "$dataset" ]; then
        echo -e "${RED}✗ Dataset not found: $dataset${NC}"
        exit 1
    fi
    
    # Count stories
    story_count=$(wc -l < "$dataset")
    echo -e "${GREEN}✓ $dataset (${story_count} stories)${NC}"
done

# Check prompt file
if [ ! -f "prompts/prompt.txt" ]; then
    echo -e "${RED}✗ Prompt template not found: prompts/prompt.txt${NC}"
    exit 1
fi
echo -e "${GREEN}✓ prompts/prompt.txt${NC}"

###############################################################################
# Step 4: Create Output Directory
###############################################################################

echo ""
echo -e "${YELLOW}[4/6] Preparing output directory...${NC}"

mkdir -p data/processed
echo -e "${GREEN}✓ Output directory ready${NC}"

###############################################################################
# Step 5: Run Experiment
###############################################################################

echo ""
echo -e "${YELLOW}[5/6] Running experiment...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}This will evaluate 3 datasets with 3 models (9 API calls total)${NC}"
echo -e "${YELLOW}Estimated time: 2-5 minutes${NC}"
echo -e "${YELLOW}Estimated cost: ~$0.50-$2.00 (depending on models)${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Experiment cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Starting evaluation...${NC}"
echo ""

# Backup existing results if present
if [ -f "data/processed/data_processed.xlsx" ]; then
    BACKUP_FILE="data/processed/data_processed_backup_$(date +%Y%m%d_%H%M%S).xlsx"
    cp data/processed/data_processed.xlsx "$BACKUP_FILE"
    echo -e "${YELLOW}⚠ Backed up existing results to: $BACKUP_FILE${NC}"
    echo ""
fi

# Run the evaluation script
START_TIME=$(date +%s)

python3 src/model_evaluation/proces_userstories.py

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${GREEN}✓ Experiment completed in ${DURATION} seconds${NC}"

###############################################################################
# Step 6: Verify Results
###############################################################################

echo ""
echo -e "${YELLOW}[6/6] Verifying results...${NC}"

if [ ! -f "data/processed/data_processed.xlsx" ]; then
    echo -e "${RED}✗ Output file not created${NC}"
    exit 1
fi

FILE_SIZE=$(du -h data/processed/data_processed.xlsx | cut -f1)
echo -e "${GREEN}✓ Results saved: data/processed/data_processed.xlsx (${FILE_SIZE})${NC}"

# Count rows in Excel (requires Python)
ROW_COUNT=$(python3 -c "import pandas as pd; df = pd.read_excel('data/processed/data_processed.xlsx'); print(len(df))")
echo -e "${GREEN}✓ Total evaluations: ${ROW_COUNT}${NC}"

###############################################################################
# Summary
###############################################################################

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Experiment Complete!                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Results:${NC}"
echo -e "  📊 Output file: ${BLUE}data/processed/data_processed.xlsx${NC}"
echo -e "  📈 Evaluations: ${BLUE}${ROW_COUNT}${NC}"
echo -e "  ⏱️  Duration: ${BLUE}${DURATION}s${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Open data/processed/data_processed.xlsx to view results"
echo -e "  2. Analyze defect distributions across models"
echo -e "  3. Generate visualizations and statistics"
echo ""
echo -e "${GREEN}For analysis help, see: DATA_README.md${NC}"
echo ""

# Deactivate virtual environment
deactivate

exit 0
