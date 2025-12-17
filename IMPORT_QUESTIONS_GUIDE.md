# Import Questions Management Command

This guide explains how to use the `import_questions` Django management command to import test questions from a JSON file.

## Command Usage

### Basic Usage (Import all questions)
```bash
python manage.py import_questions
```

### Import Specific State
```bash
python manage.py import_questions --state "California"
```

### Specify Custom JSON File
```bash
python manage.py import_questions --file path/to/questions.json
```

### Combined Options
```bash
python manage.py import_questions --state "California" --file questions.json
```

## How It Works

1. **Test Creation**: Tests are created based on the `category` field in the JSON
   - Categories like `lane_markings`, `parking`, `signals` become test titles
   - Same category across different states = same test (grouped together)
   - Each test is associated with the state(s) it belongs to

2. **Question Creation**: Questions are created for each test
   - Questions are checked for duplicates (by text) before creation
   - Each question gets a sequential order number within its test
   - Video and image links are noted in the output (manual download may be needed)

3. **Answer Creation**: Answer options are created for each question
   - The `correct` index from JSON determines which answer is correct
   - Answers maintain their order from the JSON file

4. **Duplicate Handling**: 
   - If a test already exists, it's reused and the state is added to it
   - If a question (same text) already exists in a test, it's skipped
   - Statistics are provided at the end showing what was created/skipped

## JSON File Structure

The command expects a JSON file with the following structure:

```json
{
   "state": "California",
   "questions": [
      {
         "id": 16,
         "question": "You may cross a solid white line when:",
         "video_link": null,
         "image_link": null,
         "answers": [
            "Passing another vehicle",
            "Traffic is light",
            "It is safe to avoid an obstacle",
            "Never under any condition"
         ],
         "correct": 2,
         "category": "lane_markings"
      }
   ]
}
```

### Field Descriptions:
- `state`: The state name (must match or will be created)
- `questions`: Array of question objects
- `id`: Question ID (for reference, not used in import)
- `question`: The question text
- `video_link`: URL to video (optional, noted in output)
- `image_link`: URL to image (optional, noted in output)
- `answers`: Array of answer text options
- `correct`: Index of the correct answer (0-based)
- `category`: Test category/name

## Example Output

```
Using existing state: California
Using existing test: Lane Markings
  Created question #1: You may cross a solid white line when:...
    Created 4 answers (correct: It is safe to avoid an obstacle)
  Skipping duplicate question: What should you do when approaching a yield sign?...

============================================================
Import completed!
============================================================
State: California
Tests created: 3
Tests updated (state added): 2
Questions created: 15
Questions skipped (duplicates): 5
Answers created: 60
============================================================
```

## Notes

- **Video/Image Links**: The command notes when questions have video or image links, but doesn't download them automatically. You may need to handle media files separately.
- **State Management**: States are automatically created if they don't exist
- **Test Settings**: Tests are created with default settings (80% passing, shuffled questions/answers)
- **Transaction Safety**: Each category is processed in a transaction for data integrity
