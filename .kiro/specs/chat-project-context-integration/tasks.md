# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Fault Condition** - Project Context Integration
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases: chat_mode="project" with valid project_id
  - Test that when chat_mode="project" and project_id is not null/empty, the LLM prompt includes project metadata (name, source_type, file_count, line_count, status)
  - Generate test cases with various project_id values and verify project context is present in the prompt
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., "answer() with project_id='test-project' does not include project name in prompt")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Project Mode Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs:
    - chat_mode="freeform" with any project_id (should use FREEFORM_PROMPT, no RAG)
    - chat_mode="project" with project_id=None (should use RAG but no project context)
    - chat_mode="project" with project_id="" (should use RAG but no project context)
  - Write property-based tests capturing observed behavior patterns:
    - For all freeform mode requests, verify FREEFORM_PROMPT is used and no RAG retrieval occurs
    - For all project mode requests without project_id, verify RAG works but no project metadata is added
    - For all requests, verify history management, confidence calculation, and citation extraction remain unchanged
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3. Fix for missing project context in chat

  - [x] 3.1 Add ProjectService dependency to QAService
    - Modify `QAService.__init__()` to accept `db: Session` parameter
    - Initialize `ProjectService` instance in constructor
    - Update all QAService instantiation sites to pass database session
    - _Bug_Condition: isBugCondition(input) where input.chat_mode="project" AND input.project_id IS NOT NULL AND input.project_id != ""_
    - _Expected_Behavior: Project metadata SHALL be retrieved and included in LLM prompt_
    - _Preservation: Freeform mode, no project_id requests, RAG retrieval, history management must remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Implement project metadata retrieval in answer()
    - Add logic at start of `answer()` to check if chat_mode="project" and project_id is not null/empty
    - If condition met, call `ProjectService.get_project(project_id)` to fetch project metadata
    - Handle case where project not found (log warning, continue without project context)
    - Format project metadata into context string (name, source_type, file_count, line_count, status)
    - Pass project context to `_build_context()` or prepend to existing context
    - _Bug_Condition: isBugCondition(input) where input.chat_mode="project" AND input.project_id IS NOT NULL AND input.project_id != ""_
    - _Expected_Behavior: expectedBehavior(result) - LLM prompt includes project metadata_
    - _Preservation: Preservation Requirements from design - freeform mode and no project_id cases unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_

  - [x] 3.3 Implement project metadata retrieval in answer_stream()
    - Add identical logic to `answer_stream()` method
    - Ensure project metadata retrieval happens before streaming starts
    - Maintain consistency with `answer()` implementation
    - _Bug_Condition: isBugCondition(input) where input.chat_mode="project" AND input.project_id IS NOT NULL AND input.project_id != ""_
    - _Expected_Behavior: expectedBehavior(result) - LLM prompt includes project metadata in streaming mode_
    - _Preservation: Preservation Requirements from design - streaming behavior for other modes unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_

  - [-] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Project Context Integration
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Project Mode Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `cd backend && pytest`
  - Verify type checking: `cd backend && mypy .`
  - Verify formatting: `cd backend && black . && isort .`
  - Ensure all tests pass, ask the user if questions arise
