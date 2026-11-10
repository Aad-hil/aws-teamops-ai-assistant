# SOP: CSV Encoding and Processing Failures

Project: customer-ingestion
Team: data-engineering
Environment: synthetic AWS demonstration

## Implementation facts
The current processor reads S3 object bytes with `decode("utf-8-sig")`, then parses CSV using Python `csv.DictReader`. It requires the exact headers `customer_id`, `name`, `email`. On a successful parse, it writes a CSV using `csv.DictWriter` to `processed/<execution_id>.csv`.

## Common failure patterns
- **UnicodeDecodeError:** object contains bytes that are not valid UTF-8. `utf-8-sig` accepts a UTF-8 BOM but does not support arbitrary legacy encodings such as Windows-1252.
- **Header mismatch:** the input file uses unexpected column names, leading/trailing spaces, or differing case; this results in `SCHEMA_MISMATCH`.
- **CSV irregularities:** rows with more fields than the header can introduce a `None` dictionary key, which may cause `csv.DictWriter` to fail when rewriting. Inspect the actual error; not every malformed CSV is rejected consistently.
- **Empty file:** lacks a header and therefore fails required-header validation.
- **Header-only CSV:** valid required headers with zero data rows can succeed with `record_count=0`. This may be unexpected but is not necessarily a processing exception.

## Safe investigation
1. Record the exact FAILED execution ID, source key, and sanitized error text from Diagnostics.
2. Examine the original object format and header using an authorized, read-only workflow. Avoid downloading real personal customer data into uncontrolled machines.
3. Compare encoding and column count with the expected UTF-8 CSV format.
4. Fix the upstream export in a test environment and verify parsing before proposing a new upload.

## Verification
After authorized upload of a uniquely named corrected object under `input/`, confirm the new execution is SUCCEEDED, row count matches expectations, and a matching `processed/<execution_id>.csv` exists.

## Boundaries
This demo does not enforce full data schema types, email syntax, uniqueness, or business rules. Treat 'SUCCEEDED' as successful handling by this processor, not proof of complete data quality.
