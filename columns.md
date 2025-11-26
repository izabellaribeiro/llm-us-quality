# Output Data Structure

This document describes the structure of the processed data output file.

## 📊 File: data/processed/data_processed.xlsx

### Overview

- **Format**: Microsoft Excel (.xlsx)
- **Sheets**: 1 (default sheet)
- **Rows**: 9 (3 models × 3 datasets)
- **Columns**: 5

### Column Definitions

#### 1. user_story

- **Type**: Text (long string)
- **Description**: Complete text of all user stories from the dataset
- **Format**: Newline-separated stories
- **Example**:
  ```
  As a moderator, I want to create a new game by entering a name and an optional description, so that I can start inviting estimators.
  As a moderator, I want to invite estimators by giving them a URL where they can access the game, so that we can start the game.
  [... 51 more stories ...]
  ```
- **Length**: Variable (typically 5,000-10,000 characters)
- **Encoding**: UTF-8

#### 2. model

- **Type**: String
- **Description**: OpenAI model identifier used for evaluation
- **Possible Values**:
  - `gpt-4o-mini` - Efficient, cost-effective model
  - `gpt-4` - Standard GPT-4 model
  - `gpt-4o` - Latest optimized GPT-4 variant
- **Example**: `"gpt-4o-mini"`
- **Length**: 8-20 characters

#### 3. prompt

- **Type**: Text (long string)
- **Description**: Complete QUS Framework prompt template sent to the model
- **Content**: Includes:
  - System role definition
  - QUS Framework criteria (all 7)
  - Examples for each defect type
  - Analysis instructions
  - JSON output format specification
- **Example**: `"System: You will serve as a quality analyzer for user stories based on the Quality User Story (QUS) Framework..."`
- **Length**: ~3,900 characters
- **Source**: `prompts/prompt.txt`

#### 4. response

