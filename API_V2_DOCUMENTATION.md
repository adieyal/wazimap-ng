# Wazimap-NG REST API v2 Documentation

## Overview

The Wazimap-NG REST API v2 provides comprehensive access to datasets, indicators (variables), and background task management. This API follows REST best practices with clean, predictable URLs and proper use of HTTP methods.

## Base URL

```
/api/v2/
```

## Authentication

All API endpoints require authentication using Token Authentication.

### Getting a Token

```http
POST /api/v1/rest-auth/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "key": "your_auth_token_here"
}
```

### Using the Token

Include the token in the Authorization header for all requests:

```http
Authorization: Token your_auth_token_here
```

## Datasets

### List Datasets

Get a list of all datasets you have access to.

```http
GET /api/v2/datasets/
```

Query Parameters:
- `profile`: Filter by profile ID
- `permission_type`: Filter by permission type (`public` or `private`)
- `geography_hierarchy`: Filter by geography hierarchy ID
- `search`: Search by name or profile name
- `ordering`: Order by field (`name`, `created`, `updated`)
- `page`: Page number for pagination
- `page_size`: Number of results per page

Response:
```json
{
  "count": 10,
  "next": "http://example.com/api/v2/datasets/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Population Data",
      "profile": 1,
      "profile_name": "South Africa",
      "geography_hierarchy": 1,
      "geography_hierarchy_name": "South Africa",
      "groups": ["age", "gender"],
      "permission_type": "public",
      "indicator_count": 5,
      "data_count": 1000,
      "created": "2023-01-01T00:00:00Z",
      "updated": "2023-01-02T00:00:00Z"
    }
  ]
}
```

### Create Dataset

Create a new dataset.

```http
POST /api/v2/datasets/
Content-Type: application/json

{
  "name": "Population Data",
  "profile": 1,
  "geography_hierarchy": 1,
  "permission_type": "private"
}
```

Response: 201 Created

### Get Dataset Detail

Get detailed information about a specific dataset.

```http
GET /api/v2/datasets/{id}/
```

Response:
```json
{
  "id": 1,
  "name": "Population Data",
  "profile": 1,
  "profile_name": "South Africa",
  "geography_hierarchy": 1,
  "geography_hierarchy_detail": {
    "id": 1,
    "name": "South Africa",
    "description": "South African geography hierarchy",
    "root_geography_code": "ZA",
    "root_geography_name": "South Africa"
  },
  "groups": ["age", "gender"],
  "permission_type": "public",
  "indicators": [
    {
      "id": 1,
      "name": "Total Population",
      "dataset": 1,
      "dataset_name": "Population Data",
      "groups": ["age", "gender"],
      "subindicator_count": 10
    }
  ],
  "created": "2023-01-01T00:00:00Z",
  "updated": "2023-01-02T00:00:00Z"
}
```

### Update Dataset

Update an existing dataset.

```http
PUT /api/v2/datasets/{id}/
Content-Type: application/json

{
  "name": "Updated Population Data",
  "profile": 1,
  "geography_hierarchy": 1,
  "permission_type": "public"
}
```

Response: 200 OK

### Delete Dataset

Delete a dataset and all associated data (async operation).

```http
DELETE /api/v2/datasets/{id}/
```

Response: 204 No Content

### Upload Data to Dataset

Upload a CSV or Excel file to populate a dataset.

```http
POST /api/v2/datasets/{id}/upload/
Content-Type: multipart/form-data

file: <file data>
overwrite: false
update_indicators: false
```

Response:
```json
{
  "task_id": "abc123-def456",
  "dataset": { ... },
  "message": "Upload started successfully. Use the task_id to track progress."
}
```

### Download CSV Template

Download a CSV template for uploading data to a dataset.

```http
GET /api/v2/datasets/{id}/download_template/
```

Response: CSV file

### Get Dataset Data

Get the raw data rows for a dataset.

```http
GET /api/v2/datasets/{id}/data/
```

Query Parameters:
- `geography`: Filter by geography code
- `page`: Page number for pagination
- `page_size`: Number of results per page

Response:
```json
{
  "count": 1000,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "dataset": 1,
      "geography": 1,
      "geography_code": "ZA",
      "geography_name": "South Africa",
      "data": {
        "age": "0-14",
        "gender": "male",
        "count": 5000000
      }
    }
  ]
}
```

### Make Dataset Public

Change a dataset's permission to public.

```http
POST /api/v2/datasets/{id}/make_public/
```

