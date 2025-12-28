---
description: how to run the SignLearn application
---

To run the SignLearn application, follow these steps:

1. **Install Dependencies**:
   Open a terminal in the project root and run:
   ```powershell
   python -m pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Ensure your `.env` file contains the correct MongoDB URI:
   ```env
   MONGODB_URI=mongodb+srv://...
   MONGODB_DB=signlearn
   ```

// turbo
3. **Start the Server**:
   Run the Flask application:
   ```powershell
   python app.py
   ```

4. **Access the App**:
   Open your browser and navigate to:
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

---
> [!TIP]
> On the first run, the system will automatically create the collections in MongoDB and set up the admin account.
