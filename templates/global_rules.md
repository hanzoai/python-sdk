# Hanzo AI System Rules

## Core Principles

### Code Quality Standards
- **Error Handling**: Always implement proper error handling with meaningful messages
- **Type Safety**: Use type hints in Python, TypeScript definitions for JavaScript
- **Testing**: Maintain >80% test coverage, write tests before implementation
- **Documentation**: Document complex algorithms and architectural decisions
- **Performance**: Profile before optimizing, prefer readability over premature optimization

### Security Guidelines
- **Data Protection**: Never log sensitive data (passwords, tokens, PII)
- **Environment Variables**: Use environment variables for all secrets and configuration
- **Input Validation**: Validate and sanitize all user inputs
- **Least Privilege**: Follow principle of least privilege for permissions
- **Dependencies**: Keep dependencies updated, audit for vulnerabilities

### Communication Style
- **Clarity**: Be concise but thorough in explanations
- **Context**: Provide reasoning for complex technical decisions
- **Questions**: Ask clarifying questions when requirements are ambiguous
- **Examples**: Include code examples when explaining concepts
- **Feedback**: Request feedback on uncertain implementations

## Architecture Patterns

### Database Design
- **SQLite First**: Use SQLite for embedded databases, PostgreSQL for distributed systems
- **Migrations**: Always use database migrations for schema changes
- **Indexing**: Create appropriate indexes for query performance
- **Normalization**: Normalize to 3NF unless denormalization is justified for performance

### API Design
- **RESTful**: Follow REST principles for HTTP APIs
- **Versioning**: Version APIs from day one (v1, v2, etc.)
- **Error Responses**: Consistent error response format with status codes
- **Pagination**: Implement pagination for list endpoints
- **Rate Limiting**: Implement rate limiting for public APIs

### Memory Management
- **Hybrid Storage**: Use markdown files for human-readable rules, SQLite for structured data
- **Full-Text Search**: Implement FTS5 for searchable content
- **Vector Search**: Use sqlite-vec for semantic similarity when available
- **Scoping**: Support global and project-specific memory contexts

## Development Workflow

### Git Practices
- **Commits**: Write descriptive commit messages following conventional commits
- **Branches**: Use feature branches, never commit directly to main
- **Reviews**: Require code reviews for all changes
- **CI/CD**: Automated testing and deployment pipelines

### Code Organization
- **Modules**: Keep modules focused and cohesive
- **Dependencies**: Minimize external dependencies, prefer standard libraries
- **Configuration**: Centralize configuration management
- **Logging**: Structured logging with appropriate levels

## AI Assistant Guidelines

### Code Generation
- **Completeness**: Generate complete, runnable code examples
- **Best Practices**: Follow established patterns and conventions
- **Error Handling**: Include appropriate error handling in generated code
- **Comments**: Add comments for complex logic or business rules

### Code Review
- **Constructive**: Provide constructive feedback with specific suggestions
- **Standards**: Check adherence to coding standards and patterns
- **Security**: Review for potential security vulnerabilities
- **Performance**: Identify potential performance issues

### Problem Solving
- **Analysis**: Break down complex problems into smaller components
- **Research**: Reference relevant documentation and examples
- **Testing**: Suggest appropriate testing strategies
- **Alternatives**: Consider multiple approaches and trade-offs

---

*Last updated: 2025-01-12*
*Version: 1.0*