Response:
```json
{
  "message": "Dataset \"Population Data\" is now public.",
  "dataset": { ... }
}
```

### Make Dataset Private

Change a dataset's permission to private.

```http
POST /api/v2/datasets/{id}/make_private/
```

## Indicators (Variables)

### List Indicators

Get a list of all indicators you have access to.

```http
GET /api/v2/indicators/
```

Query Parameters:
- `dataset`: Filter by dataset ID
- `universe`: Filter by universe ID
- `search`: Search by name or dataset name
- `ordering`: Order by field (`name`, `created`, `updated`)
- `page`: Page number for pagination
- `page_size`: Number of results per page

Response:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Total Population",
      "dataset": 1,
      "dataset_name": "Population Data",
      "universe": null,
      "universe_name": null,
      "groups": ["age", "gender"],
      "subindicator_count": 10,
      "created": "2023-01-01T00:00:00Z",
      "updated": "2023-01-02T00:00:00Z"
    }
  ]
}
```

### Create Indicator

Create a new indicator.

```http
POST /api/v2/indicators/
Content-Type: application/json

{
  "name": "Total Population",
  "dataset": 1,
  "universe": null,
  "groups": ["age", "gender"]
}
```

Response: 201 Created

### Get Indicator Detail

Get detailed information about a specific indicator.

```http
GET /api/v2/indicators/{id}/
```

Response:
```json
{
  "id": 1,
  "name": "Total Population",
  "dataset": 1,
  "dataset_name": "Population Data",
  "dataset_profile": "South Africa",
  "universe": null,
  "universe_detail": null,
  "groups": ["age", "gender"],
  "subindicators": ["0-14", "15-24", "25-34", ...],
  "data_count": 1000,
  "created": "2023-01-01T00:00:00Z",
  "updated": "2023-01-02T00:00:00Z"
}
```

### Update Indicator

Update an existing indicator.

```http
PUT /api/v2/indicators/{id}/
Content-Type: application/json

{
  "name": "Updated Total Population",
  "dataset": 1,
  "universe": 1,
  "groups": ["age"]
}
```

Response: 200 OK

### Delete Indicator

Delete an indicator and all associated data.

```http
DELETE /api/v2/indicators/{id}/
```

Response: 204 No Content

### Recalculate Indicator Data

Trigger recalculation of indicator data from dataset data (async operation).

```http
POST /api/v2/indicators/{id}/recalculate/
```

Response:
```json
{
  "task_id": "xyz789-abc123",
  "indicator": { ... },
  "message": "Recalculation started successfully. Use the task_id to track progress."
}
```

### Get Indicator Data

Get the aggregated data rows for an indicator.

```http
GET /api/v2/indicators/{id}/data/
```

Query Parameters:
- `geography`: Filter by geography code
- `page`: Page number for pagination
- `page_size`: Number of results per page

Response:
```json
{
  "count": 100,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "indicator": 1,
      "indicator_name": "Total Population",
      "geography": 1,
      "geography_code": "ZA",
      "geography_name": "South Africa",
      "data": [
        {"age": "0-14", "gender": "male", "count": 5000000},
        {"age": "15-24", "gender": "male", "count": 4000000}
      ]
    }
  ]
}
```

### Refresh Subindicators

Refresh the list of subindicators for an indicator.

```http
POST /api/v2/indicators/{id}/refresh_subindicators/
```

Response:
```json
{
  "message": "Subindicators refreshed successfully.",
  "indicator": { ... }
}
```

## Universes

### List Universes

Get a list of all universes (filters).

```http
GET /api/v2/universes/
```

Response:
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Adults Only",
      "filters": {"age__gte": "18"},
      "created": "2023-01-01T00:00:00Z",
      "updated": "2023-01-02T00:00:00Z"
    }
  ]
}
```

### Create Universe

```http
POST /api/v2/universes/
Content-Type: application/json

{
  "name": "Adults Only",
  "filters": {"age__gte": "18"}
}
```

### Get/Update/Delete Universe

Similar patterns to datasets and indicators.

## Task Management

### Get Task Status

Get the status of a background task.

```http
GET /api/v2/tasks/{task_id}/
```

Response:
```json
{
  "task_id": "abc123-def456",
  "status": "SUCCESS",
  "result": {
    "rows_processed": 10000,
    "errors": 0
  },
  "error": null,
  "created": "2023-01-01T00:00:00Z",
  "started": "2023-01-01T00:00:01Z",
  "completed": "2023-01-01T00:05:00Z"
}
```

