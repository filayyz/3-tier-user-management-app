# Backend API Architecture

## **3-Tier Architecture**

**Tier 1: Presentation (Web UI)** → HTML templates served by Flask  
**Tier 2: Application (API Logic)** → Flask routes and business logic  
**Tier 3: Data (Database)** → SQLite/Cloud SQL with abstraction layer

---

## **Core Components**

### **1. Database Layer (db.py)**
- Abstracts database connections (SQLite or Cloud SQL)
- SQLiteConnection wrapper converts MySQL-style `%s` placeholders to SQLite's `?`
- Supports multiple connection modes via environment variables

### **2. Initialization**
- `ensure_db()`: Runs before first request to create the `user` table
- `init_db()`: Creates table with fields: id, name, email, Address, phonenumber, password
- Handles both SQLite (AUTOINCREMENT) and MySQL (AUTO_INCREMENT) syntax

### **3. Security**
- Passwords hashed with bcrypt before storage
- Never returns password field in API responses
- Uses parameterized queries to prevent SQL injection

---

## **REST API Endpoints**

### **GET /api/users**
- Returns all users as JSON array
- Excludes password field
- Orders by ID

**Response:**
```json
{"users": [{"id": 1, "name": "John", "email": "john@example.com", "address": "123 St", "phonenumber": "555-0100"}]}
```

### **GET /api/users/<id>**
- Returns single user by ID
- Returns 404 if not found

**Response:**
```json
{"id": 1, "name": "John", "email": "john@example.com", "address": "123 St", "phonenumber": "555-0100"}
```

### **POST /api/users**
- Creates new user from JSON body
- Validates required fields: name, email, address, phonenumber, password
- Hashes password with bcrypt
- Returns created user with 201 status

**Request:**
```json
{"name": "John", "email": "john@example.com", "address": "123 St", "phonenumber": "555-0100", "password": "secret"}
```

### **DELETE /api/users/<id>**
- Deletes user by ID
- Returns 404 if user doesn't exist
- Returns success message with 200 status

---

## **Web Routes (UI)**

- **/** - Add user form
- **/submit** - Processes form submission, hashes password, inserts to DB
- **/get-data** - Lookup user by ID form
- **/users** - Lists all users (fetches via API)
- **/delete/<id>** - Confirmation page for deletion

---

## **Database Connection Pattern**

Each request:
1. Opens new connection via `get_db()`
2. Creates cursor
3. Executes query with parameterized values
4. Commits if writing
5. Closes cursor and connection in `finally` block

This ensures no connection leaks and thread safety.

---

## **Deployment**

- **Local**: SQLite with `USE_SQLITE=1`
- **Cloud Run**: SQLite in `/tmp` (ephemeral storage)
- **Production option**: Cloud SQL by setting `INSTANCE_CONNECTION_NAME`
