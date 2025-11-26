# Data Documentation

This document provides detailed information about the datasets, data structures, and quality framework used in this research.

## 📊 Table of Contents

- [Overview](#overview)
- [Data Organization](#data-organization)
- [Raw Data](#raw-data)
- [Processed Data](#processed-data)
- [QUS Framework](#qus-framework)
- [Prompt Template](#prompt-template)
- [Data Quality](#data-quality)
- [Usage Guidelines](#usage-guidelines)
- [Data Attribution](#data-attribution)

## 🎯 Overview

This repository contains:

- **3 user story datasets** from open-source projects
- **1 prompt template** implementing the QUS Framework
- **1 processed dataset** with LLM evaluation results

**Total User Stories**: 168  
**Total Models Evaluated**: 3 (GPT-5, GPT-5-mini, GPT-4)  
**Total Evaluations**: 9 (3 datasets × 3 models)

## 📁 Data Organization

```
data/
├── raw/                          # Original user story datasets
│   ├── g13-planningpoker.txt    # 53 stories, 7.6 KB
│   ├── g21-badcamp.txt          # 68 stories, 10.3 KB
│   └── g28-zooniverse.txt       # 47 stories, 6.2 KB
└── processed/                    # Analysis results
    └── data_processed.xlsx       # Model outputs, 4.9 KB

prompts/
└── prompt.txt                    # QUS Framework template, 3.9 KB
```

## 📄 Raw Data

### File Format

- **Format**: Plain text (`.txt`)
- **Encoding**: UTF-8
- **Structure**: One user story per line
- **Template**: "As a [role], I want [action], so that [benefit]"

### Dataset Details

#### g13-planningpoker.txt

- **Project**: Planning Poker estimation tool
- **Stories**: 53
- **Primary Role**: Moderator (42 stories), Estimator (11 stories)
- **Domain**: Agile estimation, game management
- **Characteristics**:
  - Well-structured stories following standard template
  - Focus on game mechanics and user management
  - Examples of CRUD operations, import/export features

**Sample Stories**:

```
As a moderator, I want to create a new game by entering a name and an optional description, so that I can start inviting estimators.
As a moderator, I want to invite estimators by giving them a URL where they can access the game, so that we can start the game.
As an estimator, I want to join a game by entering my name on the page I received the URL for, so that I can participate.
```

#### g21-badcamp.txt

- **Project**: BADCamp conference management system
- **Stories**: 68
- **Primary Roles**: Attendee, Organizer, Speaker, Sponsor
- **Domain**: Event management, conference organization
- **Characteristics**:
  - Multiple stakeholder perspectives
  - Complex workflows (registration, scheduling, payments)
  - Integration with external systems

**Sample Stories**:

```
As an attendee, I want to register for the conference online, so that I can secure my spot.
As an organizer, I want to manage speaker submissions, so that I can create the conference schedule.
As a sponsor, I want to display my company logo on the website, so that I can increase brand visibility.
```

#### g28-zooniverse.txt

- **Project**: Zooniverse citizen science platform
- **Stories**: 47
- **Primary Roles**: Volunteer, Researcher, Administrator
- **Domain**: Citizen science, data classification
- **Characteristics**:
  - Scientific workflow support
  - Gamification elements
  - Data validation and quality control

**Sample Stories**:

```
As a volunteer, I want to classify images, so that I can contribute to scientific research.
As a researcher, I want to create a new project, so that I can collect data from volunteers.
As an administrator, I want to monitor project progress, so that I can ensure data quality.
```

### Data Statistics

| Dataset           | Stories | Avg Length (chars) | Roles | Unique Verbs |
| ----------------- | ------- | ------------------ | ----- | ------------ |
| g13-planningpoker | 53      | 143                | 2     | 28           |
| g21-badcamp       | 68      | 151                | 4     | 35           |
| g28-zooniverse    | 47      | 133                | 3     | 24           |
| **Total**         | **168** | **143**            | **9** | **87**       |

## 📊 Processed Data

### File: data_processed.xlsx

**Format**: Microsoft Excel (.xlsx)  
**Sheets**: 1 (default)  
**Rows**: 9 (one per model-dataset combination)  
**Columns**: 5

### Column Descriptions

| Column       | Type   | Description                                                          | Example                                            |
| ------------ | ------ | -------------------------------------------------------------------- | -------------------------------------------------- |
| `user_story` | Text   | Complete text of all user stories in the dataset (newline-separated) | "As a moderator, I want to...\nAs an estimator..." |
| `model`      | String | OpenAI model identifier                                              | "gpt-5", "gpt-5-mini", "gpt-4"                     |
| `prompt`     | Text   | QUS Framework prompt template used                                   | "System: You will serve as a quality analyzer..."  |
| `response`   | JSON   | Structured defect analysis from the model                            | `{"defects": [...], "summary": {...}}`             |
| `time`       | Float  | Processing time in seconds                                           | 12.34                                              |

### Response JSON Schema

```json
{
  "defects": [
    {
      "story_id": <integer>,           // Story number (1-indexed)
      "story_text": "<string>",        // Full story text
      "defect_type": "<string>",       // QUS criterion code
      "message": "<string>"            // Specific fix recommendation
    }
  ],
  "summary": {
    "total_stories": <integer>,        // Number of stories analyzed
    "total_defects": <integer>,        // Total defects found
    "defect_types_count": {
      "well_formed.no_role": <integer>,
      "well_formed.no_means": <integer>,
      "atomic.conjunctions": <integer>,
      "minimal.punctuation": <integer>,
      "minimal.brackets": <integer>,
      "unique.identical": <integer>,
      "uniform.uniform": <integer>
    }
  }
}
```

### Example Row

```
user_story: "As a moderator, I want to create a new game...\n[52 more stories]"
model: "gpt-5-mini"
prompt: "System: You will serve as a quality analyzer..."
response: {"defects": [{"story_id": 4, "story_text": "As a moderator...", "defect_type": "atomic.conjunctions", "message": "Split into separate stories"}], "summary": {"total_stories": 53, "total_defects": 8, ...}}
time: 15.67
```

## 🎯 QUS Framework

### Overview

The **Quality User Story (QUS) Framework** is a systematic approach to evaluating agile user stories based on 7 quality criteria across two dimensions.

**Reference**: Lucassen, G., Dalpiaz, F., van der Werf, J. M. E., & Brinkkemper, S. (2016). The use and effectiveness of the Quality User Story framework in practice. _Requirements Engineering_, 21(2), 127-145.

### Criteria Taxonomy

```
QUS Framework
├── Syntactic Quality (Textual Structure)
│   ├── Well-formed
│   │   ├── well_formed.no_role      ❌ Missing role
│   │   └── well_formed.no_means     ❌ Missing action
│   ├── Atomic
│   │   └── atomic.conjunctions      ❌ Multiple features
│   └── Minimal
│       ├── minimal.punctuation      ❌ Excessive notes
│       └── minimal.brackets         ❌ Unnecessary brackets
└── Pragmatic Quality (Agile Practice)
    ├── Unique
    │   └── unique.identical         ❌ Duplicate stories
    └── Uniform
        └── uniform.uniform          ❌ Inconsistent phrasing
```

### Detailed Criteria

#### 1. well_formed.no_role

**Definition**: Every user story must begin with a clear role definition.

**Violation Example**:

```
❌ "I want to upload files to the system."
✅ "As a User, I want to upload files to the system."
```

**Detection Pattern**: Story doesn't start with "As a [role]"

#### 2. well_formed.no_means

**Definition**: Must specify the desired action or functionality.

**Violation Example**:

```
❌ "As a User."
✅ "As a User, I want to view my profile."
```

**Detection Pattern**: Missing "I want to" or equivalent action phrase

#### 3. atomic.conjunctions

**Definition**: Stories should describe single, independent features.

**Violation Example**:

```
❌ "As a Project Manager, I want to create a task, assign it to a member, and set a deadline."
✅ Split into 3 stories:
   - "As a Project Manager, I want to create a task."
   - "As a Project Manager, I want to assign a task to a member."
   - "As a Project Manager, I want to set a deadline for a task."
```

**Detection Pattern**: Presence of "and", "or" connecting multiple actions

#### 4. minimal.punctuation

**Definition**: Avoid supplemental notes in the main story text.

**Violation Example**:

```
❌ "As a User, I want to view reports (PDF, CSV, and Excel). NOTE: Use the new API."
✅ "As a User, I want to view reports in multiple formats."
   [Move technical notes to acceptance criteria]
```

**Detection Pattern**: "NOTE:", "TODO:", "See:", excessive parenthetical content

#### 5. minimal.brackets

**Definition**: Keep the core story clean without bracketed additions.

**Violation Example**:

```
❌ "As a User, I want to save a reimbursement (never grayed out)."
✅ "As a User, I want to save a reimbursement."
   [Move UI details to acceptance criteria]
```

**Detection Pattern**: Excessive use of parentheses or brackets

#### 6. unique.identical

**Definition**: No duplicate stories allowed in the backlog.

**Violation Example**:

```
❌ Story #1: "As a User, I want to upload files."
   Story #7: "As a User, I want to upload files."
✅ Remove duplicate, keep only one
```

**Detection Pattern**: Exact or near-exact text matches

#### 7. uniform.uniform

**Definition**: Standardize phrasing across all stories.

**Violation Example**:

```
❌ Mixed templates:
   - "As a User, I need to login daily."
   - "As a User, I am able to view reports."
   - "As a User, I want to export data."
✅ Consistent template:
   - "As a User, I want to login daily."
   - "As a User, I want to view reports."
   - "As a User, I want to export data."
```

**Detection Pattern**: Inconsistent verb phrases ("I want", "I need", "I am able to")

## 📝 Prompt Template

### File: prompts/prompt.txt

**Purpose**: Instructs LLMs to perform QUS Framework analysis

**Structure**:

1. **System Role**: Define the analyzer role
2. **Framework Definition**: Explain all 7 QUS criteria with examples
3. **Analysis Instructions**: Step-by-step evaluation process
4. **Output Format**: JSON schema specification
5. **Input Placeholder**: Where user stories are inserted

**Key Features**:

- Detailed examples for each defect type
- Emphasis on multiple defects per story
- Structured JSON output for parsing
- Summary statistics requirement

**Template Variables**:

- `{user_stories}`: Replaced with actual story text at runtime

## ✅ Data Quality

### Validation Checks

1. **Format Consistency**: All stories follow "As a [role], I want [action], so that [benefit]" pattern
2. **Encoding**: UTF-8 without BOM
3. **Line Endings**: Unix-style (LF)
4. **No Empty Lines**: Between stories
5. **Trimmed Whitespace**: No leading/trailing spaces

### Known Limitations

1. **Manual Collection**: Stories manually extracted from project repositories
2. **No Ground Truth**: No pre-labeled defects for validation
3. **Context Missing**: Stories evaluated in isolation without project context
4. **Version Control**: Single snapshot, no historical versions

### Data Preprocessing

**None required** - Raw stories used directly without:

- Tokenization
- Normalization
- Filtering
- Augmentation

## 📖 Usage Guidelines

### Loading Raw Data

```python
from pathlib import Path

def load_user_stories(file_path: Path) -> list[str]:
    """Load user stories from text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

# Example
stories = load_user_stories(Path('data/raw/g13-planningpoker.txt'))
print(f"Loaded {len(stories)} stories")
```

### Parsing Processed Data

```python
import pandas as pd
import json

# Load results
df = pd.read_excel('data/processed/data_processed.xlsx')

# Parse JSON responses
for idx, row in df.iterrows():
    response = json.loads(row['response'])
    print(f"Model: {row['model']}")
    print(f"Total defects: {response['summary']['total_defects']}")
    print(f"Defect types: {response['summary']['defect_types_count']}")
```

### Analyzing Defects

```python
def analyze_defect_distribution(df: pd.DataFrame) -> dict:
    """Analyze defect distribution across models."""
    results = {}

    for idx, row in df.iterrows():
        model = row['model']
        response = json.loads(row['response'])

        if model not in results:
            results[model] = {
                'total_defects': 0,
                'defect_types': {}
            }

        results[model]['total_defects'] += response['summary']['total_defects']

        for defect_type, count in response['summary']['defect_types_count'].items():
            if defect_type not in results[model]['defect_types']:
                results[model]['defect_types'][defect_type] = 0
            results[model]['defect_types'][defect_type] += count

    return results
```

## 🏷️ Data Attribution

### User Story Sources

#### g13-planningpoker

- **Source**: Planning Poker open-source project
- **License**: [Specify license]
- **URL**: [Project repository URL]
- **Collection Date**: [Date]
- **Modifications**: None (used as-is)

#### g21-badcamp

- **Source**: BADCamp conference management system
- **License**: [Specify license]
- **URL**: [Project repository URL]
- **Collection Date**: [Date]
- **Modifications**: None (used as-is)

#### g28-zooniverse

- **Source**: Zooniverse citizen science platform
- **License**: [Specify license]
- **URL**: [Project repository URL]
- **Collection Date**: [Date]
- **Modifications**: None (used as-is)

### QUS Framework

- **Authors**: Lucassen, G., Dalpiaz, F., van der Werf, J. M. E., & Brinkkemper, S.
- **Publication**: Requirements Engineering (2016)
- **DOI**: 10.1007/s00766-015-0222-3
- **License**: Academic use

## 🔒 Privacy and Ethics

- **No Personal Data**: User stories contain no personally identifiable information
- **Public Sources**: All datasets from publicly available open-source projects
- **API Usage**: OpenAI API used in compliance with terms of service
- **Reproducibility**: All data and code provided for verification

## 📞 Data Issues

If you find any issues with the data:

1. **Missing Data**: Contact authors for original sources
2. **Format Errors**: Open an issue on GitHub
3. **Attribution Corrections**: Submit a pull request
4. **Additional Datasets**: Suggest via GitHub discussions

---

**Last Updated**: November 2025
**Data Version**: 1.0  
**Contact**: joao.gabriel.salvador.paiva@ccc.ufcg.edu.br