Task Statuses:
- `PENDING`: Task is waiting to start
- `STARTED`: Task is currently running
- `PROGRESS`: Task is in progress (check `result.progress` for percentage)
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed (check `error` field)
- `REVOKED`: Task was cancelled

### List Recent Tasks

Get a list of recent tasks.

```http
GET /api/v2/tasks/
```

Query Parameters:
- `status`: Filter by status
- `limit`: Limit number of results (default: 50)

Response:
```json
[
  {
    "task_id": "abc123",
    "status": "SUCCESS",
    "task_name": "wazimap_ng.datasets.tasks.process_dataset_upload",
    "created": "2023-01-01T00:00:00Z",
    "started": "2023-01-01T00:00:01Z",
    "result": { ... }
  }
]
```

### Cancel Task

Cancel a running task.

```http
POST /api/v2/tasks/{task_id}/cancel/
```

Response:
```json
{
  "message": "Task abc123 has been cancelled.",
  "task_id": "abc123"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `202 Accepted`: Async operation started
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error Response Format:
```json
{
  "detail": "Error message here",
  "field_name": ["Field-specific error message"]
}
```

## Permissions

### Dataset Permissions

- **Superusers**: Full access to all datasets
- **Authenticated Users**:
  - Can view all public datasets
  - Can view/edit datasets for profiles they belong to
  - Can only create datasets for profiles they belong to

### Indicator Permissions

- Indicators follow the permissions of their parent dataset
- Users can only create indicators for datasets they have access to

## Best Practices

### File Upload

1. Validate file size and type before uploading
2. Use the download_template endpoint to get correct format
3. Monitor upload progress using the task_id
4. Handle errors from the task status endpoint

### CSV Format

The CSV file should have the following structure:

```csv
geography_code,age,gender,count
ZA,0-14,male,5000000
ZA,0-14,female,4800000
ZA,15-24,male,4000000
```

Required columns:
- `geography_code`: The code of the geography
- `count`: The numeric value
- Other columns become groups (categories)

### Pagination

All list endpoints support pagination:
- Default page size: 10
- Maximum page size: 100
- Use `page` and `page_size` query parameters

### Rate Limiting

API requests are rate-limited to prevent abuse. If you hit rate limits, you'll receive a 429 Too Many Requests response.

## Examples

### Complete Workflow: Creating and Populating a Dataset

```bash
# 1. Create a dataset
curl -X POST http://example.com/api/v2/datasets/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Population 2023",
    "profile": 1,
    "geography_hierarchy": 1,
    "permission_type": "private"
  }'

# Response: {"id": 10, ...}

# 2. Download template
curl -X GET http://example.com/api/v2/datasets/10/download_template/ \
  -H "Authorization: Token your_token" \
  -o template.csv

# 3. Fill in the template with data
# ... edit template.csv ...

# 4. Upload the data
curl -X POST http://example.com/api/v2/datasets/10/upload/ \
  -H "Authorization: Token your_token" \
  -F "file=@template.csv" \
  -F "overwrite=false" \
  -F "update_indicators=true"

# Response: {"task_id": "abc123", ...}

# 5. Check upload status
curl -X GET http://example.com/api/v2/tasks/abc123/ \
  -H "Authorization: Token your_token"

# 6. Create an indicator
curl -X POST http://example.com/api/v2/indicators/ \
  -H "Authorization: Token your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Population by Age and Gender",
    "dataset": 10,
    "groups": ["age", "gender"]
  }'

# Response: {"id": 20, ...}

# 7. Recalculate indicator data
curl -X POST http://example.com/api/v2/indicators/20/recalculate/ \
  -H "Authorization: Token your_token"

# Response: {"task_id": "xyz789", ...}
```

## Migration from API v1

The new API v2 provides several improvements over v1:

1. **Consistent RESTful design**: All resources follow standard REST patterns
2. **Better filtering and search**: All list endpoints support filtering, searching, and ordering
3. **Comprehensive task management**: Track and manage all background tasks
4. **Cleaner responses**: More consistent and predictable response formats
5. **Better permissions**: More granular and predictable permission system
6. **Progress tracking**: All long-running operations return task IDs for progress tracking

### Key Differences

| Feature | v1 | v2 |
|---------|----|----|
| Base URL | `/api/v1/` | `/api/v2/` |
| Task tracking | Limited | Comprehensive |
| Permissions | Basic | Granular |
| Filtering | Limited | Full support |
| Error messages | Inconsistent | Standardized |
| Documentation | Minimal | Complete |

Both APIs will be supported during the transition period.
