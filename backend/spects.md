### AI Service API Specification

**Base URL:** `http://localhost:8000/api/v1`

---

### 1. Career Path Detection Flow

**Endpoint Specification**

| Method | Path | Description | Access | Workflow Steps |
| --- | --- | --- | --- | --- |
| **POST** | `/analyse/profile` | Ingests user profile sources to determine viable career paths and skill gaps. | Internal (Web App) | 1. **Data Ingestion:** Uses resume text plus optional GitHub/LinkedIn URLs.<br>2. **LLMAnalysis:** Generates a structured profile summary and role recommendations.<br>3. **Persist:** Stores analysis result in MongoDB.<br>4. **Return:** Returns structured JSON with profile and recommendations. |

**Data Transfer Objects (DTOs)**

**Request DTO (`ProfileAnalysisRequest`)**

```json
{
  "user_id": "uuid-string",
  "resume_text": "Extracted raw text content from the PDF...",
  "github_url": "<https://github.com/jdoe>",
  "linkedin_url": "<https://linkedin.com/in/jdoe>",
  "preferences": {
    "interested_roles": ["Backend", "DevOps"],
    "ignored_roles": ["Frontend"]
  }
}
```

**Response DTO (`ProfileAnalysisResponse`)**

```json
{
  "profile": {
    "profile_summary": "Strong foundation in Java ecosystem...",
    "hard_skills": ["Java", "Spring Boot", "Docker"],
    "soft_skills": ["Communication", "Leadership"]
  },
  "recommendations": [
    {
      "role": "Backend Engineer",
      "match_percentage": 85,
      "missing_skills": ["Kubernetes", "GraphQL"],
      "learning_path": [
        "Learn basic K8s pods",
        "Understand GraphQL Schemas"
      ]
    },
    {
      "role": "DevOps Engineer",
      "match_percentage": 60,
      "missing_skills": ["Terraform", "Ansible", "Jenkins"],
      "learning_path": ["IaC Fundamentals", "CI/CD Pipelines"]
    }
  ]
}
```

---

### 2. Interview Simulation Flow

**Endpoint Specification**

| Method | Path | Description | Access | Workflow Steps |
| --- | --- | --- | --- | --- |
| **POST** | `/interview/generate` | Generates the next dynamic interview question based on context. | Internal (Web App) | 1. **Context Build:** `ContextBuilderNode` loads previous turns (`history`) and `role` definition.<br>2. **LLM Generation:** `QuestionGeneratorNode` creates a question that hasn't been asked yet, tailored to the current difficulty.<br>3. **Return:** Returns the question text and metadata (ID, difficulty). |
| **POST** | `/interview/evaluate` | Grades the user's verbal/textual response. | Internal (Web App) | 1. **Ingestion:** Receives the specific question asked and the user's raw answer.<br>2. **LLM Evaluation:** `ResponseEvaluatorNode` compares answer against the question's hidden rubric.<br>3. **Scoring:** `ScoreCalculationNode` standardizes the result to a 0-100 scale.<br>4. **Return:** Feedback, correct answer explanation, and score. |

**Data Transfer Objects (DTOs)**

**Request DTO (`QuestionGenerationRequest`)**

```json
{
  "role_target": "Senior Java Developer",
  "difficulty_level": "Medium",
  "topic_focus": "Microservices",
  "conversation_history": [
    {"speaker": "AI", "text": "What is DI?"},
    {"speaker": "User", "text": "Dependency Injection is..."}
  ]
}
```

**Response DTO (`QuestionGenerationResponse`)**

```json
{
  "question_id": "q-12345",
  "question_text": "How do you handle distributed transactions in a microservices architecture?",
  "hint": "Consider patterns like Saga or Two-Phase Commit.",
  "difficulty": "Hard",
  "expected_keywords": ["Saga Pattern", "Two-Phase Commit", "Eventual Consistency"]
}
```

**Request DTO (`AnswerEvaluationRequest`)**

```json
{
  "question_text": "How do you handle distributed transactions...?",
  "user_answer": "I would use the Saga pattern with choreography.",
  "role_context": "Senior Java Developer"
}
```

**Response DTO (`AnswerEvaluationResponse`)**

```json
{
  "score": 90,
  "is_passing": true,
  "feedback": "Excellent mention of the Saga pattern. You could have also mentioned Two-Phase Commit as a contrast.",
  "sentiment": "Positive"
}
```

---

### 3. Project Simulation Flow

**Endpoint Specification**

| Method | Path | Description | Access | Workflow Steps |
| --- | --- | --- | --- | --- |
| **POST** | `/project/generate` | Planned endpoint. The service implementation exists, but route wiring is not yet added in `app/main.py`. | Internal (Web App) | 1. **Initialization:** Receives target role, experience level, and preferred stack.<br>2. **LLM Generation:** Generates one project with phases and tasks.<br>3. **Normalization:** Normalizes `task_number`/`step_order` variants into API model fields.<br>4. **Return:** Structured project JSON object. |
| **POST** | `/project/evaluate` | Planned endpoint. Request/response models are defined, but service/route implementation is pending. | Internal (Web App) | 1. **Ingestion:** Receives phase/task scope plus user submission.<br>2. **Evaluation:** Validates submission and computes score.<br>3. **Return:** Pass/fail plus suggestions. |

**Data Transfer Objects (DTOs)**

**Request DTO (`ProjectGenerationRequest`)**

```json
{
    "target_role": "Full Stack Developer",
    "experience_level": "Junior",
    "preferred_tech_stack": ["React", "Spring Boot", "PostgreSQL"],
    "previous_phase_completion": []
}
```

**Response DTO (`ProjectGenerationResponse`)**

