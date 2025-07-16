# LLM Coding Instructions

## Document Maintenance
- **ALWAYS** follow these guidelines when writing or modifying code for this project
- **BEFORE** implementing new features, check if new considerations should be added to this document
- **WHEN** you identify new relevant considerations, ask the user: "Should I add [specific consideration] to the coding guidelines document?"
- **AFTER** user confirms, update this document with the new guideline

## Project Structure Requirements

### Directory Organization
- **core/**: Contains ALL business logic, data processing, and core functionality
- **ui/**: Contains ONLY presentation layer, user interface components, and display logic
- **NO** business logic should exist in ui/ directory
- **NO** UI elements should exist in core/ directory

### File Organization
- **ONE** class per .py file when the class has substantial functionality
- **EACH** class must have a single, focused responsibility
- **FILE** names should clearly indicate the class/functionality they contain

## Component Design Principles

### UI Components
- **CREATE** specialized, reusable components
- **AVOID** monolithic UI classes
- **SEPARATE** different UI concerns into different components
- **MAKE** components configurable through parameters
- **USE** existing components to avoid duplication of code


### Code Structure
- **KEEP** each file under 200 lines when possible
- **SPLIT** large files into smaller, focused modules
- **USE** clear, descriptive function and variable names

## Error Handling Requirements

### Exception Management
- **WRAP** all potentially failing operations in try-catch blocks
- **PROVIDE** meaningful fallback mechanisms for each exception
- **LOG** errors with sufficient context for debugging
- **NEVER** let exceptions crash the application silently

## Resource Management

### Memory Management
- **USE** context managers (with statements) for file operations
- **IMPLEMENT** cleanup methods for classes that manage resources
- **HANDLE** images with memory-conscious approaches
- **CALL** garbage collection explicitly when processing large datasets
- **CLOSE** files, connections, and other resources promptly

## Configuration Management

### Centralized Configuration
- **STORE** all configuration values in config.py
- **INCLUDE** algorithm weights and preferences in config.py
- **MANAGE** theme and UI constants centrally
- **MAKE** configuration values easily modifiable
- **AVOID** hardcoded values scattered throughout the codebase

## Code Style Requirements

### Comments and Documentation
- **KEEP** comments concise and focused
- **AVOID** verbose descriptions
- **UPDATE** comments when code changes

### General Style
- **MINIMIZE** line count in all files
- **PREFER** multiple small functions over large ones
- **USE** meaningful variable names that reduce need for comments

## Implementation Checklist

Before completing any code task, verify:
- [ ] Business logic is in core/
- [ ] UI code is in ui/
- [ ] Try-catch blocks are implemented
- [ ] Resources are properly managed
- [ ] Configuration is centralized
- [ ] File length is reasonable
- [ ] Comments are concise
- [ ] Code follows single responsibility principle