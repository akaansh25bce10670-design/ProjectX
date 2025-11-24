# **📄 README --- Lyrics Fetcher & Caching System**

## **📌 Project Title**

**Multi-Threaded Lyrics Fetcher with SQLite Caching**

## **📌 Overview of the Project**

This project is a Python-based system that fetches song lyrics from
online APIs, stores them in a local SQLite database, and uses
multi-threading to download multiple lyrics simultaneously.

The main goals of the project are: - Reduce repeated API calls by
caching lyrics locally. - Improve performance using worker threads. -
Provide a clean, consistent interface for managing lyrics retrieval.

## **📌 Features**

-   **Fetch song lyrics automatically**
-   **Cache lyrics using SQLite** to avoid duplicate downloads\
-   **Multi-threaded worker system** for parallel processing\
-   **Queue-based task management**\
-   **Fallback mechanism** when lyrics are unavailable\
-   **Graceful handling of errors and missing data**\
-   **Simple and easily extendable architecture**

## **📌 Technologies / Tools Used**

  Category              Tools / Technologies
  --------------------- ----------------------------------------------------
  **Language**          Python 3.x
  **Database**          SQLite3
  **Concurrency**       Python `threading` + `queue`
  **APIs**              Lyrics provider API (Genius / Lyrics.ovh / custom)
  **Other Libraries**   `requests`, `json`, `time`

## **📌 Steps to Install & Run the Project**

### **1. Install Python**

Install Python from:\
https://www.python.org/downloads/\
Ensure `sqlite3` is included.

### **2. Install required Python libraries**

``` bash
pip install requests
```

### **3. Clone or download the project**

``` bash
git clone https://github.com/your-repo/lyrics-fetcher.git
cd lyrics-fetcher
```

### **4. Run the program**

``` bash
python main.py
```

## **📌 Instructions for Testing**

### **✔ Test 1 --- Fetch a new lyric**

-   Search a song not in the database\
-   Should fetch from API and save to DB

### **✔ Test 2 --- Fetch a cached lyric**

-   Search the same song again\
-   Should return from CACHE instantly

### **✔ Test 3 --- Multi-threading**

-   Add multiple artist/title pairs\
-   Observe parallel processing

### **✔ Test 4 --- Error handling**

-   Search for a non-existent song\
-   Should gracefully return "Lyrics not found"

