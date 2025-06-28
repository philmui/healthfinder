# Chat API Test Suite Documentation

## Overview

This directory contains comprehensive test coverage for the HealthFinder agentic chat completions API. The test suite ensures the reliability, security, and performance of the multi-agent workflow system.

## Test Structure

### File: `test_chat.py`

**Main Test Class**: `TestChatCompletionsAPI`

**Total Tests**: 19 comprehensive test cases

## Test Categories

### 1. Basic Functionality Tests

- **`test_chat_completions_success`**: Validates successful chat completion requests with proper response format and agent coordination
- **`test_chat_completions_minimal_request`**: Tests basic request handling with minimal required parameters

### 2. Validation and Error Handling Tests

- **`test_chat_completions_validation_error`**: Verifies request validation with missing required fields
- **`test_chat_completions_empty_messages`**: Tests handling of empty messages array
- **`test_chat_completions_invalid_parameters`**: Validates parameter range and type checking
- **`test_chat_completions_streaming_not_implemented`**: Confirms proper handling of unimplemented streaming
- **`test_chat_completions_workflow_error_handling`**: Tests graceful error handling during workflow processing

### 3. Configuration Management Tests

- **`test_chat_status_endpoint`**: Validates system status reporting and capability information
- **`test_chat_config_update`**: Tests dynamic configuration updates
- **`test_chat_config_invalid_keys`**: Verifies filtering of invalid configuration keys
- **`test_chat_metrics_endpoint`**: Tests performance metrics collection and reporting

### 4. Integration and Domain-Specific Tests

- **`test_healthcare_query_integration`**: Validates healthcare-specific query processing
- **`test_general_query_integration`**: Tests general (non-healthcare) domain handling

### 5. Performance and Load Tests

- **`test_chat_completions_performance_metadata`**: Verifies performance information inclusion
- **`test_concurrent_requests_handling`**: Tests concurrent request processing

### 6. Edge Cases and Boundary Tests

- **`test_very_long_message_handling`**: Tests handling of very long input messages
- **`test_special_characters_handling`**: Validates Unicode and special character support

### 7. Security and Robustness Tests

- **`test_malformed_json_handling`**: Tests JSON parsing error handling
- **`test_injection_attempt_handling`**: Validates security against prompt injection attempts

## Test Fixtures

### Core Fixtures

- **`client`**: FastAPI test client
- **`sample_chat_request`**: Standard chat completion request for testing
- **`mock_research_result`**: Mock research agent result
- **`mock_web_search_result`**: Mock web search agent result
- **`mock_synthesis_result`**: Mock synthesis agent result
- **`mock_workflow_response`**: Comprehensive mock workflow response

## Mocking Strategy

All tests use comprehensive mocking to avoid external dependencies:

- **Workflow Mocking**: Tests mock the `ConciergeWorkflow` class to avoid hitting real agents
- **Global Instance Reset**: Tests reset the global workflow instance to ensure clean state
- **API Isolation**: External API calls (DuckDuckGo search) are mocked to prevent rate limiting
- **Consistent Responses**: Mocked responses follow the exact Pydantic model structure

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.api`: API endpoint tests
- `@pytest.mark.chat`: Chat functionality tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.performance`: Performance-related tests

## Key Testing Principles

### 1. Complete Isolation
- No external API calls during testing
- Mocked dependencies prevent network timeouts
- Consistent, predictable test results

### 2. Comprehensive Coverage
- All API endpoints tested
- Multiple error scenarios covered
- Edge cases and boundary conditions validated

### 3. Realistic Data
- Mock responses match production data structures
- Proper Pydantic model validation
- Real-world request/response patterns

### 4. Security Focus
- Input validation testing
- Prompt injection protection
- Malformed input handling

### 5. Performance Awareness
- Response time validation
- Concurrent request handling
- Resource usage monitoring

## Running Tests

### Run All Chat API Tests
```bash
pytest tests/api/test_chat.py -v
```

### Run Specific Test Categories
```bash
# Basic functionality tests
pytest tests/api/test_chat.py -m "api and chat" -v

# Integration tests
pytest tests/api/test_chat.py -m "integration" -v

# Performance tests
pytest tests/api/test_chat.py -m "performance" -v
```

### Run Single Test
```bash
pytest tests/api/test_chat.py::TestChatCompletionsAPI::test_chat_completions_success -v
```

## Test Output

### Success Indicators
- All 19 tests pass consistently
- No external API calls made
- Fast execution (< 1 second typically)
- Proper mocking validation

### Expected Warnings
- Pydantic deprecation warnings (expected, not errors)
- DateTime UTC warnings (expected, not errors)

## Maintenance

### Adding New Tests
1. Follow the existing mocking pattern
2. Use appropriate pytest markers
3. Include comprehensive docstrings
4. Test both success and failure scenarios

### Updating Fixtures
1. Ensure mock data matches Pydantic models
2. Update all related test expectations
3. Verify no external dependencies introduced

### Debugging Test Failures
1. Check mocking configuration
2. Verify Pydantic model compatibility
3. Ensure proper test isolation
4. Review logs for external API calls

## Integration with CI/CD

These tests are designed for:
- Automated CI/CD pipelines
- Pre-commit hooks
- Development environment validation
- Production deployment verification

The comprehensive mocking ensures reliable test execution in any environment without external dependencies or rate limiting concerns. 