```json
{
    "project_id": "proj-999",
    "title": "E-Commerce Inventory System",
  "description": "Build a full-stack e-commerce inventory management system.",
  "specifications": "Build a full-stack e-commerce inventory management system allowing CRUD operations on products, categories, and stock levels....",
    "phases": [
        {
            "title": "Backend Development",
            "description": "Set up Spring Boot application with PostgreSQL integration.",
            "tasks": [
               {
                   "task_id": "t-1",
           "task_number": 1,
                   "submission_type": "CODE_SNIPPET",
                   "title": "Database Setup",
                   "description": "Initialize a PostgreSQL container and configure Spring Data JPA.",
                   "acceptance_criteria": "Application starts without connection errors."
               },
               {
                   "task_id": "t-2",
           "task_number": 2,
                   "submission_type": "CODE_SNIPPET",
                   "title": "Product Entity",
                   "description": "Create the Product entity with ID, Name, and Price fields.",
                   "acceptance_criteria": "Entity definition is correct and can be extended."
               }
            ]
        }
    ]
}
```

**Request DTO (`TaskEvaluationRequest`)**

```json
{
  "user_id": "uuid-string",
  "project_id": "proj-999",
  "phase_number": 1,
  "task_number": 2,
  "user_submission": "@Entity public class Product { ... }",
  "submission_type": "CODE_SNIPPET"
}
```

**Response DTO (`TaskEvaluationResponse`)**

```json
{
  "project_id": "proj-999",
  "phase_number": 1,
  "task_number": 2,
  "passed": true,
  "score": 100,
  "feedback": "Correct use of @Entity and @Id annotations.",
  "suggestions": []
}
```

### Type Specifications

```json
{
  "SHARED_ENUMS": {
    "ExperienceLevel": {
      "type": "String",
      "values": ["ENTRY_LEVEL", "JUNIOR", "MID_LEVEL", "SENIOR"],
      "description": "Standardized seniority levels for profile analysis and project difficulty."
    },
    "SubmissionType": {
      "type": "String",
      "values": ["CODE_SNIPPET", "GITHUB_LINK", "TEXT_ANSWER"],
      "description": "Determines how the frontend renders the input field for a task."
    },
    "Sentiment": {
      "type": "String",
      "values": ["POSITIVE", "NEUTRAL", "NEGATIVE"],
      "description": "Used for UI feedback coloring (Green, Gray, Red)."
    },
    "Difficulty": {
      "type": "String",
      "values": ["EASY", "MEDIUM", "HARD", "EXPERT"],
      "description": "Specific difficulty for interview questions."
    }
  },
  "DTO_SCHEMAS": {
    "CAREER_FLOW": {
      "ProfileAnalysisRequest": {
        "user_id": "UUID (String)",
        "resume_text": "String (Raw Text)",
        "github_url": "String (URL)",
        "linkedin_url": "String (URL)",
        "preferences": {
          "interested_roles": "List<String>",
          "ignored_roles": "List<String>"
        }
      },
      "ProfileAnalysisResponse": {
        "profile": {
          "profile_summary": "String",
          "hard_skills": "List<String>",
          "soft_skills": "List<String>"
        },
        "recommendations": [
          {
            "role": "String",
            "match_percentage": "Integer (0-100)",
            "missing_skills": "List<String>",
            "learning_path": "List<String>"
          }
        ]
      }
    },
    "INTERVIEW_FLOW": {
      "QuestionGenerationRequest": {
        "role_target": "String",
        "difficulty_level": "Difficulty (Enum)",
        "topic_focus": "String (Optional)",
        "conversation_history": [
          {
            "speaker": "String (AI|User)",
            "text": "String"
          }
        ]
      },
      "QuestionGenerationResponse": {
        "question_id": "UUID (String)",
        "question_text": "String",
        "difficulty": "Difficulty (Enum)",
        "hint": "String",
        "expected_keywords": "List<String>"
      },
      "AnswerEvaluationRequest": {
        "question_text": "String",
        "user_answer": "String",
        "role_context": "String"
      },
      "AnswerEvaluationResponse": {
        "score": "Integer (0-100)",
        "is_passing": "Boolean",
        "feedback": "String",
        "sentiment": "Sentiment (Enum)"
      }
    },
    "PROJECT_FLOW": {
      "ProjectGenerationRequest": {
        "target_role": "String",
        "experience_level": "ExperienceLevel (Enum)",
        "preferred_tech_stack": "List<String>",
        "previous_phase_completion": "List<Object> (Optional)"
      },
      "ProjectGenerationResponse": {
        "project_id": "UUID (String)",
        "title": "String",
        "description": "String",
        "specifications": "String",
        "phases": [
          {
            "title": "String",
            "description": "String",
            "tasks": [
              {
                "task_id": "UUID (String)",
                "task_number": "Integer",
                "submission_type": "SubmissionType (Enum)",
                "title": "String",
                "description": "String",
                "acceptance_criteria": "String"
              }
            ]
          }
        ]
      },
      "TaskEvaluationRequest": {
        "user_id": "UUID (String)",
        "project_id": "UUID (String)",
        "phase_number": "Integer",
        "task_number": "Integer",
        "user_submission": "String",
        "submission_type": "SubmissionType (Enum)"
      },
      "TaskEvaluationResponse": {
        "project_id": "UUID (String)",
        "phase_number": "Integer",
        "task_number": "Integer",
        "passed": "Boolean",
        "score": "Integer (0-100)",
        "feedback": "String",
        "suggestions": "List<String>"
      }
    }
  }
}
```

![image.png](attachment:08f1cade-41a5-4a6e-8d81-1691d71f3a23:image.png)