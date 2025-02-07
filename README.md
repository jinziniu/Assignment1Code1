# RESTFUL service 
## Introduction
This project is a RESTful URL shortening service implemented using the Flask framework. It provides URL mapping management features, including:

- Short URL Generation: Uses Base62 encoding to generate unique and as short as possible IDs.
- URL Validation: Employs regular expressions to ensure the input URL format is correct.
- Basic API Operations: Supports creating, retrieving, updating, and deleting short URLs.

## Installation & setup
1. Install

2. Installation of dependencies
``` bash
 pip install flask
 ```

4. run the service
```bash
python main.py
```
The server runs on `http://127.0.0.1:8000`.

## Design & Implementation
### **1. Short URL Generation**
- Uses **Base62 encoding** (`0-9, a-z, A-Z` = 62 characters) for shorter, readable IDs.
- Implements a **global counter** to ensure unique ID generation.
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
