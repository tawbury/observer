# Meta Validator

## Purpose
Standardized meta section format validation for all document types

## Validation Rules

### 1. Required Field Verification
#### Standard Meta Field List
- Project Name
- File Name
- Document ID
- Status
- Created Date
- Last Updated
- Author
- Reviewer
- Parent Document
- Related Reference
- Version

#### Verification Conditions
- All required fields must exist
- Field values must not be empty
- Meta section format must be correct
- Version field must be standard format (1.0, 1.1, 2.0, etc.)
- Date fields must be in YYYY-MM-DD HH:MM format
- Reviewer field must be populated for L2 validation

### 2. Field Format Validation
#### Date Format Validation
- Created Date: YYYY-MM-DD HH:MM format required
- Last Updated: YYYY-MM-DD HH:MM format required
- Date consistency: Last Updated >= Created Date

#### Version Format Validation
- Standard semantic versioning: X.Y.Z
- Major version: Breaking changes
- Minor version: New features
- Patch version: Bug fixes

#### Document ID Format Validation
- Consistent ID format per document type
- Unique identifier requirement
- Category-based prefix validation

### 3. Field Value Validation
#### Author Field
- Must contain valid agent name
- Author must be Junior level agent
- Format consistency check

#### Reviewer Field
- Must contain valid Senior agent designation
- Reviewer must be Senior level agent
- Auto-population for L2 validation

#### Status Field
- Valid status values: Draft, Active, Completed, Deprecated
- Status workflow consistency
- Status change tracking

### 4. Relationship Validation
#### Parent Document Reference
- Valid parent document reference
- Parent document existence check
- Hierarchical relationship validation

#### Related Reference
- Valid reference format
- Reference existence verification
- Cross-reference consistency

## Integration
- Connect to all document validators
- Standardize meta validation across document types
- Support automated meta field population
- Enable L1/L2 role-based validation

## Usage
- Applied by all document validators
- Used for template compliance checking
- Supports automated document generation
- Enables quality assurance automation