- **Type**: JSON (stored as text)
- **Description**: Structured defect analysis returned by the model
- **Schema**: See [Response JSON Schema](#response-json-schema)
- **Example**:
  ```json
  {
    "defects": [
      {
        "story_id": 4,
        "story_text": "As a moderator, I want to see all items we try to estimate this session, so that I can answer questions about the current story such as \"does this include ___\".",
        "defect_type": "minimal.punctuation",
        "message": "Remove the quoted example from the main story text"
      }
    ],
    "summary": {
      "total_stories": 53,
      "total_defects": 8,
      "defect_types_count": {
        "minimal.punctuation": 5,
        "atomic.conjunctions": 3
      }
    }
  }
  ```
- **Length**: Variable (typically 1,000-5,000 characters)
- **Parsing**: Use `json.loads()` in Python

#### 5. time

- **Type**: Float
- **Description**: Processing time in seconds (wall clock time)
- **Measurement**: From request start to response received
- **Example**: `15.67`
- **Range**: Typically 5-30 seconds
- **Precision**: 2 decimal places
- **Unit**: Seconds

## 📋 Response JSON Schema

### Structure

```json
{
  "defects": [
    {
      "story_id": <integer>,
      "story_text": "<string>",
      "defect_type": "<string>",
      "message": "<string>"
    }
  ],
  "summary": {
    "total_stories": <integer>,
    "total_defects": <integer>,
    "defect_types_count": {
      "<defect_type>": <integer>
    }
  }
}
```

### Field Descriptions

#### defects (array)

Array of defect objects, one per detected quality issue.

**Fields**:

- `story_id` (integer): Story number (1-indexed)

  - Range: 1 to N (where N = total stories in dataset)
  - Example: `4`

- `story_text` (string): Full text of the story with the defect

  - Exact copy from input
  - Example: `"As a moderator, I want to create a task and assign it to a member."`

- `defect_type` (string): QUS Framework criterion code

  - Possible values:
    - `well_formed.no_role`
    - `well_formed.no_means`
    - `atomic.conjunctions`
    - `minimal.punctuation`
    - `minimal.brackets`
    - `unique.identical`
    - `uniform.uniform`
  - Example: `"atomic.conjunctions"`

- `message` (string): Specific fix recommendation
  - Human-readable explanation
  - Actionable guidance
  - Example: `"Split into two separate stories: one for creating a task and one for assigning it."`

#### summary (object)

Aggregate statistics for the entire evaluation.

**Fields**:

- `total_stories` (integer): Number of stories analyzed

  - Should match actual story count in dataset
  - Example: `53`

- `total_defects` (integer): Total number of defects found

  - Sum of all defect instances
  - Can be > total_stories (multiple defects per story)
  - Example: `12`

- `defect_types_count` (object): Breakdown by defect type
  - Keys: QUS criterion codes
  - Values: Count of defects for that type
  - Example:
    ```json
    {
      "well_formed.no_role": 2,
      "atomic.conjunctions": 5,
      "minimal.punctuation": 3,
      "unique.identical": 2
    }
    ```

## 📈 Data Analysis Examples

### Loading Data

```python
import pandas as pd
import json

# Load Excel file
df = pd.read_excel('data/processed/data_processed.xlsx')

# Display basic info
print(f"Total evaluations: {len(df)}")
print(f"Models: {df['model'].unique()}")
print(f"Average processing time: {df['time'].mean():.2f}s")
```

### Parsing JSON Responses

```python
# Parse all responses
for idx, row in df.iterrows():
    response = json.loads(row['response'])

    print(f"\nModel: {row['model']}")
    print(f"Stories: {response['summary']['total_stories']}")
    print(f"Defects: {response['summary']['total_defects']}")
    print(f"Defect rate: {response['summary']['total_defects'] / response['summary']['total_stories']:.2f}")
```

### Analyzing Defect Types

```python
from collections import defaultdict

# Aggregate defects across all evaluations
all_defects = defaultdict(int)

for idx, row in df.iterrows():
    response = json.loads(row['response'])
    for defect_type, count in response['summary']['defect_types_count'].items():
        all_defects[defect_type] += count

# Sort by frequency
sorted_defects = sorted(all_defects.items(), key=lambda x: x[1], reverse=True)

print("\nMost Common Defects:")
for defect_type, count in sorted_defects:
    print(f"  {defect_type}: {count}")
```

### Comparing Models

```python
# Compare defect detection across models
model_stats = {}

for model in df['model'].unique():
    model_df = df[df['model'] == model]

    total_defects = 0
    total_stories = 0

    for idx, row in model_df.iterrows():
        response = json.loads(row['response'])
        total_defects += response['summary']['total_defects']
        total_stories += response['summary']['total_stories']

    model_stats[model] = {
        'total_defects': total_defects,
        'total_stories': total_stories,
        'defect_rate': total_defects / total_stories,
        'avg_time': model_df['time'].mean()
    }

# Display comparison
for model, stats in model_stats.items():
    print(f"\n{model}:")
    print(f"  Defect rate: {stats['defect_rate']:.2f}")
    print(f"  Avg time: {stats['avg_time']:.2f}s")
```

## 🔍 Data Validation

### Checks to Perform

1. **Row Count**: Should be 9 (3 models × 3 datasets)

   ```python
   assert len(df) == 9, "Expected 9 rows"
   ```

2. **Model Coverage**: All 3 models present

   ```python
   expected_models = {'gpt-4o-mini', 'gpt-4', 'gpt-4o'}
   assert set(df['model'].unique()) == expected_models
   ```

3. **JSON Validity**: All responses parse correctly

   ```python
   for idx, row in df.iterrows():
       try:
           json.loads(row['response'])
       except json.JSONDecodeError:
           print(f"Invalid JSON in row {idx}")
   ```

4. **Story Count Consistency**: Summary matches actual count
   ```python
   for idx, row in df.iterrows():
       response = json.loads(row['response'])
       actual_count = len(row['user_story'].split('\n'))
       reported_count = response['summary']['total_stories']
       assert abs(actual_count - reported_count) <= 1  # Allow ±1 for formatting
   ```

## 📊 Expected Data Ranges

| Metric                  | Minimum | Maximum | Typical |
| ----------------------- | ------- | ------- | ------- |
| Rows                    | 9       | 9       | 9       |
| Stories per dataset     | 47      | 68      | 56      |
| Defects per dataset     | 5       | 30      | 12      |
| Defect rate             | 0.1     | 0.5     | 0.21    |
| Processing time (s)     | 5       | 30      | 15      |
| Response length (chars) | 500     | 10000   | 2500    |

## 🔗 Related Documentation

- [DATA_README.md](DATA_README.md) - Complete data documentation
- [README.md](README.md) - Project overview and usage
- [prompts/prompt.txt](prompts/prompt.txt) - QUS Framework prompt template

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Contact**: joao.gabriel.salvador.paiva@ccc.ufcg.edu.br
