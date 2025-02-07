# RESTFUL service 
## Introduction
This project is a RESTful URL shortening service implemented using the Flask framework. It provides URL mapping management features, including:

- Short URL Generation: Uses Base62 encoding to generate unique and as short as possible IDs.
- URL Validation: Employs regular expressions to ensure the input URL format is correct.
- Basic API Operations: Supports creating, retrieving, updating, and deleting short URLs.

## Installation & setup
1. Installation of dependencies
``` bash
 pip install flask
 ```

2. run the service
```bash
python main.py
```
The server runs on `http://127.0.0.1:8000`.

## API Endpoints

| **Path & Method**  | **Parameters**                          | **Return Value (HTTP Code, Response)** |
|--------------------|----------------------------------|--------------------------------|
| `/:id` **GET**     | `:id` - Unique identifier of a URL | `301, Redirect to original URL` <br> `404, "Short URL not found"` |
| `/:id` **PUT**     | `:id` - Unique identifier of a URL | `200, "Updated successfully"` <br> `400, "Invalid URL format"` <br> `404, "Short URL not found"` |
| `/:id` **DELETE**  | `:id` - Unique identifier of a URL | `204, No Content` <br> `404, "Short URL not found"` |
| `/` **GET**        | *(No parameters)*                 | `200, { "id1": "url1", "id2": "url2" }` |
| `/` **POST**       | `:url` - URL to shorten           | `201, { "id": "short_id" }` <br> `400, "Invalid URL format"` |
| `/` **DELETE**     | *(No parameters)*                 | `404, "Invalid operation"` |


## Design & Implementation
### **1. Short URL Generation**
- Uses **Base62 encoding** (`0-9, a-z, A-Z` = 62 characters) for shorter, readable IDs.
- Implements a **ID** to ensure unique ID generation.
- Uses **offset `F = 100000`** to avoid extremely short IDs.
- **Encoding function:**
  ```python
  def encode(num):
      char = string.digits + string.ascii_lowercase + string.ascii_uppercase
      base = len(char)
      num += F  # Offset for length consistency
      result = []
      while num:
          result.append(char[num % base])
          num //= base
      return ''.join(reversed(result))
  ```

### **2. URL Validation**
- Uses **regular expressions (regex)** to ensure only valid URLs are stored.
- **Validation function:**
  ```python
  def validation(url):
      regex = r'^(https?://)(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})(:\d+)?(/\S*)?$'
      return re.match(regex, url) is not None
  ```
